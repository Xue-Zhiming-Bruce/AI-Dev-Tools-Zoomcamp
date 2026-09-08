from django.test import TestCase


class HomePageTest(TestCase):
    def test_home_page_responds_200_with_empty_list(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No chores yet")
