# Prism AI Backend

Prism AI is an AI-powered trust radar backend for internship scam detection. It accepts raw text, an optional URL, or both, then runs rule-based scam checks, optional web/company verification, optional LLM reasoning, and persistence to PostgreSQL.

## Architecture

- FastAPI for the HTTP API
- Pydantic for request/response schemas
- SQLAlchemy 2.x for PostgreSQL persistence
- Alembic for schema migrations
- LangGraph for agent workflow orchestration and human-in-the-loop review
- httpx for URL fetches, LLM calls, and search provider calls
- BeautifulSoup and optional trafilatura for text extraction
- Redis support is included for future caching/rate-limiting extensions
- pytest for the test suite

## Setup

### Local Python run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Migrations

Run migrations before starting the server:

```bash
alembic upgrade head
```

### Start the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## Docker

Start the full stack with PostgreSQL and Redis:

```bash
docker compose up --build
```

The backend container runs migrations automatically before launching Uvicorn.

## Environment variables

- `DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/prism_ai`
- `REDIS_URL=redis://redis:6379/0`
- `LLM_PROVIDER=gemini`
- `GEMINI_API_KEY=`
- `GEMINI_MODEL=gemini-2.0-flash`
- `SEARCH_PROVIDER=tavily`
- `TAVILY_API_KEY=`
- `ENABLE_LLM_ANALYSIS=true`
- `ENABLE_WEB_SEARCH=true`
- `ENABLE_URL_FETCH=true`
- `CORS_ORIGINS=http://localhost:3000,http://localhost:5173`

## API

### Health

```bash
curl http://localhost:8000/health
```

### Create a scan

```bash
curl -X POST http://localhost:8000/api/scans \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Frontend Developer Internship at Nova Labs. Remote. ₹12k/month stipend. Apply through WhatsApp.",
    "category": "internship"
  }'
```

### Get a scan

```bash
curl http://localhost:8000/api/scans/<scan_id>
```

### List scans

```bash
curl "http://localhost:8000/api/scans?skip=0&limit=20"
```

### Rescan

```bash
curl -X POST http://localhost:8000/api/scans/<scan_id>/rescan \
  -H 'Content-Type: application/json' \
  -d '{}'
```

### Submit feedback

```bash
curl -X POST http://localhost:8000/api/feedback \
  -H 'Content-Type: application/json' \
  -d '{
    "scan_id": "<scan_id>",
    "user_rating": "helpful",
    "user_comment": "This helped me verify the post."
  }'
```

### Categories

```bash
curl http://localhost:8000/api/categories
```

## LangGraph Agent Workflow

Prism AI now uses LangGraph as the main orchestration layer instead of a simple linear service pipeline. The graph tracks a shared agent state, appends a trace entry at each major step, and pauses for human review whenever the scan is uncertain or risky.

Human-in-the-loop review happens at the risk gate. When Prism is unsure about the opportunity, it returns an `awaiting_human_review` response with review reasons and action buttons. The workflow can then be resumed with `POST /api/scans/{scan_id}/review`.

### Start a scan

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Data Analyst Internship. Certificate only. Pay ₹999 registration fee. Guaranteed selection. Apply on WhatsApp.",
    "category": "internship"
  }'
```

Expected response mode:

```json
{
  "workflow_status": "awaiting_human_review",
  "requires_human_review": true,
  "human_review": {
    "message": "Prism AI paused this scan because it needs human review.",
    "review_reasons": ["Payment, registration fee, or training fee language was detected."],
    "options": ["run_deeper_scan", "generate_safe_message", "mark_suspicious", "continue_anyway", "reject_opportunity"]
  }
}
```

### Resume a paused scan

```bash
curl -X POST http://localhost:8000/api/scans/{scan_id}/review \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "mark_suspicious",
    "notes": "Fee request and guaranteed selection look unsafe."
  }'
```

Expected final response mode:

```json
{
  "workflow_status": "completed",
  "requires_human_review": false,
  "risk_level": "High Risk",
  "recommended_action": "Avoid or verify manually before proceeding."
}
```

### Workflow shape

1. `receive_input`
2. `fetch_url_content`
3. `extract_details`
4. `run_rule_checks`
5. `run_web_verification`
6. `run_llm_analysis`
7. `calculate_score`
8. `risk_gate`
9. `human_review_interrupt`
10. `generate_recommendation`
11. `save_result`
12. `return_response`

The agent trace shows exactly what Prism checked, why it paused, which human decision was made, and how the final recommendation changed.

## Example response

```json
{
  "scan_id": "2f4f1a67-72e0-4fcb-a7bb-0d0f09f36a6d",
  "workflow_status": "completed",
  "requires_human_review": false,
  "risk_level": "Low Risk",
  "trust_score": 84,
  "scam_likelihood": 16,
  "confidence": "Medium",
  "summary": "This internship looks mostly genuine, but should still be verified through official company channels.",
  "extracted_details": {
    "title": "Frontend Developer Internship",
    "company": "Nova Labs",
    "stipend": "₹12k/month",
    "mode": "Remote",
    "duration": "2 months",
    "skills": ["React", "TypeScript"],
    "contact_method": "WhatsApp",
    "application_fee": false
  },
  "green_flags": [],
  "red_flags": [],
  "missing_information": [],
  "verification_signals": {},
  "recommended_action": "Apply only through the official company website or verified recruiter email.",
  "safe_message": "Hi, I’m interested in this internship. Could you please confirm the official application process, stipend, expected responsibilities, and whether any fee is required?",
  "agent_trace": []
}
```

## Limitations

- Internship analysis is the only fully supported category in this MVP.
- Web verification depends on the configured search provider and API key.
- LLM analysis is optional and may be skipped if the provider is unavailable.
- LinkedIn is not scraped directly; verification should rely on search results or user-provided links.
- The backend is cautious by design and prefers uncertainty over false certainty.

## Future roadmap

- Add category-specific rules for scholarships, PG listings, hackathons, and used laptops
- Add richer company-history verification signals
- Add caching for repeated company lookups
- Add background jobs for scheduled rescans and enrichment
- Add frontend-authenticated feedback loops for model improvement
