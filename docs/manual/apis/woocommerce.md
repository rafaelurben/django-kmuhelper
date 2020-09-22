---
permalink: /manual/apis/woocommerce
fbcontact: true
---

# WooCommerce-Integration

Sie können den KMUHelper mit einem WooCommerce Shop verbinden, um Bestellungen, Produkte und Kunden von WooCommerce zu importieren.

Import einrichten:

1.  Öffnen Sie `/admin/kmuhelper/`
2.  Klicken Sie auf `Einstellungen`
3.  Klicken Sie auf `WooCommerce Shop-Url`
4.  Geben Sie die Domain Ihrer Wordpress-Seite ein
5.  Klicken Sie auf `Sichern`
6.  Klicken Sie oben rechts auf `WooCommerce verbinden`

Sie sollten nun auf Ihren Shop weitergeleitet werden, wo Sie dem KMUHelper Lese-Berechtigungen erteilen können. Sobald Sie die Berechtigungen erteilt haben, sollten Sie zurück auf den KMUHelper weitergeleitet werden und eine Meldung mit dem Inhalt `WooCommerce erfolgreich verbunden` erhalten. Ebenfalls sollte bei der URL nun `Bestätigt` stehen.

Damit die Daten im KMUHelper auch automatisch aktualisiert werden, können sogenannte "Webhooks" eingerichtet werden, welche bei jeder Änderung in WooCommerce den KMUHelper darüber informieren. (WICHTIG: Manche Daten im KMUHelper werden bei Erhalt der Daten von WooCommerce ÜBERSCHRIEBEN! Deshalb sollten Sie Änderungen an Produkten und Kunden vorzugsweise in WooCommerce vornehmen, statt im KMUHelper, um Fehler zu vermeiden.)

Webhooks einrichten:

1.  Gehen Sie in den Wordpress-Adminbereich Ihrer Wordpress-Seite
2.  Gehen Sie zu `WooCommerce -> Einstellungen -> Erweitert -> Webhooks`
3.  Fügen Sie für folgende Themen je einen Webhook mit der Auslieferungs-URL `https://EXAMPLE.COM/kmuhelper/wc/webhooks` hinzu:
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

Im KMUHelper-Admin finden Sie nun bei Produkten, Bestellungen und Kunden einen `Importieren` Knopf. Je nach Menge von Daten kann der Importprozess von Objekten sehr lange dauern. Je nach Hosting-Provider könnte die Verbindung nach 30 Sekunden abgebrochen werden (Dies ist z.B. bei Heroku der Fall!). In diesem Fall ist ein (mehrfaches) Neuladen der Seite hilfreich.

Das Neuladen ist jedoch nicht hilfreich bei manuellem Aktualisieren von einer grösseren Menge von Objekten! In diesem Fall müssen die Objekte in mehrere Teile aufgeteilt werden.

## Zurück

[Zurück zur Einrichtung](../setup.md#integrationen)
