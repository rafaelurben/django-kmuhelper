from django.contrib import admin

# Disable "view on site" globally (for other apps too!)

admin.site.site_url = None

# Register your models here.

from kmuhelper.app.admin import (ToDoNotizenAdmin, ToDoVersandAdmin, ToDoZahlungseingangAdmin, ToDoLagerbestandAdmin, ToDoLieferungenAdmin)
from kmuhelper.main.admin import (AnsprechpartnerAdmin, BestellungsAdmin, KategorienAdmin, KostenAdmin, KundenAdmin, LieferantenAdmin, LieferungenAdmin, NotizenAdmin, ProduktAdmin, ZahlungsempfaengerAdmin, EinstellungenAdmin)
