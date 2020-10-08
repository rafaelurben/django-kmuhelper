---
permalink: /installation
fbcontact: true
---

# Installation

Falls Sie keine Ahnung von all dem "Zeugs" da unten haben, können Sie mich gerne [kontaktieren](<{{ site.kontakt_url }}>). Bei Interesse helfe ich gerne (gegen einen kleinen Unkostenbetrag) bei der Aufsetzung des KMUHelper.

Natürlich können Sie mich auch gerne bei irgendwelchen Fragen kontaktieren.

## Anforderungen

- Ein Server, welcher Python und Django unterstützt (Ich empfehle dazu [Heroku](https://heroku.com))
- Eine Datenbank
- E-Mail Account für den KMUHelper
- Ein funktionierendes Django-Projekt ([Vorlage](https://github.com/rafaelurben/django-kmuhelper-template-heroku))

## Anleitung

*Diese Anleitung ist veraltet, bitte beachten Sie die [Vorlage](https://github.com/rafaelurben/django-kmuhelper-template-heroku)!*

0. Installieren Sie den KMUHelper:

    - Stable (empfohlen): `pip install -U django-kmuhelper`
    - Entwicklungs-Version: `pip install -i https://test.pypi.org/simple/ -U django-kmuhelper`

1. Fügen Sie `kmuhelper` zu Ihren installierten Apps hinzu:

    ```python
    INSTALLED_APPS = [
        ...
        'kmuhelper',
        ...
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.messages',
    ]
    ```

2. Fügen Sie den KMUHelper zu Ihrer URL-Konfiguration hinzu:

    ```python
    urlpatterns = [
        ...
        path('kmuhelper/', include('kmuhelper.urls')),
        ...
        path('admin/', admin.site.urls),
    ]
    ```

3. Führen Sie `python manage.py migrate` aus, um die Datenbank einzurichten.

4. Besuchen Sie `/kmuhelper/`.

## Weiter

Die Installation ist nun soweit abgeschlossen. Sie können nun [zurück zur Startseite](./README.md) oder [mit der Einleitung fortfahren](manual/README.md).
