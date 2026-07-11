from fastapi import APIRouter, HTTPException

from app.db import get_connection, row_to_incident
from app.models import IncidentRecord

router = APIRouter(tags=["incidents"])


def get_incident_by_id(incident_id: str) -> IncidentRecord:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM incidents WHERE id = ?",
            (incident_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Incident not found: {incident_id}",
        )

    return IncidentRecord.model_validate(row_to_incident(row))


@router.get("/incidents/{incident_id}", response_model=IncidentRecord)
def get_incident(incident_id: str) -> IncidentRecord:
    return get_incident_by_id(incident_id)
