import pdfplumber
from typing import List


def get_page_count(pdf_path: str) -> int:
    with pdfplumber.open(pdf_path) as pdf:
        return len(pdf.pages)


def extract_text_from_pages(pdf_path: str, pages: List[int]) -> str:
    """Extract raw text from specified 1-indexed page numbers."""
    chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in pages:
            page = pdf.pages[page_num - 1]
            text = page.extract_text() or ""
            if text.strip():
                chunks.append(f"[Page {page_num}]\n{text.strip()}")
    return "\n\n".join(chunks)


def extract_tables_from_pages(pdf_path: str, pages: List[int]) -> List[dict]:
    """Extract all tables from specified 1-indexed page numbers using pdfplumber."""
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in pages:
            page = pdf.pages[page_num - 1]
            tables = page.extract_tables()
            for i, table in enumerate(tables):
                if not table:
                    continue
                results.append({
                    "page": page_num,
                    "table_index": i,
                    "data": table,
                    "title": "",          # TODO: infer from surrounding text
                    "interpretation": "", # TODO: LLM interpretation
                })
    return results


def render_page_as_image(pdf_path: str, page_num: int, dpi: int = 150) -> bytes:
    """Render a single page to PNG bytes for vision model input."""
    # TODO: implement with pdf2image or pymupdf
    # pip install pdf2image (requires poppler) or pymupdf (pip install pymupdf)
    raise NotImplementedError("Page rendering not yet implemented")
