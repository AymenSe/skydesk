from uuid import uuid4

import pytest

VALID = {"customer_email": "ana@example.com", "message": "My bag did not arrive in Lisbon"}


def test_create_ticket_is_accepted(client):
    response = client.post("/tickets", json=VALID)
    assert response.status_code == 202
    assert response.json()["intent"] == "baggage"
    assert response.json()["status"] == "queued"


def test_get_ticket_round_trip(client):
    ticket_id = client.post("/tickets", json=VALID).json()["id"]
    response = client.get(f"/tickets/{ticket_id}")
    assert response.status_code == 200
    assert response.json()["message"] == VALID["message"]
    assert response.json()["draft_reply"] is None


def test_unknown_ticket_is_404(client):
    assert client.get(f"/tickets/{uuid4()}").status_code == 404


@pytest.mark.parametrize("intent", ["complaint", "other"])
def test_complaints_and_unclear_messages_are_escalated(client, classifier, intent):
    classifier.intent = intent
    assert client.post("/tickets", json=VALID).json()["status"] == "escalated"


def test_list_filters_by_status(client, classifier):
    client.post("/tickets", json=VALID)
    classifier.intent = "complaint"
    client.post("/tickets", json=VALID)
    escalated = client.get("/tickets", params={"status": "escalated"}).json()
    assert len(escalated) == 1
    assert escalated[0]["intent"] == "complaint"


def test_invalid_input_is_422(client):
    bad = {"customer_email": "nope", "message": "hi"}
    assert client.post("/tickets", json=bad).status_code == 422
