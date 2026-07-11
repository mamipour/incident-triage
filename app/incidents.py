from fastapi import APIRouter, HTTPException

from app.db import get_connection, row_to_incident
from app.models import IncidentRecord

router = APIRouter(tags=["incidents"])


def get_incidents_by_ids(incident_ids: list[str]) -> list[IncidentRecord]:
    if not incident_ids:
        return []

    placeholders = ", ".join("?" for _ in incident_ids)
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM incidents WHERE id IN ({placeholders})",
            incident_ids,
        ).fetchall()

    records_by_id = {
        row["id"]: IncidentRecord.model_validate(row_to_incident(row)) for row in rows
    }
    return [records_by_id[incident_id] for incident_id in incident_ids if incident_id in records_by_id]


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
