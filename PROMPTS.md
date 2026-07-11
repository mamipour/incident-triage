# PROMPTS.md

---

## Prompt #1

**Tool used:** Cursor (Composer 2)

**Goal:** Make the agent ask questions before touching any code, catch spec gaps early

**Prompt:**
```
Read the spec at @SPECS.md carefully.
Before writing any code:
- Ask any clarifying questions about requirements that are ambiguous
- Flag any design flaws or gaps you see
- Point out anything that could cause problems during implementation
Do not write any code yet. Questions and concerns only.
Do not create or modify PROMPTS.md, AI-NOTES.md, or TRADEOFFS.md.
```

**Result summary:** Agent asked ~8 questions on data count, idempotency strategy, FTS scoring, filter behavior (AND vs OR), LLM provider

**What you kept:** All questions - they were on point

**What you changed manually:** Nothing - used the answers as input for Prompt #2

**Follow-up prompt:** Prompt #2 (answered all questions)

---

## Prompt #2

**Tool used:** Cursor (Composer 2)

**Goal:** Answer all the agent's questions at once, lock in all design decisions before a line of code is written

**Prompt:**
```
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

Assist:
question field becomes the FTS query directly, no separate construction step
Candidate pool: 10 (same as search)
LLM selects 3-5 from the candidates it receives
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
```

**Result summary:** Agent acknowledged all decisions and ready for the plan

**What you kept:** Everything

**What you changed manually:** Nothing - this was me writing the spec decisions, not the agent

**Follow-up prompt:** Prompt #3

---

## Prompt #3

**Tool used:** Cursor (Composer 2)

**Goal:** Generate PLAN.md from the design decisions

**Prompt:**
```
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
```

**Result summary:** 62-item checklist across 10 sections, each item mapped to a requirement

**What you kept:** Most of it

**What you changed manually:** Three things - see Prompt #4

**Follow-up prompt:** Prompt #4

---

## Prompt #4

**Tool used:** Cursor (Composer 2)

**Goal:** Fix 3 gaps in the plan before coding starts

**Prompt:**
```
Plan looks good, three things to fix before we start:

1. Add a prompt injection check task in Assist section. It should be an isolated function, keyword-based for now, returns 422 if triggered.

2. Update the "Prompt LLM" item, change "retrieved incident records only" to "retrieved incident records framed as data not instructions". It is for preventing indirect prompt injections.

3. Add a commit checkpoint at the end of each section.

Update PLAN.md, no code yet.
```

**Result summary:** PLAN.md updated with all 3 changes

**What you kept:** Everything

**What you changed manually:** Nothing

**Follow-up prompt:** Start section 1

---

## Prompt #7

**Tool used:** Cursor (Composer 2)

**Goal:** Fix repetitive data - 10 scenarios for 300 records is too uniform, search results and LLM output won't be interesting

**Prompt:**
```
10 scenarios cycling across 300 records makes the data too repetitive.
Add 20 more scenarios, extend SERVICES and TAGS_POOL too.
Regenerate the file when done and ask me to review.
```

**Result summary:** 30 scenarios, 24 services, 31 tags. Better variety.

**What you kept:** The extended generator and regenerated incidents.json

**What you changed manually:** Nothing in code - checked the distribution manually after regeneration

**Note:** I caught this by reviewing the output. Agent didn't flag it.

---

## Prompt #9

**Tool used:** Cursor (Composer 2)

**Goal:** Understand why content_hash was in the public API response before removing it

**Prompt:**
```
Why did you include content_hash in row_to_incident?
It is an internal field and exposing it is not the best practice.
Will removing it break anything downstream?
Do not remove it yet, just explain.
```

**Result summary:** Agent explained it pulled the full DB row by default. Confirmed removing it is safe - ingest reads it from the raw row directly.

**What you kept:** The explanation

**What you changed manually:** Nothing - followed with a separate prompt to remove it

**Follow-up prompt:**
```
Remove content_hash from row_to_incident then. Ingest will read it from the row directly.
Then stop and do not move forward to the next section.
```

---

## Prompt #15

**Tool used:** Cursor (Composer 2)

**Goal:** Agent said section 6 was done but tests/ was empty

**Prompt:**
```
tests/ is empty. The plan says write search filter tests alongside the search module.
```

**Result summary:** Agent wrote 11 unit tests covering query building, filter clauses, score ordering, and snippet generation

**What you kept:** All 11 tests

**What you changed manually:** Nothing

**Note:** Agent had run terminal checks, not written test files. Always verify the output, not just the claim.

---

## Prompt #18

**Tool used:** Cursor (Composer 2)

**Goal:** Fix a spec requirement missed at plan stage and at code review

**Prompt:**
```
Confirm then fix
SPECS.md says: "If nothing relevant is found, say so and ask for more info."
The system prompt in assist_service.py is missing this explicit instruction. Add it.
```

**Result summary:** Agent confirmed the gap and added the instruction to the system prompt

**What you kept:** The fix

**What you changed manually:** Nothing

**Note:** Agent missed it writing PLAN.md, I missed it reviewing the plan. Caught it by re-reading the spec.
