import pdfplumber
from typing import List


def get_page_count(pdf_path: str) -> int:
    with pdfplumber.open(pdf_path) as pdf:
        return len(pdf.pages)


def detect_page_content(pdf_path: str) -> List[dict]:
    """
    Returns per-page hints used by the classifier.
    Cheap heuristics run before any LLM call so the classifier
    only needs to confirm/refine, not discover from scratch.
    """
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            tables = page.extract_tables() or []
            images = page.images or []
            results.append({
                "page": i + 1,
                "text_preview": text[:600].strip(),
                "has_tables": len(tables) > 0,
                "has_images": len(images) > 0,
            })
    return results


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
            tables = page.extract_tables() or []
            for i, table in enumerate(tables):
                if not table:
                    continue
                results.append({
                    "page": page_num,
                    "table_index": i,
                    "data": table,
                    "title": "",
                    "interpretation": "",
                })
    return results


def render_page_as_image(pdf_path: str, page_num: int, dpi: int = 150) -> bytes:
    """Render a single page to PNG bytes for vision model input."""
    # TODO: implement with pdf2image or pymupdf
    raise NotImplementedError("Page rendering not yet implemented")
