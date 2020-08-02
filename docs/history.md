---
permalink: /history
---

# Geschichte

Die Entstehung des KMUHelpers ist eigentlich eine ziemlich lange Geschichte.

Ursprünglich war es mehr oder weniger ein kleines Testprojekt, um mich mit Web-Development auseinanderzusetzen, mittlerweile ist es jedoch ein brauchbares Tool für die Buchhaltung von Schweizer KMU.

Im Hinterkopf hatte ich immer die Hoffnung, der KMUHelper wäre irgendwann wiklich von einem KMU in Gebrauch (was er heute sogar tatsächlich ist), aber irgendwie glaubte ich nie wirklich daran.

## Flask

Die erste Version des KMUHelpers war nicht für wirklich viel zu gebrauchen, sie wurde sogar gar nie fertiggestellt. Diese Version hatte ich mit dem Python-Flask Framework gebaut, welches ich mittlerweile so gut wie nicht mehr benutze, seit ich Django brauche.

Ich weiss nicht, was ich mir damals überlegt habe, aber diese Version speicherte alle Daten in einer JSON Datei auf dem Server, was eigentlich nicht wirklich die Beste Idee ist.

## Datenbanken

Bei der zweiten Version hatte ich schon ein wenig mehr Ahnung, und machte dasselbe mit einer Loginseite, bei der man die Logindaten für eine MySql-Datenbank angeben konnte, welche dann in einem Cookie gespeichert wurden. Grundsätzlich unterschied sich diese Version nicht stark von der ersten - beide waren für nichts zu gebrauchen.

## Django

Irgendwann, während ich irgendetwas über Flask googelte, sah ich per Zufall ein Bild vom Django-Adminbereich, und dachte mir so: "Oha, das brauche ich!"

Kurz darauf beschäftigte ich mich intensiv mit Django und, nachdem ich das Tutorial-Projekt zum laufen bekommen hatte, "portierte" ich eines meiner Flask-Projekte in Django ([Hier](https://github.com/rafaelurben/django-choosemusic) können Sie sich den Müll ansehen. xD). Dies war eine sehr gute Übung für mich, auch wenn das Projekt nicht wirklich für viel ist.

Kurz darauf begann ich, den KMUHelper in Django neu zu bauen. Mit den Django-Models und Django-Admins hatte ich das ganze Projekt, wozu ich in Flask eine Ewigkeit brauchte, in wenigen Tagen auf dem selben Stand. (Ja, in Flask hatte ich alle Aktionen mit der Datenbank manuell via mysql-connector gemacht, ich wusste nicht, dass es für Flask auch so was wie Datenbank-Modelle gibt, generell hatte ich zuvor keine Ahnung von Datenbanken. xD EDIT: Scheinbar gibt es sogar flask-admin... o.O)

Mittlerweile ist der KMUHelper eine brauchbare, auf django-admin basierende Web-Applikation, welche sogar Schweizer QR-Rechnungen generieren kann.

## Heute

Mit Django wurde der KMUHelper für mich ein Projekt, in welchem ich Potential sah, da Buchhaltungssoftware für viele KMU viel zu teuer ist, und dies eine meiner Meinung nach gute Alternative zu konstenpflichtiger Buchhaltungssoftware ist.

Die [Funktionen](functions.md) des KMUHelpers werden stetig ergänzt und verbessert.

Bei Fragen könnem Sie mich gerne [kontaktieren](https://rafaelurben.github.io/diverses/rafaelurben/#kontakt).

## Zurück

[Zurück zur Startseite](./)
