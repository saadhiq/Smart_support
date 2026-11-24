"""Test settings and fixtures: fake credentials, temporary SQLite and a fake LLM."""

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="supportdesk-tests-"))
os.environ.update({
    "TEAM_USERNAME": "tester",
    "TEAM_PASSWORD": "test-password",
    "SESSION_SECRET": "test-secret-not-for-production",
    "DATABASE_URL": f"sqlite:///{(_TMP / 'test.db').as_posix()}",
    "GEMINI_API_KEY": "",
})

from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402

from app.db import get_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.replies import DraftResult  # noqa: E402

VALID_TICKET = {
    "name": "Ann",
    "email": "ann@example.com",
    "message": "I want to cancel my order please",
}


@pytest.fixture(autouse=True)
def fake_draft(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace reply drafting so no test can call the real LLM."""
    monkeypatch.setattr("app.tickets.draft_reply",
                        lambda _text: DraftResult("Fake draft", ["FAQ-01"]))


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A logged-out client with an empty database."""
    with TestClient(app) as test_client:
        SQLModel.metadata.drop_all(get_engine())
        SQLModel.metadata.create_all(get_engine())
        yield test_client


@pytest.fixture
def team_client(client: TestClient) -> TestClient:
    """The same client, logged in as the team."""
    response = client.post("/api/login", json={"username": "tester", "password": "test-password"})
    assert response.status_code == 200
    return client
