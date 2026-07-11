"""Pydantic request and response models."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

Environment = Literal["dev", "qa", "stage", "prod"]
Severity = Literal["critical", "high", "medium", "low"]


def parse_tags_filter(value: str | None) -> list[str] | None:
    if value is None:
        return None

    tags = [tag.strip() for tag in value.split(",") if tag.strip()]
    if not tags:
        raise ValueError("tags must contain at least one non-empty value")
    return tags


class IncidentRecord(BaseModel):
    id: str
    created_at: str
    environment: Environment
    service: str
    severity: Severity
    title: str
    description: str
    resolution_summary: str
    tags: list[str]


class IngestResponse(BaseModel):
    ingested: int
    skipped: int
    updated: int


class SearchResultItem(BaseModel):
    id: str
    title: str
    snippet: str
    score: float
    environment: Environment
    service: str
    severity: Severity
    tags: list[str]


class SearchResponse(BaseModel):
    total: int
    results: list[SearchResultItem]


class SearchParams(BaseModel):
    q: str
    environment: Environment | None = None
    service: str | None = None
    severity: Severity | None = None
    tags: list[str] | None = None

    @field_validator("q")
    @classmethod
    def validate_q(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("q must not be empty or whitespace")
        return stripped

    @field_validator("service")
    @classmethod
    def validate_service(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("service must not be empty or whitespace")
        return stripped


class AssistRequest(BaseModel):
    question: str = Field(..., max_length=1000)
    environment: Environment | None = None
    service: str | None = None
    severity: Severity | None = None
    tags: list[str] | None = None

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question must not be empty or whitespace")
        return stripped

    @field_validator("service")
    @classmethod
    def validate_service(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("service must not be empty or whitespace")
        return stripped

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned = [tag.strip() for tag in value if tag.strip()]
        if not cleaned:
            raise ValueError("tags must contain at least one non-empty value")
        return cleaned


class RelevantIncident(BaseModel):
    id: str
    reason: str


class AssistResponse(BaseModel):
    relevant_incidents: list[RelevantIncident]
    next_steps: list[str]
    customer_draft: str
    correlation_id: str


class AssistNoResultsResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str
    detail: str
    correlation_id: str


TagsQuery = Annotated[str | None, Field(description="Comma-separated tags (OR semantics)")]
