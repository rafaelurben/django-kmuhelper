from django.contrib import admin, messages
from django.utils.html import format_html, mark_safe
from datetime import datetime
from pytz import utc

from kmuhelper.app.models import ToDoNotiz, ToDoVersand, ToDoZahlungseingang, ToDoLagerbestand, ToDoLieferung
from kmuhelper.main.models import Ansprechpartner, Bestellung, Kategorie, Kosten, Kunde, Lieferant, Lieferung, Notiz, Produkt, Zahlungsempfaenger, Einstellung

from kmuhelper.utils import package_version, python_version
from kmuhelper.integrations.woocommerce import WooCommerce

#######

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

    fieldsets = [
        (None, {'fields': ['produkt', 'bemerkung', 'produktpreis',
                           'menge', 'rabatt', 'mwstsatz', 'zwischensumme']})
    ]

    def get_readonly_fields(self, request, obj=None):
        fields = ["zwischensumme", "mwstsatz", "produkt", "produktpreis"]
        if obj and (obj.versendet or obj.bezahlt):
            fields += ["menge"]
        if obj and obj.bezahlt:
            fields += ["rabatt"]
        return fields

    def has_change_permission(self, request, obj=None):
        return False if (obj and (obj.versendet and obj.bezahlt)) else True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False if (obj and (obj.versendet or obj.bezahlt)) else True


class BestellungInlineBestellungspostenAdd(admin.TabularInline):
    model = Bestellung.produkte.through
    verbose_name = "Bestellungsposten"
    verbose_name_plural = "Bestellungsposten hinzufügen"
    extra = 0

    autocomplete_fields = ("produkt",)

    fieldsets = [
        (None, {'fields': ['produkt', 'bemerkung', 'menge', 'rabatt']})
    ]

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

    fieldsets = [
        (None, {'fields': ['kosten_name', 'bemerkung',
                           'kostenpreis', 'rabatt', 'mwstsatz', 'zwischensumme']})
    ]

    def get_readonly_fields(self, request, obj=None):
        fields = ["zwischensumme", "mwstsatz", "kostenpreis", "kosten_name"]
        return fields

    def has_change_permission(self, request, obj=None):
        return False if (obj and obj.bezahlt) else True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False if (obj and obj.bezahlt) else True


class BestellungInlineBestellungskostenAdd(admin.TabularInline):
    model = Bestellung.kosten.through
    verbose_name = "Bestellungskosten"
    verbose_name_plural = "Bestellungskosten hinzufügen"
    extra = 0

    autocomplete_fields = ("kosten",)

    fieldsets = [
        (None, {'fields': ['kosten', 'bemerkung', 'rabatt']})
    ]

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False if (obj and obj.bezahlt) else True

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

    autocomplete_fields = ("kunde",)

    save_on_top = True

    list_select_related = ["kunde", "notiz"]

    def get_fieldsets(self, request, obj=None):
        if obj:
            return [
                ('Einstellungen', {'fields': [
                 'zahlungsempfaenger', 'ansprechpartner']}),
                ('Infos', {'fields': ['name', 'datum', 'status']}),
                ('Rechnungsoptionen', {'fields': [
                 'rechnungstitel', 'rechnungstext', 'rechnungsdatum', 'zahlungskonditionen']}),
                ('Lieferung', {'fields': ['versendet', 'trackingnummer']}),
                ('Bezahlung', {'fields': [
                 'bezahlt', 'zahlungsmethode', 'summe', 'summe_mwst', 'summe_gesamt']}),
                ('Kunde', {'fields': ['kunde']}),
                ('Notizen & Texte', {'fields': ['kundennotiz', 'html_notiz'], 'classes': [
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
                ('Rechnungsoptionen', {'fields': [
                 'rechnungstitel', 'rechnungstext', 'rechnungsdatum', 'zahlungskonditionen']}),
                ('Lieferung', {'fields': ['trackingnummer'], 'classes': [
                 "collapse"]}),
                ('Bezahlung', {'fields': ['zahlungsmethode'], 'classes': [
                 "collapse start-open"]}),
                ('Kunde', {'fields': ['kunde']}),
                ('Notizen & Texte', {'fields': ['kundennotiz'],
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
                fields += ['bezahlt', 'zahlungsmethode', 'rechnungsdatum'] + rechnungsadresse
            if obj.woocommerceid:
                fields += ["kundennotiz"]
        return fields

    def als_bezahlt_markieren(self, request, queryset):
        successcount = 0
        errorcount = 0
        for bestellung in queryset.all():
            if bestellung.bezahlt:
                errorcount += 1
            else:
                bestellung.bezahlt = True
                if bestellung.versendet:
                    bestellung.status = "completed"
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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # stock warnings
        if obj:
            stock = obj.get_future_stock()
            for p_id in stock:
                s = stock[p_id]
                p = s["product"]

                p_name = p["name"]
                p_artikelnummer = p["artikelnummer"]
                p_adminurl = p["adminurl"]

                n_current = s["current"]
                n_going = s["going"]
                n_coming = s["coming"]
                n_min = s["min"]

                adminlink = mark_safe(f'<a href="{p_adminurl}">{p_name}</a>')
                stockdata = f"Aktuell: { n_current } | Ausgehend: { n_going }" + (
                        f" | Eingehend: { n_coming }" if n_coming else "")

                formatdata = (mark_safe(adminlink), p_artikelnummer, stockdata)

                if n_current-n_going < 0:
                    msg = format_html('Zu wenig Lagerbestand bei "{}" [{}]: {}', *formatdata)
                    messages.error(request, msg)
                elif n_current-n_going < n_min:
                    msg = format_html('Knapper Lagerbestand bei "{}" [{}]: {}', *formatdata)
                    messages.warning(request, msg)


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

    list_display = ('clean_name', 'clean_beschrieb',
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
    list_display = ["clean_name", "preis", "mwstsatz"]

    search_fields = ('name', 'preis')

    fieldsets = [
        (None, {"fields": ("name", "preis", "mwstsatz")})
    ]


@admin.register(Kunde)
class KundenAdmin(admin.ModelAdmin):
    def get_fieldsets(self, request, obj=None):
        if obj:
            return [
                ('Infos', {'fields': ['vorname', 'nachname',
                                      'firma', 'email', 'sprache']}),
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
                                      'firma', 'email', 'sprache']}),
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

    list_select_related = ["notiz"]

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

    readonly_fields = ("produkt",)

    fields = ("produkt", "menge",)

    def has_change_permission(self, request, obj=None):
        return not (obj and obj.eingelagert)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return not (obj and obj.eingelagert)


class LieferungInlineProdukteAdd(admin.TabularInline):
    model = Lieferung.produkte.through
    verbose_name = "Produkt"
    verbose_name_plural = "Produkte hinzufügen"
    extra = 0

    autocomplete_fields = ("produkt",)

    fields = ("produkt", "menge",)

    def has_view_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return not (obj and obj.eingelagert)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Lieferung)
class LieferungenAdmin(admin.ModelAdmin):
    list_display = ('name', 'datum', 'anzahlprodukte',
                    'lieferant', 'eingelagert', 'html_notiz')
    list_filter = ("eingelagert", "lieferant", )

    search_fields = ["name", "datum", "lieferant", "notiz__name", "notiz__beschrieb"]

    readonly_fields = ["html_notiz"]

    ordering = ('-datum',)

    fieldsets = [
        ('Infos', {'fields': ['name', 'html_notiz']}),
        ('Lieferant', {'fields': ['lieferant']})
    ]

    inlines = [LieferungInlineProdukte, LieferungInlineProdukteAdd]

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
            form.base_fields['beschrieb'].initial = ""
            if "from_bestellung" in request.GET:
                form.base_fields['name'].initial = 'Bestellung #' + \
                    request.GET.get("from_bestellung")
                form.base_fields['beschrieb'].initial += '\n\n[Bestellung #' + \
                    request.GET.get("from_bestellung") + "]"
            if "from_produkt" in request.GET:
                form.base_fields['name'].initial = 'Produkt #' + \
                    request.GET.get("from_produkt")
                form.base_fields['beschrieb'].initial += '\n\n[Produkt #' + \
                    request.GET.get("from_produkt") + "]"
            if "from_kunde" in request.GET:
                form.base_fields['name'].initial = 'Kunde #' + \
                    request.GET.get("from_kunde")
                form.base_fields['beschrieb'].initial += '\n\n[Kunde #' + \
                    request.GET.get("from_kunde") + "]"
            if "from_lieferung" in request.GET:
                form.base_fields['name'].initial = 'Lieferung #' + \
                    request.GET.get("from_lieferung")
                form.base_fields['beschrieb'].initial += '\n\n[Lieferung #' + \
                    request.GET.get("from_lieferung") + "]"
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
            if "from_lieferung" in request.GET:
                if Lieferung.objects.filter(pk=request.GET["from_lieferung"]).exists():
                    lieferung = Lieferung.objects.get(
                        pk=request.GET["from_lieferung"])
                    obj.lieferung = lieferung
                    obj.save()
                    messages.info(request, "Lieferung #" + str(lieferung.pk) +
                                  " wurde mit dieser Notiz verknüpft.")
                else:
                    messages.warning(
                        request, "Lieferung #" + request.GET["from_lieferung"] + " konnte nicht gefunden werden. Die Notiz wurde trotzdem erstellt.")


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
                 'mengenbezeichnung', 'verkaufspreis', 'mwstsatz', 'lagerbestand', 'soll_lagerbestand']}),
                ('Lieferant', {'fields': [
                 'lieferant', 'lieferant_preis', 'lieferant_artikelnummer', 'lieferant_url'], 'classes': [
                    "collapse start-open"]}),
                ('Aktion', {'fields': ['aktion_von', 'aktion_bis', 'aktion_preis'], 'classes': [
                 "collapse start-open"]}),
                ('Links', {'fields': ['datenblattlink', 'bildlink'], 'classes': [
                 "collapse"]}),
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
                 'mengenbezeichnung', 'verkaufspreis', 'mwstsatz', 'lagerbestand', 'soll_lagerbestand']}),
                ('Lieferant', {'fields': [
                 'lieferant', 'lieferant_preis', 'lieferant_artikelnummer', 'lieferant_url'], 'classes': [
                    "collapse start-open"]}),
                ('Aktion', {'fields': ['aktion_von', 'aktion_bis', 'aktion_preis'], 'classes': [
                 "collapse start-open"]}),
                ('Links', {'fields': ['datenblattlink', 'bildlink'], 'classes': [
                 "collapse"]}),
                # packlistenbemerkung
                ('Bemerkung', {'fields': ['bemerkung'], 'classes': [
                 "collapse start-open"]})
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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj:
            n_current = obj.lagerbestand
            n_going = obj.get_reserved_stock()
            n_coming = obj.get_incoming_stock()
            n_min = obj.soll_lagerbestand

            stockdata = f"Aktuell: { n_current } | Offene Bestellungen: { n_going }" + (
                f" | Kommende Lieferungen: { n_coming }" if n_coming else "")

            if n_current-n_going < 0:
                messages.error(request, f"Zu wenig Lagerbestand! "+stockdata)
            elif n_current-n_going < n_min:
                messages.warning(request, f"Knapper Lagerbestand! "+stockdata)


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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj and not obj.has_valid_qr_iban():
            messages.error(request, "Ungültige QR-IBAN!")
        if obj and not obj.has_valid_uid():
            messages.warning(request, "Ungültige UID!")


################### Einstellungen

@admin.register(Einstellung)
class EinstellungenAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ('name', 'get_inhalt')
    ordering = ('name',)

    search_fields = ['name', 'char', 'text', 'inte', 'floa', 'url', 'email']

    readonly_fields = ["id", "name"]

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            ('Name', {'fields': ['name']}),
            ('Inhalt', {'fields': [
                'char' if obj.typ == 'char' else
                'text' if obj.typ == 'text' else
                'boo' if obj.typ == 'bool' else
                'inte' if obj.typ == 'int' else
                'floa' if obj.typ == 'float' else
                'url' if obj.typ == 'url' else
                'email' if obj.typ == 'email' else ''
            ]}),
        ]
        return fieldsets


#

modeladmins = [
    (Ansprechpartner, AnsprechpartnerAdmin),
    (Bestellung, BestellungsAdmin),
    (Kategorie, KategorienAdmin),
    (Kosten, KostenAdmin),
    (Kunde, KundenAdmin),
    (Lieferant, LieferantenAdmin),
    (Lieferung, LieferungenAdmin),
    (Notiz, NotizenAdmin),
    (Produkt, ProduktAdmin),
    (Zahlungsempfaenger, ZahlungsempfaengerAdmin),
    (Einstellung, EinstellungenAdmin),
]
