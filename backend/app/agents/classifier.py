import time
from ..graph import PipelineState
from ..tools.mlflow_logger import log_stage
from ..tools.pdf_parser import get_page_count


async def run(state: PipelineState) -> PipelineState:
    """
    Reads each page of the PDF and decides which agents it needs.
    Emits a PageClassification per page and records routing decisions.
    """
    start = time.time()
    document_id = state["document_id"]
    pdf_path = state["pdf_path"]

    # TODO: use LiteLLM to classify each page (text/table/chart detection)
    # For now, stub returns all content types present
    page_count = get_page_count(pdf_path)

    classifications = []
    for i in range(page_count):
        classifications.append({
            "page": i + 1,
            "content_types": ["text"],  # stub — real classifier populates this
            "has_ocr_needed": False,
        })

    latency = time.time() - start

    await log_stage(document_id, "classifier", latency=latency, cost=0.0)

    return {
        **state,
        "page_classifications": classifications,
    }
