=========
KMUHelper
=========

Der KMUHelper ist, wie der Name schon sagt, ein Helfer für KMU, hauptsächlich für Schweizer, da der Hauptgrund für
die Entwicklung dieser Djangoapp die neue schweizer QR-Rechnung ist.

Bei Fragen oder Probleme bitte unbedingt bei [mir](https://t.me/rafaelurben) melden!

Requirements
------------

Django Admin is installed and activated.

Quick start
-----------

1. Add "kmuhelper" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'kmuhelper',
    ]

2. Include the kmuhelper URLconf in your project urls.py like this::

    path('kmuhelper/', include('kmuhelper.urls')),

3. Run `python manage.py migrate` to create the models.

4. Visit http://127.0.0.1:8000/admin/kmuhelper
