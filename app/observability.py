"""Correlation ID helpers."""

from __future__ import annotations

import uuid

from fastapi import Request

CORRELATION_ID_HEADER = "X-Correlation-ID"


def get_correlation_id(request: Request) -> str:
    header_value = request.headers.get(CORRELATION_ID_HEADER)
    if header_value and header_value.strip():
        return header_value.strip()
    return str(uuid.uuid4())
