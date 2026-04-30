import uuid
from typing import Optional


async def emit(
    document_id: str,
    stage: str,
    decision_type: str,
    choice_made: str,
    alternatives: Optional[list] = None,
    rationale: str = "",
    cost_impact: float = 0.0,
):
    """
    Persists a pipeline decision to the decisions table.
    Called by agents before executing their chosen path so the decision
    trace populates in real time as the pipeline runs.

    decision_type: routing | model_selection | method_selection | skip
    cost_impact: estimated $ saved (negative) or added vs default
    """
    from ..database import AsyncSessionLocal
    from ..models import Decision

    async with AsyncSessionLocal() as db:
        decision = Decision(
            id=uuid.uuid4(),
            document_id=uuid.UUID(document_id),
            stage=stage,
            decision_type=decision_type,
            choice_made=choice_made,
            alternatives_considered=alternatives or [],
            rationale=rationale,
            cost_impact=cost_impact,
        )
        db.add(decision)
        await db.commit()
