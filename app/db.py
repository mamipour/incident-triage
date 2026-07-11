"""SQLite database initialization and helpers."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from app.config import get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    environment TEXT NOT NULL,
    service TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    resolution_summary TEXT NOT NULL,
    tags TEXT NOT NULL,
    content_hash TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS incidents_fts USING fts5(
    title,
    description,
    resolution_summary,
    content='incidents',
    content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS incidents_ai AFTER INSERT ON incidents BEGIN
    INSERT INTO incidents_fts(rowid, title, description, resolution_summary)
    VALUES (new.rowid, new.title, new.description, new.resolution_summary);
END;

CREATE TRIGGER IF NOT EXISTS incidents_ad AFTER DELETE ON incidents BEGIN
    INSERT INTO incidents_fts(incidents_fts, rowid, title, description, resolution_summary)
    VALUES ('delete', old.rowid, old.title, old.description, old.resolution_summary);
END;

CREATE TRIGGER IF NOT EXISTS incidents_au AFTER UPDATE ON incidents BEGIN
    INSERT INTO incidents_fts(incidents_fts, rowid, title, description, resolution_summary)
    VALUES ('delete', old.rowid, old.title, old.description, old.resolution_summary);
    INSERT INTO incidents_fts(rowid, title, description, resolution_summary)
    VALUES (new.rowid, new.title, new.description, new.resolution_summary);
END;
"""


def compute_content_hash(incident: dict[str, Any]) -> str:
    """Return SHA-256 of canonical incident content (excluding id)."""
    tags = incident["tags"]
    if isinstance(tags, list):
        tags = sorted(tags)

    payload = {
        "created_at": incident["created_at"],
        "description": incident["description"],
        "environment": incident["environment"],
        "resolution_summary": incident["resolution_summary"],
        "service": incident["service"],
        "severity": incident["severity"],
        "tags": tags,
        "title": incident["title"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def serialize_tags(tags: list[str]) -> str:
    return json.dumps(tags)


def parse_tags(tags_json: str) -> list[str]:
    return json.loads(tags_json)


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def row_to_incident(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "environment": row["environment"],
        "service": row["service"],
        "severity": row["severity"],
        "title": row["title"],
        "description": row["description"],
        "resolution_summary": row["resolution_summary"],
        "tags": parse_tags(row["tags"]),
    }
