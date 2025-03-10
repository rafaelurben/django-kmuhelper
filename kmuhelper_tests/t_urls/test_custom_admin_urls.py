"""
Tests custom admin URLs to check for unexpected 500 errors caused by mistakes in views or templates.
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase

from kmuhelper.modules.emails.models import EMail
from kmuhelper.modules.main.models import ContactPerson, PaymentReceiver, Order, Supply


def _create_test_order():
    return Order.objects.create(
        contact_person=ContactPerson.objects.create(
            name="X X", phone="x", email="x@x"
        ),
        payment_receiver=PaymentReceiver.objects.create(),
    )


class CustomAdminURLTests(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = Client()
        self.client.cookies.load({settings.LANGUAGE_COOKIE_NAME: "de"})
        self.user = User.objects.create_user(
            username="testuser", password="<PASSWORD>", is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)

    # Utils

    def _require_successful_get(self, url, code=200):
        """Checks that a GET request to a given URL is successful and returns the request object."""
        response = self.client.get(url)
        print(f"Checking GET to {url}")
        self.assertEqual(response.status_code, code, msg=f"Couldn't GET {url}, code {response.status_code}")
        return response

    def _require_successful_post(self, url, data=None, code=200):
        """Checks that a POST request to a given URL is successful and returns the request object."""
        response = self.client.post(url, data)
        print(f"Checking POST to {url}")
        self.assertEqual(response.status_code, code, msg=f"Couldn't POST {url}, code {response.status_code}")
        return response

    # Custom order admin URLs

    def test_admin_order_duplicate(self):
        obj = _create_test_order()
        self._require_successful_post(f"/admin/kmuhelper/order/{obj.pk}/duplicate/", code=302)

        count = Order.objects.count()
        self.assertEqual(count, 2, msg="Did not create any order!")

    def test_admin_order_return(self):
        obj = _create_test_order()
        self._require_successful_post(f"/admin/kmuhelper/order/{obj.pk}/return/", code=302)

        count = Supply.objects.count()
        self.assertEqual(count, 1, msg="Did not create any supply!")

    def test_admin_order_email_invoice(self):
        obj = _create_test_order()
        self._require_successful_post(f"/admin/kmuhelper/order/{obj.pk}/email/invoice/", code=302)

        count = EMail.objects.count()
        self.assertEqual(count, 1, msg="Did not create any email!")

    def test_admin_order_email_shipped(self):
        obj = _create_test_order()
        self._require_successful_post(f"/admin/kmuhelper/order/{obj.pk}/email/shipped/", code=302)

        count = EMail.objects.count()
        self.assertEqual(count, 1, msg="Did not create any email!")

    def test_admin_order_pdf(self):
        obj = _create_test_order()
        response = self._require_successful_get(f"/admin/kmuhelper/order/{obj.pk}/pdf/")
        self.assertEqual(response.headers.get('Content-Type'), 'application/pdf', msg="Returned wrong content type!")

    def test_admin_order_pdf_form(self):
        obj = _create_test_order()
        self._require_successful_get(f"/admin/kmuhelper/order/{obj.pk}/pdf/form/", code=302)
