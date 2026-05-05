# Briefed

Upload any document — reports, financial statements, research papers, anything. Briefed extracts text, tables, and charts, then explains what it all means in plain language.

Every design decision made by the pipeline is surfaced in the UI: which model was chosen and why, what was skipped, what it cost, and how faithful the output was to the source.

**Live:** [briefed-phi.vercel.app](https://briefed-phi.vercel.app) · **Backend:** Fly.io · **Experiment tracking:** MLflow

---

## What it does

Upload a PDF → the pipeline classifies each page, routes only to the agents that are needed, extracts content, synthesises a plain-language explanation, and scores it with an LLM-as-judge. Results show up in the UI with a full breakdown of cost, latency, quality score, and every decision the pipeline made.

A second upload of the same document returns instantly from cache at $0.00.

---

## Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph (sequential conditional routing) |
| LLM calls | ChatLiteLLM → OpenAI gpt-4o / gpt-4o-mini |
| Tracing | LangSmith (nested under LangGraph runs) |
| Experiment tracking | MLflow (runs, metrics, model registry, prompt registry) |
| Config management | MLflow Model Registry champion/challenger aliases |
| Prompt management | MLflow Prompt Registry — all 6 agent prompts versioned and hot-reloadable |
| Quality scoring | LLM-as-judge (faithfulness + completeness claims) |
| PDF parsing | pdfplumber (text/tables), pymupdf (page images) |
| Cache | Redis · SHA-256(pdf_bytes) key |
| Database | PostgreSQL + SQLAlchemy async |
| Backend | FastAPI + uvicorn |
| Frontend | React + Vite + Tailwind + Recharts |
| Deploy | Fly.io (backend + MLflow) + Vercel (frontend) |
| CI/CD | GitHub Actions |

---

## Pipeline

```
classify → [text] → [table] → [chart] → synthesize → score_quality
```

The classifier runs on every page and tags it as text / table / chart (or multiple). Agents not needed by any page are skipped — the skip decision, rationale, and estimated cost saved are recorded in the decisions table and shown in the UI.

---

## Observability

Every pipeline run produces:

- **MLflow run** — config bundle version, model params, cost, latency, quality score per stage
- **LangSmith trace** — single nested run showing all agent spans with token counts
- **Decision trace** — every routing / model selection / skip decision with rationale and cost impact, rendered in the UI
- **Quality detail** — faithful claims (✓), unfaithful claims (✗), missing content (△)

---

## Prompt registry

All 6 agent prompts are versioned in the MLflow Prompt Registry (`briefed-classifier`, `briefed-text`, `briefed-table`, `briefed-chart`, `briefed-synthesis`, `briefed-judge`). Prompts are registered at startup if they don't exist, and loaded from the registry on each pipeline run. Editing a prompt in the MLflow UI takes effect on the next run — no redeploy needed.

---

## A/B model testing

Config bundles (model selections for all 6 agents) are stored in the MLflow Model Registry. The current production config is the `champion` alias.

To run an experiment:

1. Open the **A/B Experiment** panel in the UI
2. Select challenger models for any of the 6 agents and hit **Start Experiment**
3. Uploads are routed 50/50 between champion and challenger — `params.config_variant` is logged on every MLflow run
4. Compare results in MLflow: filter by `params.config_variant = "champion"` vs `"challenger"`, select runs, hit **Compare**
5. Hit **Promote Challenger** to make it the new champion, or **End Experiment** to discard

The champion/challenger banner in the UI shows only the models that differ between the two configs.

---

## Local development

**Prerequisites:** Docker Desktop, an OpenAI API key, a LangSmith API key.

```bash
git clone https://github.com/YOUR_USERNAME/briefed
cd briefed
cp .env.example .env   # fill in API keys
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| MLflow UI | http://localhost:5050 |

---

## Deployment

Backend and MLflow run on Fly.io. Frontend on Vercel. GitHub Actions deploys on push to `main` (MLflow → backend → frontend, sequential).

Fly.io secrets required on `briefed-backend`: `DATABASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `REDIS_URL`, `MLFLOW_TRACKING_URI`, `LANGSMITH_API_KEY`.

---

## Project structure

```
briefed/
├── backend/
│   ├── app/
│   │   ├── agents/          # classifier, text, table, chart, synthesis, quality
│   │   ├── routers/         # documents, metrics, config (A/B endpoints)
│   │   ├── tools/           # llm, decisions, config_bundle, mlflow_logger, prompt_registry, pdf_parser
│   │   ├── graph.py         # LangGraph pipeline + champion/challenger routing
│   │   ├── state.py         # PipelineState TypedDict
│   │   └── main.py          # lifespan: waits for MLflow, registers config + prompts
│   └── requirements.txt
├── frontend/
│   └── src/
│       └── components/      # UploadPanel, DocumentDetail, MetricCards, QualityTrendChart,
│                            # ChallengerBanner, ConfigPanel
├── mlflow/                  # MLflow server Dockerfile + fly.toml
└── .github/workflows/       # deploy.yml
```
