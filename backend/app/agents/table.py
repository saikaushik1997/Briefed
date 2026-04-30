import time
import json
import litellm
from langchain_core.messages import HumanMessage
from ..state import PipelineState
from ..tools.mlflow_logger import log_stage
from ..tools.pdf_parser import extract_tables_from_pages
from ..tools.llm import agent_trace, get_model, extract_usage

TABLE_PROMPT = """\
You are analyzing a table extracted from a document.

Table data (rows, first row is usually the header):
{table_data}

Surrounding context (text near this table on the page):
{context}

Return JSON only, no markdown:
{{
  "title": "descriptive title for this table",
  "interpretation": "what this table shows, what the key figures mean, and any notable patterns or takeaways"
}}

Be specific — reference actual values from the table in your interpretation.\
"""


def _format_table(data: list) -> str:
    if not data:
        return "(empty table)"
    rows = []
    for row in data[:20]:  # cap at 20 rows to stay within token limits
        rows.append(" | ".join(str(cell or "").strip() for cell in row))
    return "\n".join(rows)


@agent_trace("table_agent")
async def run(state: PipelineState) -> PipelineState:
    start = time.time()
    document_id = state["document_id"]
    pdf_path = state["pdf_path"]
    config = state.get("config", {})
    model_name = config.get("table_model", "gpt-4o-mini")

    table_pages = [
        p["page"] for p in state["page_classifications"]
        if "table" in p.get("content_types", [])
    ]

    raw_tables = extract_tables_from_pages(pdf_path, table_pages)

    # Get surrounding text for context
    from ..tools.pdf_parser import extract_text_from_pages
    context_text = extract_text_from_pages(pdf_path, table_pages)[:2000]

    interpreted_tables = []
    total_tokens_in = total_tokens_out = 0
    total_cost = 0.0

    if raw_tables:
        llm = get_model(model_name, temperature=0, max_tokens=512)

        for t in raw_tables:
            formatted = _format_table(t["data"])
            response = await llm.ainvoke([
                HumanMessage(content=TABLE_PROMPT.format(
                    table_data=formatted,
                    context=context_text,
                ))
            ])

            usage = extract_usage(response)
            total_tokens_in += usage["input_tokens"]
            total_tokens_out += usage["output_tokens"]

            try:
                total_cost += litellm.completion_cost(
                    model=model_name,
                    prompt=formatted,
                    completion=response.content,
                )
            except Exception:
                pass

            raw = response.content.strip()
            try:
                if raw.startswith("```"):
                    raw = raw.split("```")[1].lstrip("json").strip()
                parsed = json.loads(raw)
                title = parsed.get("title", f"Table {t['table_index'] + 1}")
                interpretation = parsed.get("interpretation", "")
            except (json.JSONDecodeError, KeyError):
                title = f"Table {t['table_index'] + 1}"
                interpretation = raw

            interpreted_tables.append({
                "page": t["page"],
                "table_index": t["table_index"],
                "data": t["data"],
                "title": title,
                "interpretation": interpretation,
            })

    latency = time.time() - start

    await log_stage(
        document_id,
        "table",
        model_used=model_name if raw_tables else "",
        tokens_in=total_tokens_in,
        tokens_out=total_tokens_out,
        cost=total_cost,
        latency=latency,
    )

    return {
        **state,
        "table_result": {
            "pages": table_pages,
            "tables": interpreted_tables,
        },
    }
