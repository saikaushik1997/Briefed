from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Integer
from ..database import get_db
from ..models import Document

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            func.count(Document.id).label("total_documents"),
            func.avg(Document.total_cost).label("avg_cost"),
            func.avg(Document.total_latency).label("avg_latency"),
            func.avg(Document.quality_score).label("avg_quality"),
            func.sum(cast(Document.cache_hit, Integer)).label("cache_hits"),
        ).where(Document.status == "complete")
    )
    row = result.one()

    total = row.total_documents or 0
    cache_hits = int(row.cache_hits or 0)

    return {
        "total_documents": total,
        "avg_cost": round(row.avg_cost or 0.0, 4),
        "avg_latency": round(row.avg_latency or 0.0, 2),
        "avg_quality": round(row.avg_quality or 0.0, 3),
        "cache_hit_rate": round(cache_hits / total, 3) if total > 0 else 0.0,
    }
