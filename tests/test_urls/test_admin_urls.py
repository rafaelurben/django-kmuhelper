"""
Tests admin URLs to check for unexpected 500 errors caused by mistakes in admin configs or templates.
"""

from django.conf import settings
from django.contrib.admin.models import ADDITION
from django.contrib.auth.models import User
from django.test import Client, TestCase
from kmuhelper.modules.api.models import ApiKey
from kmuhelper.modules.emails.models import Attachment, EMail, EMailTemplate
from kmuhelper.modules.integrations.paymentimport.models import PaymentImport
from kmuhelper.modules.log.models import AdminLogEntry
from kmuhelper.modules.main.models import (
    ContactPerson,
    Customer,
    Fee,
    Note,
    Order,
    PaymentReceiver,
    Product,
    ProductCategory,
    Supplier,
    Supply,
)
from kmuhelper.modules.settings.models import Setting


class AdminURLTests(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = Client()
        self.client.cookies.load({settings.LANGUAGE_COOKIE_NAME: "de"})
        self.user = User.objects.create_user(
            username="testuser", password="<PASSWORD>", is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)

    # Utils

    def _require_successful_get(self, url):
        """Checks that a GET request to a given URL is successful and returns the request object."""
        response = self.client.get(url)
        print(f"Checking GET to {url}")
        self.assertEqual(response.status_code, 200, msg=f"Couldn't open {url}")
        return response

    def _test_model_admins(
        self,
        model_name,
        pk,
        check_add=True,
        check_change=True,
        check_delete=True,
        check_history=True,
    ):
        self._require_successful_get(f"/admin/kmuhelper/{model_name}/")
        if check_add:
            self._require_successful_get(f"/admin/kmuhelper/{model_name}/add/")
        if check_change:
            self._require_successful_get(f"/admin/kmuhelper/{model_name}/{pk}/change/")
        if check_delete:
            self._require_successful_get(f"/admin/kmuhelper/{model_name}/{pk}/delete/")
        if check_history:
            self._require_successful_get(f"/admin/kmuhelper/{model_name}/{pk}/history/")

    # General tests

    def test_admin_index(self):
        response = self._require_successful_get("/admin/")
        self.assertInHTML("<h2>KMUHelper öffnen</h2>", response.content.decode())

    def test_admin_app_index(self):
        self._require_successful_get("/admin/kmuhelper/")

    # Test model admins: api

    def test_model_admin_api_key(self):
        obj = ApiKey.objects.create(name="test", user=self.user)
        self._test_model_admins("apikey", obj.pk)

    # Test model admins: emails

    def test_model_admin_attachment(self):
        obj = Attachment.objects.create()
        self._test_model_admins("attachment", obj.pk)

    def test_model_admin_email(self):
        obj = EMail.objects.create()
        self._test_model_admins("email", obj.pk)

    def test_model_admin_email_template(self):
        obj = EMailTemplate.objects.create()
        self._test_model_admins("emailtemplate", obj.pk)

    # Test model admins: log

    def test_model_admin_log_entry(self):
        obj = AdminLogEntry.objects.create(user=self.user, action_flag=ADDITION)
        self._test_model_admins(
            "adminlogentry",
            obj.pk,
            check_add=False,
            check_change=False,
            check_delete=False,
            check_history=False,
        )

    # Test model admins: main & app

    def test_model_admin_contact_person(self):
        obj = ContactPerson.objects.create(
            name="Rafael Urben", phone="+41 123 456 78 90", email="contact@tpto.ch"
        )
        self._test_model_admins("contactperson", obj.pk)

    def test_model_admin_customer(self):
        obj = Customer.objects.create()
        self._test_model_admins("customer", obj.pk)

    def test_model_admin_fee(self):
        obj = Fee.objects.create()
        self._test_model_admins("fee", obj.pk)

    def test_model_admin_note(self):
        obj = Note.objects.create()
        self._test_model_admins("note", obj.pk)
        self._test_model_admins("app_todo", obj.pk)

    def test_model_admin_order(self):
        obj = Order.objects.create(
            contact_person=ContactPerson.objects.create(
                name="X X", phone="x", email="x@x"
            ),
            payment_receiver=PaymentReceiver.objects.create(),
        )
        self._test_model_admins("order", obj.pk)
        self._test_model_admins("app_shipping", obj.pk)
        self._test_model_admins("app_incomingpayments", obj.pk)

    def test_model_admin_payment_receiver(self):
        obj = PaymentReceiver.objects.create()
        self._test_model_admins("paymentreceiver", obj.pk)

    def test_model_admin_product(self):
        obj = Product.objects.create()
        self._test_model_admins("product", obj.pk)
        self._test_model_admins("app_stock", obj.pk)

    def test_model_admin_product_category(self):
        obj = ProductCategory.objects.create()
        self._test_model_admins("productcategory", obj.pk)

    def test_model_admin_supplier(self):
        obj = Supplier.objects.create()
        self._test_model_admins("supplier", obj.pk)

    def test_model_admin_supply(self):
        obj = Supply.objects.create()
        self._test_model_admins("supply", obj.pk)
        self._test_model_admins("app_arrival", obj.pk)

    # Test model admins: payment import

    def test_model_admin_payment_import(self):
        obj = PaymentImport.objects.create(data_creationdate="2024-01-01")
        self._test_model_admins("paymentimport", obj.pk, check_add=False)

    # Test model admins: settings

    def test_model_admin_setting(self):
        obj = Setting.objects.get(pk="email-signature")
        self._test_model_admins("setting", obj.pk, check_add=False, check_delete=False)
