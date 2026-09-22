"""API integration test: acceptance scenario 1 from SPEC.md against a live server.

Runs against the real running API and its real database (SQLite or PostgreSQL):

    RELAY_BASE_URL=http://127.0.0.1:8000 uv run pytest test_integration.py -q

Registers two agents, sends a task, claims it as the recipient, completes it,
and asserts the sender sees the completed result.
"""

from __future__ import annotations

import os

import httpx
import pytest

BASE_URL = os.getenv("RELAY_BASE_URL", "http://127.0.0.1:8000")


@pytest.fixture(scope="module")
def client() -> httpx.Client:
    # trust_env=False: this machine runs a local system proxy that would
    # otherwise intercept 127.0.0.1 requests and answer 502.
    with httpx.Client(base_url=BASE_URL, timeout=30, trust_env=False) as http:
        yield http


def register(client: httpx.Client, name: str) -> dict:
    response = client.post("/api/v1/agents", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def test_agents_exchange_task_and_result(client: httpx.Client):
    sender = register(client, "integration-sender")
    recipient = register(client, "integration-worker")
    sender_auth = {"Authorization": f"Bearer {sender['token']}"}
    recipient_auth = {"Authorization": f"Bearer {recipient['token']}"}

    # sender sends a task to the recipient
    response = client.post(
        "/api/v1/tasks",
        json={"to": recipient["agent_id"], "input": "hello agent relay"},
        headers=sender_auth,
    )
    assert response.status_code == 201, response.text
    task_id = response.json()["task_id"]
    assert response.json()["status"] == "queued"

    # recipient claims the task
    response = client.post(
        "/api/v1/tasks/claim",
        json={"worker_id": "integration-laptop-1", "wait_seconds": 0},
        headers=recipient_auth,
    )
    assert response.status_code == 200, response.text
    claim = response.json()
    assert claim["task_id"] == task_id
    assert claim["input"] == "hello agent relay"

    # recipient completes it with the claim token
    response = client.post(
        f"/api/v1/tasks/{task_id}/complete",
        json={"claim_token": claim["claim_token"], "output": "HELLO AGENT RELAY"},
        headers=recipient_auth,
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "completed"

    # sender reads the result
    response = client.get(f"/api/v1/tasks/{task_id}", headers=sender_auth)
    assert response.status_code == 200, response.text
    task = response.json()
    assert task["status"] == "completed"
    assert task["output"] == "HELLO AGENT RELAY"
    assert task["error"] is None
    assert task["finished_at"] is not None
