import time
from ..graph import PipelineState
from ..tools.mlflow_logger import log_stage
from ..tools.pdf_parser import extract_tables_from_pages


async def run(state: PipelineState) -> PipelineState:
    """
    Extracts tables using pdfplumber and interprets each one with LiteLLM.
    Records extraction method selection as a Decision.
    """
    start = time.time()
    document_id = state["document_id"]
    pdf_path = state["pdf_path"]

    table_pages = [
        p["page"] for p in state["page_classifications"]
        if "table" in p.get("content_types", [])
    ]

    # TODO: run pdfplumber extraction, call LiteLLM to interpret each table
    tables = extract_tables_from_pages(pdf_path, table_pages)

    latency = time.time() - start

    await log_stage(document_id, "table", latency=latency, cost=0.0)

    return {
        **state,
        "table_result": {
            "pages": table_pages,
            "tables": tables,  # list of {title, data, interpretation}
        },
    }
