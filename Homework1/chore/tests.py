from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

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
