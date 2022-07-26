"""Methods to get settings form different places"""

from django.conf import settings as djangoconfig
from django.core.exceptions import ObjectDoesNotExist

from kmuhelper.modules.settings.models import Einstellung, Geheime_Einstellung
from kmuhelper.modules.settings.constants import SETTINGS, SECRET_SETTINGS

DEBUG = djangoconfig.DEBUG
AUTH_USER_MODEL = djangoconfig.AUTH_USER_MODEL


def setup_settings():
    """Setup the database settings"""

    for setting in SETTINGS:
        Einstellung.objects.update_or_create(
            id=setting, defaults=SETTINGS[setting])

    for secretsetting in SECRET_SETTINGS:
        Geheime_Einstellung.objects.update_or_create(
            id=secretsetting, defaults=SECRET_SETTINGS[secretsetting])


# File settings

def get_file_setting(name, default=None):
    """Get a setting from the settings.py file"""

    return getattr(djangoconfig, name, default)


def has_file_setting(name):
    """Check if a setting in the settings.py file has been set"""

    return hasattr(djangoconfig, name)

# Get db


def get_db_setting(settingid, default=None):
    """Get a setting from the 'Einstellung' model"""

    try:
        setting = Einstellung.objects.get(id=settingid)
        if setting.typ in ['char', 'text'] and setting.content == "":
            return default
        return setting.content
    except ObjectDoesNotExist:
        return default


def get_secret_db_setting(settingid, default=None):
    """Get a setting from the 'Geheime_Einstellung' model"""

    try:
        return Geheime_Einstellung.objects.get(id=settingid).content
    except ObjectDoesNotExist:
        return default


# Set db

def set_db_setting(settingid, content):
    """Update a database setting"""

    try:
        obj = Einstellung.objects.get(id=settingid)
        obj.content = content
        obj.save()
        return True
    except ObjectDoesNotExist:
        return False


def set_secret_db_setting(settingid, content):
    """Update a secret database setting"""

    try:
        obj = Geheime_Einstellung.objects.get(id=settingid)
        obj.content = content
        obj.save()
        return True
    except ObjectDoesNotExist:
        return False
