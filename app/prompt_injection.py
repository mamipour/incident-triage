"""Keyword-based prompt injection detection."""

from __future__ import annotations

INJECTION_KEYWORDS = [
    "ignore previous instructions",
    "ignore all instructions",
    "ignore the above",
    "disregard previous",
    "disregard all instructions",
    "override instructions",
    "system prompt",
    "you are now",
    "new instructions",
    "jailbreak",
    "prompt injection",
    "do anything now",
]


def check_prompt_injection(text: str) -> bool:
    """Return True if keyword-based injection patterns are detected."""
    normalized = text.casefold()
    return any(keyword in normalized for keyword in INJECTION_KEYWORDS)
