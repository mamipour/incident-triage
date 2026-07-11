# Incident Triage

Search and AI assistant for incident triage (FastAPI + SQLite FTS + OpenAI).

## Prerequisites

- Python 3.12+
- OpenAI API key (for `/assist`)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set your OpenAI key:

```bash
LLM_API_KEY=sk-...
```

## Data generation

Synthetic incident data lives at `data/incidents.json` (300 records). The file is pre-generated and committed to the repo.

If the file is missing, generate it once before ingesting:

```bash
python3 generate_data.py
```

If `data/incidents.json` already exists, the script prints a skip message and exits without overwriting.

## Start the server

```bash
source .venv/bin/activate
python3 -m app.main
```

Or with uvicorn directly:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

## Ingest incidents

Loads incidents from `DATA_PATH` (default `data/incidents.json`) into SQLite. Idempotent — a second run on unchanged data reports all records as skipped.

```bash
curl -X POST http://localhost:8000/ingest
```

Example response:

```json
{"ingested": 300, "skipped": 0, "updated": 0}
```

## Search incidents

```bash
curl "http://localhost:8000/search?q=database+timeout&environment=prod&tags=timeout,database"
```

Example response:

```json
{
  "total": 10,
  "results": [
    {
      "id": "INC-00017",
      "title": "...",
      "snippet": "...",
      "score": 1.23,
      "environment": "prod",
      "service": "payment-api",
      "severity": "high",
      "tags": ["database", "timeout"]
    }
  ]
}
```

Query parameters:

| Param | Required | Description |
|---|---|---|
| `q` | yes | Text query (token AND) |
| `environment` | no | `dev`, `qa`, `stage`, or `prod` |
| `service` | no | Service name |
| `severity` | no | `critical`, `high`, `medium`, or `low` |
| `tags` | no | Comma-separated tags (OR semantics) |

## Get incident details

```bash
curl http://localhost:8000/incidents/INC-00001
```

## Assist (LLM)

Requires a valid `LLM_API_KEY` in `.env`.

```bash
curl -X POST http://localhost:8000/assist \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: demo-123" \
  -d '{
    "question": "database connection timeout in prod",
    "environment": "prod",
    "severity": "high"
  }'
```

Example response:

```json
{
  "relevant_incidents": [
    {"id": "INC-00017", "reason": "..."}
  ],
  "next_steps": ["..."],
  "customer_draft": "...",
  "correlation_id": "demo-123"
}
```

View the recorded trace for an assist request:

```bash
curl http://localhost:8000/debug/trace/demo-123
```

## Run tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `LLM_API_KEY` | — | OpenAI API key (required for `/assist`) |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `PORT` | `8000` | Server port when using `python3 -m app.main` |
| `DATA_PATH` | `data/incidents.json` | Path to incident JSON file for ingest |
| `DATABASE_PATH` | `data/incidents.db` | SQLite database file path |

Copy `.env.example` to `.env` and adjust as needed:

```bash
LLM_API_KEY=your-key-here
LLM_MODEL=gpt-4o-mini
PORT=8000
DATA_PATH=data/incidents.json
DATABASE_PATH=data/incidents.db
```

If `/assist` returns 503 with `"Set LLM_API_KEY. See README."`, add your key to `.env` and restart the server.
