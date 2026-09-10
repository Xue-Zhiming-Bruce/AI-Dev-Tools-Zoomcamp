"""Restart-persistence test (issue #13).

Simulates a backend restart cheaply: write with engine 1 on a file DB, dispose
it, open a fresh engine 2 on the same file, and assert the data survived and
the default board was NOT re-seeded.
"""

from datetime import date

from sqlalchemy import create_engine

from app import store


def test_data_survives_restart_and_no_reseed(tmp_path):
    db_file = tmp_path / "mykanban.db"
    url = f"sqlite:///{db_file}"
    connect_args = {"check_same_thread": False}

    # "first process": fresh DB, seeded, then data written
    engine1 = create_engine(url, connect_args=connect_args)
    store.set_engine(engine1)
    store.create_schema()
    store.seed_if_empty()
    col = store.create_column("Blocked")
    todo_id = next(c["id"] for c in store.list_columns() if c["title"] == "To Do")
    card = store.create_card(todo_id, "Write report", "some notes", date(2026, 9, 20))
    engine1.dispose()

    # "second process": brand-new engine on the same file, startup path runs
    engine2 = create_engine(url, connect_args=connect_args)
    store.set_engine(engine2)
    store.create_schema()
    store.seed_if_empty()  # must be a no-op on a populated DB

    cols = store.list_columns()
    titles = [c["title"] for c in cols]
    assert titles == ["To Do", "Doing", "Done", "Blocked"], (
        "restart must not duplicate or reset the default board"
    )
    todo = next(c for c in cols if c["title"] == "To Do")
    assert todo["cards"] == [
        {
            "id": card["id"],
            "column_id": todo_id,
            "title": "Write report",
            "notes": "some notes",
            "due_date": date(2026, 9, 20),
        }
    ]
    engine2.dispose()
