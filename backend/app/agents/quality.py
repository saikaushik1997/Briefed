import time
from ..graph import PipelineState
from ..tools.mlflow_logger import log_stage


async def run(state: PipelineState) -> PipelineState:
    """
    LLM-as-judge: checks whether the plain explanation is faithful to the
    source document. Returns a score + specific faithful/unfaithful claims.

    Output shape:
    {
        "score": 0.88,
        "faithful_claims": [...],
        "unfaithful_claims": [...],
        "missing_from_explanation": [...],
        "judge_model": "gpt-4o-mini"
    }
    """
    start = time.time()
    document_id = state["document_id"]
    config = state.get("config", {})
    judge_model = config.get("judge_model", "gpt-4o-mini")

    # TODO:
    # 1. Build judge prompt: source text vs plain_explanation
    # 2. Call LiteLLM with judge_model
    # 3. Parse structured quality output
    # 4. Persist quality_detail + quality_score to DB
    # 5. Log quality_score to MLflow

    latency = time.time() - start

    await log_stage(
        document_id,
        "quality",
        model_used=judge_model,
        latency=latency,
        cost=0.0,
    )

    return {
        **state,
        "quality_result": {
            "score": 0.0,
            "faithful_claims": [],
            "unfaithful_claims": [],
            "missing_from_explanation": [],
            "judge_model": judge_model,
        },
    }
