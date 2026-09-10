"""SQLAlchemy + SQLite store for MyKanban (issue #13).

Replaces the in-memory mock from issue #10. The module-level function API is
unchanged, so route handlers and tests need no knowledge of the database.
Board semantics preserved: 0-based positions, append-on-create, delete-column
cascades its cards, move clamps past-the-end, partial card update.

The default engine is the file DB `backend/mykanban.db` (gitignored); tests
swap in an in-memory engine via `set_engine` (see tests/conftest.py).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Engine, Integer, String, Text, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DEFAULT_COLUMNS = ["To Do", "Doing", "Done"]
DATABASE_URL = "sqlite:///./mykanban.db"


class NotFoundError(Exception):
    """Requested column or card does not exist."""


class ReorderError(Exception):
    """column_ids must contain exactly the ids of all existing columns, once each."""


class Base(DeclarativeBase):
    pass


class ColumnModel(Base):
    __tablename__ = "columns"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    position: Mapped[int] = mapped_column(Integer)


class CardModel(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    column_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    position: Mapped[int] = mapped_column(Integer)


# --- engine management (module-level, swappable for tests) ---

_engine: Engine | None = None
_Session: sessionmaker[Session] | None = None


def set_engine(engine: Engine) -> None:
    """Point the store at an engine (tests swap in in-memory SQLite)."""
    global _engine, _Session
    _engine = engine
    _Session = sessionmaker(bind=engine, expire_on_commit=False)


def _session() -> Session:
    if _Session is None:
        set_engine(create_engine(DATABASE_URL, connect_args={"check_same_thread": False}))
    return _Session()


def create_schema() -> None:
    """Create tables if missing (app startup lifespan)."""
    if _engine is None:
        _session()  # ensures default engine exists
    Base.metadata.create_all(_engine)


def seed_if_empty() -> None:
    """Seed the default board only when no columns exist (startup path).

    A restart against a populated DB must not re-seed, duplicate, or reset.
    """
    with _session() as s:
        if s.scalar(select(ColumnModel.id).limit(1)) is None:
            for position, title in enumerate(DEFAULT_COLUMNS):
                s.add(ColumnModel(title=title, position=position))
            s.commit()


def reset() -> None:
    """Wipe and re-seed (test convenience only; not used at startup)."""
    if _engine is None:
        _session()
    Base.metadata.drop_all(_engine)
    Base.metadata.create_all(_engine)
    seed_if_empty()


# --- columns ---

def list_columns() -> list[dict]:
    with _session() as s:
        cols = s.scalars(select(ColumnModel).order_by(ColumnModel.position)).all()
        cards = s.scalars(select(CardModel).order_by(CardModel.position)).all()
        by_col: dict[int, list[CardModel]] = {}
        for card in cards:
            by_col.setdefault(card.column_id, []).append(card)
        return [_column_out(col, by_col.get(col.id, [])) for col in cols]


def create_column(title: str) -> dict:
    with _session() as s:
        # append: after the current last position (max, not count — deletes leave gaps)
        position = s.scalar(
            select(ColumnModel.position).order_by(ColumnModel.position.desc()).limit(1)
        )
        col = ColumnModel(title=title, position=(position + 1) if position is not None else 0)
        s.add(col)
        s.commit()
        return _column_out(col, [])


def rename_column(column_id: int, title: str) -> dict:
    with _session() as s:
        col = _get_column(s, column_id)
        col.title = title
        s.commit()
        cards = s.scalars(
            select(CardModel)
            .where(CardModel.column_id == column_id)
            .order_by(CardModel.position)
        ).all()
        return _column_out(col, cards)


def delete_column(column_id: int) -> None:
    with _session() as s:
        col = _get_column(s, column_id)
        # cascade: the column's cards go with it (app-level, portable)
        for card in s.scalars(select(CardModel).where(CardModel.column_id == column_id)):
            s.delete(card)
        s.delete(col)
        s.commit()
    # renumber remaining columns 0-based by their current order
    with _session() as s:
        for position, c in enumerate(
            s.scalars(select(ColumnModel).order_by(ColumnModel.position)).all()
        ):
            c.position = position
        s.commit()


def reorder_columns(column_ids: list[int]) -> list[dict]:
    with _session() as s:
        existing = set(s.scalars(select(ColumnModel.id)))
        if sorted(column_ids) != sorted(existing) or len(column_ids) != len(existing):
            raise ReorderError(
                "column_ids must contain exactly the ids of all existing columns, once each"
            )
        for position, cid in enumerate(column_ids):
            col = s.get(ColumnModel, cid)
            col.position = position
        s.commit()
        return list_columns()


# --- cards ---

def create_card(
    column_id: int, title: str, notes: str | None, due_date: date | None
) -> dict:
    with _session() as s:
        _get_column(s, column_id)
        count = s.scalar(
            select(func.count()).select_from(CardModel).where(CardModel.column_id == column_id)
        )
        card = CardModel(
            column_id=column_id,
            title=title,
            notes=notes,
            due_date=due_date,
            position=count,  # append-on-create
        )
        s.add(card)
        s.commit()
        return _card_out(card)


def update_card(
    card_id: int,
    title: str | None,
    notes: str | None,
    due_date: date | None,
    notes_provided: bool,
    due_date_provided: bool,
) -> dict:
    with _session() as s:
        card = _get_card(s, card_id)
        if title is not None:
            card.title = title
        if notes_provided:
            card.notes = notes
        if due_date_provided:
            card.due_date = due_date
        s.commit()
        return _card_out(card)


def delete_card(card_id: int) -> None:
    with _session() as s:
        card = _get_card(s, card_id)
        s.delete(card)
        s.commit()


def move_card(card_id: int, column_id: int, position: int) -> dict:
    with _session() as s:
        card = _get_card(s, card_id)
        dest = s.get(ColumnModel, column_id)
        if dest is None:
            raise NotFoundError("column not found")
        source_id = card.column_id
        # same-column move: remove from old spot before inserting
        for other in s.scalars(
            select(CardModel).where(
                CardModel.column_id == source_id, CardModel.position > card.position
            )
        ):
            other.position -= 1
        dest_count = s.scalar(
            select(func.count()).select_from(CardModel).where(CardModel.column_id == column_id)
        )
        if source_id == column_id:
            dest_count -= 1  # card already removed from this column above
        target = min(position, dest_count)  # clamp past-the-end
        # shift destination cards to open the slot
        for other in s.scalars(
            select(CardModel).where(
                CardModel.column_id == column_id, CardModel.position >= target
            )
        ):
            other.position += 1
        card.column_id = column_id
        card.position = target
        s.commit()
        return _card_out(card)


# --- internals ---

def _get_column(s: Session, column_id: int) -> ColumnModel:
    col = s.get(ColumnModel, column_id)
    if col is None:
        raise NotFoundError("column not found")
    return col


def _get_card(s: Session, card_id: int) -> CardModel:
    card = s.get(CardModel, card_id)
    if card is None:
        raise NotFoundError("card not found")
    return card


def _column_out(col: ColumnModel, cards: list[CardModel]) -> dict:
    return {
        "id": col.id,
        "title": col.title,
        "position": col.position,
        "cards": [_card_out(card) for card in cards],
    }


def _card_out(card: CardModel) -> dict:
    return {
        "id": card.id,
        "column_id": card.column_id,
        "title": card.title,
        "notes": card.notes,
        "due_date": card.due_date,
    }
