import mlflow
from ..config import settings

mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
EXPERIMENT_NAME = "briefed-pipeline"

try:
    mlflow.set_experiment(EXPERIMENT_NAME)
except Exception:
    pass


async def start_run(document_id: str) -> str:
    run = mlflow.start_run(run_name=document_id, nested=False)
    mlflow.log_param("document_id", document_id)
    return run.info.run_id


async def end_run(run_id: str, status: str = "FINISHED"):
    mlflow.end_run(status=status)


async def log_stage(
    document_id: str,
    stage: str,
    model_used: str = "",
    tokens_in: int = 0,
    tokens_out: int = 0,
    cost: float = 0.0,
    latency: float = 0.0,
    experiment_tag: str = "",
):
    prefix = f"{stage}"
    mlflow.log_metric(f"{prefix}_latency", latency)
    mlflow.log_metric(f"{prefix}_cost", cost)
    mlflow.log_metric(f"{prefix}_tokens_in", tokens_in)
    mlflow.log_metric(f"{prefix}_tokens_out", tokens_out)

    if tokens_in > 0:
        mlflow.log_metric(f"{prefix}_token_efficiency", tokens_out / tokens_in)

    if model_used:
        mlflow.log_param(f"{prefix}_model", model_used)

    if experiment_tag:
        mlflow.set_tag(f"{prefix}_experiment", experiment_tag)

    # Persist to DB as well
    from ..database import AsyncSessionLocal
    from ..models import PipelineStage, Document
    from sqlalchemy import select
    import uuid

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(PipelineStage).where(
                PipelineStage.document_id == uuid.UUID(document_id),
                PipelineStage.stage == stage,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.status = "complete"
            existing.model_used = model_used
            existing.tokens_in = tokens_in
            existing.tokens_out = tokens_out
            existing.cost = cost
            existing.latency = latency
            existing.token_efficiency_ratio = (tokens_out / tokens_in) if tokens_in > 0 else None
            existing.experiment_tag = experiment_tag
        else:
            stage_row = PipelineStage(
                document_id=uuid.UUID(document_id),
                stage=stage,
                status="complete",
                model_used=model_used,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost=cost,
                latency=latency,
                token_efficiency_ratio=(tokens_out / tokens_in) if tokens_in > 0 else None,
                experiment_tag=experiment_tag,
            )
            db.add(stage_row)

        await db.commit()


async def log_quality(document_id: str, score: float):
    mlflow.log_metric("quality_score", score)


async def log_totals(document_id: str, total_cost: float, total_latency: float):
    mlflow.log_metric("total_cost", total_cost)
    mlflow.log_metric("total_latency", total_latency)
