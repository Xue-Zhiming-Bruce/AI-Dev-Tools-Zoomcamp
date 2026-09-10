"""Tests for the MyKanban API (issue #10).

Written before the implementations (tests-first). Covers every endpoint in
openapi.yaml plus the resolved decisions: 0-based positions, clamped moves,
full-set reorder validation, partial PATCH with null clearing, append-on-create.
"""

from fastapi.testclient import TestClient

from app.main import app
from app import store


def client() -> TestClient:
    store.reset()
    return TestClient(app)


def make_card(c: TestClient, column_id: int, title: str) -> dict:
    r = c.post(f"/columns/{column_id}/cards", json={"title": title})
    assert r.status_code == 201
    return r.json()


def columns(c: TestClient) -> list[dict]:
    r = c.get("/columns")
    assert r.status_code == 200
    return r.json()


# --- /health ---


def test_health():
    c = client()
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# --- fresh board seeding ---


def test_fresh_store_seeds_default_board():
    c = client()
    cols = columns(c)
    assert [col["title"] for col in cols] == ["To Do", "Doing", "Done"]
    assert [col["position"] for col in cols] == [0, 1, 2]
    assert all(col["cards"] == [] for col in cols)


# --- columns: list/create/rename/delete/reorder ---


def test_create_column_appends_at_end():
    c = client()
    r = c.post("/columns", json={"title": "Blocked"})
    assert r.status_code == 201
    col = r.json()
    assert col["title"] == "Blocked"
    assert col["position"] == 3
    assert col["cards"] == []
    assert [x["title"] for x in columns(c)] == ["To Do", "Doing", "Done", "Blocked"]


def test_create_column_requires_title():
    c = client()
    r = c.post("/columns", json={})
    assert r.status_code == 422


def test_rename_column():
    c = client()
    col_id = columns(c)[0]["id"]
    r = c.patch(f"/columns/{col_id}", json={"title": "Backlog"})
    assert r.status_code == 200
    assert r.json()["title"] == "Backlog"
    assert columns(c)[0]["title"] == "Backlog"


def test_rename_missing_column_404():
    c = client()
    r = c.patch("/columns/9999", json={"title": "Nope"})
    assert r.status_code == 404


def test_delete_column_cascades_cards():
    c = client()
    col_id = columns(c)[0]["id"]
    card = make_card(c, col_id, "Doomed task")
    r = c.delete(f"/columns/{col_id}")
    assert r.status_code == 204
    remaining = columns(c)
    assert [x["title"] for x in remaining] == ["Doing", "Done"]
    # positions renumbered 0-based
    assert [x["position"] for x in remaining] == [0, 1]
    # the card is gone from every response
    all_card_ids = [card_['id'] for col in remaining for card_ in col['cards']]
    assert card["id"] not in all_card_ids


def test_delete_missing_column_404():
    c = client()
    r = c.delete("/columns/9999")
    assert r.status_code == 404


def test_reorder_columns_full_set():
    c = client()
    ids = [col["id"] for col in columns(c)]
    r = c.post("/columns/reorder", json={"column_ids": [ids[2], ids[0], ids[1]]})
    assert r.status_code == 200
    body = r.json()
    assert [col["title"] for col in body] == ["Done", "To Do", "Doing"]
    assert [col["position"] for col in body] == [0, 1, 2]


def test_reorder_columns_wrong_id_set_422():
    c = client()
    ids = [col["id"] for col in columns(c)]
    # missing one id
    r = c.post("/columns/reorder", json={"column_ids": ids[:2]})
    assert r.status_code == 422
    # duplicate id
    r = c.post("/columns/reorder", json={"column_ids": [ids[0], ids[0], ids[1]]})
    assert r.status_code == 422
    # unknown id
    r = c.post("/columns/reorder", json={"column_ids": ids + [9999]})
    assert r.status_code == 422


# --- cards: create/edit/delete ---


def test_create_card_appends_with_fields():
    c = client()
    col_id = columns(c)[0]["id"]
    r = c.post(
        f"/columns/{col_id}/cards",
        json={"title": "Write spec", "notes": "first draft", "due_date": "2026-09-14"},
    )
    assert r.status_code == 201
    card = r.json()
    assert card["title"] == "Write spec"
    assert card["notes"] == "first draft"
    assert card["due_date"] == "2026-09-14"
    assert card["column_id"] == col_id
    # appended at the end
    second = make_card(c, col_id, "Second")
    assert columns(c)[0]["cards"][-1]["id"] == second["id"]


def test_create_card_defaults_and_validation():
    c = client()
    col_id = columns(c)[0]["id"]
    r = c.post(f"/columns/{col_id}/cards", json={"title": "Bare"})
    assert r.status_code == 201
    assert r.json()["notes"] is None
    assert r.json()["due_date"] is None
    # title is required
    r = c.post(f"/columns/{col_id}/cards", json={"notes": "no title"})
    assert r.status_code == 422


def test_create_card_missing_column_404():
    c = client()
    r = c.post("/columns/9999/cards", json={"title": "Orphan"})
    assert r.status_code == 404


def test_patch_card_partial_update():
    c = client()
    col_id = columns(c)[0]["id"]
    card = make_card(c, col_id, "Original")
    c.patch(f"/cards/{card['id']}", json={"notes": "added", "due_date": "2026-09-15"})
    # partial: only title changes, notes/due_date kept
    r = c.patch(f"/cards/{card['id']}", json={"title": "Renamed"})
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Renamed"
    assert body["notes"] == "added"
    assert body["due_date"] == "2026-09-15"
    # null clears optional fields
    r = c.patch(f"/cards/{card['id']}", json={"notes": None, "due_date": None})
    assert r.status_code == 200
    assert r.json()["notes"] is None
    assert r.json()["due_date"] is None


def test_patch_missing_card_404():
    c = client()
    r = c.patch("/cards/9999", json={"title": "Nope"})
    assert r.status_code == 404


def test_delete_card():
    c = client()
    col_id = columns(c)[0]["id"]
    card = make_card(c, col_id, "Trash me")
    r = c.delete(f"/cards/{card['id']}")
    assert r.status_code == 204
    assert columns(c)[0]["cards"] == []
    r = c.delete(f"/cards/{card['id']}")
    assert r.status_code == 404


# --- cards: move ---


def test_move_card_cross_column():
    c = client()
    col_ids = [col["id"] for col in columns(c)]
    a = make_card(c, col_ids[0], "A")
    make_card(c, col_ids[0], "B")
    r = c.post(f"/cards/{a['id']}/move", json={"column_id": col_ids[1], "position": 0})
    assert r.status_code == 200
    assert r.json()["column_id"] == col_ids[1]
    cols = columns(c)
    assert [x["title"] for x in cols[0]["cards"]] == ["B"]
    assert [x["title"] for x in cols[1]["cards"]] == ["A"]


def test_move_card_within_column_reorders():
    c = client()
    col_id = columns(c)[0]["id"]
    a = make_card(c, col_id, "A")
    make_card(c, col_id, "B")
    cc = make_card(c, col_id, "C")
    # move C from index 2 to index 0
    r = c.post(f"/cards/{cc['id']}/move", json={"column_id": col_id, "position": 0})
    assert r.status_code == 200
    assert [x["title"] for x in columns(c)[0]["cards"]] == ["C", "A", "B"]
    # move A to the end (position 2 after removal it's index 1 -> end)
    r = c.post(f"/cards/{a['id']}/move", json={"column_id": col_id, "position": 2})
    assert r.status_code == 200
    assert [x["title"] for x in columns(c)[0]["cards"]] == ["C", "B", "A"]


def test_move_card_position_beyond_end_clamps():
    c = client()
    col_ids = [col["id"] for col in columns(c)]
    a = make_card(c, col_ids[0], "A")
    r = c.post(f"/cards/{a['id']}/move", json={"column_id": col_ids[2], "position": 100})
    assert r.status_code == 200
    assert [x["title"] for x in columns(c)[2]["cards"]] == ["A"]


def test_move_card_negative_position_422():
    c = client()
    col_ids = [col["id"] for col in columns(c)]
    a = make_card(c, col_ids[0], "A")
    r = c.post(f"/cards/{a['id']}/move", json={"column_id": col_ids[0], "position": -1})
    assert r.status_code == 422


def test_move_card_missing_card_404():
    c = client()
    col_ids = [col["id"] for col in columns(c)]
    r = c.post("/cards/9999/move", json={"column_id": col_ids[0], "position": 0})
    assert r.status_code == 404


def test_move_card_missing_destination_404():
    c = client()
    col_ids = [col["id"] for col in columns(c)]
    a = make_card(c, col_ids[0], "A")
    r = c.post(f"/cards/{a['id']}/move", json={"column_id": 9999, "position": 0})
    assert r.status_code == 404
