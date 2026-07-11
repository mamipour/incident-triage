# Search + AI Assistant for Incident Triage

## Tech choices

* Language: Python (FastAPI)
* Search backend: SQLite FTS
* LLM: must call a real LLM at runtime: OpenAI

---

## What to build

### Data

Use 200 to 500 incident tickets. You must:

* Generate synthetic data 

Each incident must include:

* `id`, `created_at`, `environment` (dev/qa/stage/prod), `service`, `severity`
* `title`, `description`, `resolution_summary`, `tags` (array)

Include the generator and a fixed seed so results are repeatable.

---

## API requirements

### 1) Ingest

`POST /ingest`

* Loads incidents into your search store
* Idempotent: running twice does not create duplicates
* Returns counts: ingested, skipped, updated

### 2) Search

`GET /search`

Query params:

* `q` (mandatory text query)
* optional filters: `environment`, `service`, `severity`, `tags`

Returns:

* Top 10 results: id, title, short snippet, relevance score
* Total hit count

### 3) Incident details

`GET /incidents/{id}`

* Returns the full incident record

### 4) Assist

`POST /assist`

Input:

* `question` (string, required, max 1000 characters)
* optional filters (same as search)

Behavior:

1. Retrieves candidates using the same search code path as `/search` and logs it as a tool step (example: `tool:search`).
2. Calls a real LLM.
3. Returns:
    * The 3 to 5 most relevant incident IDs and why they are relevant
    * "Next steps" checklist
    * A short customer facing draft response

#### Grounding and safety rules (hard requirement)

* Must cite the incident IDs used.
* Must not invent incident details that are not in retrieved records.
* If nothing relevant is found, say so and ask for more info.
* If the LLM call fails (missing key, timeout, etc.), return a clear error explaining what to set and how to run it.

---

## Observability requirements (keep it simple)

* Generate or accept a `correlation_id` per request (header or generated).
* Include `correlation_id` in every log line.
* For `/assist`, log a step list that includes at least:

    * `tool:search` input summary (query, filters)
    * `tool:search` output summary (hit count, top IDs)
    * selected incident IDs

Mandatory: `GET /debug/trace/{correlation_id}` that returns recorded steps.

---

## Minimum quality requirements

### Maintainability

* Clear separation of concerns (ingest, search, assist, config, observability)
* Configuration via environment variables
* Code should be easy to extend (clean interfaces, not one giant file)

### Robustness

* Input validation and useful error messages
* Timeouts for external calls (LLM and any network calls)
* Reasonable limits: search returns at most 10 results; question field max 1000 characters

### Testing (minimum)

* At least 2 unit tests focused on:

    * Query building and filtering, and/or
    * Guardrails (no invented details, must cite IDs)

Integration tests are not needed.

### Docs

* `README.md` with exact run steps and curl examples:

    * how to start
    * how to ingest
    * how to search
    * how to call assist
    * how to run tests



## Environment variables

Document what you use, but expect something like:

* `LLM_PROVIDER` (openai, azure-openai, etc.)
* `LLM_API_KEY`
* `LLM_MODEL`
* Provider specific vars (endpoint, deployment name, api version)
* `PORT`
* `DATA_PATH` (if applicable)



## IMPORTANT:
* Do not create or modify PROMPTS.md, AI-NOTES.md, or TRADEOFFS.md. These files already exist and are authored manually.