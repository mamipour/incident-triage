# Implementation Plan

Checklist for building the incident triage search + AI assistant. Each item maps to a requirement from `SPECS.md` and the agreed design decisions.

---

## Project structure and configuration

- [x] Create package layout with separate modules for config, ingest, search, assist, observability, and models — **Maintainability: separation of concerns**
- [x] Add `app/config.py` using pydantic-settings to load env vars (`LLM_API_KEY`, `LLM_MODEL`, `PORT`, `DATA_PATH`) — **Config via environment variables**
- [x] Add `app/main.py` FastAPI app factory with router registration — **Tech: Python (FastAPI)**
- [x] Pin runtime dependencies in `requirements.txt` (already scaffolded) — **Maintainability**
- [x] Update `.env.example` with OpenAI-only vars (`LLM_API_KEY`, `LLM_MODEL`, `PORT`, `DATA_PATH`) — **Environment variables**
- [ ] **Commit checkpoint:** project scaffold, config, and dependencies

---

## Data generation

- [x] Create `generate_data.py` with fixed seed (`SEED = 42`) for repeatable output — **Data: fixed seed**
- [x] Generate exactly 300 synthetic incidents with fields: `id`, `created_at`, `environment`, `service`, `severity`, `title`, `description`, `resolution_summary`, `tags` — **Data: 200–500 tickets, required fields**
- [x] Use `environment` values from `dev` / `qa` / `stage` / `prod` — **Data: environment enum**
- [x] Use `severity` enum: `critical`, `high`, `medium`, `low` — **Design decision: severity enum**
- [x] Set `created_at` as ISO 8601 UTC, randomly spread over the last 6 months — **Design decision: created_at format**
- [x] Store `tags` as a JSON array of strings — **Data: tags (array)**
- [x] Write output to `data/incidents.json` — **Design decision: generate once, write to file**
- [x] Skip generation with a message if `data/incidents.json` already exists — **Design decision: skip if file exists**
- [x] Pre-generate and commit `data/incidents.json` to the repo — **Design decision: pre-generated and committed**
- [x] Document `python generate_data.py` in README (run once if file missing) — **Docs: how to start / ingest prep**
- [ ] **Commit checkpoint:** data generator and pre-generated incidents

---

## Database and search store

- [x] Create `app/db.py` (or equivalent) to initialize SQLite with incidents table and FTS5 virtual table — **Search backend: SQLite FTS**
- [x] Store full incident records in a primary `incidents` table keyed by `id` — **GET /incidents/{id}: full record**
- [x] Add `content_hash` column (SHA-256 of canonical content) for idempotent ingest — **Design decision: hash for skipped vs updated**
- [x] Create FTS5 index on `title`, `description`, `resolution_summary` (tags excluded) — **Design decision: FTS fields; tags are filter-only**
- [x] Store `tags` as JSON text and filter via `json_each` — **Design decision: tags filtered via json_each**
- [x] Wire FTS sync triggers (insert/update/delete) so index stays consistent on ingest — **POST /ingest: loads into search store**
- [ ] **Commit checkpoint:** SQLite schema, FTS5 index, and sync triggers

---

## Domain models and validation

- [x] Define Pydantic models for incident record, ingest response, search response, assist request/response, and error payloads — **Robustness: input validation**
- [x] Validate `environment`, `service`, `severity`, and comma-separated `tags` on search and assist filters — **GET /search, POST /assist: optional filters**
- [x] Reject empty or whitespace-only `q` on `/search` with HTTP 422 — **Design decision: empty q → 422**
- [x] Validate `question` on `/assist`: required, max 1000 characters — **POST /assist: question max 1000 chars; Robustness: limits**
- [ ] **Commit checkpoint:** Pydantic models and input validation

---

## Ingest (`POST /ingest`)

- [x] Implement ingest service that reads incidents from `DATA_PATH` (default `data/incidents.json`) — **POST /ingest: loads incidents; Design decision: ingest reads file only**
- [x] Do not invoke the generator from the ingest endpoint — **Design decision: generator and ingest are separate**
- [x] For each incident: lookup by `id`, compare `content_hash`, skip if match — **Idempotent: skipped = same id + same hash**
- [x] For changed content: `INSERT OR REPLACE` and increment `updated` — **Idempotent: updated = same id, different content**
- [x] For new incidents: insert and increment `ingested` — **POST /ingest: ingested count**
- [x] Return `{"ingested": N, "skipped": N, "updated": N}` — **POST /ingest: return counts**
- [x] Second run on unchanged data yields all skipped, zero ingested/updated — **Idempotent: no duplicates**
- [ ] **Commit checkpoint:** idempotent ingest endpoint

---

## Search (`GET /search`)

- [x] Implement shared search function used by both `/search` and `/assist` — **POST /assist: same search code path**
- [x] Build FTS query with simple token AND semantics — **Design decision: FTS token AND**
- [x] Apply optional filters (`environment`, `service`, `severity`, `tags`) with AND logic — **GET /search: filters; Design decision: filter AND**
- [x] Parse `tags` filter as comma-separated OR match via `json_each` — **Design decision: tags OR, comma-separated**
- [x] Return raw FTS5 rank negated so higher score = better match — **Design decision: negated rank score**
- [x] Return top 10 results with `id`, `title`, `snippet`, `score` — **GET /search: top 10 results**
- [x] Build snippet as first 150 chars of `description`, plain text, no highlighting — **Design decision: snippet rules**
- [x] Return total hit count alongside results — **GET /search: total hit count**
- [x] Return `{"total": N, "results": [...]}` response shape — **Design decision: search response schema**
- [ ] **Commit checkpoint:** search endpoint and shared search function

---

## Incident details (`GET /incidents/{id}`)

- [x] Implement endpoint returning the full stored incident record — **GET /incidents/{id}: full record**
- [x] Return 404 with useful error when incident id is not found — **Robustness: useful error messages**
- [ ] **Commit checkpoint:** incident details endpoint

---

## Assist (`POST /assist`)

- [x] Accept `question` (required) and optional filters (same as search) — **POST /assist: input**
- [x] Add isolated prompt-injection check function (keyword-based) on `question`; return HTTP 422 if triggered — **Robustness: input validation; Design decision: prompt injection guard**
- [x] Pass `question` directly as the FTS query (no separate query construction) — **Design decision: question = FTS query**
- [x] Retrieve top 10 candidates via the shared search function — **Design decision: candidate pool = 10**
- [x] On zero search hits: return HTTP 200 with `"message": "No relevant incidents found. Please refine your question."` and do not call the LLM — **Grounding: nothing relevant; Design decision: zero hits, no LLM**
- [x] Call OpenAI with real API at runtime (`temperature=0`, `timeout=30s`, `max_tokens=1000`) — **LLM: OpenAI at runtime; Design decision: LLM params**
- [x] Prompt LLM with retrieved incident records framed as data, not instructions; ask it to pick 3–5 relevant IDs with reasons — **POST /assist: 3–5 relevant IDs and why; Design decision: prevent indirect prompt injection**
- [x] Return `next_steps` checklist and `customer_draft` short response — **POST /assist: next steps + customer-facing draft**
- [x] Return response schema: `relevant_incidents`, `next_steps`, `customer_draft`, `correlation_id` — **Design decision: assist response schema**
- [x] When LLM finds no relevant incidents among candidates: return 200 with empty `relevant_incidents` and guidance in `next_steps` — **Design decision: option A**
- [x] Enforce grounding via prompt + post-validation (cited IDs must be in candidate set; no fields outside retrieved records) — **Grounding: cite IDs, no invented details**
- [x] On LLM failure (missing key, timeout, etc.): return HTTP 503 with `error`, `detail`, `correlation_id` — **Grounding: LLM failure error; Robustness: timeouts**
- [ ] **Commit checkpoint:** assist endpoint with LLM integration and grounding guardrails

---

## Observability

- [x] Add middleware to accept or generate `X-Correlation-ID` per request — **Observability: correlation_id per request**
- [x] Echo `X-Correlation-ID` on every response — **Design decision: header echoed**
- [x] Configure structured JSON logging with `correlation_id` on every log line — **Observability: correlation_id in every log line**
- [x] Record `/assist` trace steps: `tool:search` input (query, filters), `tool:search` output (hit count, top IDs), LLM selected IDs — **Observability: assist step list**
- [x] Store traces in in-memory dict, max 100 entries, drop oldest on overflow — **Design decision: trace storage**
- [x] Implement `GET /debug/trace/{correlation_id}` returning recorded steps — **Observability: debug trace endpoint**
- [x] Return 404 for unknown or expired correlation IDs — **Design decision: trace 404**
- [x] Use agreed trace payload shape (`correlation_id`, `steps` with `tool:search` and `llm` entries) — **Design decision: trace step format**
- [ ] **Commit checkpoint:** correlation ID middleware, structured logging, and trace endpoint

---

## Testing

- [ ] Add unit test for search query building (token AND) and filter combination (AND filters, tags OR) — **Testing: query building and filtering**
- [ ] Add unit test for assist guardrails (cited IDs in candidate set, rejection of invented details) — **Testing: guardrails**
- [ ] Do not add integration tests — **Testing: integration tests not needed**
- [ ] **Commit checkpoint:** unit tests

---

## Documentation

- [ ] Write `README.md` with exact steps to install dependencies and start the server — **Docs: how to start**
- [ ] Add curl example for `POST /ingest` — **Docs: how to ingest**
- [ ] Add curl example for `GET /search` — **Docs: how to search**
- [ ] Add curl example for `POST /assist` — **Docs: how to call assist**
- [ ] Add instructions to run `pytest` — **Docs: how to run tests**
- [ ] Document all environment variables and LLM setup (`LLM_API_KEY`, etc.) — **Environment variables; Grounding: explain what to set**
- [ ] **Commit checkpoint:** README and documentation

---

## Final verification

- [ ] Manually verify ingest → search → assist → trace flow end-to-end — **API requirements (all endpoints)**
- [ ] Confirm idempotent ingest: second run reports all skipped — **POST /ingest: idempotent**
- [ ] Confirm `/assist` returns 503 with helpful detail when `LLM_API_KEY` is missing — **Grounding: LLM failure error**
- [ ] Do not create or modify `PROMPTS.md`, `AI-NOTES.md`, or `TRADEOFFS.md` — **SPECS.md: IMPORTANT constraint**
- [ ] **Commit checkpoint:** final verification pass
