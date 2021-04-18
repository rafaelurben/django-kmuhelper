"""Methods to get settings form different places"""

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from kmuhelper.main import models


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
        return models.Einstellung.objects.get(id=settingid).inhalt
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
