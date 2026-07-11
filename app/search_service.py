"""Shared incident search over SQLite FTS5."""

from __future__ import annotations

from app.db import get_connection, parse_tags
from app.models import SearchParams, SearchResponse, SearchResultItem

MAX_RESULTS = 10
SNIPPET_LENGTH = 150


def build_fts_query(q: str) -> str:
    """Build a simple token AND FTS5 query."""
    tokens = q.split()
    quoted = [f'"{token.replace('"', '""')}"' for token in tokens]
    return " AND ".join(quoted)


def _build_filter_clauses(params: SearchParams) -> tuple[list[str], list[object]]:
    clauses: list[str] = []
    values: list[object] = []

    if params.environment is not None:
        clauses.append("i.environment = ?")
        values.append(params.environment)

    if params.service is not None:
        clauses.append("i.service = ?")
        values.append(params.service)

    if params.severity is not None:
        clauses.append("i.severity = ?")
        values.append(params.severity)

    if params.tags:
        placeholders = ", ".join("?" for _ in params.tags)
        clauses.append(
            f"""
            EXISTS (
                SELECT 1 FROM json_each(i.tags) AS je
                WHERE je.value IN ({placeholders})
            )
            """
        )
        values.extend(params.tags)

    return clauses, values


def search_incidents(
    params: SearchParams,
    limit: int = MAX_RESULTS,
) -> SearchResponse:
    fts_query = build_fts_query(params.q)
    filter_clauses, filter_values = _build_filter_clauses(params)

    where_parts = ["incidents_fts MATCH ?"]
    where_values: list[object] = [fts_query]
    where_parts.extend(filter_clauses)
    where_values.extend(filter_values)

    where_clause = " AND ".join(where_parts)
    from_clause = """
        FROM incidents i
        INNER JOIN incidents_fts ON incidents_fts.rowid = i.rowid
    """

    count_sql = f"SELECT COUNT(*) {from_clause} WHERE {where_clause}"
    search_sql = f"""
        SELECT
            i.id,
            i.title,
            i.description,
            i.environment,
            i.service,
            i.severity,
            i.tags,
            -(incidents_fts.rank) AS score
        {from_clause}
        WHERE {where_clause}
        ORDER BY incidents_fts.rank
        LIMIT ?
    """

    with get_connection() as conn:
        total = conn.execute(count_sql, where_values).fetchone()[0]
        rows = conn.execute(search_sql, [*where_values, limit]).fetchall()

    results = [
        SearchResultItem(
            id=row["id"],
            title=row["title"],
            snippet=row["description"][:SNIPPET_LENGTH],
            score=float(row["score"]),
            environment=row["environment"],
            service=row["service"],
            severity=row["severity"],
            tags=parse_tags(row["tags"]),
        )
        for row in rows
    ]

    return SearchResponse(total=total, results=results)
