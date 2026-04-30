from typing import TypedDict, List, Optional


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
