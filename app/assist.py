from typing import Union

from fastapi import APIRouter, HTTPException, Request

from app.assist_service import llm_error_response, run_assist
from app.models import AssistNoResultsResponse, AssistRequest, AssistResponse
from app.prompt_injection import check_prompt_injection

router = APIRouter(tags=["assist"])

AssistResponseUnion = Union[AssistResponse, AssistNoResultsResponse]


@router.post("/assist", response_model=AssistResponseUnion)
def assist(request: AssistRequest, http_request: Request) -> AssistResponseUnion:
    correlation_id = http_request.state.correlation_id

    if check_prompt_injection(request.question):
        raise HTTPException(
            status_code=422,
            detail="Prompt injection detected in question",
        )

    try:
        return run_assist(request, correlation_id)
    except HTTPException as exc:
        if exc.status_code == 503:
            return llm_error_response(exc, correlation_id)
        raise
