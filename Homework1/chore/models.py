from datetime import date, timedelta

from django.db import models
from django.utils import timezone


class ChoreQuerySet(models.QuerySet):
    def grouped_by_urgency(self, today=None):
        """Active chores grouped by due-date urgency, most-urgent-first.

        Exactly one group per chore, decided only by due_date vs `today`
        (defaults to the local date): due_date < today -> overdue,
        due_date == today -> due_today, due_date > today -> upcoming,
        no due_date -> undated. Due today is NOT overdue. Each group is
        ordered most-urgent-first; ties break oldest created_at first.
        Templates must not compute dates themselves — today is resolved
        here, in the model layer.
        """
        if today is None:
            today = timezone.localdate()
        active = self.filter(done=False)
        return {
            "overdue": active.filter(due_date__lt=today).order_by(
                "due_date", "created_at"
            ),
            "due_today": active.filter(due_date=today).order_by("created_at"),
            "upcoming": active.filter(due_date__gt=today).order_by(
                "due_date", "created_at"
            ),
            "undated": active.filter(due_date__isnull=True).order_by("created_at"),
        }


class Chore(models.Model):
    objects = ChoreQuerySet.as_manager()

    class Recurrence(models.TextChoices):
        NONE = "none", "None"
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"

    name = models.CharField(max_length=200)
    due_date = models.DateField(null=True, blank=True)
    done = models.BooleanField(default=False)
    recurrence = models.CharField(
        max_length=10,
        choices=Recurrence.choices,
        default=Recurrence.NONE,
    )
    # Comma-separated ISO weekday numbers (1=Mon .. 7=Sun), e.g. "1,4".
    # Only used when recurrence is weekly.
    weekdays = models.CharField(max_length=13, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def weekday_numbers(self):
        try:
            return sorted(int(w) for w in self.weekdays.split(",") if w)
        except ValueError:
            return []

    def complete(self):
        """Complete this chore.

        One-off chores (recurrence None) are marked done. Recurring chores
        stay active (done stays False) and their due_date advances from its
        current value, which may be stale/overdue — the completion date
        never affects scheduling, so overdue completions are deterministic.
        Recurrence settings themselves never change.
        """
        if self.recurrence == self.Recurrence.DAILY and self.due_date:
            self.due_date += timedelta(days=1)
        elif (
            self.recurrence == self.Recurrence.WEEKLY
            and self.due_date
            and self.weekday_numbers
        ):
            self.due_date = self._next_weekday_after(self.due_date)
        else:
            self.done = True
        self.save()

    def snooze(self, days, from_date=None):
        """Postpone this chore: set due_date to from_date + `days` calendar
        days (from_date defaults to today). Only due_date moves — recurrence,
        weekdays, and done are never touched. Raises ValueError for chores
        without a due date; nothing changes in that case.
        """
        if self.due_date is None:
            raise ValueError("cannot snooze a chore without a due date")
        if from_date is None:
            from_date = date.today()
        self.due_date = from_date + timedelta(days=days)
        self.save()

    def _next_weekday_after(self, from_date):
        """Nearest chosen weekday strictly after from_date (wraps a week)."""
        chosen = set(self.weekday_numbers)
        candidate = from_date + timedelta(days=1)
        for _ in range(7):
            if candidate.isoweekday() in chosen:
                return candidate
            candidate += timedelta(days=1)
        raise ValueError("no chosen weekday within the next 7 days")
