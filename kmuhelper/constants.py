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
    (2.6, _("2.6% (Reduzierter Satz)")),
    (3.8, _("3.8% (Sondersatz für Beherbergung)")),
    (8.1, _("8.1% (Normalsatz)")),
    (2.5, _("2.5% (Bis 2023: Reduzierter Satz)")),
    (3.7, _("3.7% (Bis 2023: Sondersatz für Beherbergung)")),
    (7.7, _("7.7% (Bis 2023: Normalsatz)")),
]
VAT_RATE_DEFAULT = 8.1

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

INVOICE_DISPLAY_MODES = [
    ("business_orders", _("Geschäftlich (Bestellungen)")),
    ("business_services", _("Geschäftlich (Dienstleistungen)")),
    ("club", _("Verein")),
    ("private", _("Privat")),
]

# Addresses

ADDR_FIELDS_WITHOUT_CONTACT = [
    "first_name",
    "last_name",
    "company",
    "address_1",
    "address_2",
    "postcode",
    "city",
    "state",
    "country",
]

ADDR_FIELDS = ADDR_FIELDS_WITHOUT_CONTACT + [
    "email",
    "phone",
]

ADDR_BILLING_FIELDS_WITHOUT_CONTACT = list(
    map(lambda f: f"addr_billing_{f}", ADDR_FIELDS_WITHOUT_CONTACT)
)

ADDR_BILLING_FIELDS = list(map(lambda f: f"addr_billing_{f}", ADDR_FIELDS))

ADDR_BILLING_FIELDS_CATEGORIZED = [
    ("addr_billing_first_name", "addr_billing_last_name"),
    "addr_billing_company",
    ("addr_billing_address_1", "addr_billing_address_2"),
    ("addr_billing_postcode", "addr_billing_city"),
    ("addr_billing_state", "addr_billing_country"),
    ("addr_billing_email", "addr_billing_phone"),
]

ADDR_SHIPPING_FIELDS_WITHOUT_CONTACT = list(
    map(lambda f: f"addr_shipping_{f}", ADDR_FIELDS_WITHOUT_CONTACT)
)

ADDR_SHIPPING_FIELDS = list(map(lambda f: f"addr_shipping_{f}", ADDR_FIELDS))

ADDR_SHIPPING_FIELDS_CATEGORIZED = [
    ("addr_shipping_first_name", "addr_shipping_last_name"),
    "addr_shipping_company",
    ("addr_shipping_address_1", "addr_shipping_address_2"),
    ("addr_shipping_postcode", "addr_shipping_city"),
    ("addr_shipping_state", "addr_shipping_country"),
    ("addr_shipping_email", "addr_shipping_phone"),
]
