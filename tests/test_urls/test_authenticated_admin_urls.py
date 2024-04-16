from django.contrib.auth.models import User
from django.test import Client, TestCase


class SimpleTest(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="<PASSWORD>", is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)

    def test_general_admin_views(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/admin/password_change/")
        self.assertEqual(response.status_code, 200)

    def test_index(self):
        response = self.client.get("/admin/kmuhelper/")
        self.assertEqual(response.status_code, 200)
