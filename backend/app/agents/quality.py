import time
import json
import uuid
import litellm
from langchain_core.messages import HumanMessage
from ..state import PipelineState
from ..tools.mlflow_logger import log_stage, log_quality
from ..tools.llm import agent_trace, get_model, extract_usage

JUDGE_PROMPT = """\
You are a faithfulness judge. Your job is to check whether a plain language explanation accurately reflects what the source document actually says.

SOURCE DOCUMENT (raw extracted text):
{source}

EXPLANATION TO EVALUATE:
{explanation}

Evaluate the explanation for faithfulness — does it only claim things that are supported by the source?

Return JSON only, no markdown:
{{
  "score": 0.0,
  "faithful_claims": ["claims in the explanation that are supported by the source"],
  "unfaithful_claims": ["claims in the explanation that contradict or go beyond the source"],
  "missing_from_explanation": ["important facts in the source that the explanation omits"]
}}

score is a float from 0.0 to 1.0:
- 1.0 = every claim is supported, nothing important omitted
- 0.0 = explanation is entirely unsupported or fabricated
Be precise. Quote or paraphrase specific text when listing claims.\
"""


@agent_trace("quality_agent")
async def run(state: PipelineState) -> PipelineState:
    start = time.time()
    document_id = state["document_id"]
    config = state.get("config", {})
    judge_model = config.get("judge_model", "gpt-4o-mini")

    synthesis = state.get("synthesis_result") or {}
    plain_explanation = synthesis.get("plain_explanation", "")

    # Source = raw text extracted by text agent (ground truth)
    source_text = (state.get("text_result") or {}).get("raw_text", "")

    score = 0.0
    faithful_claims = []
    unfaithful_claims = []
    missing = []
    tokens_in = tokens_out = 0
    cost = 0.0

    if plain_explanation and source_text:
        llm = get_model(judge_model, temperature=0, max_tokens=1024)
        from ..tools.prompt_registry import load_prompt, render_prompt
        template = load_prompt("briefed-judge", JUDGE_PROMPT)
        response = await llm.ainvoke([
            HumanMessage(content=render_prompt(template, source=source_text[:4000], explanation=plain_explanation))
        ])

        usage = extract_usage(response)
        tokens_in = usage["input_tokens"]
        tokens_out = usage["output_tokens"]

        try:
            cost = litellm.completion_cost(
                model=judge_model,
                prompt=source_text[:4000],
                completion=response.content,
            )
        except Exception:
            pass

        raw = response.content.strip()
        try:
            if raw.startswith("```"):
                raw = raw.split("```")[1].lstrip("json").strip()
            parsed = json.loads(raw)
            score = float(parsed.get("score", 0.0))
            faithful_claims = parsed.get("faithful_claims", [])
            unfaithful_claims = parsed.get("unfaithful_claims", [])
            missing = parsed.get("missing_from_explanation", [])
        except (json.JSONDecodeError, ValueError, KeyError):
            pass

    quality_detail = {
        "score": score,
        "faithful_claims": faithful_claims,
        "unfaithful_claims": unfaithful_claims,
        "missing_from_explanation": missing,
        "judge_model": judge_model,
    }

    # Persist quality detail + score to DB
    from ..database import AsyncSessionLocal
    from ..models import Document, Result
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # Update Result with quality detail
        result_row = await db.execute(
            select(Result).where(Result.document_id == uuid.UUID(document_id))
        )
        result = result_row.scalar_one_or_none()
        if result:
            result.quality_detail = quality_detail

        # Update Document quality score
        doc_row = await db.execute(
            select(Document).where(Document.id == uuid.UUID(document_id))
        )
        doc = doc_row.scalar_one_or_none()
        if doc:
            doc.quality_score = score

        await db.commit()

    latency = time.time() - start

    await log_stage(
        document_id,
        "quality",
        model_used=judge_model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost=cost,
        latency=latency,
    )
    await log_quality(document_id, score)

    return {
        **state,
        "quality_result": quality_detail,
    }
