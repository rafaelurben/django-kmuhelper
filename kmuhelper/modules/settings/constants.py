from django.utils.functional import lazy
from django.utils.html import format_html
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy

from kmuhelper.utils import faq

_ = gettext_lazy
_t = format_lazy
_h = lazy(format_html, str)

SETTINGS = {
    "wc-url": {
        "typ": "url",
        "name": _("Shop-URL"),
        "description": _(
            "URL des WooCommerce-/Wordpress-Shops, z.B. https://shop.example.com"
        ),
    },
    "wc-webhook-secret": {
        "typ": "char",
        "name": _("Webhook-Secret"),
        "description": _("Secret-Key für WooCommerce-Webhooks"),
    },
    "email-stock-warning-receiver": {
        "typ": "email",
        "name": _("E-Mail-Adresse für Warnungen zum Lagerbestand"),
        "description": _t(
            "{}\n\n{}\n\n{}",
            _(
                "Wenn durch den Import von Bestellungen der Lagerbestand-Soll-Wert unterschritten wird, wird eine "
                "Warnung an diese E-Mail-Adresse gesendet."
            ),
            _("Leer lassen, um diese E-Mails zu deaktivieren."),
            _(
                "Bemerkung: Entsteht die Unterschreitung durch eine manuelle Aktion, wird eine Warnung direkt "
                "angezeigt."
            ),
        ),
    },
    "email-show-buttons": {
        "typ": "bool",
        "name": _("E-Mail-Knöpfe anzeigen"),
        "description": _(
            "Aktivieren oder Deaktivieren der E-Mail-Knöpfe bei Bestellungen und Kunden."
        ),
    },
    "email-signature": {
        "typ": "text",
        "name": _("E-Mail-Signatur"),
        "description": _("Standardsignatur für E-Mails"),
    },
    "default-payment-conditions": {
        "typ": "char",
        "name": _("Standardzahlungskonditionen"),
        "description": _h(
            "{} {}\n\n{} -> {}",
            _("Standardwert der Zahlungskonditionen für neue Bestellungen."),
            _("Beispiele: 0:30 oder 2:10;0:30"),
            _("Mehr über Zahlungskonditionen erfahren"),
            faq("wie-funktionieren-zahlungskonditionen"),
        ),
    },
    "print-payment-conditions": {
        "typ": "bool",
        "name": _("Zahlungskonditionen drucken"),
        "description": _h(
            "{}\n\n{}\n\n{} -> {}",
            _(
                "Wenn aktiviert, werden die Zahlungskonditionen bei Rechnungen in menschenlesbarer Form unter dem "
                "Rechnungstotal gedruckt."
            ),
            _(
                "Die Zahlungskonditionen werden unabhängig von dieser Einstellung immer auch in maschinenlesbarer "
                "Form im QR-Code integriert."
            ),
            _("Mehr über Zahlungskonditionen erfahren"),
            faq("wie-funktionieren-zahlungskonditionen"),
        ),
    },
}

SETTINGS_FIELDSETS = [
    {
        "name": _("Zahlungskonditionen"),
        "fields": ["default-payment-conditions", "print-payment-conditions"],
        "classes": "wide",
    },
    {
        "name": _("E-Mails"),
        "fields": [
            "email-show-buttons",
            "email-signature",
            "email-stock-warning-receiver",
        ],
        "classes": "wide",
    },
]

SECRET_SETTINGS = {
    "wc-consumer_key": {"typ": "char"},
    "wc-consumer_secret": {"typ": "char"},
    "wc-url": {"typ": "url"},
}
