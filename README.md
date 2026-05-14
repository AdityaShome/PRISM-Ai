# PRISM-Ai

Prism AI is a trust-scanning app that helps users evaluate opportunities, listings, and messages before they act. It combines a React/Vite frontend with a FastAPI backend, then runs a multi-step agent workflow that extracts details, searches the web, scores risk, and pauses for human review when needed.

## What the name means

PRISM stands for:

- Probe
- Review
- Insight
- Score
- Move

That is also the basic workflow of the product: collect the signal, inspect it, score it, and decide what to do next.

## How the system is organized

The repository is split into two parts:

- `./` is the frontend app built with React, TypeScript, Vite, and Tailwind CSS.
- `./prism-ai-backend/` is the FastAPI backend with LangGraph-based orchestration, SQLAlchemy models, and service modules for search, scoring, and review.

The frontend talks to the backend over HTTP. The backend stores scans in a database and returns a structured scan result, including trust score, risk level, flags, summaries, and review state.

## Product workflow

The user flow is intentionally simple:

1. The user pastes text or adds a URL for a listing, message, or opportunity.
2. The frontend sends the request to the backend API.
3. The backend seeds a scan record and starts the Prism agent workflow.
4. The workflow extracts details, checks for risky patterns, optionally fetches and verifies supporting evidence, and may call the LLM analysis step.
5. The workflow calculates trust and risk scores and produces a recommendation.
6. If the scan needs manual input, the backend pauses and returns a human review payload.
7. The frontend shows the result and lets the user review history, submit a decision, or leave feedback.

## Backend workflow

The backend is built around a scan lifecycle.

### 1. Request intake

The API accepts a scan request at `POST /api/scans` with text, URL, and category data.

### 2. Graph execution

`PrismAgent` builds a LangGraph workflow and runs it against a per-scan thread id. The workflow state keeps track of:

- extracted details
- green and red flags
- verification signals
- trust and scam scores
- confidence level
- review status
- trace output

### 3. Verification and scoring

The agent can use:

- rule-based checks for suspicious patterns
- web search for public evidence
- LLM analysis through Gemini
- recommendation logic for a final action

### 4. Human-in-the-loop review

If the scan cannot be completed with enough confidence, the backend marks it as awaiting human review and returns a review payload. The user can then submit a decision to continue, reject, or generate a safer message.

### 5. Persistence

Each scan is saved in the database so the frontend can show history and revisit individual scan results later.

## Frontend workflow

The frontend is a single-page app with these main areas:

- a landing/hero section that explains the product
- a scan form for text and URL input
- a results area that shows trust, risk, and flags
- a history panel for previous scans
- a review panel for human decisions
- an educational section that explains common scam patterns

The API client in `src/lib/api.ts` handles communication with the backend. It tries the configured backend URL first, then falls back to `http://localhost:8001` and `http://localhost:8000` if needed.

## API endpoints

The backend exposes the following routes:

- `GET /health` - service health check
- `GET /api/categories` - supported categories for the UI
- `POST /api/scans` - start a new scan
- `GET /api/scans` - list scan history
- `GET /api/scans/{scan_id}` - fetch one scan
- `POST /api/scans/{scan_id}/rescan` - run the scan again with updated input
- `POST /api/scans/{scan_id}/review` - submit a human review decision
- `POST /api/feedback` - submit feedback about a scan

## Repository layout

- `src/` - frontend source code
- `index.html` - Vite entry HTML for the frontend app
- `prism-ai-backend/app/` - backend application code
- `prism-ai-backend/app/api/routes/` - API route handlers
- `prism-ai-backend/app/agents/` - LangGraph orchestration and scan agent logic
- `prism-ai-backend/app/services/` - extraction, search, LLM, scoring, recommendation, and trace services
- `prism-ai-backend/app/models/` - SQLAlchemy models
- `prism-ai-backend/app/schemas/` - request and response schemas
- `prism-ai-backend/app/repositories/` - database access layer
- `prism-ai-backend/alembic/` - database migration files

## Prerequisites

You will need:

- Node.js 18+ and npm
- Python 3.12+
- A Gemini API key for LLM analysis
- A Tavily API key for web search verification

## Environment setup

### Frontend

Create a root `.env` file with the backend URL:

```bash
VITE_API_URL=http://localhost:8001
```

### Backend

Create `prism-ai-backend/.env` with your backend settings. A typical local setup looks like:

```bash
DATABASE_URL=sqlite:///./dev.db
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.0-flash
TAVILY_API_KEY=your_tavily_key
ENABLE_LLM_ANALYSIS=true
ENABLE_WEB_SEARCH=true
ENABLE_URL_FETCH=true
AUTO_CREATE_TABLES=true
CORS_ORIGINS=http://localhost:5173
```

Notes:

- The backend reads `.env` from inside `prism-ai-backend/`.
- `AUTO_CREATE_TABLES=true` is useful for local SQLite development.
- `CORS_ORIGINS` should include the frontend origin if you change the default port.

## Local development

Run the backend in one terminal:

```bash
cd prism-ai-backend
uvicorn app.main:app --reload --port 8001
```

Run the frontend in another terminal:

```bash
npm install
npm run dev
```

Open the app at `http://localhost:5173`.

If you change `.env` files, restart the dev server so Vite and FastAPI reload the new values.

## Build and preview

Frontend build:

```bash
npm run build
```

Preview the production frontend locally:

```bash
npm run preview
```

## Backend commands

Useful backend commands from `prism-ai-backend/`:

```bash
uvicorn app.main:app --reload --port 8001
pytest
alembic upgrade head
```

## Docker

The backend includes a `Dockerfile` that installs Python dependencies, runs migrations, and starts Uvicorn on port 8000 inside the container. That is the recommended starting point if you want to containerize the backend.

## Troubleshooting

### Frontend says "failed to fetch"

- Confirm the backend is running on `http://localhost:8001`.
- Confirm the root `.env` contains `VITE_API_URL=http://localhost:8001`.
- Restart `npm run dev` after changing environment files.
- Check that CORS allows the frontend origin.

### Scan returns manual review

This is expected when the agent does not have enough confidence. Use the review actions in the UI to continue, reject, or generate a safer message.

### No scans appear in history

- Confirm the backend database file exists and is writable.
- Confirm the scan request completed successfully.
- If you are using SQLite locally, make sure the backend started with `AUTO_CREATE_TABLES=true` or the tables were created with Alembic.

## Development notes

- `index.html` must stay at the project root because Vite uses it as the app entry point.
- The frontend reads `src/main.tsx` from that HTML file.
- The backend persists scans so you can refresh the page and keep history.
- The API client tries the configured backend URL first, then fallback ports, which helps when switching between local environments.

## Project goal

The intent of Prism AI is not to guarantee safety. It is to make risky opportunities easier to inspect by combining structured extraction, web verification, score-based reasoning, and human review when confidence is low.
