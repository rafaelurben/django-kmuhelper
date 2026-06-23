import datetime

from django.conf import settings
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from reportlab import rl_config

from kmuhelper.modules.main.models import ContactPerson, PaymentReceiver, Order
from kmuhelper.modules.pdfgeneration.swiss_qr_invoice import QRInvoiceFlowable

EXPECTED_PAYLOAD = """SPC
0200
1

S





CH








CHF







QRR
000000000000000000000100002
23.06.2026
EPD
//S1/10/1/11/260623/31/260623/32/0.0:30.55;7.7:9.95"""


class OrderPdfGenerationTest(TestCase):
    def setUp(self):
        self.contact_person = ContactPerson.objects.create(name="X X", phone="x", email="x@x")
        self.payment_receiver = PaymentReceiver.objects.create(
            logourl="https://raw.githubusercontent.com/rafaelurben/django-kmuhelper/refs/heads/main/kmuhelper/static/kmuhelper/images/icons/icon-144x144.png"
        )

        # Create a test user with appropriate permissions
        self.user = User.objects.create_user(
            username="testuser", password="testpass", is_staff=True, is_superuser=True
        )

        # Create a test client and log in
        self.client = Client()
        self.client.cookies.load({settings.LANGUAGE_COOKIE_NAME: "de"})
        self.client.force_login(self.user)

        # Create a test order
        self.order = Order.objects.create(
            contact_person=self.contact_person,
            payment_receiver=self.payment_receiver,
            invoice_date=datetime.date(2026, 6, 23),
        )

        rl_config.trustedHosts = ["localhost", "raw.githubusercontent.com"]


class QRInvoiceFlowableTest(OrderPdfGenerationTest):
    def testQrPayload(self):
        # add some products to the order
        self.order.products.through.objects.bulk_create(
            [
                self.order.products.through(
                    product_price=10.5, quantity=1, vat_rate=0.0, order=self.order
                ),
                self.order.products.through(
                    product_price=5.05, quantity=2, vat_rate=0.0, order=self.order
                ),
            ]
        )
        # add some fees to the order
        self.order.fees.through.objects.bulk_create(
            [
                self.order.fees.through(price=9.95, vat_rate=0.0, order=self.order),
                self.order.fees.through(price=9.95, vat_rate=7.7, order=self.order),
            ]
        )
        # test generated payload is not empty
        flowable = QRInvoiceFlowable.from_order(self.order)
        payload = flowable.get_swiss_qr_payload()
        self.assertIsNotNone(payload)
        self.assertEqual(
            EXPECTED_PAYLOAD,
            payload,
        )


class OrderCreatePdfFormTest(OrderPdfGenerationTest):
    """Test kmuhelper.modules.pdfgeneration.order.views.order_create_pdf_form"""

    def test_get_displays_form(self):
        """Test that GET request displays the PDF form"""
        url = reverse("admin:kmuhelper_order_pdf_form", args=[self.order.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/kmuhelper/order/pdf_form.html")
        self.assertIn("form", response.context)

    def test_post_valid_form_redirects_correctly(self):
        """Test that POST with valid form data redirects to order_view_pdf with correct parameters"""
        url = reverse("admin:kmuhelper_order_pdf_form", args=[self.order.id])

        form_data = {
            "preset": "invoice",
            "title": "Custom Invoice Title",
            "text": "Custom invoice text",
            "language": "de",
            "do_print": False,
            "do_download": False,
        }

        response = self.client.post(url, form_data, follow=False)

        # Check that it redirects
        self.assertEqual(response.status_code, 302)

        # Check that redirect URL contains expected parameters
        expected_url = reverse("admin:kmuhelper_order_pdf", args=[self.order.id])
        self.assertIn(expected_url, response.url)
        self.assertIn("custom", response.url)
        self.assertIn("preset=invoice", response.url)
        self.assertIn("language=de", response.url)

    def test_post_with_print_option(self):
        """Test that do_print option is reflected in redirect URL"""
        url = reverse("admin:kmuhelper_order_pdf_form", args=[self.order.id])

        form_data = {
            "preset": "invoice",
            "title": "",
            "text": "",
            "language": "de",
            "do_print": True,
            "do_download": False,
        }

        response = self.client.post(url, form_data, follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn("&print", response.url)

    def test_post_with_download_option(self):
        """Test that do_download option is reflected in redirect URL"""
        url = reverse("admin:kmuhelper_order_pdf_form", args=[self.order.id])

        form_data = {
            "preset": "invoice",
            "title": "",
            "text": "",
            "language": "de",
            "do_print": False,
            "do_download": True,
        }

        response = self.client.post(url, form_data, follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn("&download", response.url)

    def test_post_saves_order_settings(self):
        """Test that POST saves custom title and text to order"""
        url = reverse("admin:kmuhelper_order_pdf_form", args=[self.order.id])

        custom_title = "My Custom Title"
        custom_text = "This is my custom text"

        form_data = {
            "preset": "invoice",
            "title": custom_title,
            "text": custom_text,
            "language": "de",
            "do_print": False,
            "do_download": False,
        }

        self.client.post(url, form_data)

        # Refresh order from database
        self.order.refresh_from_db()

        self.assertEqual(self.order.pdf_title, custom_title)
        self.assertEqual(self.order.pdf_text, custom_text)

    def test_post_with_all_presets(self):
        """Test POST with all available presets"""
        url = reverse("admin:kmuhelper_order_pdf_form", args=[self.order.id])

        for preset in ["invoice", "delivery-note", "payment-reminder"]:
            form_data = {
                "preset": preset,
                "title": "",
                "text": "",
                "language": "de",
                "do_print": False,
                "do_download": False,
            }

            response = self.client.post(url, form_data, follow=False)

            self.assertEqual(response.status_code, 302)
            self.assertIn(f"preset={preset}", response.url)


class OrderViewPdfTest(OrderPdfGenerationTest):
    """Test kmuhelper.modules.pdfgeneration.order.views.order_view_pdf"""

    def _get(self, url: str):
        with self.assertNoLogs(level="WARNING"):
            return self.client.get(url)

    def test_invoice_generation_succeeds(self):
        """Test that invoice PDF generation succeeds without exceptions"""
        url = reverse("admin:kmuhelper_order_pdf", args=[self.order.id]) + "?preset=invoice"
        response = self._get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_delivery_note_generation_succeeds(self):
        """Test that delivery-note PDF generation succeeds without exceptions"""
        url = reverse("admin:kmuhelper_order_pdf", args=[self.order.id]) + "?preset=delivery-note"
        response = self._get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_payment_reminder_generation_succeeds(self):
        """Test that payment-reminder PDF generation succeeds without exceptions"""
        url = (
            reverse("admin:kmuhelper_order_pdf", args=[self.order.id]) + "?preset=payment-reminder"
        )
        response = self._get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_custom_title_and_text(self):
        """Test PDF generation with custom title and text"""
        custom_title = "My Custom Title"
        custom_text = "Custom text content"

        url = (
            reverse("admin:kmuhelper_order_pdf", args=[self.order.id])
            + f"?custom&preset=invoice&title={custom_title}&text={custom_text}"
        )
        response = self._get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_different_languages(self):
        """Test PDF generation with different languages"""
        for lang in ["de", "fr", "it", "en"]:
            url = (
                reverse("admin:kmuhelper_order_pdf", args=[self.order.id])
                + f"?preset=invoice&language={lang}"
            )
            response = self._get(url)

            self.assertEqual(
                response.status_code, 200, msg=f"PDF generation failed for language {lang}"
            )
            self.assertEqual(response["Content-Type"], "application/pdf")

    def test_print_version(self):
        """Test PDF generation with print version flag"""
        url = reverse("admin:kmuhelper_order_pdf", args=[self.order.id]) + "?preset=invoice&print"
        response = self._get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_download_flag(self):
        """Test PDF generation with download flag"""
        url = (
            reverse("admin:kmuhelper_order_pdf", args=[self.order.id]) + "?preset=invoice&download"
        )
        response = self._get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        # Check that Content-Disposition header is set for attachment
        self.assertIn("Content-Disposition", response)
        self.assertIn("attachment", response["Content-Disposition"])

    def test_invalid_preset_returns_error(self):
        """Test that invalid preset returns 400 error"""
        url = reverse("admin:kmuhelper_order_pdf", args=[self.order.id]) + "?preset=invalid-preset"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)

    def test_invalid_language_defaults_to_order_language(self):
        """Test that invalid language parameter is ignored and order language is used"""
        url = (
            reverse("admin:kmuhelper_order_pdf", args=[self.order.id])
            + "?preset=invoice&language=xx"
        )
        response = self._get(url)

        # Should still succeed with default language
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_log_entry_created_for_invoice(self):
        """Test that LogEntry is created with correct preset for invoice"""
        LogEntry.objects.all().delete()  # Clear any existing log entries

        url = reverse("admin:kmuhelper_order_pdf", args=[self.order.id]) + "?preset=invoice"
        response = self._get(url)

        self.assertEqual(response.status_code, 200)

        # Check that a LogEntry was created
        log_entries = LogEntry.objects.filter(
            object_id=str(self.order.id),
            action_flag=CHANGE,
        )

        self.assertEqual(log_entries.count(), 1)

        log_entry = log_entries.first()
        # Check that the log message contains a PDF title and the preset name
        self.assertIn('PDF "', log_entry.change_message)
        self.assertIn('aus Vorlage "invoice"', log_entry.change_message)
        self.assertIn("erstellt", log_entry.change_message)

    def test_log_entry_created_for_delivery_note(self):
        """Test that LogEntry is created with correct preset for delivery-note"""
        LogEntry.objects.all().delete()

        url = reverse("admin:kmuhelper_order_pdf", args=[self.order.id]) + "?preset=delivery-note"
        response = self._get(url)

        self.assertEqual(response.status_code, 200)

        log_entries = LogEntry.objects.filter(
            object_id=str(self.order.id),
            action_flag=CHANGE,
        )

        self.assertEqual(log_entries.count(), 1)

        log_entry = log_entries.first()
        # Check that the log message contains a PDF title and the preset name
        self.assertIn('PDF "', log_entry.change_message)
        self.assertIn('aus Vorlage "delivery-note"', log_entry.change_message)
        self.assertIn("erstellt", log_entry.change_message)

    def test_log_entry_with_custom_text(self):
        """Test that LogEntry includes custom text in change_message"""
        LogEntry.objects.all().delete()

        custom_text = "My custom text"
        # First, save custom text to the order using the form
        form_url = reverse("admin:kmuhelper_order_pdf_form", args=[self.order.id])
        form_data = {
            "preset": "invoice",
            "title": "",
            "text": custom_text,
            "language": "de",
            "do_print": False,
            "do_download": False,
        }
        self.client.post(form_url, form_data)

        # Now request the PDF with custom flag
        LogEntry.objects.all().delete()
        url = (
            reverse("admin:kmuhelper_order_pdf", args=[self.order.id])
            + "?custom&preset=invoice&language=de"
        )
        response = self._get(url)

        self.assertEqual(response.status_code, 200)

        log_entries = LogEntry.objects.filter(
            object_id=str(self.order.id),
            action_flag=CHANGE,
        )

        self.assertEqual(log_entries.count(), 1)

        log_entry = log_entries.first()
        # Check that custom text is in the log message
        self.assertIn(f'Text: "{custom_text}"', log_entry.change_message)

    def test_log_entry_without_custom_text(self):
        """Test that LogEntry message is different when no custom text is provided"""
        LogEntry.objects.all().delete()

        url = reverse("admin:kmuhelper_order_pdf", args=[self.order.id]) + "?preset=invoice"
        response = self._get(url)

        self.assertEqual(response.status_code, 200)

        log_entries = LogEntry.objects.filter(
            object_id=str(self.order.id),
            action_flag=CHANGE,
        )

        self.assertEqual(log_entries.count(), 1)

        log_entry = log_entries.first()
        # When no custom text, message should end with "erstellt."
        self.assertTrue(log_entry.change_message.endswith("erstellt."))
        self.assertNotIn("Text:", log_entry.change_message)
