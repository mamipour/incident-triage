from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError

from app.models import (
    Environment,
    SearchParams,
    SearchResponse,
    Severity,
    TagsQuery,
    parse_tags_filter,
)
from app.search_service import search_incidents

router = APIRouter(tags=["search"])


def format_validation_errors(exc: ValidationError) -> list[dict[str, object]]:
    return [
        {
            "loc": list(error["loc"]),
            "msg": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]


def get_search_params(
    q: str = Query(..., description="Text query"),
    environment: Environment | None = Query(None),
    service: str | None = Query(None),
    severity: Severity | None = Query(None),
    tags: TagsQuery = Query(None),
) -> SearchParams:
    try:
        parsed_tags = parse_tags_filter(tags)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        return SearchParams.model_validate(
            {
                "q": q,
                "environment": environment,
                "service": service,
                "severity": severity,
                "tags": parsed_tags,
            }
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=format_validation_errors(exc),
        ) from exc


@router.get("/search", response_model=SearchResponse)
def search(params: SearchParams = Depends(get_search_params)) -> SearchResponse:
    return search_incidents(params)
