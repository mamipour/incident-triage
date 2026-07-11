from app.guardrails import validate_assist_output
from app.models import RelevantIncident


CANDIDATE_IDS = {"INC-00001", "INC-00002", "INC-00003"}


def test_validate_assist_output_accepts_grounded_response():
    errors = validate_assist_output(
        relevant_incidents=[
            RelevantIncident(
                id="INC-00001",
                reason="Matches database timeout symptoms described in the record.",
            )
        ],
        next_steps=["Review connection pool settings for INC-00001."],
        customer_draft="We found incident INC-00001 related to your database timeout report.",
        candidate_ids=CANDIDATE_IDS,
    )

    assert errors == []


def test_validate_assist_output_rejects_cited_id_not_in_candidate_set():
    errors = validate_assist_output(
        relevant_incidents=[
            RelevantIncident(id="INC-99999", reason="Looks relevant."),
        ],
        next_steps=[],
        customer_draft="",
        candidate_ids=CANDIDATE_IDS,
    )

    assert any("not in candidate set" in error for error in errors)


def test_validate_assist_output_rejects_missing_reason():
    errors = validate_assist_output(
        relevant_incidents=[
            RelevantIncident(id="INC-00001", reason="   "),
        ],
        next_steps=[],
        customer_draft="",
        candidate_ids=CANDIDATE_IDS,
    )

    assert any("Missing reason" in error for error in errors)


def test_validate_assist_output_rejects_unknown_id_in_customer_draft():
    errors = validate_assist_output(
        relevant_incidents=[
            RelevantIncident(id="INC-00001", reason="Related to database timeouts."),
        ],
        next_steps=[],
        customer_draft="This matches incident INC-00444 from last week.",
        candidate_ids=CANDIDATE_IDS,
    )

    assert any("Referenced unknown incident ID: INC-00444" in error for error in errors)


def test_validate_assist_output_rejects_unknown_id_in_next_steps():
    errors = validate_assist_output(
        relevant_incidents=[
            RelevantIncident(id="INC-00002", reason="Auth failures after deploy."),
        ],
        next_steps=["Compare logs with INC-00099 for similar token errors."],
        customer_draft="",
        candidate_ids=CANDIDATE_IDS,
    )

    assert any("Referenced unknown incident ID: INC-00099" in error for error in errors)


def test_validate_assist_output_rejects_unknown_id_in_reason_text():
    errors = validate_assist_output(
        relevant_incidents=[
            RelevantIncident(
                id="INC-00003",
                reason="Similar to INC-00088 where queue backlog caused delays.",
            ),
        ],
        next_steps=[],
        customer_draft="",
        candidate_ids=CANDIDATE_IDS,
    )

    assert any("Referenced unknown incident ID: INC-00088" in error for error in errors)
