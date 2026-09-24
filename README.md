# AI-Powered Sustainable Campus Resource Assistant

A polished student prototype for the **1M1B AI for Sustainability Virtual Internship**, focused on **SDG 12: Responsible Consumption and Production**.

**Live Deployment:** https://greenpulse-ai-sustainability-1.onrender.com/

It combines transparent analysis of a clearly labelled simulated dataset, local retrieval-augmented responses, an agentic recommendation workflow, and visible responsible-AI safeguards.

## Important data notice

All resource information is **Demo Dataset – Simulated Resource Data**. This project is not deployed on a campus and makes no claims about actual consumption, savings, emissions, institutional integration, or user adoption.

## Features

- React/Vite sustainability dashboard with trends, category distribution and explainable alerts
- FastAPI API with simulated electricity, water, paper and waste records persisted in SQLite
- Rule-based analysis comparing recent consumption to an earlier baseline
- Local RAG-style lexical retrieval over sustainability knowledge documents; source names returned with answers
- Safe **Demo AI Mode** when no provider credentials are configured
- Agentic, reviewable chain: analysis → retrieval → recommendation → responsible-AI check
- Dedicated Knowledge Base, Responsible AI, SDG Alignment and project pages

## Architecture

`React UI → FastAPI → analysis service / local knowledge retrieval / SQLite demo seed`

The recommendation endpoint emits the logical agents used for the workflow. This is intentionally a small, transparent student-prototype architecture rather than autonomous infrastructure.

## Quick start

Prerequisites: Python 3.10+ (or `uv`) and Node.js with a working npm installation.

```powershell
cd backend
uv venv
uv pip install -r requirements.txt
uv run uvicorn app.main:app --reload --port 8000
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (normally `http://localhost:5173`). The backend documentation is at `http://127.0.0.1:8000/docs`.

## Environment

Copy `.env.example` to `.env` only if you later add a provider adapter. The delivered prototype deliberately uses `LLM_PROVIDER=demo`; no API key is needed. Never commit `.env`.

## API

`GET /health`, `/api/resources`, `/api/resources/summary`, `/api/resources/trends`, `/api/knowledge`, `/api/sdgs`, `/api/responsible-ai` and `POST /api/analyze`, `/api/recommendations`, `/api/chat` are implemented. Input is Pydantic-validated.

## Tests

```powershell
cd backend
uv run pytest -q
```

Tests cover health, summary, trends, explainable high-use detection, recommendation generation, retrieval, chat fallback and validation.

## Responsible AI and limitations

Responses use local retrieved text where possible, label the demo mode, return source filenames, avoid fabricated numerical impact claims and ask for human review. Retrieval is lightweight lexical matching, not semantic embeddings; a production system would add authenticated data ingestion, measured baselines, access controls and a configurable provider adapter.

See [architecture documentation](docs/architecture.md), [AI workflow](docs/ai-workflow.md), [responsible AI](docs/responsible-ai.md), [demo script](docs/demo-script.md) and [project description](docs/project-description.md).
