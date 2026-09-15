# Chore Manager — MVP plan

## Goal

A web app (Django) that manages the user's household chores like a personal
to-do list: add chores, tick them off, and let repeating chores come back
on their own schedule so nothing is forgotten.

## Users

- Single user (the owner). No accounts, no login, no other household members.
- Uses the app in a browser (desktop or phone).

## Behavior spec

### Chores

- Add a chore: a form with a name and an optional due date.
- List view: shows chores grouped as **Overdue**, **Due today**, **Upcoming**,
  with the most urgent first.
- Tick off: mark a chore done. One-off chores leave the list; recurring
  chores schedule their next occurrence automatically.
- Recurring chores: a chore can repeat on a schedule (daily, or weekly on
  specific days, e.g. "trash: every Tuesday").
- Snooze/postpone: push a chore's due date ("tomorrow", "next week")
  without marking it done.

### Storage

- SQLite (Django's default). Single-user scale.

## Non-goals (explicitly out of v1)

- Multi-user support, households, accounts, or login
- Chore assignment to other people / rotation
- Points, gamification, or fairness statistics
- Telegram bot or notifications/reminders (a "due today" view covers it)
- REST API — server-rendered Django templates only
