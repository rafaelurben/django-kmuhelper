---
permalink: /installation
---

# Installation

Falls Sie keine Ahnung von all dem "Zeugs" da unten haben, können Sie mich gerne [kontaktieren](https://rafaelurben.github.io/diverses/rafaelurben/#kontakt). Bei Interesse helfe ich gerne (gegen einen kleinen Unkostenbetrag) bei der Aufsetzung des KMUHelpers.

Natürlich können Sie mich auch gerne bei irgendwelchen Fragen kontaktieren.

## Anforderungen

-   Ein Django-Projekt
    -   Django-Admin aktiviert
    -   Funktionierende Datenbank-Verbindung
    -   Funktionierende E-Mail Einstellungen
-   Alle Module aus requirements.txt sind installiert

## Anleitung

1.  Fügen Sie `kmuhelper` zu Ihren installierten Apps hinzu:

    ```python
    INSTALLED_APPS = [
        ...
        'kmuhelper',
        ...
        'django.contrib.messages',
        'django.contrib.admin',
    ]
    ```

2.  Fügen Sie den KMUHelper zu Ihrer URL-Konfiguration hinzu:

    ```python
    urlpatterns = [
        ...
        path('kmuhelper/', include('kmuhelper.urls')),
        ...
        path('admin/', admin.site.urls),
    ]
    ```

3.  Führen Sie `python manage.py migrate` aus, um die Datenbank einzurichten.

4.  Besuchen Sie den Admin-Bereich Ihrer Webseite.

## Zurück

[Zurück zur Startseite](./)
