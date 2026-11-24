"""Tests for the REST API, team access and HTML page safety."""

import pytest
from fastapi.testclient import TestClient

from app.models import Priority
from app.priority import assign_priority
from app.replies import DraftResult
from tests.conftest import VALID_TICKET


def create(client: TestClient, message: str = VALID_TICKET["message"]) -> dict:
    """Create a ticket and return its JSON."""
    response = client.post("/api/tickets", json={**VALID_TICKET, "message": message})
    assert response.status_code == 201
    return response.json()


def error_fields(response) -> set[str]:
    """The field names in a 422 response."""
    return {error["field"] for error in response.json()["errors"]}


def test_create_ticket_returns_201_with_prediction(client: TestClient) -> None:
    """A valid ticket is stored with a category, confidence, priority and open status."""
    ticket = create(client)
    assert ticket["id"] == 1
    assert ticket["category"] == "ORDER"
    assert 0 <= ticket["category_confidence"] <= 1
    assert ticket["priority"] == "medium"
    assert ticket["status"] == "open"


def test_bad_email_returns_422(client: TestClient) -> None:
    """An invalid email names the email field."""
    response = client.post("/api/tickets", json={**VALID_TICKET, "email": "not-an-email"})
    assert response.status_code == 422
    assert error_fields(response) == {"email"}


@pytest.mark.parametrize("message", ["", "    ", "hi"])
def test_empty_or_short_message_returns_422(client: TestClient, message: str) -> None:
    """Blank and too-short messages are rejected after trimming."""
    response = client.post("/api/tickets", json={**VALID_TICKET, "message": message})
    assert response.status_code == 422
    assert error_fields(response) == {"message"}


def test_message_over_limit_returns_422(client: TestClient) -> None:
    """A message longer than 2000 characters is rejected."""
    response = client.post("/api/tickets", json={**VALID_TICKET, "message": "x" * 2001})
    assert response.status_code == 422


@pytest.mark.parametrize("method,url,body", [
    ("get", "/api/tickets", None),
    ("get", "/api/tickets/1", None),
    ("patch", "/api/tickets/1/status", {"status": "closed"}),
    ("post", "/api/tickets/1/draft", None),
])
def test_team_endpoints_require_login(client: TestClient, method: str, url: str,
                                      body: dict | None) -> None:
    """Every team endpoint returns 401 when logged out."""
    create(client)
    response = client.request(method, url, json=body)
    assert response.status_code == 401


def test_wrong_password_returns_401(client: TestClient) -> None:
    """A wrong password does not log the client in."""
    response = client.post("/api/login", json={"username": "tester", "password": "wrong"})
    assert response.status_code == 401
    assert client.get("/api/tickets").status_code == 401


def test_list_and_filter_by_category(team_client: TestClient) -> None:
    """The category filter returns only matching tickets."""
    order = create(team_client)
    newsletter = create(team_client, "how do i unsubscribe from the newsletter")
    assert [t["id"] for t in team_client.get("/api/tickets").json()] == [newsletter["id"], order["id"]]
    filtered = team_client.get("/api/tickets", params={"category": "SUBSCRIPTION"}).json()
    assert [t["id"] for t in filtered] == [newsletter["id"]]


def test_unknown_category_returns_422(team_client: TestClient) -> None:
    """An unknown filter value is a clear error."""
    assert team_client.get("/api/tickets", params={"category": "NOPE"}).status_code == 422


def test_valid_status_update_persists(team_client: TestClient) -> None:
    """A status change is still there on the next read."""
    ticket = create(team_client)
    response = team_client.patch(f"/api/tickets/{ticket['id']}/status", json={"status": "closed"})
    assert response.status_code == 200
    assert team_client.get(f"/api/tickets/{ticket['id']}").json()["status"] == "closed"


def test_invalid_status_returns_422(team_client: TestClient) -> None:
    """A status outside the allowed values is rejected and changes nothing."""
    ticket = create(team_client)
    response = team_client.patch(f"/api/tickets/{ticket['id']}/status", json={"status": "done"})
    assert response.status_code == 422
    assert team_client.get(f"/api/tickets/{ticket['id']}").json()["status"] == "open"


@pytest.mark.parametrize("method,url,body", [
    ("get", "/api/tickets/999", None),
    ("patch", "/api/tickets/999/status", {"status": "closed"}),
    ("post", "/api/tickets/999/draft", None),
])
def test_unknown_id_returns_404(team_client: TestClient, method: str, url: str,
                                body: dict | None) -> None:
    """Unknown ticket ids return 404."""
    assert team_client.request(method, url, json=body).status_code == 404


def test_draft_is_saved_on_ticket(team_client: TestClient) -> None:
    """The background task stores the draft and its FAQ ids."""
    ticket = create(team_client)
    saved = team_client.get(f"/api/tickets/{ticket['id']}").json()
    assert saved["draft_status"] == "ready"
    assert saved["draft_reply"] == "Fake draft"
    assert saved["used_faq_ids"] == ["FAQ-01"]


def test_llm_failure_keeps_ticket_and_marks_draft_failed(
        team_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """If drafting fails, the ticket still exists with a failed draft."""
    monkeypatch.setattr("app.tickets.draft_reply",
                        lambda _text: DraftResult("Fallback", error="LLM down"))
    ticket = create(team_client)
    saved = team_client.get(f"/api/tickets/{ticket['id']}").json()
    assert saved["draft_status"] == "failed"
    assert saved["draft_error"] == "LLM down"


def test_team_page_redirects_to_login(client: TestClient) -> None:
    """A logged-out browser is sent to the login page."""
    response = client.get("/team", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_logged_out_status_form_changes_nothing(client: TestClient) -> None:
    """The HTML status form cannot be used without logging in."""
    ticket = create(client)
    response = client.post(f"/team/tickets/{ticket['id']}/status", data={"status": "closed"},
                           follow_redirects=False)
    assert response.status_code == 303
    client.post("/api/login", json={"username": "tester", "password": "test-password"})
    assert client.get(f"/api/tickets/{ticket['id']}").json()["status"] == "open"


def test_ticket_page_escapes_html(team_client: TestClient) -> None:
    """Customer text is displayed as text, never as HTML."""
    ticket = create(team_client, "<script>alert(1)</script> refund please")
    page = team_client.get(f"/team/tickets/{ticket['id']}").text
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page


@pytest.mark.parametrize("message,category,expected", [
    ("I was charged twice", "PAYMENT", Priority.high),
    ("please help ASAP", "CONTACT", Priority.high),
    ("where is my order", "ORDER", Priority.medium),
    ("your service is terrible", "FEEDBACK", Priority.medium),
    ("how do i join the newsletter", "SUBSCRIPTION", Priority.low),
])
def test_priority_rules(message: str, category: str, expected: Priority) -> None:
    """Priority follows the documented rules."""
    assert assign_priority(message, category) == expected
