from django.test import TestCase
from django.urls import reverse

from .models import Todo


class TodoViewsTests(TestCase):
    def setUp(self):
        self.todo = Todo.objects.create(
            title="Test Task",
            description="desc",
            due_date=None,
            is_resolved=False,
        )

    def test_list_view_displays_items(self):
        resp = self.client.get(reverse("todos:list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Test Task")

    def test_create_view_creates_todo(self):
        resp = self.client.post(
            reverse("todos:create"),
            {
                "title": "New",
                "description": "d",
                "due_date": "",  # optional
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Todo.objects.filter(title="New").exists())

    def test_update_view_updates_fields_and_resolved(self):
        resp = self.client.post(
            reverse("todos:edit", args=[self.todo.pk]),
            {
                "title": "Updated",
                "description": "z",
                "due_date": "",
                "is_resolved": True,
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.title, "Updated")
        self.assertTrue(self.todo.is_resolved)

    def test_toggle_resolved_flips_flag(self):
        self.assertFalse(self.todo.is_resolved)
        resp = self.client.get(reverse("todos:resolve", args=[self.todo.pk]))
        self.assertEqual(resp.status_code, 302)
        self.todo.refresh_from_db()
        self.assertTrue(self.todo.is_resolved)

    def test_delete_view_removes_item(self):
        # GET should render confirmation
        resp_get = self.client.get(reverse("todos:delete", args=[self.todo.pk]))
        self.assertEqual(resp_get.status_code, 200)
        # POST should delete and redirect
        resp_post = self.client.post(reverse("todos:delete", args=[self.todo.pk]))
        self.assertEqual(resp_post.status_code, 302)
        self.assertFalse(Todo.objects.filter(pk=self.todo.pk).exists())


# Create your tests here.
