from fastapi import APIRouter, HTTPException

from app.models import AssistRequest, AssistResponse

router = APIRouter(tags=["assist"])


@router.post("/assist", response_model=AssistResponse)
def assist(request: AssistRequest) -> AssistResponse:
    raise HTTPException(status_code=501, detail="Assist not implemented yet")
