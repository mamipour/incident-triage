PROMPT #1

Read the spec at @SPECS.md carefully.
Before writing any code:
- Ask any clarifying questions about requirements that are ambiguous
- Flag any design flaws or gaps you see
- Point out anything that could cause problems during implementation
Do not write any code yet. Questions and concerns only.
Do not create or modify PROMPTS.md, AI-NOTES.md, or TRADEOFFS.md.




PROMPT #2

Data:
Count: 300 exactly
Generator vs file: generate once, write to data/incidents.json, ingest always reads from that file. Ingest does not run the generator everytime. those are separated functionalities.
When to generate: pre-generated and committed. README should tell the user to run python generate_data.py once before ingesting if the file is not there. if there file exists, skip the generation and show a message
created_at: ISO 8601 with UTC timezone if fine, spread randomly over the last 6 months
Severity: fixed enum , critical, high, medium, low is fine
Tags filter: OR , comma-separated string (tags=timeout,database)

Ingest idempotency:
Skipped: same id, same content (hash match)
Updated: same id, different content
Second run on same data: all skipped, zero ingested/updated
Implementation: INSERT OR REPLACE on id + compare hash for skipped vs updated count

Search:
FTS query: default simple token AND
Fields indexed: title, description, resolution_summary, tags filtered separately via json_each
Filter combination: AND
Score: raw FTS5 rank negated so higher = better match
Snippet: first 150 chars of description, plain text, no highlighting
Empty/whitespace q: Reject with 422 code


Assist
question field becomes the FTS query directly, no separate construction step
Candidate pool: 10 (same as search)
LLM selects 3–5 from the candidates it receives
Response schema:
{
  "relevant_incidents": [{"id": "...", "reason": "..."}],
  "next_steps": ["..."],
  "customer_draft": "...",
  "correlation_id": "..."
}
"Nothing relevant": zero search hits = return 200 with "message": "No relevant incidents found. Please refine your question." and LLM never gets called
LLM failure: 503 with {"error": "...", "detail": "Set LLM_API_KEY. See README.", "correlation_id": "..."}



Observability:
Header: X-Correlation-ID, echoed in every response
Trace recording: /assist steps only, but correlation_id on all log lines
Trace storage: in-memory dict, max 100 entries (drop oldest), 404 for unknown IDs
Log format: structured JSON


LLM:
OpenAI only, no multi-provider needed
temperature: 0, timeout: 30s, max_tokens: 1000



PROMPT #3:

1- Option A
2- Tags are metadata filters only. A search for q=timeout matches on text fields
3- Proposition is fine
4- Proposition is fine
5- Proposition is fine
6- Proposition is fine
7- Proposition is fine
8- Drop

Now write PLAN.md as a GitHub-flavoured markdown checklist, one task per line, each mapped to the requirement it satisfies. Do not write any code yet. 
We will start iterating over the plan after I review it.


PROPMT #4:
Plan looks good, three things to fix before we start:

1. Add a prompt injection check task in Assist section. It should be an isolated function, keyword-based for now, returns 422 if triggered. 

2. Update the "Prompt LLM" item, change "retrieved incident records only" to "retrieved incident records framed as data not instructions". It is for preventing indirect prompt injections.

3. Add a commit checkpoint at the end of each section.

Update PLAN.md, no code yet.


PROMPT #5:
I fixed the .env permissions, set it to 600. Confirm if it's ok now
Do not move forward yet


PROMPT #6:
Looks good, committed. Start section 2. Do it completely, then stop and wait for me to review.

PROMPT #7:
10 scenarios cycling across 300 records makes the data too repetitive. 
Add 20 more scenarios, extend SERVICES and TAGS_POOL too. 
Regenerate the file when done and ask me to review.


PROMPT #8:
Committed. Start only section 3. Then stop and wait for me to review.


PROMPT #9:
Why did you include content_hash in row_to_incident? 
It is an internal field and exposing it it not the best practice.
Will removing it break anything downstream? 
Do not remove it yet, just explain.


PROMPT #10:
Remove content_hash from row_to_incident then. Ingest will read it from the row directly.
Then stop and do not move forward to the next section.



PROPMT #11:
Committed. Start only section 4. Then stop and wait for me to review.


PROMPT #12:
SearchResultItem is missing environment, service, severity, tags
My review is not done yet, just fix this one and stop.


PROMPT #13:
Committed. Start only section 5. Then stop and wait for me to review.


PROMPT #14:
Committed. Start only section 6. Then stop and wait for me to review.


PROMPT #15:
tests/ is empty. The plan says write search filter tests alongside the search module. 


PROMPT #16:
Committed. Start only section 7. Then stop and wait for me to review.


PROMPT #17:
Committed. Start only section 8. Then stop and wait for me to review.


PROMPT #18:
Confirm then fix
SPECS.md  says: "If nothing relevant is found, say so and ask for more info." 
The system prompt in assist_service.py is missing this explicit instruction. Add it.


PROMPT #19:
Committed. Start only section 9. Then stop and wait for me to review.

PROMPT #20:
Committed. Start only section 10. Then stop and wait for me to review.

PROMPT #21:
Committed. Start only section 11. Then stop and wait for me to review.

PROMPT #22:
Committed. Start only section 12. Then stop and wait for me to review.