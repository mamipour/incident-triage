from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.config import get_settings
from app.db import compute_content_hash, get_connection, serialize_tags
from app.models import IncidentRecord, IngestResponse

router = APIRouter(tags=["ingest"])


def load_incidents_from_file(data_path: Path) -> list[IncidentRecord]:
    if not data_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Data file not found: {data_path}. Run `python3 generate_data.py` first.",
        )

    try:
        payload = json.loads(data_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid JSON in data file: {exc.msg}",
        ) from exc

    if not isinstance(payload, list):
        raise HTTPException(status_code=422, detail="Data file must contain a JSON array")

    records: list[IncidentRecord] = []
    for index, item in enumerate(payload):
        try:
            records.append(IncidentRecord.model_validate(item))
        except ValidationError as exc:
            raise HTTPException(
                status_code=422,
                detail={"index": index, "errors": exc.errors()},
            ) from exc

    return records


def ingest_incidents(records: list[IncidentRecord]) -> IngestResponse:
    ingested = 0
    skipped = 0
    updated = 0

    with get_connection() as conn:
        for record in records:
            incident = record.model_dump()
            content_hash = compute_content_hash(incident)

            existing = conn.execute(
                "SELECT content_hash FROM incidents WHERE id = ?",
                (record.id,),
            ).fetchone()

            if existing is not None and existing["content_hash"] == content_hash:
                skipped += 1
                continue

            if existing is None:
                conn.execute(
                    """
                    INSERT INTO incidents (
                        id, created_at, environment, service, severity,
                        title, description, resolution_summary, tags, content_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.id,
                        record.created_at,
                        record.environment,
                        record.service,
                        record.severity,
                        record.title,
                        record.description,
                        record.resolution_summary,
                        serialize_tags(record.tags),
                        content_hash,
                    ),
                )
                ingested += 1
            else:
                conn.execute(
                    """
                    UPDATE incidents SET
                        created_at = ?,
                        environment = ?,
                        service = ?,
                        severity = ?,
                        title = ?,
                        description = ?,
                        resolution_summary = ?,
                        tags = ?,
                        content_hash = ?
                    WHERE id = ?
                    """,
                    (
                        record.created_at,
                        record.environment,
                        record.service,
                        record.severity,
                        record.title,
                        record.description,
                        record.resolution_summary,
                        serialize_tags(record.tags),
                        content_hash,
                        record.id,
                    ),
                )
                updated += 1

    return IngestResponse(ingested=ingested, skipped=skipped, updated=updated)


@router.post("/ingest", response_model=IngestResponse)
def ingest() -> IngestResponse:
    settings = get_settings()
    records = load_incidents_from_file(Path(settings.data_path))
    return ingest_incidents(records)
