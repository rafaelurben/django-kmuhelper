---
permalink: /manual/emails
---

# E-Mails

Mit dem KMUHelper können auch E-Mails versendet werden.

## Dashboard

Das E-Mail Dashboard kann über den Startbildschirm erreicht werden. Es besteht aus drei Seiten:

- E-Mail
- Anhänge
- E-Mail Vorlagen

### E-Mail

E-Mails besitzen folgende Einstellungsmöglichkeiten, welche wie bei normalen E-Mails funktionieren:

- Betreff
- Empfänger (Je eine E-Mail pro Zeile)
  - Direkte(r) Empfänger
  - CC (Kopie)
  - BCC (Blindkopie)
- Anhänge

Zusätzlich können festgelegt werden:

- Designvorlage
  - Sollte in den meisten Fällen nicht verändert werden.
  - Es handelt sich dabei um in `kmuhelper/emails/` gespeicherte HTML-Dateien.
- Text
  - Der Hauptinhalt der E-Mail.
  - Je nach Designvorlage wird dieser nicht zwingend verwendet.
  - Unterstützt KEIN HTML
  - Links und E-Mail-Adressen werden in Links verwandelt.
- Daten
  - Zusätzliche Daten, mit welchen die Designvorlage befüllt wird.
  - In den meisten Fällen überflüssig.
  - Müssen im JSON-Format angegeben werden.
  - Die Vorlage `default.html` unterstützt folgende Einstellungen:
    - `title`: Der Text im Header
    - `header-background`: Die Hintergrundfarbe des Headers (HEX, z.B. `#FFFFFF`)
    - `header-foreground`: Die Vordergrundfarbde des Headers (HEX, z.B. `#000000`)
    - `firstcontent`: Inhalt vor dem Hauptinhalt (gleiche Funktionen wie Text)
    - `lastcontent`: Inhalt nach dem Hauptinhalt (gleiche Funktionen wie Text)

### Anhänge

Anhänge können manuell hochgeladen und an eine E-Mail angehängt werden. Diese können auch beliebig gelöscht werden, sofern sie nicht an einer E-Mail angehängt sind. Um diese trotzdem zu löschen, müsste zuerst die E-Mail gelöscht werden, dies würde aber "online ansehen" Links unbrauchbar machen.

### E-Mail Vorlagen

E-Mail Vorlagen betreffen nur den Text einer E-Mail. Diese sind jedoch nicht mit den in Dateien gespeicherten Designvorlagen zu verwechseln! Mit E-Mail Vorlagen können zum Beispiel häufig verwendete Texte einfach kopiert und angepasst werden. Diese Vorlagen unterstützen sogar eine Platzhalter-Fähigkeit. Diese ist auf der Erstellungsseite für Vorlagen erklärt.

Hinweis: Die Vorlagen werden mit der E-Mail NICHT verknüpft, diese werden nur zum Generieren einer E-Mail verwendet.

## "Online ansehen"

E-Mails werden, sofern in den [Einstellungen](#einstellungen-(fortgeschritten)) aktiviert, mit einem "online ansehen" Link versendet. Personen, welche einen veralteten E-Mail Client verwenden, können die E-Mail so im Browser ansehen.

## Automatisch generierte E-Mails

Die Rechnung zu einer Bestellung kann per Knopfdruck an die hinterlegte E-Mail-Adresse in der Rechnungsadresse gesendet werden. Dazu erscheint, sofern E-Mail Knöpfe in den Admin-Einstellungen aktiviert sind und benötigte Berechtigungen vorhanden sind, in der oberen rechten Ecke ein Knopf. Die Vorlage dazu (`kmuhelper/emails/bestellung_rechnung.html`) muss möglicherweise je nach Verwendungszweck überschrieben werden.

## Automatisierte E-Mails

Wenn in den Einstellungen eine E-Mail-Adresse für Warnungen zum Lagerbestand angegeben wurde, wird beim Import von Bestellungen automatisch geprüft, ob diese Bestellung den Lagerbestand mancher Produkte gefährdet. Sollte dies der Fall sein, wird automatisch eine E-Mail versendet, in welcher ersichtlich ist, von welchen Produkten noch wie viel vorhanden sind. Dies wird übrigens auch beim Speichern einer Bestellung sowie eines Produktes geprüft, jedoch wird in diesem Fall keine E-Mail versendet.

Alle automatischen E-Mails werden auch in der E-Mail-Ansicht aufgeführt.

## Einstellungen (fortgeschritten)

Hinweis: Hierbei handelt es sich nicht um die Einstellungen im Adminbereich, sondern um die Einstellungsdatei `settings.py`. Für all diese Einstellungen befindet sich in der [Einstellungsdatei der Vorlage](https://github.com/rafaelurben/djangoproject-template-kmuhelper-heroku/blob/master/mysite/settings.py) ein Beispiel.

1. Um zu jeder E-Mail einen "online ansehen" Link hinzuzufügen, muss die Einstellung `KMUHELPER_DOMAIN` gesetzt sein.
2. Mit `KMUHELPER_LOG_EMAIL` kann eine E-Mail Adresse festgelegt werden, welche zu allen ausgehenden E-Mails als BCC hinzugefügt wird.
3. Ausserdem können mit `KMUHELPER_EMAILS_DEFAULT_CONTEXT` ein paar Einstellungen für das Aussehen getroffen werden. Darunter z.B. die Farben des "Headers", der Text darin sowie Text vor und nach dem Hauptinhalt. Diese Einstellungen können auch für einzelne E-Mails angepasst werden. ("Daten")

## Zurück

[Zurück zum Handbuch](./README.md)
