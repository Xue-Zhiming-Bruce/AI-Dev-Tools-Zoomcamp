from datetime import timedelta

from django.db import models


class Chore(models.Model):
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

    def _next_weekday_after(self, from_date):
        """Nearest chosen weekday strictly after from_date (wraps a week)."""
        chosen = set(self.weekday_numbers)
        candidate = from_date + timedelta(days=1)
        for _ in range(7):
            if candidate.isoweekday() in chosen:
                return candidate
            candidate += timedelta(days=1)
        raise ValueError("no chosen weekday within the next 7 days")
