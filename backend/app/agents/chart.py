import time
from ..state import PipelineState
from ..tools.mlflow_logger import log_stage
from ..tools.llm import agent_trace


@agent_trace("chart_agent")
async def run(state: PipelineState) -> PipelineState:
    """
    Renders chart pages as images, passes to vision model via LiteLLM,
    then interprets the described chart with a second LLM call.

    Model is read from the active config bundle in MLflow Registry —
    swapping gpt-4o vs claude-3.5-sonnet requires no code change.
    """
    start = time.time()
    document_id = state["document_id"]
    config = state.get("config", {})

    chart_pages = [
        p["page"] for p in state["page_classifications"]
        if "chart" in p.get("content_types", [])
    ]

    # TODO:
    # 1. Render each chart page to PNG (pdf2image / pymupdf)
    # 2. Call LiteLLM vision model: config.get("chart_model", "gpt-4o")
    # 3. Call LiteLLM to interpret the description
    # 4. Emit Decision for model_selection
    # 5. Log tokens + cost (most expensive stage)

    latency = time.time() - start

    await log_stage(
        document_id,
        "chart",
        model_used=config.get("chart_model", "gpt-4o"),
        latency=latency,
        cost=0.0,
    )

    return {
        **state,
        "chart_result": {
            "pages": chart_pages,
            "charts": [],  # TODO: list of {description, insight}
        },
    }
