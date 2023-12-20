---
permalink: /manual/languages
---

# Sprachen

Der KMUHelper selbst ist aktuell nur in Deutsch verfügbar und eine Übersetzung ist vorerst nicht geplant, jedoch können
die Rechnungen in Deutsch, Französisch, Italienisch und Englisch gedruckt werden. Dabei wird immer die beim verlinkten
Kunden eingestellte Sprache verwendet.

Um auch Produkte und Mengenbezeichnungen zu übersetzen, wird der gleiche Syntax wie beim Wordpress Plugin `qTranslate-X`
verwendet.

Beispiel: `[:de]Stück[:fr]Pièce[:it]Pezzo[:en]Piece[:]`

Die Unterstützung für mehrere Sprachen existiert bei folgenden Feldern:

- Produkt: Name
- Produkt: Beschreibung
- Produkt: Mengenbezeichnung
- Kosten: Name

Auf Übersichtsseiten im Admin-Bereich wird ausschliesslich die Deutsche Bezeichnung angezeigt.

## Automatische Übersetzung

Folgende Mengenbezeichnungen werden bei exaktem Wortlaut automatisch übersetzt:

- Stück
- Stunden
- Einheiten
- Flasche
- Tube

Folgende Kostenbezeichnungen werden bei exaktem Wortlaut automatisch übersetzt:

- Versandkosten

## Zurück

[Zurück zum Handbuch](./README.md)
