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
| Experiment tracking | MLflow (runs, metrics, model registry) |
| Config management | MLflow Model Registry champion/challenger aliases |
| Quality scoring | LLM-as-judge (faithfulness + completeness claims) |
| PDF parsing | pdfplumber (text/tables), pymupdf (page images) |
| Cache | Redis · SHA-256(pdf_bytes) key |
| Database | PostgreSQL + SQLAlchemy async + Alembic |
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

- **MLflow run** — config bundle version, model params, cost, latency, quality score
- **LangSmith trace** — single nested run showing all agent spans
- **Decision trace** — every routing / model selection / skip decision with rationale and cost impact, queryable from the API and rendered in the UI
- **Quality detail** — faithful claims (✓), unfaithful claims (✗), missing content (△)

---

## A/B model testing

Config bundles are stored in the MLflow Model Registry. The current production config is the `champion` alias. Registering a new version and tagging it `challenger` activates an experiment indicator in the UI — showing which model each alias uses and the traffic split. Promoting the challenger to champion requires a manual action in MLflow, leaving a full audit trail.

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

Backend and MLflow run on Fly.io. Frontend on Vercel. GitHub Actions deploys on push to `main` (MLflow → backend → frontend).

First-time setup:
```bash
fly auth login
bash scripts/fly-setup.sh
```

Set Fly.io secrets (see `scripts/fly-setup.sh` for the full list), then push to `main`.

---

## Project structure

```
briefed/
├── backend/
│   ├── app/
│   │   ├── agents/          # classifier, text, table, chart, synthesis, quality
│   │   ├── routers/         # documents, metrics, config
│   │   ├── tools/           # llm, decisions, config_bundle, mlflow_logger, pdf_parser
│   │   ├── graph.py         # LangGraph pipeline
│   │   ├── state.py         # PipelineState TypedDict
│   │   └── main.py
│   └── alembic/             # database migrations
├── frontend/
│   └── src/
│       └── components/      # UploadPanel, DocumentDetail, MetricCards, QualityTrendChart, ChallengerBanner
├── mlflow/                  # MLflow server Dockerfile + fly.toml
└── .github/workflows/       # deploy.yml
```
