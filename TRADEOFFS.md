# TRADEOFFS.md

## What is done

- All 4 endpoints: POST /ingest, GET /search, GET /incidents/{id}, POST /assist
- Idempotent ingest with content_hash — skipped/updated/ingested counts on every run
- SQLite FTS5 full-text search with environment, service, severity, tags filters
- OpenAI integration with retry logic and fallback on guardrail failure
- Keyword-based prompt injection check on /assist input
- Multi-layer guardrails: input validation, search gate, strict system prompt, output citation check
- Correlation ID middleware — accepted or generated, echoed in every response header
- Structured JSON logging with correlation_id on every line
- In-memory trace store with /debug/trace/{correlation_id}
- 19 unit tests covering search query building, filter logic, guardrails, prompt injection
- README with exact run steps and curl examples for all endpoints
- generate_data.py with fixed seed (42), 300 incidents pre-generated and committed

## What is not done

- Integration tests — timebox decision, unit tests cover the critical logic
- No limit parameter exposed in search — fixed cap of 10 internally, simpler API
- No pagination
- No auth on any endpoint
- No rate limiting
- LLM-based prompt injection sanitizer — keyword check only for now, seam is there for upgrade

## Known issues and risks

- `q=database+timeout` in curl returns 0 results — synthetic data scenarios use distinct vocabulary per template, no cross-scenario incidents. Would fix by adding mixed-vocabulary templates in the generator.
- Keyword injection check is bypassable with creative phrasing — acceptable for this scope, documented
- Trace store is lost on restart — in-memory only
- No persistent log storage beyond structured stdout

## What I would do next with 2 more hours

- Replace keyword injection check with LLM-based sanitizer
- Fix the curl example in README (+ vs %20 for spaces)
- Add one integration test for the full /assist flow end-to-end

## What I would do next with 2 more days

- Swap SQLite FTS5 for Postgres FTS or OpenSearch for production-grade search and scalability
- Add auth layer on all endpoints
- Rate limiting on /assist (LLM calls are expensive)
- Persist trace store to SQLite table so traces survive restarts
- Add pagination to /search
- Support multiple LLM providers (Azure OpenAI at minimum for enterprise use)
