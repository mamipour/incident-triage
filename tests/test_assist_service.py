from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.assist_service import call_llm, normalize_llm_payload, parse_llm_response


def test_parse_llm_response_rejects_non_object():
    with pytest.raises(ValueError, match="JSON object"):
        parse_llm_response("[]")


def test_normalize_llm_payload_rejects_invalid_shape():
    with pytest.raises(ValueError, match="relevant_incidents must be a list"):
        normalize_llm_payload(
            {"relevant_incidents": "bad", "next_steps": [], "customer_draft": ""}
        )


@patch("app.assist_service.get_settings")
@patch("app.assist_service.OpenAI")
def test_call_llm_returns_503_on_malformed_json(mock_openai, mock_settings):
    mock_settings.return_value.llm_api_key = "test-key"
    mock_settings.return_value.llm_model = "gpt-4o-mini"

    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="{not valid json"))
    ]

    with pytest.raises(HTTPException) as exc_info:
        call_llm("database timeout", [])

    assert exc_info.value.status_code == 503
    assert "invalid JSON" in exc_info.value.detail["detail"]
