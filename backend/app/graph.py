import uuid
from langgraph.graph import StateGraph, END

from .state import PipelineState
from .agents import classifier, text, table, chart, synthesis, quality


def _needed_agents(state: PipelineState) -> set:
    needed = set()
    for page in state.get("page_classifications", []):
        for ct in page.get("content_types", []):
            needed.add(ct)
    return needed


def _route_after_classify(state: PipelineState) -> str:
    needed = _needed_agents(state)
    if "text" in needed:
        return "text_extract"
    if "table" in needed:
        return "table_extract"
    if "chart" in needed:
        return "chart_extract"
    return "synthesize"


def _route_after_text(state: PipelineState) -> str:
    needed = _needed_agents(state)
    if "table" in needed:
        return "table_extract"
    if "chart" in needed:
        return "chart_extract"
    return "synthesize"


def _route_after_table(state: PipelineState) -> str:
    needed = _needed_agents(state)
    if "chart" in needed:
        return "chart_extract"
    return "synthesize"


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
    graph.add_conditional_edges(
        "text_extract",
        _route_after_text,
        {
            "table_extract": "table_extract",
            "chart_extract": "chart_extract",
            "synthesize": "synthesize",
        },
    )
    graph.add_conditional_edges(
        "table_extract",
        _route_after_table,
        {
            "chart_extract": "chart_extract",
            "synthesize": "synthesize",
        },
    )

    graph.add_edge("chart_extract", "synthesize")
    graph.add_edge("synthesize", "score_quality")
    graph.add_edge("score_quality", END)

    return graph.compile()


_graph = build_graph()


async def run_graph(document_id: str, pdf_path: str):
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

    from .tools.mlflow_logger import start_run, end_run, log_totals

    mlflow_run_id = await start_run(document_id)

    initial_state: PipelineState = {
        "document_id": document_id,
        "pdf_path": pdf_path,
        "config": {},
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
        final_state = await _graph.ainvoke(initial_state)

        # Roll up totals from all stages and mark complete
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Document).where(Document.id == uuid.UUID(document_id))
            )
            doc = result.scalar_one_or_none()
            if doc:
                from sqlalchemy import select as sa_select
                from .models import PipelineStage
                stages_result = await db.execute(
                    sa_select(PipelineStage).where(PipelineStage.document_id == uuid.UUID(document_id))
                )
                stages = stages_result.scalars().all()
                doc.total_cost = sum(s.cost or 0 for s in stages)
                doc.total_latency = sum(s.latency or 0 for s in stages)
                doc.quality_score = (
                    final_state.get("quality_result", {}) or {}
                ).get("score")
                doc.status = "complete"
                await db.commit()

        await log_totals(document_id, doc.total_cost, doc.total_latency)
        await end_run(mlflow_run_id, status="FINISHED")

    except Exception as e:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Document).where(Document.id == uuid.UUID(document_id))
            )
            doc = result.scalar_one_or_none()
            if doc:
                doc.status = "failed"
                await db.commit()
        await end_run(mlflow_run_id, status="FAILED")
        raise
