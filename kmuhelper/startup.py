from rich import print

from django.conf import settings
from kmuhelper.main.models import Einstellung, Geheime_Einstellung


def log(string, *args):
    print("[deep_pink4][KMUHelper startup.py][/] -", string, *args)

# Einstellungen festlegen


log("Started... DEBUG is", settings.DEBUG)

try:
    Einstellung.objects.update_or_create(
        id="wc-url", defaults={
            "typ": "url",
            "name": "WooCommerce Shop-Url",
            "description": "Falls vorhanden: Die URL der Wordpress-Seite."})
    Einstellung.objects.update_or_create(
        id="email-stock-warning-receiver", defaults={
            "typ": "email",
            "name": "E-Mail-Adresse für Warnungen zum Lagerbestand",
            "description": "E-Mail-Adresse für E-Mails zu durch " +
                           "Bestellungsimport hervorgerufenem, geringem Lagerbestand.\n\n" +
                           "Leer lassen, um diese E-Mails zu deaktivieren."})
    Einstellung.objects.update_or_create(
        id="email-show-buttons", defaults={
            "typ": "bool",
            "name": "E-Mail-Knöpfe anzeigen",
            "description": "Aktivieren oder Deaktivieren der E-Mail-Knöpfe bei Bestellungen und Kunden."})
    Einstellung.objects.update_or_create(
        id="email-signature", defaults={
            "typ": "text",
            "name": "E-Mail-Signatur",
            "description": "Standardsignatur bei E-Mails"})
    Einstellung.objects.update_or_create(
        id="default-payment-conditions", defaults={
            "typ": "char",
            "name": "Standardzahlungskonditionen",
            "description": "Standardwert für neue Bestellungen.\n" + 
                           "Skonto und Zahlfrist nach Syntaxdefinition von Swico.\n\n" +
                           "Beispiel: '2:15;0:30' steht für 2% Skonto bei Zahlung innerhalb " +
                           "von 15 Tagen und eine Zahlungsfrist von 30 Tagen.\n\n" +
                           "Wenn leer gelassen, wird '0:30' als Standard verwendet."})

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
    log("Failed: Error while adding/updating settings:", type(error), error)

log("Ended.")
