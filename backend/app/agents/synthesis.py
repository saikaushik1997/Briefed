import time
import json
import uuid
import litellm
from langchain_core.messages import HumanMessage
from ..state import PipelineState
from ..tools.mlflow_logger import log_stage
from ..tools.llm import agent_trace, get_model, extract_usage

SYNTHESIS_PROMPT = """\
You are synthesizing extracted content from a document into a structured analysis.

--- EXTRACTED CONTENT ---
{context}
-------------------------

Return JSON only, no markdown:
{{
  "summary": "2-3 sentence overview of what this document is and its main point",
  "plain_explanation": "A clear, plain language explanation of the document's content and significance. Write as if explaining to someone unfamiliar with the topic. 3-5 sentences.",
  "key_metrics": {{
    "metric name": "value with units"
  }},
  "tables": [
    {{
      "title": "table title or description",
      "interpretation": "what this table shows and why it matters"
    }}
  ],
  "charts": [
    {{
      "description": "what the chart shows",
      "insight": "the key trend or takeaway"
    }}
  ]
}}

key_metrics should only include concrete numbers, dates, or named facts from the document.
If there are no tables or charts, return empty arrays.\
"""


def _build_context(state: PipelineState) -> str:
    parts = []

    text = state.get("text_result") or {}
    if text.get("summary"):
        parts.append(f"TEXT SUMMARY:\n{text['summary']}")
    if text.get("key_facts"):
        parts.append("KEY FACTS:\n" + "\n".join(f"- {f}" for f in text["key_facts"]))
    if text.get("raw_text"):
        parts.append(f"RAW TEXT (first 3000 chars):\n{text['raw_text'][:3000]}")

    tables = (state.get("table_result") or {}).get("tables", [])
    for i, t in enumerate(tables):
        rows = t.get("data", [])
        preview = "\n".join(str(r) for r in rows[:5])
        parts.append(f"TABLE {i+1} (page {t.get('page', '?')}):\n{preview}")

    charts = (state.get("chart_result") or {}).get("charts", [])
    for i, c in enumerate(charts):
        parts.append(f"CHART {i+1}:\nDescription: {c.get('description', '')}\nInsight: {c.get('insight', '')}")

    return "\n\n".join(parts) or "No content extracted."


@agent_trace("synthesis_agent")
async def run(state: PipelineState) -> PipelineState:
    start = time.time()
    document_id = state["document_id"]
    config = state.get("config", {})
    model_name = config.get("synthesis_model", "gpt-4o-mini")

    context = _build_context(state)
    llm = get_model(model_name, temperature=0, max_tokens=2048)
    from ..tools.prompt_registry import load_prompt, render_prompt
    template = load_prompt("briefed-synthesis", SYNTHESIS_PROMPT)
    response = await llm.ainvoke([
        HumanMessage(content=render_prompt(template, context=context))
    ])

    usage = extract_usage(response)
    cost = 0.0
    try:
        cost = litellm.completion_cost(
            model=model_name,
            prompt=context,
            completion=response.content,
        )
    except Exception:
        pass

    raw = response.content.strip()
    try:
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        parsed = json.loads(raw)
    except (json.JSONDecodeError, KeyError):
        parsed = {}

    summary = parsed.get("summary", "")
    plain_explanation = parsed.get("plain_explanation", "")
    key_metrics = parsed.get("key_metrics", {})
    tables = parsed.get("tables", [])
    charts = parsed.get("charts", [])

    structured_json = {
        "summary": summary,
        "tables": tables,
        "charts": charts,
    }

    # Persist to DB
    from ..database import AsyncSessionLocal
    from ..models import Document, Result
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result_row = Result(
            id=uuid.uuid4(),
            document_id=uuid.UUID(document_id),
            structured_json=structured_json,
            plain_explanation=plain_explanation,
            key_metrics=key_metrics,
        )
        db.add(result_row)

        # Update table/chart counts on the document
        doc_result = await db.execute(
            select(Document).where(Document.id == uuid.UUID(document_id))
        )
        doc = doc_result.scalar_one_or_none()
        if doc:
            doc.table_count = len(tables)
            doc.chart_count = len(charts)

        await db.commit()

    latency = time.time() - start

    await log_stage(
        document_id,
        "synthesis",
        model_used=model_name,
        tokens_in=usage["input_tokens"],
        tokens_out=usage["output_tokens"],
        cost=cost,
        latency=latency,
    )

    return {
        **state,
        "synthesis_result": {
            "summary": summary,
            "plain_explanation": plain_explanation,
            "key_metrics": key_metrics,
            "tables": tables,
            "charts": charts,
        },
    }
