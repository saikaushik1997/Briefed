import uuid
from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from .agents import classifier, text, table, chart, synthesis, quality
from .tools.mlflow_logger import pipeline_run


class PageClassification(TypedDict):
    page: int
    content_types: List[str]  # text, table, chart
    has_ocr_needed: bool


class PipelineState(TypedDict):
    document_id: str
    pdf_path: str
    config: dict
    page_classifications: List[PageClassification]
    text_result: Optional[dict]
    table_result: Optional[dict]
    chart_result: Optional[dict]
    synthesis_result: Optional[dict]
    quality_result: Optional[dict]
    decisions: List[dict]
    errors: List[str]


def _route_after_classify(state: PipelineState) -> List[str]:
    """Fan out to whichever agents are needed based on classifier output."""
    pages = state.get("page_classifications", [])
    needed = set()
    for page in pages:
        for content_type in page.get("content_types", []):
            needed.add(content_type)

    routes = []
    if "text" in needed:
        routes.append("text_extract")
    if "table" in needed:
        routes.append("table_extract")
    if "chart" in needed:
        routes.append("chart_extract")

    # If nothing detected (empty doc), go straight to synthesis
    return routes or ["synthesize"]


def _all_extractions_done(state: PipelineState) -> str:
    """Called after each extraction node — only proceeds to synthesis when all are done."""
    pages = state.get("page_classifications", [])
    needed = set()
    for page in pages:
        for ct in page.get("content_types", []):
            needed.add(ct)

    text_done = "text" not in needed or state.get("text_result") is not None
    table_done = "table" not in needed or state.get("table_result") is not None
    chart_done = "chart" not in needed or state.get("chart_result") is not None

    if text_done and table_done and chart_done:
        return "synthesize"
    return "wait"


def build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("classify", classifier.run)
    graph.add_node("text_extract", text.run)
    graph.add_node("table_extract", table.run)
    graph.add_node("chart_extract", chart.run)
    graph.add_node("synthesize", synthesis.run)
    graph.add_node("score_quality", quality.run)

    graph.set_entry_point("classify")

    graph.add_conditional_edges(
        "classify",
        _route_after_classify,
        {
            "text_extract": "text_extract",
            "table_extract": "table_extract",
            "chart_extract": "chart_extract",
            "synthesize": "synthesize",
        },
    )

    for extraction_node in ["text_extract", "table_extract", "chart_extract"]:
        graph.add_conditional_edges(
            extraction_node,
            _all_extractions_done,
            {"synthesize": "synthesize", "wait": END},
        )

    graph.add_edge("synthesize", "score_quality")
    graph.add_edge("score_quality", END)

    return graph.compile()


_graph = build_graph()


async def run_graph(document_id: str, pdf_path: str):
    from .tools.mlflow_logger import start_run, end_run
    from .database import AsyncSessionLocal
    from .models import Document
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document).where(Document.id == uuid.UUID(document_id)))
        doc = result.scalar_one_or_none()
        if not doc:
            return

        doc.status = "processing"
        await db.commit()

    mlflow_run_id = await start_run(document_id)

    initial_state: PipelineState = {
        "document_id": document_id,
        "pdf_path": pdf_path,
        "config": {},  # loaded from MLflow Registry in each agent
        "page_classifications": [],
        "text_result": None,
        "table_result": None,
        "chart_result": None,
        "synthesis_result": None,
        "quality_result": None,
        "decisions": [],
        "errors": [],
    }

    try:
        await _graph.ainvoke(initial_state)
        await end_run(mlflow_run_id, status="FINISHED")
    except Exception as e:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Document).where(Document.id == uuid.UUID(document_id)))
            doc = result.scalar_one_or_none()
            if doc:
                doc.status = "failed"
                await db.commit()
        await end_run(mlflow_run_id, status="FAILED")
        raise
