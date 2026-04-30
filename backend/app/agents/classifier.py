import time
import json
import litellm
from langchain_core.messages import HumanMessage
from ..state import PipelineState
from ..tools.mlflow_logger import log_stage
from ..tools.pdf_parser import detect_page_content
from ..tools.llm import agent_trace, get_model

CLASSIFIER_PROMPT = """\
Analyze this PDF page and classify the content types present.

Page {page_num}:
- Text preview: {text_preview}
- Structured tables detected by parser: {has_tables}
- Images/figures detected by parser: {has_images}

Return JSON only, no markdown:
{{"content_types": [...], "has_ocr_needed": false}}

Rules:
- "text" = prose, narrative, paragraphs
- "table" = structured tabular data (rows and columns)
- "chart" = charts, graphs, or data visualizations (not logos or decorative images)
- Only include types actually present
- has_ocr_needed = true only if the page appears to be a scanned image with no selectable text\
"""


@agent_trace("classifier")
async def run(state: PipelineState) -> PipelineState:
    start = time.time()
    document_id = state["document_id"]
    pdf_path = state["pdf_path"]
    config = state.get("config", {})
    model_name = config.get("classifier_model", "gpt-4o-mini")

    page_infos = detect_page_content(pdf_path)
    llm = get_model(model_name, temperature=0, max_tokens=120)

    classifications = []
    total_tokens_in = 0
    total_tokens_out = 0
    total_cost = 0.0

    for info in page_infos:
        prompt = CLASSIFIER_PROMPT.format(
            page_num=info["page"],
            text_preview=info["text_preview"] or "(no text detected)",
            has_tables=info["has_tables"],
            has_images=info["has_images"],
        )

        response = await llm.ainvoke([HumanMessage(content=prompt)])
        raw = response.content.strip()

        # Approximate token counts from response metadata if available
        usage = getattr(response, "usage_metadata", None) or getattr(response, "response_metadata", {}).get("usage", {})
        total_tokens_in += usage.get("input_tokens", 0) if isinstance(usage, dict) else getattr(usage, "input_tokens", 0)
        total_tokens_out += usage.get("output_tokens", 0) if isinstance(usage, dict) else getattr(usage, "output_tokens", 0)

        try:
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            parsed = json.loads(raw)
            content_types = parsed.get("content_types", ["text"])
            has_ocr = parsed.get("has_ocr_needed", False)
        except (json.JSONDecodeError, KeyError):
            content_types = ["text"]
            has_ocr = False

        # Cost via litellm using the same model string
        try:
            total_cost += litellm.completion_cost(
                model=model_name,
                prompt=prompt,
                completion=raw,
            )
        except Exception:
            pass

        classifications.append({
            "page": info["page"],
            "content_types": content_types,
            "has_ocr_needed": has_ocr,
        })

    latency = time.time() - start

    from ..database import AsyncSessionLocal
    from ..models import Document
    from sqlalchemy import select
    import uuid

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Document).where(Document.id == uuid.UUID(document_id))
        )
        doc = result.scalar_one_or_none()
        if doc:
            doc.page_count = len(page_infos)
            doc.status = "processing"
            await db.commit()

    await log_stage(
        document_id,
        "classifier",
        model_used=model_name,
        tokens_in=total_tokens_in,
        tokens_out=total_tokens_out,
        cost=total_cost,
        latency=latency,
    )

    return {
        **state,
        "page_classifications": classifications,
    }
