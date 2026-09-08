# Backlog — Chore Manager (Django)

Tasks are also tracked as GitHub issues; this file is the homework-visible
copy. Work proceeds lowest issue number first.

---

## Task 1 — Django scaffold with a passing test

## Goal

A Django project exists with a `chore` app registered, and the test runner
passes with one trivial test.

## Acceptance criteria

- [ ] `uv run python manage.py test` passes
- [ ] Home page responds 200 and renders an empty chore list
- [ ] App is included in the project (`settings.py`)

## Out of scope

- Any chore CRUD behavior (Task 2)

## Constraints

- Python + `uv`, SQLite (Django default), server-rendered templates
- Stay inside `Homework1/`

---

## Task 2 — Chore model, add and list

## Goal

User can add a chore (name + optional due date) and see all chores on the
home page.

## Acceptance criteria

- [ ] Chore model with name, due date (optional), done flag
- [ ] Add form on the home page; submitted chores persist (SQLite)
- [ ] List shows all chores with name and due date

## Out of scope

- Marking done (Task 3), recurrence (Task 4)

## Constraints

- Server-rendered Django templates, no JS frameworks

---

## Task 3 — Mark a chore done

## Goal

User can tick a chore off from the list.

## Acceptance criteria

- [ ] A done control on each chore; clicking marks it done
- [ ] Done one-off chores no longer appear in the active list
- [ ] Done state persists across restarts

## Out of scope

- Scheduling the next occurrence of recurring chores (Task 4)

## Constraints

- Standard Django views/forms, no client-side framework

---

## Task 4 — Recurring chores

## Goal

A chore can repeat daily or weekly on chosen weekdays; completing it
schedules the next occurrence automatically.

## Acceptance criteria

- [ ] Recurrence options on add form: none, daily, weekly (weekday picker)
- [ ] Completing a recurring chore creates/schedules its next due date
- [ ] Completing a one-off chore behaves as in Task 3
- [ ] `done` on recurring chores never marks the chore finished forever

## Out of scope

- Snoozing (Task 5)

## Constraints

- Recurrence logic in the model layer, unit-tested

---

## Task 5 — Snooze / postpone

## Goal

User can push a chore's due date without marking it done.

## Acceptance criteria

- [ ] Snooze control with "tomorrow" and "next week" options
- [ ] Works for both one-off and recurring chores
- [ ] Snoozed chore's new due date is visible immediately

## Out of scope

- Custom date picking (moved out of MVP)

## Constraints

- Due-date math in the model layer, unit-tested

---

## Task 6 — Urgency grouping

## Goal

The list is grouped Overdue / Due today / Upcoming, most urgent first.

## Acceptance criteria

- [ ] Three visible groups: Overdue, Due today, Upcoming
- [ ] Chores appear in exactly one group based on due date
- [ ] Overdue group sorts oldest first; Upcoming soonest first
- [ ] Grouping is unit-tested (boundary: due today is not overdue)

## Out of scope

- Time-of-day precision; dates only

## Constraints

- Grouping logic in the model/queryset layer, unit-tested
