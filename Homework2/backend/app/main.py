"""MyKanban API route handlers (issue #10).

Thin handlers: all state logic lives in app.store so the store can be swapped
for a real database in issue #13.
"""

from datetime import date

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app import store
from app.store import NotFoundError, ReorderError

app = FastAPI(
    title="MyKanban API",
    description="Backend for the MyKanban personal Kanban board. "
    "The committed openapi.yaml is the reviewed contract (issue #9).",
    version="0.1.0",
)

# Allow the Vite dev server origin (issue #12). The only backend change in #12.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ColumnCreate(BaseModel):
    title: str


class ColumnUpdate(BaseModel):
    title: str


class ColumnReorder(BaseModel):
    column_ids: list[int]


class CardCreate(BaseModel):
    title: str
    notes: str | None = None
    due_date: date | None = None


class CardUpdate(BaseModel):
    title: str | None = None
    notes: str | None = None
    due_date: date | None = None


class CardMove(BaseModel):
    column_id: int
    position: int = Field(ge=0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/columns")
def list_columns() -> list[dict]:
    return store.list_columns()


@app.post("/columns", status_code=201)
def create_column(body: ColumnCreate) -> dict:
    return store.create_column(body.title)


@app.post("/columns/reorder")
def reorder_columns(body: ColumnReorder) -> list[dict]:
    try:
        return store.reorder_columns(body.column_ids)
    except ReorderError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.patch("/columns/{column_id}")
def rename_column(column_id: int, body: ColumnUpdate) -> dict:
    try:
        return store.rename_column(column_id, body.title)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/columns/{column_id}", status_code=204)
def delete_column(column_id: int) -> None:
    try:
        store.delete_column(column_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/columns/{column_id}/cards", status_code=201)
def create_card(column_id: int, body: CardCreate) -> dict:
    try:
        return store.create_card(column_id, body.title, body.notes, body.due_date)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.patch("/cards/{card_id}")
def update_card(card_id: int, body: CardUpdate) -> dict:
    try:
        return store.update_card(
            card_id,
            body.title,
            body.notes,
            body.due_date,
            notes_provided="notes" in body.model_fields_set,
            due_date_provided="due_date" in body.model_fields_set,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/cards/{card_id}", status_code=204)
def delete_card(card_id: int) -> None:
    try:
        store.delete_card(card_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/cards/{card_id}/move")
def move_card(card_id: int, body: CardMove) -> dict:
    try:
        return store.move_card(card_id, body.column_id, body.position)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
