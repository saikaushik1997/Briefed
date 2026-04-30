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
