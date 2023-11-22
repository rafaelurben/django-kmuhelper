"""Useful constants used in multiple places"""

from django.utils.translation import gettext_lazy as _

URL_MANUAL = "https://rafaelurben.github.io/django-kmuhelper/manual/"
URL_FAQ = "https://rafaelurben.github.io/django-kmuhelper/manual/faq"

ORDERSTATUS = [
    ("pending", _("Zahlung ausstehend")),
    ("processing", _("In Bearbeitung")),
    ("on-hold", _("In Wartestellung")),
    ("completed", _("Abgeschlossen")),
    ("cancelled", _("Storniert/Abgebrochen")),
    ("refunded", _("Rückerstattet")),
    ("failed", _("Fehlgeschlagen")),
    ("trash", _("Gelöscht")),
]

VAT_RATES = [
    (0.0, _("0.0% (Mehrwertsteuerfrei)")),
    (2.5, _("2.5% (Bis 2023: Reduzierter Satz)")),
    (2.6, _("2.6% (Ab 2024: Reduzierter Satz)")),
    (3.7, _("3.7% (Bis 2023: Sondersatz für Beherbergung)")),
    (3.8, _("3.8% (Ab 2024: Sondersatz für Beherbergung)")),
    (7.7, _("7.7% (Bis 2023: Normalsatz)")),
    (8.1, _("8.1% (Ab 2024: Normalsatz)")),
]
VAT_RATE_DEFAULT = 7.7

PAYMENTMETHODS = [
    ("bacs", _("Überweisung")),
    ("cheque", _("Scheck")),
    ("cod", _("Rechnung / Nachnahme")),
    ("paypal", _("PayPal")),
]

COUNTRIES = [("CH", _("Schweiz")), ("LI", _("Liechtenstein"))]

LANGUAGES = [
    ("de", _("Deutsch [DE]")),
    ("fr", _("Französisch [FR]")),
    ("it", _("Italienisch [IT]")),
    ("en", _("Englisch [EN]")),
]

ADDR_BILLING_FIELDS_WITHOUT_CONTACT = [
    "addr_billing_first_name",
    "addr_billing_last_name",
    "addr_billing_company",
    "addr_billing_address_1",
    "addr_billing_address_2",
    "addr_billing_postcode",
    "addr_billing_city",
    "addr_billing_state",
    "addr_billing_country",
]

ADDR_BILLING_FIELDS = [
    "addr_billing_first_name",
    "addr_billing_last_name",
    "addr_billing_company",
    "addr_billing_address_1",
    "addr_billing_address_2",
    "addr_billing_postcode",
    "addr_billing_city",
    "addr_billing_state",
    "addr_billing_country",
    "addr_billing_email",
    "addr_billing_phone",
]

ADDR_BILLING_FIELDS_CATEGORIZED = [
    ("addr_billing_first_name", "addr_billing_last_name"),
    "addr_billing_company",
    ("addr_billing_address_1", "addr_billing_address_2"),
    ("addr_billing_postcode", "addr_billing_city"),
    ("addr_billing_state", "addr_billing_country"),
    ("addr_billing_email", "addr_billing_phone"),
]

ADDR_SHIPPING_FIELDS_WITHOUT_CONTACT = [
    "addr_shipping_first_name",
    "addr_shipping_last_name",
    "addr_shipping_company",
    "addr_shipping_address_1",
    "addr_shipping_address_2",
    "addr_shipping_postcode",
    "addr_shipping_city",
    "addr_shipping_state",
    "addr_shipping_country",
]

ADDR_SHIPPING_FIELDS = [
    "addr_shipping_first_name",
    "addr_shipping_last_name",
    "addr_shipping_company",
    "addr_shipping_address_1",
    "addr_shipping_address_2",
    "addr_shipping_postcode",
    "addr_shipping_city",
    "addr_shipping_state",
    "addr_shipping_country",
    "addr_shipping_email",
    "addr_shipping_phone",
]

ADDR_SHIPPING_FIELDS_CATEGORIZED = [
    ("addr_shipping_first_name", "addr_shipping_last_name"),
    "addr_shipping_company",
    ("addr_shipping_address_1", "addr_shipping_address_2"),
    ("addr_shipping_postcode", "addr_shipping_city"),
    ("addr_shipping_state", "addr_shipping_country"),
    ("addr_shipping_email", "addr_shipping_phone"),
]

INVOICE_DISPLAY_MODES = [
    ("business_orders", _("Geschäftlich (Bestellungen)")),
    ("business_services", _("Geschäftlich (Dienstleistungen)")),
    ("club", _("Verein")),
    ("private", _("Privat")),
]
