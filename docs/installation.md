# Installation

## Anforderungen

-   Ein Django-Projekt
    -   Django-Admin aktiviert
    -   E-Mail Einstellungen funktionierend
-   Alle Module aus requirements.txt

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
