"""Useful constants used in multiple places"""

URL_MANUAL = "https://rafaelurben.github.io/django-kmuhelper/manual/"
URL_FAQ = "https://rafaelurben.github.io/django-kmuhelper/manual/faq"

ORDERSTATUS = [
    ("pending", "Zahlung ausstehend"),
    ("processing", "In Bearbeitung"),
    ("on-hold", "In Wartestellung"),
    ("completed", "Abgeschlossen"),
    ("cancelled", "Storniert/Abgebrochen"),
    ("refunded", "Rückerstattet"),
    ("failed", "Fehlgeschlagen"),
    ("trash", "Gelöscht")
]

MWSTSETS = [
    (0.0, "0.0% (Mehrwertsteuerfrei)"),
    (2.5, "2.5% (Bis 2023: Reduzierter Satz)"),
    (2.6, "2.6% (Ab 2024: Reduzierter Satz)"),
    (3.7, "3.7% (Bis 2023: Sondersatz für Beherbergung)"),
    (3.8, "3.8% (Ab 2024: Sondersatz für Beherbergung)"),
    (7.7, "7.7% (Bis 2023: Normalsatz)"),
    (8.1, "8.1% (Ab 2024: Normalsatz)"),
]
MWST_DEFAULT = 7.7

PAYMENTMETHODS = [
    ("bacs", "Überweisung"),
    ("cheque", "Scheck"),
    ("cod", "Rechnung / Nachnahme"),
    ("paypal", "PayPal")
]

COUNTRIES = [
    ("CH", "Schweiz"),
    ("LI", "Liechtenstein")
]

LANGUAGES = [
    ("de", "Deutsch [DE]"),
    ("fr", "Französisch [FR]"),
    ("it", "Italienisch [IT]"),
    ("en", "Englisch [EN]")
]

ADDR_BILLING_FIELDS_WITHOUT_CONTACT = [
    'addr_billing_first_name', 'addr_billing_last_name',
    'addr_billing_company',
    'addr_billing_address_1', 'addr_billing_address_2',
    'addr_billing_postcode', 'addr_billing_city',
    'addr_billing_state', 'addr_billing_country',
]

ADDR_BILLING_FIELDS = [
    'addr_billing_first_name', 'addr_billing_last_name',
    'addr_billing_company',
    'addr_billing_address_1', 'addr_billing_address_2',
    'addr_billing_postcode', 'addr_billing_city',
    'addr_billing_state', 'addr_billing_country',
    'addr_billing_email', 'addr_billing_phone'
]

ADDR_BILLING_FIELDS_CATEGORIZED = [
    ('addr_billing_first_name', 'addr_billing_last_name'),
    'addr_billing_company',
    ('addr_billing_address_1',
     'addr_billing_address_2'),
    ('addr_billing_postcode', 'addr_billing_city'),
    ('addr_billing_state', 'addr_billing_country'),
    ('addr_billing_email', 'addr_billing_phone')
]

ADDR_SHIPPING_FIELDS_WITHOUT_CONTACT = [
    'addr_shipping_first_name', 'addr_shipping_last_name',
    'addr_shipping_company',
    'addr_shipping_address_1', 'addr_shipping_address_2',
    'addr_shipping_postcode', 'addr_shipping_city',
    'addr_shipping_state', 'addr_shipping_country',
]

ADDR_SHIPPING_FIELDS = [
    'addr_shipping_first_name', 'addr_shipping_last_name',
    'addr_shipping_company',
    'addr_shipping_address_1', 'addr_shipping_address_2',
    'addr_shipping_postcode', 'addr_shipping_city',
    'addr_shipping_state', 'addr_shipping_country',
    'addr_shipping_email', 'addr_shipping_phone'
]

ADDR_SHIPPING_FIELDS_CATEGORIZED = [
    ('addr_shipping_first_name', 'addr_shipping_last_name'),
    'addr_shipping_company',
    ('addr_shipping_address_1',
     'addr_shipping_address_2'),
    ('addr_shipping_postcode', 'addr_shipping_city'),
    ('addr_shipping_state', 'addr_shipping_country'),
    ('addr_shipping_email', 'addr_shipping_phone')
]
