import time
import json
import base64
import litellm
from langchain_core.messages import HumanMessage
from ..state import PipelineState
from ..tools.mlflow_logger import log_stage
from ..tools.pdf_parser import render_page_as_image
from ..tools.llm import agent_trace, get_model, extract_usage

CHART_PROMPT = """\
You are analyzing a chart or figure from a document page.

Describe what the chart shows and extract the key insight.

Return JSON only, no markdown:
{{
  "description": "chart type, what axes/categories represent, and the data shown",
  "insight": "the key trend, pattern, or takeaway — be specific about values if visible"
}}

If this page contains no meaningful chart (just text or a logo), return:
{{"description": "", "insight": ""}}\
"""


def _image_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


@agent_trace("chart_agent")
async def run(state: PipelineState) -> PipelineState:
    start = time.time()
    document_id = state["document_id"]
    pdf_path = state["pdf_path"]
    config = state.get("config", {})

    # Primary A/B testing target — model comes from config bundle
    model_name = config.get("chart_model", "gpt-4o")

    chart_pages = [
        p["page"] for p in state["page_classifications"]
        if "chart" in p.get("content_types", [])
    ]

    charts = []
    total_tokens_in = total_tokens_out = 0
    total_cost = 0.0

    if chart_pages:
        llm = get_model(model_name, temperature=0, max_tokens=512)

        for page_num in chart_pages:
            try:
                image_bytes = render_page_as_image(pdf_path, page_num, dpi=150)
            except Exception:
                continue

            image_b64 = _image_to_base64(image_bytes)

            response = await llm.ainvoke([
                HumanMessage(content=[
                    {"type": "text", "text": CHART_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ])
            ])

            usage = extract_usage(response)
            total_tokens_in += usage["input_tokens"]
            total_tokens_out += usage["output_tokens"]

            try:
                total_cost += litellm.completion_cost(
                    model=model_name,
                    prompt=CHART_PROMPT,
                    completion=response.content,
                )
            except Exception:
                pass

            raw = response.content.strip()
            try:
                if raw.startswith("```"):
                    raw = raw.split("```")[1].lstrip("json").strip()
                parsed = json.loads(raw)
                description = parsed.get("description", "")
                insight = parsed.get("insight", "")
            except (json.JSONDecodeError, KeyError):
                description = raw
                insight = ""

            # Only include if the model found an actual chart
            if description:
                charts.append({
                    "page": page_num,
                    "description": description,
                    "insight": insight,
                    "model_used": model_name,
                })

    latency = time.time() - start

    await log_stage(
        document_id,
        "chart",
        model_used=model_name if chart_pages else "",
        tokens_in=total_tokens_in,
        tokens_out=total_tokens_out,
        cost=total_cost,
        latency=latency,
        experiment_tag=config.get("experiment_tag", ""),
    )

    return {
        **state,
        "chart_result": {
            "pages": chart_pages,
            "charts": charts,
        },
    }
