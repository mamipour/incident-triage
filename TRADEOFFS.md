




LATER:

Upgrade prompt injection check from keyword-based to a lightweight LLM sanitizer, the function is already an isolated seam, so the change is one swap with no impact on the rest of the assist flow.

Ingest service functions raise HTTPException directly. Couples business logic to the HTTP layer. Would refactor to domain exceptions and handle translation in the router for better testability and reuse.