from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import documents, metrics, config
from .tools import llm


@asynccontextmanager
async def lifespan(app: FastAPI):
    llm.setup()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from .tools.config_bundle import ensure_champion_exists
    ensure_champion_exists()

    from .tools.prompt_registry import ensure_prompts_exist
    from .agents.classifier import CLASSIFIER_PROMPT
    from .agents.text import TEXT_PROMPT
    from .agents.table import TABLE_PROMPT
    from .agents.chart import CHART_PROMPT
    from .agents.synthesis import SYNTHESIS_PROMPT
    from .agents.quality import JUDGE_PROMPT
    import threading
    threading.Thread(target=ensure_prompts_exist, args=({
        "briefed/classifier": (CLASSIFIER_PROMPT, "Page content classifier — routes pages to text/table/chart agents"),
        "briefed/text": (TEXT_PROMPT, "Text summarization — extracts summary and key facts from prose"),
        "briefed/table": (TABLE_PROMPT, "Table interpretation — titles and interprets extracted table data"),
        "briefed/chart": (CHART_PROMPT, "Chart analysis — describes chart and extracts key insight from page image"),
        "briefed/synthesis": (SYNTHESIS_PROMPT, "Synthesis — assembles all extracted content into structured plain-language explanation"),
        "briefed/judge": (JUDGE_PROMPT, "LLM-as-judge — scores faithfulness of explanation against source text"),
    },), daemon=True).start()
    yield
    await engine.dispose()


app = FastAPI(title="Briefed", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(metrics.router)
app.include_router(config.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
