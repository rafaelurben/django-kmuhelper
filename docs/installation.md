# Installation

Falls du keine Ahnung von all dem "Zeugs" da unten hast, kannst du mich gerne [kontaktieren](https://rafaelurben.github.io/diverses/rafaelurben/#kontakt). Bei Interesse helfe ich gerne (gegen einen kleinen Unkostenbetrag) bei der Aufsetzung des KMUHelpers.

Natürlich kannst du mich auch gerne bei irgendwelchen Fragen kontaktieren.

## Anforderungen

-   Ein Django-Projekt
    -   Django-Admin aktiviert
    -   Funktionierende Datenbank-Verbindung
    -   Funktionierende E-Mail Einstellungen
-   Alle Module aus requirements.txt sind installiert

## Anleitung

1.  Füge "kmuhelper" zu deinen installierten Apps hinzu:

    ```python
    INSTALLED_APPS = [
        ...
        'kmuhelper',
        ...
        'django.contrib.messages',
        'django.contrib.admin',
    ]
    ```

2.  Füge den KMUHelper zu deiner URL-Konfiguration hinzu:

    ```python
    urlpatterns = [
        ...
        path('kmuhelper/', include('kmuhelper.urls')),
        ...
        path('admin/', admin.site.urls),
    ]
    ```

3.  Führe `python manage.py migrate` aus, um die Datenbank einzurichten.

4.  Besuche den Admin-Bereich deiner Webseite.
