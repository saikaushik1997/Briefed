import time
import litellm
from langchain_core.messages import HumanMessage
from ..state import PipelineState
from ..tools.mlflow_logger import log_stage
from ..tools.pdf_parser import extract_text_from_pages
from ..tools.llm import agent_trace, get_model, extract_usage
from ..tools.decisions import emit as emit_decision

TEXT_PROMPT = """\
You are analyzing extracted text from a document. Summarize the content clearly and extract any concrete facts, figures, or claims.

Extracted text:
{text}

Return JSON only, no markdown:
{{
  "summary": "concise summary of what this text covers",
  "key_facts": ["fact 1", "fact 2"]
}}

key_facts should be specific and concrete — numbers, dates, names, claims. Not generic observations.\
"""


@agent_trace("text_agent")
async def run(state: PipelineState) -> PipelineState:
    start = time.time()
    document_id = state["document_id"]
    pdf_path = state["pdf_path"]
    config = state.get("config", {})
    model_name = config.get("text_model", "gpt-4o-mini")

    text_pages = [
        p["page"] for p in state["page_classifications"]
        if "text" in p.get("content_types", [])
    ]

    raw_text = extract_text_from_pages(pdf_path, text_pages)

    summary = ""
    key_facts = []
    tokens_in = tokens_out = 0
    cost = 0.0

    await emit_decision(
        document_id=document_id,
        stage="text_agent",
        decision_type="model_selection",
        choice_made=model_name,
        alternatives=[{"option": "gpt-4o", "reason_rejected": "cost — gpt-4o-mini sufficient for text summarization"}],
        rationale="Text summarization does not require a large model",
        cost_impact=0.0,
    )

    if raw_text.strip():
        llm = get_model(model_name, temperature=0, max_tokens=1024)
        response = await llm.ainvoke([
            HumanMessage(content=TEXT_PROMPT.format(text=raw_text[:6000]))
        ])

        usage = extract_usage(response)
        tokens_in = usage["input_tokens"]
        tokens_out = usage["output_tokens"]

        try:
            cost = litellm.completion_cost(
                model=model_name,
                prompt=raw_text[:6000],
                completion=response.content,
            )
        except Exception:
            pass

        import json
        raw = response.content.strip()
        try:
            if raw.startswith("```"):
                raw = raw.split("```")[1].lstrip("json").strip()
            parsed = json.loads(raw)
            summary = parsed.get("summary", "")
            key_facts = parsed.get("key_facts", [])
        except (json.JSONDecodeError, KeyError):
            summary = raw
            key_facts = []

    latency = time.time() - start

    await log_stage(
        document_id,
        "text",
        model_used=model_name,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost=cost,
        latency=latency,
    )

    return {
        **state,
        "text_result": {
            "pages": text_pages,
            "raw_text": raw_text,
            "summary": summary,
            "key_facts": key_facts,
        },
    }
