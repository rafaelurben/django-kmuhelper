"""Useful constants used in multiple places"""

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

RECHNUNGSADRESSE_FIELDS_WITHOUT_CONTACT = [
    'rechnungsadresse_vorname', 'rechnungsadresse_nachname',
    'rechnungsadresse_firma',
    'rechnungsadresse_adresszeile1', 'rechnungsadresse_adresszeile2',
    'rechnungsadresse_plz', 'rechnungsadresse_ort',
    'rechnungsadresse_kanton', 'rechnungsadresse_land',
]

RECHNUNGSADRESSE_FIELDS = [
    'rechnungsadresse_vorname', 'rechnungsadresse_nachname',
    'rechnungsadresse_firma',
    'rechnungsadresse_adresszeile1', 'rechnungsadresse_adresszeile2',
    'rechnungsadresse_plz', 'rechnungsadresse_ort',
    'rechnungsadresse_kanton', 'rechnungsadresse_land',
    'rechnungsadresse_email', 'rechnungsadresse_telefon'
]

RECHNUNGSADRESSE_FIELDS_CATEGORIZED = [
    ('rechnungsadresse_vorname', 'rechnungsadresse_nachname'),
    'rechnungsadresse_firma',
    ('rechnungsadresse_adresszeile1',
     'rechnungsadresse_adresszeile2'),
    ('rechnungsadresse_plz', 'rechnungsadresse_ort'),
    ('rechnungsadresse_kanton', 'rechnungsadresse_land'),
    ('rechnungsadresse_email', 'rechnungsadresse_telefon')
]

LIEFERADRESSE_FIELDS_WITHOUT_CONTACT = [
    'lieferadresse_vorname', 'lieferadresse_nachname',
    'lieferadresse_firma',
    'lieferadresse_adresszeile1', 'lieferadresse_adresszeile2',
    'lieferadresse_plz', 'lieferadresse_ort',
    'lieferadresse_kanton', 'lieferadresse_land',
]

LIEFERADRESSE_FIELDS = [
    'lieferadresse_vorname', 'lieferadresse_nachname',
    'lieferadresse_firma',
    'lieferadresse_adresszeile1', 'lieferadresse_adresszeile2',
    'lieferadresse_plz', 'lieferadresse_ort',
    'lieferadresse_kanton', 'lieferadresse_land',
    'lieferadresse_email', 'lieferadresse_telefon'
]

LIEFERADRESSE_FIELDS_CATEGORIZED = [
    ('lieferadresse_vorname', 'lieferadresse_nachname'),
    'lieferadresse_firma',
    ('lieferadresse_adresszeile1',
     'lieferadresse_adresszeile2'),
    ('lieferadresse_plz', 'lieferadresse_ort'),
    ('lieferadresse_kanton', 'lieferadresse_land'),
    ('lieferadresse_email', 'lieferadresse_telefon')
]
