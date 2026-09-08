from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from .forms import ChoreForm
from .models import Chore

class ChoreModelTest(TestCase):
    def test_create_chore_with_due_date(self):
        chore = Chore.objects.create(name="Take out trash", due_date=date(2026, 9, 10))
        self.assertEqual(chore.name, "Take out trash")
        self.assertEqual(chore.due_date, date(2026, 9, 10))
        self.assertFalse(chore.done)

    def test_create_chore_without_due_date(self):
        chore = Chore.objects.create(name="Dust shelves")
        self.assertIsNone(chore.due_date)

    def test_name_is_required(self):
        chore = Chore(name="", due_date=date(2026, 9, 10))
        with self.assertRaises(ValidationError):
            chore.full_clean()

    def test_chore_persists(self):
        Chore.objects.create(name="Water plants")
        self.assertEqual(Chore.objects.count(), 1)
        self.assertEqual(Chore.objects.first().name, "Water plants")


class HomeViewTest(TestCase):
    def test_home_page_responds_200_with_empty_list(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No chores yet")
        self.assertContains(response, "<form")

    def test_post_creates_chore_and_shows_it(self):
        response = self.client.post("/", {"name": "Take out trash", "due_date": "2026-09-10"})
        self.assertEqual(Chore.objects.count(), 1)
        self.assertEqual(Chore.objects.first().name, "Take out trash")
        follow_up = self.client.get("/")
        self.assertContains(follow_up, "Take out trash")

    def test_post_without_due_date_creates_chore(self):
        self.client.post("/", {"name": "Dust shelves"})
        chore = Chore.objects.first()
        self.assertIsNotNone(chore)
        self.assertIsNone(chore.due_date)
        self.assertContains(self.client.get("/"), "Dust shelves — —")

    def test_blank_name_is_rejected(self):
        for bad_name in ("", "   "):
            response = self.client.post("/", {"name": bad_name})
            self.assertEqual(Chore.objects.count(), 0)
            self.assertContains(response, "This field is required")

    def test_lists_all_chores_with_due_dates(self):
        Chore.objects.create(name="A", due_date=date(2026, 9, 10))
        Chore.objects.create(name="B")
        response = self.client.get("/")
        self.assertContains(response, "A — 2026-09-10")
        self.assertContains(response, "B — —")


class MarkDoneViewTest(TestCase):
    def test_done_chore_disappears_from_active_list(self):
        chore = Chore.objects.create(name="Take out trash")
        response = self.client.post(f"/chore/{chore.id}/done/")
        self.assertRedirects(response, "/")
        self.assertTrue(Chore.objects.get(pk=chore.id).done)
        self.assertNotContains(self.client.get("/"), "Take out trash")

    def test_done_state_survives_restart(self):
        chore = Chore.objects.create(name="Water plants")
        self.client.post(f"/chore/{chore.id}/done/")
        # Re-read from the database as a fresh server process would.
        reloaded = Chore.objects.get(pk=chore.id)
        self.assertTrue(reloaded.done)

    def test_done_is_idempotent(self):
        chore = Chore.objects.create(name="Dust shelves")
        self.client.post(f"/chore/{chore.id}/done/")
        response = self.client.post(f"/chore/{chore.id}/done/")
        self.assertRedirects(response, "/")
        self.assertTrue(Chore.objects.get(pk=chore.id).done)

    def test_nonexistent_chore_returns_404(self):
        response = self.client.post("/chore/9999/done/")
        self.assertEqual(response.status_code, 404)

    def test_get_is_not_allowed(self):
        chore = Chore.objects.create(name="Sweep floor")
        response = self.client.get(f"/chore/{chore.id}/done/")
        self.assertEqual(response.status_code, 405)
        self.assertFalse(Chore.objects.get(pk=chore.id).done)

    def test_done_form_is_on_home_page(self):
        chore = Chore.objects.create(name="Take out trash")
        response = self.client.get("/")
        self.assertContains(response, f"/chore/{chore.id}/done/")
        self.assertContains(response, ">Done</button>")


class RecurrenceModelTest(TestCase):
    def test_daily_advances_one_day_from_due_date(self):
        chore = Chore.objects.create(
            name="Water plants",
            due_date=date(2026, 9, 10),
            recurrence=Chore.Recurrence.DAILY,
        )
        chore.complete()
        chore.refresh_from_db()
        self.assertFalse(chore.done)
        self.assertEqual(chore.due_date, date(2026, 9, 11))

    def test_daily_due_today_completing_today_becomes_tomorrow(self):
        today = date(2026, 9, 10)
        chore = Chore.objects.create(
            name="Feed cat",
            due_date=today,
            recurrence=Chore.Recurrence.DAILY,
        )
        chore.complete()
        chore.refresh_from_db()
        self.assertEqual(chore.due_date, today + timedelta(days=1))

    def test_daily_overdue_advances_from_stale_due_date(self):
        chore = Chore.objects.create(
            name="Sweep floor",
            due_date=date(2026, 9, 1),
            recurrence=Chore.Recurrence.DAILY,
        )
        chore.complete()
        chore.refresh_from_db()
        self.assertEqual(chore.due_date, date(2026, 9, 2))

    def test_weekly_two_weekdays_due_monday_next_is_thursday(self):
        # 2026-09-07 is a Monday; 2026-09-10 is the Thursday after.
        chore = Chore.objects.create(
            name="Trash",
            due_date=date(2026, 9, 7),
            recurrence=Chore.Recurrence.WEEKLY,
            weekdays="1,4",
        )
        chore.complete()
        chore.refresh_from_db()
        self.assertEqual(chore.due_date, date(2026, 9, 10))

    def test_weekly_wraps_to_next_week(self):
        # 2026-09-11 is a Friday; next chosen Monday is 2026-09-14.
        chore = Chore.objects.create(
            name="Laundry",
            due_date=date(2026, 9, 11),
            recurrence=Chore.Recurrence.WEEKLY,
            weekdays="1",
        )
        chore.complete()
        chore.refresh_from_db()
        self.assertEqual(chore.due_date, date(2026, 9, 14))

    def test_weekly_overdue_completed_deterministically(self):
        # Due Monday 2026-08-31, completed "Thursday" — next due must be
        # Monday 2026-09-07 regardless of when complete() runs.
        chore = Chore.objects.create(
            name="Trash",
            due_date=date(2026, 8, 31),
            recurrence=Chore.Recurrence.WEEKLY,
            weekdays="1",
        )
        chore.complete()
        chore.refresh_from_db()
        self.assertEqual(chore.due_date, date(2026, 9, 7))

    def test_recurrence_settings_never_change_on_completion(self):
        chore = Chore.objects.create(
            name="Trash",
            due_date=date(2026, 9, 7),
            recurrence=Chore.Recurrence.WEEKLY,
            weekdays="1,4",
        )
        chore.complete()
        chore.refresh_from_db()
        self.assertEqual(chore.recurrence, Chore.Recurrence.WEEKLY)
        self.assertEqual(chore.weekdays, "1,4")

    def test_one_off_completion_unchanged(self):
        chore = Chore.objects.create(
            name="Dust shelves",
            due_date=date(2026, 9, 10),
            recurrence=Chore.Recurrence.NONE,
        )
        chore.complete()
        chore.refresh_from_db()
        self.assertTrue(chore.done)
        self.assertEqual(chore.due_date, date(2026, 9, 10))


class RecurrenceFormTest(TestCase):
    def test_recurring_requires_due_date(self):
        form = ChoreForm(
            data={"name": "Trash", "recurrence": Chore.Recurrence.DAILY}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("due_date", form.errors)

    def test_weekly_requires_weekday(self):
        form = ChoreForm(
            data={
                "name": "Trash",
                "due_date": "2026-09-10",
                "recurrence": Chore.Recurrence.WEEKLY,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("weekdays", form.errors)

    def test_weekly_with_weekdays_saves_sorted(self):
        form = ChoreForm(
            data={
                "name": "Trash",
                "due_date": "2026-09-10",
                "recurrence": Chore.Recurrence.WEEKLY,
                "weekdays": ["4", "1"],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        chore = form.save()
        self.assertEqual(chore.weekdays, "1,4")

    def test_form_offers_recurrence_choices_and_weekday_picker(self):
        form = ChoreForm()
        html = str(form)
        self.assertIn("daily", html)
        self.assertIn("weekly", html)
        self.assertIn("Monday", html)


class RecurrenceViewTest(TestCase):
    def test_daily_chore_stays_in_list_after_done(self):
        self.client.post(
            "/",
            {
                "name": "Feed cat",
                "due_date": "2026-09-10",
                "recurrence": "daily",
            },
        )
        chore = Chore.objects.get(name="Feed cat")
        self.client.post(f"/chore/{chore.id}/done/")
        response = self.client.get("/")
        self.assertContains(response, "Feed cat")
        self.assertContains(response, "2026-09-11")
        chore.refresh_from_db()
        self.assertFalse(chore.done)

    def test_weekly_chore_advances_and_stays(self):
        self.client.post(
            "/",
            {
                "name": "Trash",
                "due_date": "2026-09-07",
                "recurrence": "weekly",
                "weekdays": ["1"],
            },
        )
        chore = Chore.objects.get(name="Trash")
        self.client.post(f"/chore/{chore.id}/done/")
        response = self.client.get("/")
        self.assertContains(response, "Trash")
        self.assertContains(response, "2026-09-14")

    def test_one_off_chore_leaves_list(self):
        self.client.post("/", {"name": "Dust shelves", "recurrence": "none"})
        chore = Chore.objects.get(name="Dust shelves")
        self.client.post(f"/chore/{chore.id}/done/")
        self.assertNotContains(self.client.get("/"), "Dust shelves")
