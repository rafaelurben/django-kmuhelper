---
permalink: /manual/faq
---

# Häufig gestellte Fragen

Zurück zum [Benutzerhandbuch](./).

## Inhalt

- [Was passiert, wenn ich eine Bestellung als bezahlt/versendet markiere?](#was-passiert-wenn-ich-eine-bestellung-als-bezahltversendet-markiere)
- [Wie funktionieren Zahlungskonditionen?](#wie-funktionieren-zahlungskonditionen)

### Was passiert, wenn ich eine Bestellung als bezahlt/versendet markiere?

Wenn eine Bestellung als bezahlt markiert wird, können keine Änderungen mehr getätigt werden, welche den Endbetrag sowie die Zahlungsmöglichkeiten betreffen. Auch kann die Rechnungsadresse nicht mehr geändert werden.
Wenn eine Bestellung als versendet markiert wird, können keine Änderungen mehr getätigt werden, welche die Produkte betreffen. Auch kann die Lieferadresse nicht mehr geändert werden. Die Trackingnummer ist davon nicht betroffen.

Die dadurch gesperrten Felder können durch Anhängen von `?unlock` an die URL wieder entsperrt werden. Dies kann jedoch zu unerwünschten Seiteneffekten führen und sollte nur in Ausnahmefällen verwendet werden.

### Wie funktionieren Zahlungskonditionen?

Im Feld "Zahlungskonditionen" können Zahlungskonditionen für die Bestellung angegeben werden. Die Zahlungskonditionen besagen, in wie vielen Tagen eine Rechnung bezahlt werden muss und bis nach wie vielen Tagen Skonto gewährt wird. Die Zahlungskonditionen werden in die QR-Rechnung integriert und, sofern in den Einstellungen aktiviert, auf der Rechnung angezeigt.

Syntax: `Skonto in Prozent:Tage;Skonto in Prozent:Tage;...;0:Zahlungsfrist in Tagen`

Beispiel: `2:10;1:20;0:30` bedeutet, dass 2% Skonto gewährt wird, wenn die Rechnung innerhalb von 10 Tagen bezahlt wird. 1% Skonto wird gewährt, wenn die Rechnung innerhalb von 20 Tagen bezahlt wird. Die Zahlungsfrist beträgt 30 Tage.

Eine Zahlungsfrist **muss** vorhanden sein und am Schluss aufgeführt werden. Der Standardwert beträgt `0:30`, also 30 Tage Zahlungsfrist.
