from kmuhelper.utils import faq

SETTINGS = {
    "wc-url": {
        "typ": "url",
        "name": "WooCommerce Shop-Url",
        "description": "Falls vorhanden: Die URL der Wordpress-Seite."
    },
    "email-stock-warning-receiver": {
        "typ": "email",
        "name": "E-Mail-Adresse für Warnungen zum Lagerbestand",
        "description": "Wenn durch den Import von Bestellungen der Lagerbestand-Soll-Wert unterschritten wird, " +
                       "wird eine Warnung an diese E-Mail-Adresse gesendet.\n\n" +
                       "Leer lassen, um diese E-Mails zu deaktivieren.\n\n" +
                       "Bemerkung: Entsteht die Unterschreitung durch eine manuelle Aktion, wird eine Warnung direkt angezeigt."
    },
    "email-show-buttons": {
        "typ": "bool",
        "name": "E-Mail-Knöpfe anzeigen",
        "description": "Aktivieren oder Deaktivieren der E-Mail-Knöpfe bei Bestellungen und Kunden."
    },
    "email-signature": {
        "typ": "text",
        "name": "E-Mail-Signatur",
        "description": "Standardsignatur für E-Mails"
    },
    "default-payment-conditions": {
        "typ": "char",
        "name": "Standardzahlungskonditionen",
        "description": "Standardwert der Zahlungskonditionen für neue Bestellungen. " +
                       "Wenn leer gelassen, wird '0:30' als Standard verwendet.\n\n"
                       "Weitere Informationen zu Zahlungskonditionen befinden sich " +
                       faq('wie-funktionieren-zahlungskonditionen', 'hier')
    },
    "print-payment-conditions": {
        "typ": "bool",
        "name": "Zahlungskonditionen drucken",
        "description": "Wenn aktiviert, werden die Zahlungskonditionen bei Rechnungen " +
                       "in menschenlesbarer Form unter dem Rechnungstotal gedruckt.\n\n" +
                       "Die Zahlungskonditionen werden unabhängig von dieser Einstellung " +
                       "immer auch in manschinenlesbarer Form im QR-Code integriert.\n\n" +
                       "Weitere Informationen zu Zahlungskonditionen befinden sich " +
                       faq('wie-funktionieren-zahlungskonditionen', 'hier')
    },
}

SETTINGS_FIELDSETS = [
    {
        'name': 'Zahlungskonditionen',
        'fields': ['default-payment-conditions', 'print-payment-conditions'],
        'classes': 'wide',
    },
    {
        'name': 'E-Mails',
        'fields': ['email-show-buttons', 'email-signature', 'email-stock-warning-receiver'],
        'classes': 'wide',
    },
    {
        'name': 'WooCommerce-Integration',
        'fields': ['wc-url'],
        'classes': 'wide',
    },
]

SECRET_SETTINGS = {
    "wc-consumer_key": {"typ": "char"},
    "wc-consumer_secret": {"typ": "char"},
    "wc-url": {"typ": "url"},
}
