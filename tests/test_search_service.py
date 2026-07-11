from app.models import SearchParams
from app.search_service import _build_filter_clauses, build_fts_query, search_incidents


def test_build_fts_query_single_token():
    assert build_fts_query("database") == '"database"'


def test_build_fts_query_token_and():
    assert build_fts_query("database timeout") == '"database" AND "timeout"'


def test_build_fts_query_escapes_quotes():
    assert build_fts_query('foo "bar"') == '"foo" AND """bar"""'


def test_build_filter_clauses_empty():
    clauses, values = _build_filter_clauses(SearchParams(q="database"))
    assert clauses == []
    assert values == []


def test_build_filter_clauses_and_combination():
    params = SearchParams(
        q="database",
        environment="prod",
        service="payment-api",
        severity="critical",
    )
    clauses, values = _build_filter_clauses(params)

    assert len(clauses) == 3
    assert "i.environment = ?" in clauses
    assert "i.service = ?" in clauses
    assert "i.severity = ?" in clauses
    assert values == ["prod", "payment-api", "critical"]


def test_build_filter_clauses_tags_or():
    params = SearchParams(q="database", tags=["timeout", "auth"])
    clauses, values = _build_filter_clauses(params)

    assert len(clauses) == 1
    assert "json_each(i.tags)" in clauses[0]
    assert "je.value IN (?, ?)" in clauses[0]
    assert values == ["timeout", "auth"]


def test_search_applies_environment_filter(search_db):
    response = search_incidents(SearchParams(q="database", environment="prod"))

    assert response.total == 1
    assert len(response.results) == 1
    assert response.results[0].id == "INC-00001"


def test_search_applies_combined_filters_with_and(search_db):
    response = search_incidents(
        SearchParams(
            q="payment",
            environment="prod",
            service="payment-api",
            severity="high",
        )
    )

    assert response.total == 1
    assert response.results[0].id == "INC-00003"


def test_search_tags_filter_uses_or_semantics(search_db):
    response = search_incidents(SearchParams(q="payment", tags=["auth"]))

    assert response.total == 0

    response = search_incidents(SearchParams(q="payment", tags=["timeout", "auth"]))

    assert response.total == 2
    result_ids = {item.id for item in response.results}
    assert result_ids == {"INC-00001", "INC-00003"}


def test_search_snippet_is_plain_text_truncated_description(search_db):
    response = search_incidents(SearchParams(q="database"))

    assert response.results[0].snippet == response.results[0].snippet.strip()
    assert len(response.results[0].snippet) <= 150
    assert "Monitoring alerted" in response.results[0].snippet


def test_search_results_ordered_by_score_descending(search_db):
    response = search_incidents(SearchParams(q="payment"))

    scores = [item.score for item in response.results]
    assert scores == sorted(scores, reverse=True)
