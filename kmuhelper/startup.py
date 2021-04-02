from rich import print

from django.conf import settings
from kmuhelper.main.models import Einstellung, Geheime_Einstellung

def log(string, *args):
    print("[deep_pink4][KMUHelper][/] -", string, *args)

# Einstellungen festlegen

log("startup.py running...")

log("startup.py DEBUG is", settings.DEBUG)

try:
    Einstellung.objects.get_or_create(id="wc-url", typ="url", name="WooCommerce Shop-Url")
    Einstellung.objects.get_or_create(id="email-stock-warning-receiver", typ="email", name="E-Mail für Warnungen zum Lagerbestand")
    Einstellung.objects.get_or_create(id="email-show-buttons", typ="bool", name="E-Mail Knöpfe anzeigen")

    Geheime_Einstellung.objects.get_or_create(id="wc-consumer_key")
    Geheime_Einstellung.objects.get_or_create(id="wc-consumer_secret")
    Geheime_Einstellung.objects.get_or_create(id="wc-url")
except Exception as e:
    log("startup.py failed: Error while adding settings:", e)

log("startup.py ended")