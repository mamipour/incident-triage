import pytest

from app.config import get_settings
from app.db import compute_content_hash, get_connection, init_db, serialize_tags


@pytest.fixture
def search_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    get_settings.cache_clear()
    init_db()

    incidents = [
        {
            "id": "INC-00001",
            "created_at": "2026-01-01T00:00:00Z",
            "environment": "prod",
            "service": "payment-api",
            "severity": "critical",
            "title": "Database connection pool exhausted on payment-api",
            "description": "Monitoring alerted on payment-api in prod: all database connections in use.",
            "resolution_summary": "Increased pool size and terminated long-running queries.",
            "tags": ["database", "timeout"],
        },
        {
            "id": "INC-00002",
            "created_at": "2026-01-02T00:00:00Z",
            "environment": "dev",
            "service": "user-auth",
            "severity": "low",
            "title": "Authentication failures after user-auth deploy",
            "description": "Following a deployment to dev, user-auth began rejecting valid tokens.",
            "resolution_summary": "Rolled back the deployment and rotated signing keys.",
            "tags": ["auth", "deployment"],
        },
        {
            "id": "INC-00003",
            "created_at": "2026-01-03T00:00:00Z",
            "environment": "prod",
            "service": "payment-api",
            "severity": "high",
            "title": "Connection timeout on payment-api",
            "description": "Users reported widespread timeout failures when calling payment-api in prod.",
            "resolution_summary": "Scaled payment-api replicas and restarted unhealthy pods.",
            "tags": ["timeout", "api"],
        },
    ]

    with get_connection() as conn:
        for incident in incidents:
            content_hash = compute_content_hash(incident)
            conn.execute(
                """
                INSERT INTO incidents (
                    id, created_at, environment, service, severity,
                    title, description, resolution_summary, tags, content_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident["id"],
                    incident["created_at"],
                    incident["environment"],
                    incident["service"],
                    incident["severity"],
                    incident["title"],
                    incident["description"],
                    incident["resolution_summary"],
                    serialize_tags(incident["tags"]),
                    content_hash,
                ),
            )

    yield

    get_settings.cache_clear()
