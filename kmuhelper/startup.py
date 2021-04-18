from rich import print

from django.conf import settings
from kmuhelper.main.models import Einstellung, Geheime_Einstellung


def log(string, *args):
    print("[deep_pink4][KMUHelper][/] -", string, *args)

# Einstellungen festlegen


log("startup.py running...")

log("startup.py DEBUG is", settings.DEBUG)

try:
    Einstellung.objects.update_or_create(
        id="wc-url", defaults={
            "typ": "url", "name": "WooCommerce Shop-Url"})
    Einstellung.objects.update_or_create(
        id="email-stock-warning-receiver", defaults={
            "typ": "email", "name": "E-Mail für Warnungen zum Lagerbestand"})
    Einstellung.objects.update_or_create(
        id="email-show-buttons", defaults={
            "typ": "bool", "name": "E-Mail Knöpfe anzeigen"})
    Einstellung.objects.update_or_create(
        id="email-signature", defaults={
            "typ": "text", "name": "E-Mail Signatur"})

    Geheime_Einstellung.objects.update_or_create(
        id="wc-consumer_key", defaults={
            "typ": "char"})
    Geheime_Einstellung.objects.update_or_create(
        id="wc-consumer_secret", defaults={
            "typ": "char"})
    Geheime_Einstellung.objects.update_or_create(
        id="wc-url", defaults={
            "typ": "url"})
except Exception as error:
    log("startup.py failed: Error while adding settings:", type(error), error)

log("startup.py ended")
