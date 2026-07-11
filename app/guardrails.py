"""Post-validation guardrails for assist LLM output."""

from __future__ import annotations

import re

from app.models import RelevantIncident

INCIDENT_ID_PATTERN = re.compile(r"INC-\d{5}")


def validate_assist_output(
    relevant_incidents: list[RelevantIncident],
    next_steps: list[str],
    customer_draft: str,
    candidate_ids: set[str],
) -> list[str]:
    """Return validation errors. Empty list means output passed guardrails."""
    errors: list[str] = []

    for item in relevant_incidents:
        if item.id not in candidate_ids:
            errors.append(f"Cited incident ID not in candidate set: {item.id}")
        if not item.reason.strip():
            errors.append(f"Missing reason for incident ID: {item.id}")

    referenced_ids = set(INCIDENT_ID_PATTERN.findall(customer_draft))
    for step in next_steps:
        referenced_ids.update(INCIDENT_ID_PATTERN.findall(step))
    for item in relevant_incidents:
        referenced_ids.update(INCIDENT_ID_PATTERN.findall(item.reason))

    unknown_ids = referenced_ids - candidate_ids
    for incident_id in sorted(unknown_ids):
        errors.append(f"Referenced unknown incident ID: {incident_id}")

    return errors
