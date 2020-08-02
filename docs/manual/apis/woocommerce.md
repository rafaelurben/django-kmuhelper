# WooCommerce-Integration

Du kannst den KMUHelper mit einem WooCommerce Shop verbinden, um Bestellungen, Produkte und Kunden von WooCommerce zu importieren.

Import einrichten:

1.  Klicke auf `Einstellungen`
2.  Klicke auf `WooCommerce Shop-Url`
3.  Gib die Domain deines Shops ein.
4.  Klicke auf `Sichern`
5.  Klicke oben rechts auf `WooCommerce verbinden`

Du solltest nun auf deinen Shop weitergeleitet werden, wo du dem KMUHelper Lese-Berechtigungen erteilen kannst. Sobald du die Berechtigungen erteilt hast, solltest du zurück auf den KMUHelper weitergeleitet werden und du solltest eine Meldung `WooCommerce erfolgreich verbunden` erhalten. Ebenfalls sollte bei der URL nun `Bestätigt` stehen. - Bei den

Damit die Daten im KMUHelper auch automatisch aktualisiert werden, können sogenannte "Webhooks" eingerichtet werden, welche bei jeder Änderung in WooCommerce den KMUHelper darüber informieren. (WICHTIG: Daten im KMUHelper werden bei Erhalt der Daten von WooCommerce ÜBERSCHRIEBEN! Deshalb solltest du Änderungen an Produkten, Kunden und Bestellungen in WooCommerce vornehmen, statt im KMUHelper.)

Webhooks einrichten:

1.  Gehe in den Wordpress-Adminbereich deiner Webseite
2.  Gehe zu `WooCommerce -> Einstellungen -> Erweitert -> Webhooks`
3.  Füge für folgende Themen je einen Webhook mit der Auslieferungs-URL `https://EXAMPLE.COM/kmuhelper/wc/webhooks` hinzu:
    -   Bestellung erstellt (order.created)
    -   Bestellung aktualisiert (order.updated)
    -   Bestellung gelöscht (order.deleted)
    -   Kunde erstellt (customer.created)
    -   Kunde aktualisiert (customer.updated)
    -   Kunde gelöscht (customer.deleted)
    -   Produkt erstellt (product.created)
    -   Produkt aktualisiert (product.updated)
    -   Produkt entfernt (product.deleted)

## Verwendung

Im KMUHelper-Admin findest du nun bei Produkten, Bestellungen und Kunden einen Importieren-Knopf. Je nach Menge von Daten kann der Importprozess von Objekten sehr lange dauern. Je nach Hosting-Provider könnte die Verbindung nach 30 Sekunden abgebrochen werden. In diesem Fall ist ein (mehrfaches) Neu-laden der Seite hilfreich.

## Zurück

WooCommerce ist nun mit dem KMUHelper verbunden. [Zurück zur Einrichtung](../setup#integrationen)
