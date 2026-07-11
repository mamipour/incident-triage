

PROMPT #6 output:
Generator initially had 10 scenarios cycling across 300 records , too repetitive for meaningful search/LLM patterns. In PROMPT #7 I asked for 20 more. Agent extended to 30 scenarios, 24 services, 31 tags. Much better distribution.


PROMPT #8 output:
Agent exposed content_hash in row_to_incident() , this is an internal field, not part of the API contract. I caught it and asked to remove it from the public-facing dict. Small thing but the kind of leak that shows up in production when internal fields end up in API responses clients start depending on


PROPMT #11:
Agent defined SearchResultItem with only id, title, snippet, score — technically matches the spec's minimum, but search results without environment, service, severity, tags are not very useful. Should have caught it in the specs.


PROMPT #14:
Agent said 'search tests ok' but tests/ was empty — it had run ad-hoc checks in the terminal, not written actual test files. The plan said write tests alongside the module — the agent skipped that step without flagging it.

PROMPT #17:
Spec says 'if nothing relevant is found, say so and ask for more info' as a hard requirement. Agent missed it when writing PLAN.md, I missed it reviewing the plan. Caught it later re-reading the spec. The system prompt handled zero hits in code but never told the LLM what to say when candidates exist but none are relevant. Fixed by adding the explicit instruction to the system prompt.