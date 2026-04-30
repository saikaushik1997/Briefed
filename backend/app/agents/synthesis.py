import time
from ..state import PipelineState
from ..tools.mlflow_logger import log_stage
from ..tools.llm import agent_trace


@agent_trace("synthesis_agent")
async def run(state: PipelineState) -> PipelineState:
    """
    Takes text, table, and chart outputs and produces:
    - structured JSON (key metrics, tables, charts)
    - plain language explanation
    Uses the synthesis model from the active config bundle.
    """
    start = time.time()
    document_id = state["document_id"]
    config = state.get("config", {})

    # TODO:
    # 1. Assemble context from text_result, table_result, chart_result
    # 2. Call LiteLLM: config.get("synthesis_model", "gpt-4o-mini")
    # 3. Parse structured JSON output
    # 4. Persist Result to DB

    latency = time.time() - start

    await log_stage(
        document_id,
        "synthesis",
        model_used=config.get("synthesis_model", "gpt-4o-mini"),
        latency=latency,
        cost=0.0,
    )

    return {
        **state,
        "synthesis_result": {
            "summary": "",            # TODO
            "key_metrics": {},        # TODO
            "tables": [],             # TODO
            "charts": [],             # TODO
            "plain_explanation": "",  # TODO
        },
    }
