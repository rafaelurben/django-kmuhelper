"""Useful constants used in multiple places"""

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
