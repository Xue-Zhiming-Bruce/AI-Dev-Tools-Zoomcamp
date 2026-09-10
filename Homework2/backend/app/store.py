"""In-memory mock store for MyKanban (issue #10).

All board state and manipulation logic lives here so route handlers stay thin
and the store can be swapped for SQLAlchemy in issue #13.
"""

from __future__ import annotations

from datetime import date

DEFAULT_COLUMNS = ["To Do", "Doing", "Done"]


class NotFoundError(Exception):
    """Requested column or card does not exist."""


class ReorderError(Exception):
    """column_ids must contain exactly the ids of all existing columns, once each."""


class Store:
    def __init__(self) -> None:
        self._next_column_id = 1
        self._next_card_id = 1
        # column_id -> {"id", "title", "cards": [card dicts]}
        self._columns: dict[int, dict] = {}
        self._order: list[int] = []
        for title in DEFAULT_COLUMNS:
            self.create_column(title)

    def reset(self) -> None:
        """Re-seed the store to the default board."""
        self.__init__()  # noqa: PLW1641 - intentional re-init for the mock store

    # --- columns ---

    def list_columns(self) -> list[dict]:
        return [self._column_out(cid) for cid in self._order]

    def create_column(self, title: str) -> dict:
        col = {"id": self._next_column_id, "title": title, "cards": []}
        self._next_column_id += 1
        self._columns[col["id"]] = col
        self._order.append(col["id"])
        return self._column_out(col["id"])

    def rename_column(self, column_id: int, title: str) -> dict:
        col = self._get_column(column_id)
        col["title"] = title
        return self._column_out(column_id)

    def delete_column(self, column_id: int) -> None:
        self._get_column(column_id)
        del self._columns[column_id]
        self._order.remove(column_id)

    def reorder_columns(self, column_ids: list[int]) -> list[dict]:
        if sorted(column_ids) != sorted(self._columns) or len(column_ids) != len(
            self._columns
        ):
            raise ReorderError(
                "column_ids must contain exactly the ids of all existing columns, once each"
            )
        self._order = list(column_ids)
        return self.list_columns()

    # --- cards ---

    def create_card(
        self, column_id: int, title: str, notes: str | None, due_date: date | None
    ) -> dict:
        col = self._get_column(column_id)
        card = {
            "id": self._next_card_id,
            "column_id": column_id,
            "title": title,
            "notes": notes,
            "due_date": due_date,
        }
        self._next_card_id += 1
        col["cards"].append(card)  # append-on-create
        return dict(card)

    def update_card(
        self,
        card_id: int,
        title: str | None,
        notes: str | None,
        due_date: date | None,
        notes_provided: bool,
        due_date_provided: bool,
    ) -> dict:
        card = self._get_card(card_id)
        if title is not None:
            card["title"] = title
        if notes_provided:
            card["notes"] = notes
        if due_date_provided:
            card["due_date"] = due_date
        return dict(card)

    def delete_card(self, card_id: int) -> None:
        card = self._get_card(card_id)
        col = self._columns[card["column_id"]]
        col["cards"].remove(card)

    def move_card(self, card_id: int, column_id: int, position: int) -> dict:
        card = self._get_card(card_id)
        if column_id not in self._columns:
            raise NotFoundError("column not found")
        source = self._columns[card["column_id"]]
        source["cards"].remove(card)  # same-column move: remove before insert
        dest = self._columns[column_id]
        card["column_id"] = column_id
        position = min(position, len(dest["cards"]))  # clamp past-the-end
        dest["cards"].insert(position, card)
        return dict(card)

    # --- internals ---

    def _get_column(self, column_id: int) -> dict:
        if column_id not in self._columns:
            raise NotFoundError("column not found")
        return self._columns[column_id]

    def _get_card(self, card_id: int) -> dict:
        for col in self._columns.values():
            for card in col["cards"]:
                if card["id"] == card_id:
                    return card
        raise NotFoundError("card not found")

    def _column_out(self, column_id: int) -> dict:
        col = self._columns[column_id]
        return {
            "id": col["id"],
            "title": col["title"],
            "position": self._order.index(column_id),
            "cards": [dict(card) for card in col["cards"]],
        }


# Module-level API: route handlers and tests call these functions, so issue #13
# can swap the storage by rewriting this module only.
_store = Store()


def reset() -> None:
    _store.reset()


def list_columns() -> list[dict]:
    return _store.list_columns()


def create_column(title: str) -> dict:
    return _store.create_column(title)


def rename_column(column_id: int, title: str) -> dict:
    return _store.rename_column(column_id, title)


def delete_column(column_id: int) -> None:
    _store.delete_column(column_id)


def reorder_columns(column_ids: list[int]) -> list[dict]:
    return _store.reorder_columns(column_ids)


def create_card(
    column_id: int, title: str, notes: str | None, due_date: date | None
) -> dict:
    return _store.create_card(column_id, title, notes, due_date)


def update_card(
    card_id: int,
    title: str | None,
    notes: str | None,
    due_date: date | None,
    notes_provided: bool,
    due_date_provided: bool,
) -> dict:
    return _store.update_card(
        card_id, title, notes, due_date, notes_provided, due_date_provided
    )


def delete_card(card_id: int) -> None:
    _store.delete_card(card_id)


def move_card(card_id: int, column_id: int, position: int) -> dict:
    return _store.move_card(card_id, column_id, position)
