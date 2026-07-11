# AI-NOTES.md

## How I used AI across the build

Before writing the first prompt, I annotated the original spec into SPECS.md - made every "optional" into a hard decision, resolved all ambiguities, and added explicit design choices (SQLite FTS5, OpenAI only, fixed cap of 10, mandatory trace endpoint). The goal was to remove ambiguity before the agent touched anything, so it never had to guess.

Then a clarify pass: first prompt was questions only, no code. Agent flagged gaps, I answered them all in one shot. Only after that did I ask for PLAN.md.

This is a lightweight spec-driven workflow. Spec first, plan second, code section by section. The agent never ran ahead - every section ended with a hard stop. This is what kept the build reviewable and the mistakes catchable.

Used Cursor Composer 2 for everything: scaffolding all modules, writing unit tests, generating README, and section-by-section implementation. The approach was one section at a time - agent builds it, I review, then commit. No big-bang generation. Each section had a hard stop before moving to the next.

---

## How I validated changes

- Read the code after each section, not just the terminal output
- Ran `pytest` after tests were written, checked all pass
- Manual curl tests for ingest, search, assist, trace endpoints
- Re-read the original spec after the build, not just the annotated one - that's how I caught the "say I don't know" gap

---

## Prompt patterns that worked

- "Do not write any code yet" - forces questions and planning before implementation
- "Stop and wait for me to review" at the end of each prompt - prevents the agent from running ahead
- "Explain before you change" (Prompt #9) - ask why before asking to fix, avoids blind changes
- One section per prompt - smaller scope, easier to review, easier to catch mistakes

---

## Where AI was wrong or weak

**PROMPT #6 output:**

Generator initially had 10 scenarios cycling across 300 records , too repetitive for meaningful search/LLM patterns. In PROMPT #7 I asked for 20 more. Agent extended to 30 scenarios, 24 services, 31 tags. Much better distribution.

---

**PROMPT #8 output:**

Agent exposed content_hash in row_to_incident() , this is an internal field, not part of the API contract. I caught it and asked to remove it from the public-facing dict. Small thing but the kind of leak that shows up in production when internal fields end up in API responses clients start depending on

---

**PROMPT #11:**

Agent defined SearchResultItem with only id, title, snippet, score - technically matches the spec's minimum, but search results without environment, service, severity, tags are not very useful. Should have caught it in the specs.

---

**PROMPT #14:**

Agent said 'search tests ok' but tests/ was empty - it had run ad-hoc checks in the terminal, not written actual test files. The plan said write tests alongside the module - the agent skipped that step without flagging it.

---

**PROMPT #17:**

Spec says 'if nothing relevant is found, say so and ask for more info' as a hard requirement. Agent missed it when writing PLAN.md, I missed it reviewing the plan. Caught it later re-reading the spec. The system prompt handled zero hits in code but never told the LLM what to say when candidates exist but none are relevant. Fixed by adding the explicit instruction to the system prompt.
