---
permalink: /manual/integrations/paymentimport
---

# Zahlungsimport

Wenn Ihre Bank ihnen **detaillierte** Zahlungsdaten im XML-Format anbietet (camt.053d), können Sie diese im KMUHelper verarbeiten und entsprechende Bestellungen als bezahlt markieren. Dieses Feature konnte bisher nur mit Raiffeisen getestet werden und ist bisher spezifisch für Raiffeisen eingestellt. Auf [Anfrage](<{{ site.kontakt_url }}>) füge ich gerne andere Banken oder Formate hinzu, sofern diese die nötigen Kriterien erfüllen.

## Vorbereitung

1. Gehen Sie zu `/admin/kmuhelper/paymentimport/upload`
2. Wählen Sie Ihre Datei aus
3. Klicken Sie auf `Hochladen`
4. Sie sollten nun auf der Seite `Zahlungsimport - Verarbeitung` landen

## Verarbeitung

Auf dieser Seite befinden sich alle Zahlungen, kategorisiert in folgende Kategorien.

### Kategorien

Kategorien, welche keine Zahlungen enthalten, werden nicht angezeigt.

#### Unbekannte Zahlungen

Zahlungen, dessen Referenznummer nicht dem Format einer KMUHelper-Bestellung entspricht und deshalb nicht verarbeitet werden können.

#### Zahlungen mit unbekannten Bestellungen

Zahlungen, dessen Bestellnummer keinem Eintrag einer Bestellung entspricht.

#### Korrekte Zahlungen

Einer Bestellung zugeordnete Zahlungen, deren Betrag exakt übereinstimmt. Diese können ohne Bedenken alle als bezahlt markiert werden.

#### Zahlungen mit bereits als bezahlt markierten Bestellungen

Einer Bestellung zugeordnete Zahlungen, deren Betrag exakt übereinstimmt, die Bestellung jedoch bereits als bezahlt markiert wurde. Hierbei hat der Kunde möglicherweise die alte Bestellnummer für eine identische Bestellung verwendet oder eine Rechnung doppelt bezahlt.

#### Unklare Zahlungen

Zahlungen, welche einer Bestellung zugeordnet werden konnten, deren Betrag jedoch nicht übereinstimmt. Hierbei ist manuelle Überprüfung notwendig.

### Zusätzliche Infos

Falls vorhanden, werden andere unbezahlte Bestellungen des gleichen Kunden sowie (fast) identische Zahlungen angezeigt (welche entweder doppelt importiert oder **doppelt bezahlt** wurden).

## Zurück

[Zurück zum Handbuch](../README.md#inhalt)
