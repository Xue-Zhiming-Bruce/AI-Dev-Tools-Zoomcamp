# Chore Bot — MVP plan

## Goal

A Telegram bot that manages the user's household chores like a personal
to-do list: add chores, tick them off, and let repeating chores come back
on their own schedule with reminders so nothing is forgotten.

## Users

- Single user (the owner). No accounts, no other household members.
- Interacts exclusively through a Telegram bot chat.

## Behavior spec

### Chores

- Add a chore: `add take out trash` → creates a one-off chore.
- Recurring chores: a chore can repeat on a schedule (daily, weekly on
  specific days, e.g. "trash: every Tuesday"). When done, the next
  occurrence is scheduled automatically.
- List: `list` (or "what's due today?") → shows due today, overdue, and
  upcoming chores.
- Tick off: `done take out trash` (or tapping a button) marks it done.
  One-off chores disappear; recurring chores schedule their next due date.
- Snooze/postpone: `snooze <chore> tomorrow` / "next week" — pushes the
  due date without marking done.

### Reminders

- Due/overdue reminder: the bot pings the user when a chore becomes due
  or is overdue.
- Daily digest: at a fixed, configurable time each morning the bot sends
  a summary ("3 chores due today: …, 1 overdue: …").

### Storage

- SQLite file. Single-user scale; no migrations beyond what the ORM
  needs at this size.

## Non-goals (explicitly out of v1)

- Multi-user support, households, accounts, or sharing
- Chore assignment to other people / rotation
- Points, gamification, or fairness statistics
- Web UI or any interface other than Telegram
- Notifications to anyone other than the owner
