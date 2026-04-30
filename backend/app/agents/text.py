import time
from ..graph import PipelineState
from ..tools.mlflow_logger import log_stage
from ..tools.pdf_parser import extract_text_from_pages


async def run(state: PipelineState) -> PipelineState:
    """
    Extracts and summarises prose text from pages classified as text.
    Uses LiteLLM with the model specified in the active config bundle.
    """
    start = time.time()
    document_id = state["document_id"]
    pdf_path = state["pdf_path"]

    text_pages = [
        p["page"] for p in state["page_classifications"]
        if "text" in p.get("content_types", [])
    ]

    # TODO: extract text, call LiteLLM to summarise, log tokens + cost
    raw_text = extract_text_from_pages(pdf_path, text_pages)

    latency = time.time() - start

    await log_stage(document_id, "text", latency=latency, cost=0.0)

    return {
        **state,
        "text_result": {
            "pages": text_pages,
            "raw_text": raw_text,
            "summary": "",  # TODO: LLM summary
        },
    }
