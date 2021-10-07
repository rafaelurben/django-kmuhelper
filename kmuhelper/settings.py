"""Methods to get settings form different places"""

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from kmuhelper.main import models

DEBUG = settings.DEBUG
AUTH_USER_MODEL = settings.AUTH_USER_MODEL


# Database settings overview

SETTINGS = {
    "wc-url": {
        "typ": "url",
        "name": "WooCommerce Shop-Url",
        "description": "Falls vorhanden: Die URL der Wordpress-Seite."
    },
    "email-stock-warning-receiver": {
        "typ": "email",
        "name": "E-Mail-Adresse für Warnungen zum Lagerbestand",
        "description": "E-Mail-Adresse für E-Mails zu durch " +
                       "Bestellungsimport hervorgerufenem, geringem Lagerbestand.\n\n" +
                       "Leer lassen, um diese E-Mails zu deaktivieren."
    },
    "email-show-buttons": {
        "typ": "bool",
        "name": "E-Mail-Knöpfe anzeigen",
        "description": "Aktivieren oder Deaktivieren der E-Mail-Knöpfe bei Bestellungen und Kunden."
    },
    "email-signature": {
        "typ": "text",
        "name": "E-Mail-Signatur",
        "description": "Standardsignatur bei E-Mails"
    },
    "default-payment-conditions": {
        "typ": "char",
        "name": "Standardzahlungskonditionen",
        "description": "Standardwert für neue Bestellungen.\n" +
                       "Skonto und Zahlungsfrist nach Syntaxdefinition von Swico.\n\n" +
                       "Beispiel: '2:15;0:30' steht für 2% Skonto bei Zahlung innerhalb " +
                       "von 15 Tagen und eine Zahlungsfrist von 30 Tagen.\n\n" +
                       "Eine Zahlungsfrist MUSS vorhanden sein und am Schluss aufgeführt werden.\n\n" +
                       "Wenn leer gelassen, wird '0:30' als Standard verwendet."
    },
    "print-payment-conditions": {
        "typ": "bool",
        "name": "Zahlungskonditionen drucken",
        "description": "Wenn aktiviert, werden die Zahlungskonditionen bei Rechnungen " +
                       "in menschenlesbarer Form unter dem Rechnungstotal gedruckt.\n\n" + 
                       "Die Zahlungskonditionen werden unabhängig von dieser Einstellung " + 
                       "immer auch in manschinenlesbarer Form im QR-Code integriert."
    },
}

SECRET_SETTINGS = {
    "wc-consumer_key": {"typ": "char"},
    "wc-consumer_secret": {"typ": "char"},
    "wc-url": {"typ": "url"},
}


def setup_settings():
    """Setup the database settings"""

    for setting in SETTINGS:
        models.Einstellung.objects.update_or_create(
            id=setting, defaults=SETTINGS[setting])

    for secretsetting in SECRET_SETTINGS:
        models.Geheime_Einstellung.objects.update_or_create(
            id=secretsetting, defaults=SECRET_SETTINGS[secretsetting])


# File settings

def get_file_setting(name, default=None):
    """Get a setting from the settings.py file"""

    return getattr(settings, name, default)


def has_file_setting(name):
    """Check if a setting in the settings.py file has been set"""

    return hasattr(settings, name)

# Get db


def get_db_setting(settingid, default=None):
    """Get a setting from the 'Einstellung' model"""

    try:
        setting = models.Einstellung.objects.get(id=settingid)
        if setting.typ in ['char', 'text'] and setting.inhalt == "":
            return default
        return setting.inhalt
    except ObjectDoesNotExist:
        return default


def get_secret_db_setting(settingid, default=None):
    """Get a setting from the 'Geheime_Einstellung' model"""

    try:
        return models.Geheime_Einstellung.objects.get(id=settingid).inhalt
    except ObjectDoesNotExist:
        return default


# Set db

def set_db_setting(settingid, content):
    """Update a database setting"""

    try:
        obj = models.Einstellung.objects.get(id=settingid)
        obj.inhalt = content
        obj.save()
        return True
    except ObjectDoesNotExist:
        return False


def set_secret_db_setting(settingid, content):
    """Update a secret database setting"""

    try:
        obj = models.Geheime_Einstellung.objects.get(id=settingid)
        obj.inhalt = content
        obj.save()
        return True
    except ObjectDoesNotExist:
        return False
