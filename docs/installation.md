---
permalink: /installation
fbcontact: true
---

# Installation

Falls Sie keine Ahnung von all dem "Zeugs" da unten haben, können Sie mich gerne [kontaktieren](<{{ site.kontakt_url }}>). Bei Interesse helfe ich gerne (gegen einen kleinen Unkostenbetrag) bei der Aufsetzung des KMUHelpers.

Natürlich können Sie mich auch gerne bei irgendwelchen Fragen kontaktieren.

## Anforderungen

-   Ein Django-Projekt
    -   Django-Admin aktiviert
    -   Funktionierende Datenbank-Verbindung
    -   Funktionierende E-Mail Einstellungen

## Anleitung

0.  Installieren Sie den KMUHelper:

    -   Stable (empfohlen): `pip install -U django-kmuhelper`
    -   Dev-Version: `pip install -i https://test.pypi.org/simple/ -U django-kmuhelper`

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

## Weiter

Die Installation ist nun soweit abgeschlossen. Sie können nun [zurück zur Startseite](./) oder [mit der Einleitung fortfahren](manual/).
