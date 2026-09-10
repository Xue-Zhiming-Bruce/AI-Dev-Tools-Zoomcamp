import yaml
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_yaml_is_valid_and_covers_contract():
    with open("openapi.yaml") as f:
        spec = yaml.safe_load(f)
    assert spec["openapi"].startswith("3.")
    expected_paths = {
        "/health",
        "/columns",
        "/columns/reorder",
        "/columns/{column_id}",
        "/columns/{column_id}/cards",
        "/cards/{card_id}",
        "/cards/{card_id}/move",
    }
    assert expected_paths == set(spec["paths"])
    card_fields = set(spec["components"]["schemas"]["Card"]["properties"])
    assert card_fields == {"id", "column_id", "title", "notes", "due_date"}
    assert set(spec["components"]["schemas"]["CardCreate"]["required"]) == {"title"}
