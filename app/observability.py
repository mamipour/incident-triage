"""Correlation ID handling, structured logging, and request tracing."""

from __future__ import annotations

import json
import logging
import uuid
from collections import OrderedDict
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

CORRELATION_ID_HEADER = "X-Correlation-ID"
MAX_TRACE_ENTRIES = 100

correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)

trace_store: OrderedDict[str, dict[str, Any]] = OrderedDict()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None)
            or correlation_id_ctx.get(),
        }

        for key in ("errors", "attempt"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


def get_correlation_id(request: Request) -> str:
    header_value = request.headers.get(CORRELATION_ID_HEADER)
    if header_value and header_value.strip():
        return header_value.strip()
    return str(uuid.uuid4())


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        correlation_id = get_correlation_id(request)
        request.state.correlation_id = correlation_id
        token = correlation_id_ctx.set(correlation_id)

        try:
            response = await call_next(request)
        finally:
            correlation_id_ctx.reset(token)

        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response


def save_trace(correlation_id: str, steps: list[dict[str, Any]]) -> None:
    if correlation_id in trace_store:
        del trace_store[correlation_id]

    trace_store[correlation_id] = {
        "correlation_id": correlation_id,
        "steps": steps,
    }

    while len(trace_store) > MAX_TRACE_ENTRIES:
        trace_store.popitem(last=False)


def get_trace(correlation_id: str) -> dict[str, Any] | None:
    return trace_store.get(correlation_id)


def build_search_filters(request_data: dict[str, Any]) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    for key in ("environment", "service", "severity", "tags"):
        value = request_data.get(key)
        if value is not None:
            filters[key] = value
    return filters


router = APIRouter(tags=["debug"])


@router.get("/debug/trace/{correlation_id}")
def get_trace_by_correlation_id(correlation_id: str) -> dict[str, Any]:
    trace = get_trace(correlation_id)
    if trace is None:
        raise HTTPException(
            status_code=404,
            detail=f"Trace not found: {correlation_id}",
        )
    return trace
