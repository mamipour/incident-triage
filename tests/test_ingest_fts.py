from app.db import get_connection, init_db
from app.ingest import ingest_incidents
from app.models import IncidentRecord, SearchParams
from app.search_service import search_incidents


def _sample_record(**overrides) -> IncidentRecord:
    data = {
        "id": "INC-00099",
        "created_at": "2026-01-01T00:00:00Z",
        "environment": "prod",
        "service": "payment-api",
        "severity": "high",
        "title": "UniqueOldTitle marker",
        "description": "Initial description for FTS sync test.",
        "resolution_summary": "Initial resolution.",
        "tags": ["database"],
    }
    data.update(overrides)
    return IncidentRecord.model_validate(data)


def test_ingest_update_syncs_fts_index(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    from app.config import get_settings

    get_settings.cache_clear()
    init_db()

    original = _sample_record()
    ingest_incidents([original])

    with get_connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM incidents_fts WHERE incidents_fts MATCH 'UniqueOldTitle'"
        ).fetchone()[0] == 1

    updated = _sample_record(
        title="UniqueNewTitle marker",
        description="Updated description for FTS sync test.",
    )
    result = ingest_incidents([updated])
    assert result.model_dump() == {"ingested": 0, "skipped": 0, "updated": 1}

    with get_connection() as conn:
        old_hits = conn.execute(
            "SELECT COUNT(*) FROM incidents_fts WHERE incidents_fts MATCH 'UniqueOldTitle'"
        ).fetchone()[0]
        new_hits = conn.execute(
            "SELECT COUNT(*) FROM incidents_fts WHERE incidents_fts MATCH 'UniqueNewTitle'"
        ).fetchone()[0]

    assert old_hits == 0
    assert new_hits == 1

    get_settings.cache_clear()


def test_assist_search_uses_or_operator(search_db):
    and_results = search_incidents(
        SearchParams(q="database timeout in prod"),
        fts_operator="AND",
    )
    or_results = search_incidents(
        SearchParams(q="database timeout in prod"),
        fts_operator="OR",
    )

    assert and_results.total == 0
    assert or_results.total >= 1
