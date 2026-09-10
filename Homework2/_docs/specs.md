# MyKanban — Specification

A single-page Kanban board for one person to track their own tasks.

## Users

One local user. No login, no sharing.

## Behavior

- The app is **one board** — no board list, no board creation.
- **Columns** are fully customizable:
  - add a column
  - rename a column
  - delete a column (with its cards)
  - reorder columns
- Default starting board: To Do / Doing / Done.
- **Cards** have: title, notes (free text), due date (optional).
- Create a card in a column; edit all card fields; delete a card.
- Move a card between columns and reorder within a column by **drag & drop**.
- Cards, columns, and their order persist (database) — survives refresh.

## Non-goals (v1)

- No login/auth
- No collaboration or sharing
- No labels, colors, checklists, attachments
- No search/filter

## Stack

- Frontend: Node.js SPA in `frontend/`, backend calls centralized in one module and mocked first
- Backend: FastAPI in `backend/`, managed with `uv`; mock DB first, then SQLAlchemy (SQLite)
- Contract: OpenAPI (`openapi.yaml`) as source of truth between frontend and backend
