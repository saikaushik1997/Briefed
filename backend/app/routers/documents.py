import uuid
import hashlib
import os
import time
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from ..database import get_db
from ..models import Document, PipelineStage, Result, Decision

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _hash_file(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    file_hash = _hash_file(content)

    # Check document-level cache
    cached = await db.execute(
        select(Document).where(
            Document.storage_path.contains(file_hash),
            Document.status == "complete",
        )
    )
    cached_doc = cached.scalar_one_or_none()
    if cached_doc:
        return {
            "document_id": str(cached_doc.id),
            "status": "complete",
            "cache_hit": True,
        }

    # Save file locally (swap for R2 upload in production)
    storage_path = os.path.join(UPLOAD_DIR, f"{file_hash}.pdf")
    if not os.path.exists(storage_path):
        with open(storage_path, "wb") as f:
            f.write(content)

    doc = Document(
        id=uuid.uuid4(),
        filename=file.filename,
        storage_path=storage_path,
        status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(run_pipeline, str(doc.id), storage_path)

    return {"document_id": str(doc.id), "status": "pending", "cache_hit": False}


@router.get("")
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).order_by(desc(Document.created_at))
    )
    docs = result.scalars().all()
    return [_doc_summary(d) for d in docs]


@router.get("/{document_id}")
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document)
        .where(Document.id == uuid.UUID(document_id))
        .options(
            selectinload(Document.stages),
            selectinload(Document.result),
            selectinload(Document.decisions),
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return _doc_detail(doc)


def _doc_summary(doc: Document) -> dict:
    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "status": doc.status,
        "page_count": doc.page_count,
        "table_count": doc.table_count,
        "chart_count": doc.chart_count,
        "total_cost": doc.total_cost,
        "total_latency": doc.total_latency,
        "quality_score": doc.quality_score,
        "cache_hit": doc.cache_hit,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


def _doc_detail(doc: Document) -> dict:
    base = _doc_summary(doc)
    base["stages"] = [
        {
            "stage": s.stage,
            "status": s.status,
            "model_used": s.model_used,
            "tokens_in": s.tokens_in,
            "tokens_out": s.tokens_out,
            "cost": s.cost,
            "latency": s.latency,
            "token_efficiency_ratio": s.token_efficiency_ratio,
            "experiment_tag": s.experiment_tag,
        }
        for s in doc.stages
    ]
    base["decisions"] = [
        {
            "stage": d.stage,
            "decision_type": d.decision_type,
            "choice_made": d.choice_made,
            "alternatives_considered": d.alternatives_considered,
            "rationale": d.rationale,
            "cost_impact": d.cost_impact,
        }
        for d in doc.decisions
    ]
    if doc.result:
        base["result"] = {
            "structured_json": doc.result.structured_json,
            "plain_explanation": doc.result.plain_explanation,
            "key_metrics": doc.result.key_metrics,
            "quality_detail": doc.result.quality_detail,
        }
    return base


async def run_pipeline(document_id: str, pdf_path: str):
    # Imported here to avoid circular import at module load
    from ..graph import run_graph
    await run_graph(document_id, pdf_path)
