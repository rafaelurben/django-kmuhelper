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
