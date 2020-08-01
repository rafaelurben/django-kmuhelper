from .models import ToDoNotiz, ToDoVersand, ToDoZahlungseingang, ToDoLagerbestand, ToDoLieferung
from django.contrib import admin, messages
from datetime import datetime
from pytz import utc

from .models import Ansprechpartner, Bestellung, Kategorie, Kosten, Kunde, Lieferant, Lieferung, Notiz, Produkt, Zahlungsempfaenger, Einstellung
from .apis import WooCommerce

# Disable "view on site" globally

admin.site.site_url = None

# Register your models here.


@admin.register(Ansprechpartner)
class AnsprechpartnerAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Name", {'fields': ['name']}),
        ('Daten', {'fields': ['telefon', 'email']})
    ]

    ordering = ('name',)

    list_display = ('name', 'telefon', 'email')
    search_fields = ['name', 'telefon', 'email']


class BestellungInlineBestellungsposten(admin.TabularInline):
    model = Bestellung.produkte.through
    verbose_name = "Bestellungsposten"
    verbose_name_plural = "Bestellungsposten"
    extra = 0

    readonly_fields = ["zwischensumme", "mwstsatz", "produkt", "produktpreis"]
    fieldsets = [(None, {'fields': ['produkt', 'bemerkung',
                                    'produktpreis', 'menge', 'mwstsatz', 'zwischensumme']})]

    def has_change_permission(self, request, obj=None):
        return False if (obj and (obj.versendet or obj.bezahlt)) else True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False if (obj and (obj.versendet or obj.bezahlt)) else True


class BestellungInlineBestellungspostenAdd(admin.TabularInline):
    model = Bestellung.produkte.through
    verbose_name = "Bestellungsposten"
    verbose_name_plural = "Bestellungsposten hinzufügen"
    extra = 0

    raw_id_fields = ("produkt",)

    fieldsets = [(None, {'fields': ['produkt', 'bemerkung', 'menge']})]

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False if (obj and (obj.versendet or obj.bezahlt)) else True

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return False


class BestellungInlineBestellungskosten(admin.TabularInline):
    model = Bestellung.kosten.through
    verbose_name = "Bestellungskosten"
    verbose_name_plural = "Bestellungskosten"
    extra = 0

    readonly_fields = ["zwischensumme", "mwstsatz", "kosten"]
    fieldsets = [
        (None, {'fields': ['kosten', 'bemerkung', 'mwstsatz', 'zwischensumme']})]

    def has_change_permission(self, request, obj=None):
        return False if (obj and (obj.versendet or obj.bezahlt)) else True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False if (obj and (obj.versendet or obj.bezahlt)) else True


class BestellungInlineBestellungskostenAdd(admin.TabularInline):
    model = Bestellung.kosten.through
    verbose_name = "Bestellungskosten"
    verbose_name_plural = "Bestellungskosten hinzufügen"
    extra = 0

    fieldsets = [(None, {'fields': ['kosten', 'bemerkung']})]

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False if (obj and (obj.versendet or obj.bezahlt)) else True

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return False


@admin.register(Bestellung)
class BestellungsAdmin(admin.ModelAdmin):
    list_display = ('id', 'datum', 'kunde', 'status', 'zahlungsmethode',
                    'versendet', 'bezahlt', 'fix_summe', 'html_notiz')
    list_filter = ('status', 'bezahlt', 'versendet', 'zahlungsmethode')
    search_fields = ['id', 'datum', 'notiz__name', 'notiz__beschrieb', 'kundennotiz', 'trackingnummer', 'rechnungsadresse_vorname',
                     'rechnungsadresse_nachname', 'rechnungsadresse_firma', 'rechnungsadresse_plz', 'rechnungsadresse_ort']

    ordering = ("versendet", "bezahlt", "-datum")

    inlines = [BestellungInlineBestellungsposten, BestellungInlineBestellungspostenAdd,
               BestellungInlineBestellungskosten, BestellungInlineBestellungskostenAdd]

    raw_id_fields = ("kunde",)

    save_on_top = True

    list_select_related = ["kunde"]

    def get_fieldsets(self, request, obj=None):
        if obj:
            return [
                ('Einstellungen', {'fields': [
                 'zahlungsempfaenger', 'ansprechpartner']}),
                ('Infos', {'fields': ['name', 'datum', 'status']}),
                ('Lieferung', {'fields': ['versendet', 'trackingnummer']}),
                ('Bezahlung', {'fields': [
                 'bezahlt', 'zahlungsmethode', 'summe', 'summe_mwst', 'summe_gesamt']}),
                ('Kunde', {'fields': ['kunde']}),
                ('Notizen', {'fields': ['kundennotiz', 'html_notiz'], 'classes': [
                 "collapse start-open"]}),
                ('Rechnungsadresse', {'fields': ['rechnungsadresse_vorname', 'rechnungsadresse_nachname', 'rechnungsadresse_firma', 'rechnungsadresse_adresszeile1', 'rechnungsadresse_adresszeile2',
                                                 'rechnungsadresse_plz', 'rechnungsadresse_ort', 'rechnungsadresse_kanton', 'rechnungsadresse_land', 'rechnungsadresse_email', 'rechnungsadresse_telefon'], 'classes': ["collapse default-open"]}),
                ('Lieferadresse', {'fields': ['lieferadresse_vorname', 'lieferadresse_nachname', 'lieferadresse_firma', 'lieferadresse_adresszeile1',
                                              'lieferadresse_adresszeile2', 'lieferadresse_plz', 'lieferadresse_ort', 'lieferadresse_kanton', 'lieferadresse_land'], 'classes': ["collapse start-open"]})
            ]
        else:
            return [
                ('Einstellungen', {'fields': [
                 'zahlungsempfaenger', 'ansprechpartner']}),
                ('Lieferung', {'fields': ['trackingnummer']}),
                ('Bezahlung', {'fields': ['bezahlt', 'zahlungsmethode']}),
                ('Kunde', {'fields': ['kunde']}),
                ('Notizen', {'fields': ['kundennotiz'],
                             'classes': ["collapse start-open"]}),
            ]

    def get_readonly_fields(self, request, obj=None):
        rechnungsadresse = ['rechnungsadresse_vorname', 'rechnungsadresse_nachname', 'rechnungsadresse_firma', 'rechnungsadresse_adresszeile1', 'rechnungsadresse_adresszeile2',
                            'rechnungsadresse_plz', 'rechnungsadresse_ort', 'rechnungsadresse_kanton', 'rechnungsadresse_land', 'rechnungsadresse_email', 'rechnungsadresse_telefon']
        lieferadresse = ['lieferadresse_vorname', 'lieferadresse_nachname', 'lieferadresse_firma', 'lieferadresse_adresszeile1',
                         'lieferadresse_adresszeile2', 'lieferadresse_plz', 'lieferadresse_ort', 'lieferadresse_kanton', 'lieferadresse_land']
        fields = ['html_notiz', 'name', 'trackinglink',
                  'summe', 'summe_mwst', 'summe_gesamt']
        if obj:
            if obj.versendet:
                fields += ['versendet', 'trackingnummer'] + lieferadresse
            if obj.bezahlt:
                fields += ['bezahlt', 'zahlungsmethode'] + rechnungsadresse
            if obj.woocommerceid:
                fields += ["kundennotiz"]
        else:
            fields += ["status"]
        return fields

    def als_bezahlt_markieren(self, request, queryset):
        successcount = 0
        errorcount = 0
        for bestellung in queryset.all():
            if bestellung.bezahlt:
                errorcount += 1
            else:
                bestellung.bezahlt = True
                bestellung.save()
                successcount += 1
        messages.success(request, (('{} Bestellungen' if successcount !=
                                    1 else 'Eine Bestellung') + ' als bezahlt markiert!').format(successcount))
        if errorcount:
            messages.error(request, ('Beim als bezahlt markieren von ' + ('{} Bestellungen' if errorcount !=
                                                                          1 else 'einer Bestellung') + ' ist ein Fehler aufgetreten!').format(errorcount))
    als_bezahlt_markieren.short_description = "Als bezahlt markieren"

    def wc_update(self, request, queryset):
        result = WooCommerce.order_bulk_update(queryset.all())
        messages.success(request, ((
            '{} Bestellungen' if result[0] != 1 else 'Eine Bestellung') + ' von WooCommerce aktualisiert!').format(result[0]))
        if result[1]:
            messages.error(request, ('Beim Import von ' + (
                '{} Bestellungen' if result[1] != 1 else 'einer Bestellung') + ' von WooCommerce ist ein Fehler aufgetreten!').format(result[1]))
    wc_update.short_description = "Bestellungen von WooCommerce aktualisieren"

    actions = [als_bezahlt_markieren, wc_update]


class KategorienInlineUntergeordneteKategorien(admin.TabularInline):
    model = Produkt.kategorien.through
    verbose_name = "Produkt in dieser Kategorie"
    verbose_name_plural = "Produkte in dieser Kategorie"
    extra = 0


@admin.register(Kategorie)
class KategorienAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Infos', {'fields': ['name', 'beschrieb', 'bildlink']}),
        ('Übergeordnete Kategorie', {'fields': ['uebergeordnete_kategorie']})
    ]

    list_display = ('name', 'beschrieb',
                    'uebergeordnete_kategorie', 'bild', 'anzahl_produkte')
    search_fields = ['name', 'beschrieb']

    ordering = ("uebergeordnete_kategorie", "name")

    inlines = [KategorienInlineUntergeordneteKategorien]

    list_select_related = ("uebergeordnete_kategorie",)

    def wc_update(self, request, queryset):
        result = WooCommerce.category_bulk_update(queryset.all())
        messages.success(request, ((
            '{} Kategorien' if result[0] != 1 else 'Eine Kategorie') + ' von WooCommerce aktualisiert!').format(result[0]))
        if result[1]:
            messages.error(request, ('Beim Import von ' + (
                '{} Kategorien' if result[1] != 1 else 'einer Kategorie') + ' von WooCommerce ist ein Fehler aufgetreten!').format(result[1]))
    wc_update.short_description = "Kategorien von WooCommerce aktualisieren"

    actions = ["wc_update"]


@admin.register(Kosten)
class KostenAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ("name", "preis", "mwstsatz")})
    ]

    def get_readonly_fields(self, request, obj=None):
        return ("preis", "versteuerbar") if obj else []


@admin.register(Kunde)
class KundenAdmin(admin.ModelAdmin):
    def get_fieldsets(self, request, obj=None):
        if obj:
            return [
                ('Infos', {'fields': ['vorname', 'nachname',
                                      'firma', 'email', 'benutzername', 'sprache']}),
                ('Rechnungsadresse', {'fields': [('rechnungsadresse_vorname', 'rechnungsadresse_nachname'), 'rechnungsadresse_firma', ('rechnungsadresse_adresszeile1', 'rechnungsadresse_adresszeile2'), (
                    'rechnungsadresse_plz', 'rechnungsadresse_ort'), ('rechnungsadresse_kanton', 'rechnungsadresse_land'), ('rechnungsadresse_email', 'rechnungsadresse_telefon')]}),
                ('Lieferadresse', {'fields': [('lieferadresse_vorname', 'lieferadresse_nachname'), 'lieferadresse_firma', ('lieferadresse_adresszeile1', 'lieferadresse_adresszeile2'), (
                    'lieferadresse_plz', 'lieferadresse_ort'), ('lieferadresse_kanton', 'lieferadresse_land')], 'classes': ["collapse start-open"]}),
                ('Diverses', {'fields': [
                 'webseite', 'bemerkung', 'html_notiz']}),
                ('Erweitert', {'fields': [
                 'zusammenfuegen'], 'classes': ["collapse"]})
            ]
        else:
            return [
                ('Infos', {'fields': ['vorname', 'nachname',
                                      'firma', 'email', 'benutzername', 'sprache']}),
                ('Rechnungsadresse', {'fields': [('rechnungsadresse_vorname', 'rechnungsadresse_nachname'), 'rechnungsadresse_firma', ('rechnungsadresse_adresszeile1', 'rechnungsadresse_adresszeile2'), (
                    'rechnungsadresse_plz', 'rechnungsadresse_ort'), ('rechnungsadresse_kanton', 'rechnungsadresse_land'), ('rechnungsadresse_email', 'rechnungsadresse_telefon')]}),
                ('Lieferadresse', {'fields': [('lieferadresse_vorname', 'lieferadresse_nachname'), 'lieferadresse_firma', ('lieferadresse_adresszeile1', 'lieferadresse_adresszeile2'), (
                    'lieferadresse_plz', 'lieferadresse_ort'), ('lieferadresse_kanton', 'lieferadresse_land')], 'classes': ["collapse start-open"]}),
                ('Diverses', {'fields': ['webseite', 'bemerkung']})
            ]

    ordering = ('rechnungsadresse_plz', 'firma', 'nachname', 'vorname')

    list_display = ('id', 'firma', 'nachname', 'vorname', 'rechnungsadresse_plz',
                    'rechnungsadresse_ort', 'email', 'avatar', 'html_notiz')
    search_fields = ['id', 'nachname', 'vorname', 'firma', 'email', 'benutzername', 'rechnungsadresse_vorname', 'rechnungsadresse_nachname', 'rechnungsadresse_firma', 'rechnungsadresse_adresszeile1', 'rechnungsadresse_adresszeile2', 'rechnungsadresse_ort', 'rechnungsadresse_kanton', 'rechnungsadresse_plz', 'rechnungsadresse_land',
                     'rechnungsadresse_email', 'rechnungsadresse_telefon', 'lieferadresse_vorname', 'lieferadresse_nachname', 'lieferadresse_firma', 'lieferadresse_adresszeile1', 'lieferadresse_adresszeile2', 'lieferadresse_ort', 'lieferadresse_kanton', 'lieferadresse_kanton', 'lieferadresse_plz', 'lieferadresse_land', 'webseite', 'notiz__name', 'notiz__beschrieb']

    readonly_fields = ["html_notiz"]

    actions = ["wc_update"]

    save_on_top = True

    def wc_update(self, request, queryset):
        result = WooCommerce.customer_bulk_update(queryset.all())
        messages.success(request, ((
            '{} Kunden' if result[0] != 1 else 'Ein Kunde') + ' von WooCommerce aktualisiert!').format(result[0]))
        if result[1]:
            messages.error(request, ('Beim Import von ' + (
                '{} Kunden' if result[1] != 1 else 'einem Kunden') + ' von WooCommerce ist ein Fehler aufgetreten!').format(result[1]))
    wc_update.short_description = "Kunden von WooCommerce aktualisieren"


@admin.register(Lieferant)
class LieferantenAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Infos', {'fields': ['kuerzel', 'name']}),
        ('Firma', {'fields': ['webseite', 'telefon', 'email']}),
        ('Texte', {'fields': ['adresse', 'notiz'], 'classes': ["collapse"]}),
        ('Ansprechpartner', {'fields': [
         'ansprechpartner', 'ansprechpartnertel', 'ansprechpartnermail'], 'classes': ["collapse"]})
    ]

    ordering = ('kuerzel',)

    list_display = ('kuerzel', 'name', 'notiz')
    search_fields = ['kuerzel', 'name', 'adresse', 'notiz']


class LieferungInlineProdukte(admin.TabularInline):
    model = Lieferung.produkte.through
    verbose_name = "Produkt"
    verbose_name_plural = "Produkte"
    extra = 0

    raw_id_fields = ("produkt",)

    def has_change_permission(self, request, obj=None):
        if obj and obj.eingelagert:
            return False
        else:
            return True

    def has_add_permission(self, request, obj=None):
        if obj and obj.eingelagert:
            return False
        else:
            return True

    def has_delete_permission(self, request, obj=None):
        if obj and obj.eingelagert:
            return False
        else:
            return True


@admin.register(Lieferung)
class LieferungenAdmin(admin.ModelAdmin):
    list_display = ('name', 'datum', 'notiz', 'anzahlprodukte', 'eingelagert')
    list_filter = ("eingelagert",)

    search_fields = ["name", "datum", "notiz"]

    ordering = ('name',)

    fieldsets = [
        ('Infos', {'fields': ['name', 'notiz']}),
        ('Lieferant', {'fields': ['lieferant']})
    ]

    inlines = [LieferungInlineProdukte]

    save_on_top = True

    actions = ["einlagern"]

    def einlagern(self, request, queryset):
        successcount = 0
        errorcount = 0
        for lieferung in queryset.all():
            if lieferung.einlagern():
                successcount += 1
            else:
                errorcount += 1
        messages.success(request, (('{} Lieferungen' if successcount !=
                                    1 else 'Eine Lieferung') + ' wurde eingelagert!').format(successcount))
        if errorcount:
            messages.error(request, ('Beim Einlagern von ' + ('{} Lieferungen' if errorcount !=
                                                              1 else 'einer Lieferung') + ' ist ein Fehler aufgetreten!').format(errorcount))
    einlagern.short_description = "Lieferungen einlagern"


@admin.register(Notiz)
class NotizenAdmin(admin.ModelAdmin):
    list_display = ["name", "beschrieb", "priority", "erledigt", "erstellt_am"]
    list_filter = ["erledigt", "priority"]

    readonly_fields = ["links"]

    ordering = ["erledigt", "-priority", "erstellt_am"]

    search_fields = ("name", "beschrieb")

    def get_fieldsets(self, request, obj=None):
        if obj:
            return [
                ("Infos", {"fields": ["name", "beschrieb"]}),
                ("Daten", {"fields": ["erledigt", "priority"]}),
                ("Verknüpfungen", {"fields": ["links"]}),
            ]
        else:
            return [
                ("Infos", {"fields": ["name", "beschrieb"]}),
                ("Daten", {"fields": ["erledigt", "priority"]}),
            ]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:
            if "from_bestellung" in request.GET:
                form.base_fields['name'].initial = 'Bestellung #' + \
                    request.GET.get("from_bestellung")
                form.base_fields['beschrieb'].initial = '\n\nDiese Notiz gehört zu Bestellung #' + \
                    request.GET.get("from_bestellung")
            if "from_produkt" in request.GET:
                form.base_fields['name'].initial = 'Produkt #' + \
                    request.GET.get("from_produkt")
                form.base_fields['beschrieb'].initial = '\n\nDiese Notiz gehört zu Produkt ' + \
                    request.GET.get("from_produkt")
            if "from_kunde" in request.GET:
                form.base_fields['name'].initial = 'Kunde #' + \
                    request.GET.get("from_kunde")
                form.base_fields['beschrieb'].initial = '\n\nDiese Notiz gehört zu Kunde ' + \
                    request.GET.get("from_kunde")
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            if "from_bestellung" in request.GET:
                if Bestellung.objects.filter(pk=request.GET["from_bestellung"]).exists():
                    bestellung = Bestellung.objects.get(
                        pk=request.GET["from_bestellung"])
                    obj.bestellung = bestellung
                    obj.save()
                    messages.info(
                        request, "Bestellung #" + str(bestellung.pk) + " wurde mit dieser Notiz verknüpft.")
                else:
                    messages.warning(
                        request, "Bestellung #" + request.GET["from_bestellung"] + " konnte nicht gefunden werden. Die Notiz wurde trotzdem erstellt.")
            if "from_produkt" in request.GET:
                if Produkt.objects.filter(pk=request.GET["from_produkt"]).exists():
                    produkt = Produkt.objects.get(
                        pk=request.GET["from_produkt"])
                    obj.produkt = produkt
                    obj.save()
                    messages.info(
                        request, "Produkt #" + str(produkt.pk) + " wurde mit dieser Notiz verknüpft.")
                else:
                    messages.warning(
                        request, "Produkt #" + request.GET["from_produkt"] + " konnte nicht gefunden werden. Die Notiz wurde trotzdem erstellt.")
            if "from_kunde" in request.GET:
                if Kunde.objects.filter(pk=request.GET["from_kunde"]).exists():
                    kunde = Kunde.objects.get(pk=request.GET["from_kunde"])
                    obj.kunde = kunde
                    obj.save()
                    messages.info(request, "Kunde #" + str(kunde.pk) +
                                  " wurde mit dieser Notiz verknüpft.")
                else:
                    messages.warning(
                        request, "Kunde #" + request.GET["from_kunde"] + " konnte nicht gefunden werden. Die Notiz wurde trotzdem erstellt.")


class ProduktInlineProduktkategorien(admin.TabularInline):
    model = Produkt.kategorien.through
    extra = 0


@admin.register(Produkt)
class ProduktAdmin(admin.ModelAdmin):
    def get_fieldsets(self, request, obj=None):
        if obj:
            return [
                ('Infos', {'fields': ['artikelnummer', 'name']}),
                ('Beschrieb', {'fields': [
                 'kurzbeschrieb', 'beschrieb'], 'classes': ["collapse start-open"]}),
                ('Daten', {'fields': [
                 'mengenbezeichnung', 'verkaufspreis', 'mwstsatz', 'lagerbestand']}),
                ('Lieferant', {'fields': [
                 'lieferant', 'lieferant_preis', 'lieferant_artikelnummer']}),
                ('Aktion', {'fields': ['aktion_von', 'aktion_bis', 'aktion_preis'], 'classes': [
                 "collapse start-open"]}),
                ('Links', {'fields': ['datenblattlink', 'bildlink'], 'classes': [
                 "collapse start-open"]}),
                # packlistenbemerkung
                ('Bemerkung / Notiz',
                 {'fields': ['bemerkung', 'html_notiz'], 'classes': ["collapse start-open"]})
            ]
        else:
            return [
                ('Infos', {'fields': ['artikelnummer', 'name']}),
                ('Beschrieb', {'fields': [
                 'kurzbeschrieb', 'beschrieb'], 'classes': ["collapse start-open"]}),
                ('Daten', {'fields': [
                 'mengenbezeichnung', 'verkaufspreis', 'mwstsatz', 'lagerbestand']}),
                ('Lieferant', {'fields': [
                 'lieferant', 'lieferant_preis', 'lieferant_artikelnummer']}),
                ('Aktion', {'fields': ['aktion_von', 'aktion_bis', 'aktion_preis'], 'classes': [
                 "collapse start-open"]}),
                ('Links', {'fields': ['datenblattlink', 'bildlink'], 'classes': [
                 "collapse start-open"]}),
                ('Bemerkung', {'fields': ['bemerkung'], 'classes': [
                 "collapse start-open"]})  # packlistenbemerkung
            ]

    ordering = ('artikelnummer', 'name')

    list_display = ('artikelnummer', 'clean_name', 'clean_kurzbeschrieb',
                    'clean_beschrieb', 'preis', 'in_aktion', 'lagerbestand', 'bild', 'html_notiz')
    list_filter = ('lieferant', 'kategorien', 'lagerbestand')
    search_fields = ['artikelnummer', 'name', 'kurzbeschrieb',
                     'beschrieb', 'bemerkung', 'notiz__name', 'notiz__beschrieb']

    readonly_fields = ["html_notiz"]

    inlines = (ProduktInlineProduktkategorien,)

    save_on_top = True

    actions = ["wc_update", "lagerbestand_zuruecksetzen", "aktion_beenden"]

    list_select_related = ["notiz"]

    def wc_update(self, request, queryset):
        result = WooCommerce.product_bulk_update(queryset.all())
        messages.success(request, ((
            '{} Produkte' if result[0] != 1 else 'Ein Produkt') + ' von WooCommerce aktualisiert!').format(result[0]))
        if result[1]:
            messages.error(request, ('Beim Import von ' + (
                '{} Produkten' if result[1] != 1 else 'einem Produkt') + ' von WooCommerce ist ein Fehler aufgetreten!').format(result[1]))
    wc_update.short_description = "Produkte von WooCommerce aktualisieren"

    def lagerbestand_zuruecksetzen(self, request, queryset):
        for produkt in queryset.all():
            produkt.lagerbestand = 0
            produkt.save()
        messages.success(request, (('Lagerbestand von {} Produkten' if queryset.count(
        ) != 1 else 'Lagerbestand von einem Produkt') + ' zurückgesetzt!').format(queryset.count()))
    lagerbestand_zuruecksetzen.short_description = "Lagerbestand zurücksetzen"

    def aktion_beenden(self, request, queryset):
        for produkt in queryset.all():
            produkt.aktion_bis = datetime.now(utc)
            produkt.save()
        messages.success(request, (('Aktion von {} Produkten' if queryset.count(
        ) != 1 else 'Aktion von einem Produkt') + ' beendet!').format(queryset.count()))
    aktion_beenden.short_description = "Aktion beenden"


@admin.register(Zahlungsempfaenger)
class ZahlungsempfaengerAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Infos", {"fields": [
         "qriban", "logourl", "firmenname", "firmenuid"]}),
        ("Adresse", {"fields": ["adresszeile1", "adresszeile2", "land"]}),
        ("Daten", {"fields": ["email", "telefon", "webseite"]})
    ]

    list_display = ('firmenname', 'firmenuid', 'qriban')
    list_filter = ('land',)
    search_fields = ['firmenname', 'adresszeile1',
                     'adresszeile2', 'qriban', 'firmenuid']

    save_on_top = True


###################

@admin.register(Einstellung)
class EinstellungenAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ('name', 'get_inhalt')
    ordering = ('name',)

    search_fields = ["name"]

    readonly_fields = ["id", "name"]

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            ('Name', {'fields': ['name']}),
            ('Inhalt', {'fields': ['char']}),
        ]
        if obj.typ == "char":
            fieldsets[1][1]["fields"][0] = "char"
        elif obj.typ == "text":
            fieldsets[1][1]["fields"][0] = "text"
        elif obj.typ == "int":
            fieldsets[1][1]["fields"][0] = "inte"
        elif obj.typ == "floa":
            fieldsets[1][1]["fields"][0] = "floa"
        elif obj.typ == "url":
            fieldsets[1][1]["fields"][0] = "url"

        return fieldsets

# TO DO


@admin.register(ToDoNotiz)
class ToDoNotizenAdmin(NotizenAdmin):
    list_editable = ["priority", "erledigt"]
    list_filter = ["priority"]

    ordering = ["-priority", "erstellt_am"]

    def has_module_permission(self, request):
        return {}

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        from django.urls import path
        from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe
        from functools import update_wrapper

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(allow_iframe(view))(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        return [
            path('', wrap(self.changelist_view),
                 name='%s_%s_changelist' % info),
            path('add/', wrap(self.add_view), name='%s_%s_add' % info),
            path('autocomplete/', wrap(self.autocomplete_view),
                 name='%s_%s_autocomplete' % info),
            path('<path:object_id>/history/', wrap(self.history_view),
                 name='%s_%s_history' % info),
            # path('<path:object_id>/delete/', wrap(self.delete_view), name='%s_%s_delete' % info),
            path('<path:object_id>/change/', wrap(self.change_view),
                 name='%s_%s_change' % info),
        ]


@admin.register(ToDoVersand)
class ToDoVersandAdmin(BestellungsAdmin):
    list_display = ('id', 'info', 'trackingnummer',
                    'versendet', 'status', 'html_todo_notiz')
    list_editable = ("trackingnummer", "versendet", "status")
    list_filter = ('status', 'bezahlt')

    ordering = ("bezahlt", "-datum")

    actions = ()

    def has_module_permission(self, request):
        return {}

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        from django.urls import path
        from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe
        from functools import update_wrapper

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(allow_iframe(view))(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        return [
            path('', wrap(self.changelist_view),
                 name='%s_%s_changelist' % info),
            path('add/', wrap(self.add_view), name='%s_%s_add' % info),
            path('autocomplete/', wrap(self.autocomplete_view),
                 name='%s_%s_autocomplete' % info),
            path('<path:object_id>/history/', wrap(self.history_view),
                 name='%s_%s_history' % info),
            # path('<path:object_id>/delete/', wrap(self.delete_view), name='%s_%s_delete' % info),
            path('<path:object_id>/change/', wrap(self.change_view),
                 name='%s_%s_change' % info),
        ]


@admin.register(ToDoZahlungseingang)
class ToDoZahlungseingangAdmin(BestellungsAdmin):
    list_display = ('id', 'info', 'bezahlt', 'status',
                    'fix_summe', 'html_todo_notiz')
    list_editable = ("bezahlt", "status")
    list_filter = ('status', 'versendet', 'zahlungsmethode')

    ordering = ("versendet", "-datum")

    actions = ()

    def has_module_permission(self, request):
        return {}

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        from django.urls import path
        from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe
        from functools import update_wrapper

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(allow_iframe(view))(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        return [
            path('', wrap(self.changelist_view),
                 name='%s_%s_changelist' % info),
            path('add/', wrap(self.add_view), name='%s_%s_add' % info),
            path('autocomplete/', wrap(self.autocomplete_view),
                 name='%s_%s_autocomplete' % info),
            path('<path:object_id>/history/', wrap(self.history_view),
                 name='%s_%s_history' % info),
            # path('<path:object_id>/delete/', wrap(self.delete_view), name='%s_%s_delete' % info),
            path('<path:object_id>/change/', wrap(self.change_view),
                 name='%s_%s_change' % info),
        ]


@admin.register(ToDoLagerbestand)
class ToDoLagerbestandAdmin(ProduktAdmin):
    list_display = ('nr', 'clean_name', 'lagerbestand',
                    'preis', 'bemerkung', 'html_todo_notiz')
    list_editable = ["lagerbestand"]

    actions = ["lagerbestand_zuruecksetzen"]

    def has_module_permission(self, request):
        return {}

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        from django.urls import path
        from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe
        from functools import update_wrapper

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(allow_iframe(view))(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        return [
            path('', wrap(self.changelist_view),
                 name='%s_%s_changelist' % info),
            path('add/', wrap(self.add_view), name='%s_%s_add' % info),
            path('autocomplete/', wrap(self.autocomplete_view),
                 name='%s_%s_autocomplete' % info),
            path('<path:object_id>/history/', wrap(self.history_view),
                 name='%s_%s_history' % info),
            # path('<path:object_id>/delete/', wrap(self.delete_view), name='%s_%s_delete' % info),
            path('<path:object_id>/change/', wrap(self.change_view),
                 name='%s_%s_change' % info),
        ]


@admin.register(ToDoLieferung)
class ToDoLieferungenAdmin(LieferungenAdmin):
    list_display = ('name', 'anzahlprodukte', 'eingelagert',
                    'notiz', 'html_todo_notiz_erstellen')
    list_editable = ("eingelagert",)
    list_filter = ()

    def has_module_permission(self, request):
        return {}

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        from django.urls import path
        from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe
        from functools import update_wrapper

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(allow_iframe(view))(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        return [
            path('', wrap(self.changelist_view),
                 name='%s_%s_changelist' % info),
            path('add/', wrap(self.add_view), name='%s_%s_add' % info),
            path('autocomplete/', wrap(self.autocomplete_view),
                 name='%s_%s_autocomplete' % info),
            path('<path:object_id>/history/', wrap(self.history_view),
                 name='%s_%s_history' % info),
            # path('<path:object_id>/delete/', wrap(self.delete_view), name='%s_%s_delete' % info),
            path('<path:object_id>/change/', wrap(self.change_view),
                 name='%s_%s_change' % info),
        ]
