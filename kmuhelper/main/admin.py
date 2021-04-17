from datetime import datetime
from pytz import utc

from django.contrib import admin, messages
from django.urls import path

from kmuhelper.constants import (
    RECHNUNGSADRESSE_FIELDS_WITHOUT_CONTACT,
    RECHNUNGSADRESSE_FIELDS, RECHNUNGSADRESSE_FIELDS_CATEGORIZED,
    LIEFERADRESSE_FIELDS_WITHOUT_CONTACT,
    LIEFERADRESSE_FIELDS, LIEFERADRESSE_FIELDS_CATEGORIZED,
)
from kmuhelper.integrations.woocommerce import WooCommerce
from kmuhelper.main import views
from kmuhelper.main.models import (
    Ansprechpartner, Bestellung, Kategorie, Kosten, Kunde,
    Lieferant, Lieferung, Notiz, Produkt, Zahlungsempfaenger, Einstellung
)
from kmuhelper.overrides import CustomModelAdmin


#######


@admin.register(Ansprechpartner)
class AnsprechpartnerAdmin(CustomModelAdmin):
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

    # Permissions

    def has_change_permission(self, request, obj=None):
        return False if (obj and (obj.versendet and obj.bezahlt)) else super().has_change_permission(request, obj)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False if (obj and (obj.versendet or obj.bezahlt)) else super().has_delete_permission(request, obj)


class BestellungInlineBestellungspostenAdd(admin.TabularInline):
    model = Bestellung.produkte.through
    verbose_name = "Bestellungsposten"
    verbose_name_plural = "Bestellungsposten hinzufügen"
    extra = 0

    autocomplete_fields = ("produkt",)

    fieldsets = [
        (None, {'fields': ['produkt', 'bemerkung', 'menge', 'rabatt']})
    ]

    # Permissions

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False if (obj and (obj.versendet or obj.bezahlt)) else super().has_add_permission(request, obj)

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

    # Permissions

    def has_change_permission(self, request, obj=None):
        return False if (obj and obj.bezahlt) else super().has_change_permission(request, obj)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False if (obj and obj.bezahlt) else super().has_delete_permission(request, obj)


class BestellungInlineBestellungskostenAdd(admin.TabularInline):
    model = Bestellung.kosten.through
    verbose_name = "Bestellungskosten"
    verbose_name_plural = "Bestellungskosten hinzufügen"
    extra = 0

    autocomplete_fields = ("kosten",)

    fieldsets = [
        (None, {'fields': ['kosten', 'bemerkung', 'rabatt']})
    ]

    # Permissions

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False if (obj and obj.bezahlt) else super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return False


@admin.register(Bestellung)
class BestellungsAdmin(CustomModelAdmin):
    list_display = ('id', 'datum', 'kunde', 'status', 'zahlungsmethode',
                    'versendet', 'bezahlt', 'fix_summe', 'html_notiz')
    list_filter = ('status', 'bezahlt', 'versendet', 'zahlungsmethode')
    search_fields = ['id', 'datum', 'notiz__name', 'notiz__beschrieb', 'kundennotiz',
                     'trackingnummer'] + RECHNUNGSADRESSE_FIELDS + LIEFERADRESSE_FIELDS

    ordering = ("versendet", "bezahlt", "-datum")

    inlines = [BestellungInlineBestellungsposten, BestellungInlineBestellungspostenAdd,
               BestellungInlineBestellungskosten, BestellungInlineBestellungskostenAdd]

    autocomplete_fields = ("kunde", "zahlungsempfaenger", "ansprechpartner", )

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
                ('Notizen & Texte', {
                    'fields': ['kundennotiz', 'html_notiz'],
                    'classes': ["collapse start-open"]}),
                ('Rechnungsadresse', {
                    'fields': RECHNUNGSADRESSE_FIELDS if obj.bezahlt else RECHNUNGSADRESSE_FIELDS_CATEGORIZED,
                    'classes': ["collapse default-open"]}),
                ('Lieferadresse', {
                    'fields': LIEFERADRESSE_FIELDS if obj.versendet else LIEFERADRESSE_FIELDS_CATEGORIZED,
                    'classes': ["collapse start-open"]})
            ]

        return [
            ('Einstellungen', {'fields': [
                'zahlungsempfaenger', 'ansprechpartner']}),
            ('Rechnungsoptionen', {'fields': [
                'rechnungstitel', 'rechnungstext', 'rechnungsdatum', 'zahlungskonditionen']}),
            ('Lieferung', {
                'fields': ['trackingnummer'],
                'classes': ["collapse"]}),
            ('Bezahlung', {
                'fields': ['zahlungsmethode'],
                'classes': ["collapse start-open"]}),
            ('Kunde', {'fields': ['kunde']}),
            ('Notizen & Texte', {
                'fields': ['kundennotiz'],
                'classes': ["collapse start-open"]}),
        ]

    def get_readonly_fields(self, request, obj=None):
        fields = ['html_notiz', 'name', 'trackinglink',
                  'summe', 'summe_mwst', 'summe_gesamt']
        if obj:
            if obj.versendet:
                fields += ['versendet'] + LIEFERADRESSE_FIELDS_WITHOUT_CONTACT
            if obj.bezahlt:
                fields += ['bezahlt', 'zahlungsmethode', 'rechnungsdatum', 'rechnungstitel',
                           'rechnungstext', 'zahlungskonditionen'] + RECHNUNGSADRESSE_FIELDS_WITHOUT_CONTACT
            if obj.woocommerceid:
                fields += ["kundennotiz"]
        return fields

    # Actions

    @admin.action(description="Als bezahlt markieren", permissions=["change"])
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

    @admin.action(description="Bestellungen von WooCommerce aktualisieren", permissions=["change"])
    def wc_update(self, request, queryset):
        result = WooCommerce.order_bulk_update(queryset.all())
        messages.success(request, ((
            '{} Bestellungen' if result[0] != 1 else 'Eine Bestellung') + ' von WooCommerce aktualisiert!').format(result[0]))
        if result[1]:
            messages.error(request, ('Beim Import von ' + (
                '{} Bestellungen' if result[1] != 1 else 'einer Bestellung') + ' von WooCommerce ist ein Fehler aufgetreten!').format(result[1]))

    actions = [als_bezahlt_markieren, wc_update]

    # Save

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # stock warnings
        if obj:
            for product in obj.produkte.all():
                product.show_stock_warning(request)

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path('<path:object_id>/pdf', self.admin_site.admin_view(views.bestellung_pdf_ansehen),
                 name='%s_%s_pdf' % info),
            path('<path:object_id>/email/rechnung', self.admin_site.admin_view(views.bestellung_email_rechnung),
                 name='%s_%s_email_rechnung' % info),
            path('<path:object_id>/email/lieferung', self.admin_site.admin_view(views.bestellung_email_lieferung),
                 name='%s_%s_email_lieferung' % info),
            path('<path:object_id>/duplizieren', self.admin_site.admin_view(views.bestellung_duplizieren),
                 name='%s_%s_duplizieren' % info),
            path('<path:object_id>/zu-lieferung', self.admin_site.admin_view(views.bestellung_zu_lieferung),
                 name='%s_%s_zu_lieferung' % info),
        ]
        return my_urls + urls


class KategorienAdminProduktInline(admin.StackedInline):
    model = Produkt.kategorien.through
    verbose_name = "Produkt in dieser Kategorie"
    verbose_name_plural = "Produkte in dieser Kategorie"
    extra = 0

    autocomplete_fields = ("produkt", )

    # Permissions

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Kategorie)
class KategorienAdmin(CustomModelAdmin):
    fieldsets = [
        ('Infos', {'fields': ['name', 'beschrieb', 'bildlink']}),
        ('Übergeordnete Kategorie', {'fields': ['uebergeordnete_kategorie']})
    ]

    list_display = ('clean_name', 'clean_beschrieb',
                    'uebergeordnete_kategorie', 'bild', 'anzahl_produkte')
    search_fields = ['name', 'beschrieb']

    ordering = ("uebergeordnete_kategorie", "name")

    inlines = [KategorienAdminProduktInline]

    list_select_related = ("uebergeordnete_kategorie",)

    autocomplete_fields = ("uebergeordnete_kategorie", )

    # Actions

    @admin.action(description="Kategorien von WooCommerce aktualisieren", permissions=["change"])
    def wc_update(self, request, queryset):
        result = WooCommerce.category_bulk_update(queryset.all())
        messages.success(request, ((
            '{} Kategorien' if result[0] != 1 else 'Eine Kategorie') + ' von WooCommerce aktualisiert!').format(result[0]))
        if result[1]:
            messages.error(request, ('Beim Import von ' + (
                '{} Kategorien' if result[1] != 1 else 'einer Kategorie') + ' von WooCommerce ist ein Fehler aufgetreten!').format(result[1]))

    actions = ["wc_update"]


@admin.register(Kosten)
class KostenAdmin(CustomModelAdmin):
    list_display = ["clean_name", "preis", "mwstsatz"]

    search_fields = ('name', 'preis')

    ordering = ('preis', 'mwstsatz',)

    fieldsets = [
        (None, {"fields": ("name", "preis", "mwstsatz")})
    ]


class KundenAdminBestellungsInline(admin.TabularInline):
    model = Bestellung
    verbose_name = "Bestellung"
    verbose_name_plural = "Bestellungen"
    extra = 0

    show_change_link = True

    ordering = ('-datum', )

    fields = ('id', 'datum', 'fix_summe', 'versendet', 'bezahlt')

    # Permissions

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Kunde)
class KundenAdmin(CustomModelAdmin):
    def get_fieldsets(self, request, obj=None):
        default = [
            ('Infos', {'fields': [
                'vorname', 'nachname', 'firma', 'email', 'sprache']}),
            ('Rechnungsadresse', {
                'fields': RECHNUNGSADRESSE_FIELDS_CATEGORIZED}),
            ('Lieferadresse', {
                'fields': LIEFERADRESSE_FIELDS_CATEGORIZED,
                'classes': ["collapse start-open"]}),
        ]

        if obj:
            return default + [
                ('Diverses', {
                    'fields': [
                        'webseite', 'bemerkung', 'html_notiz'
                    ]}),
                ('Erweitert', {
                    'fields': [
                        'zusammenfuegen'
                    ], 'classes': ["collapse"]})
            ]

        return default + [
            ('Diverses', {'fields': ['webseite', 'bemerkung']})
        ]

    ordering = ('rechnungsadresse_plz', 'firma', 'nachname', 'vorname')

    list_display = ('id', 'firma', 'nachname', 'vorname', 'rechnungsadresse_plz',
                    'rechnungsadresse_ort', 'email', 'avatar', 'html_notiz')
    search_fields = ['id', 'nachname', 'vorname', 'firma', 'email', 'benutzername', 'webseite',
                     'notiz__name', 'notiz__beschrieb'] + RECHNUNGSADRESSE_FIELDS + LIEFERADRESSE_FIELDS

    readonly_fields = ["html_notiz"]

    list_select_related = ["notiz"]

    autocomplete_fields = ["zusammenfuegen"]

    inlines = [KundenAdminBestellungsInline]

    save_on_top = True

    # Actions

    @admin.action(description="Kunden von WooCommerce aktualisieren", permissions=["change"])
    def wc_update(self, request, queryset):
        result = WooCommerce.customer_bulk_update(queryset.all())
        messages.success(request, ((
            '{} Kunden' if result[0] != 1 else 'Ein Kunde') + ' von WooCommerce aktualisiert!').format(result[0]))
        if result[1]:
            messages.error(request, ('Beim Import von ' + (
                '{} Kunden' if result[1] != 1 else 'einem Kunden') + ' von WooCommerce ist ein Fehler aufgetreten!').format(result[1]))

    actions = ["wc_update"]

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path('<path:object_id>/email/registriert', self.admin_site.admin_view(views.kunde_email_registriert),
                 name='%s_%s_email_registriert' % info),
        ]
        return my_urls + urls


@admin.register(Lieferant)
class LieferantenAdmin(CustomModelAdmin):
    fieldsets = [
        ('Infos', {'fields': ['kuerzel', 'name']}),
        ('Firma', {'fields': ['webseite', 'telefon', 'email']}),
        ('Texte', {
            'fields': ['adresse', 'notiz'],
            'classes': ["collapse"]}),
        ('Ansprechpartner', {
            'fields': [
                'ansprechpartner', 'ansprechpartnertel', 'ansprechpartnermail'
            ], 'classes': ["collapse"]})
    ]

    ordering = ('kuerzel',)

    list_display = ('kuerzel', 'name', 'notiz')
    search_fields = ['kuerzel', 'name', 'adresse', 'notiz']

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path('<path:object_id>/zuordnen', self.admin_site.admin_view(views.lieferant_zuordnen),
                 name='%s_%s_zuordnen' % info),
        ]
        return my_urls + urls


class LieferungInlineProdukte(admin.TabularInline):
    model = Lieferung.produkte.through
    verbose_name = "Produkt"
    verbose_name_plural = "Produkte"
    extra = 0

    readonly_fields = ("produkt",)

    fields = ("produkt", "menge",)

    # Permissions

    def has_change_permission(self, request, obj=None):
        return False if obj and obj.eingelagert else super().has_change_permission(request, obj)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False if obj and obj.eingelagert else super().has_delete_permission(request, obj)


class LieferungInlineProdukteAdd(admin.TabularInline):
    model = Lieferung.produkte.through
    verbose_name = "Produkt"
    verbose_name_plural = "Produkte hinzufügen"
    extra = 0

    autocomplete_fields = ("produkt",)

    fields = ("produkt", "menge",)

    # Permissions

    def has_view_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False if obj and obj.eingelagert else super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Lieferung)
class LieferungenAdmin(CustomModelAdmin):
    list_display = ('name', 'datum', 'anzahlprodukte',
                    'lieferant', 'eingelagert', 'html_notiz')
    list_filter = ("eingelagert", "lieferant", )

    search_fields = ["name", "datum", "lieferant",
                     "notiz__name", "notiz__beschrieb"]

    readonly_fields = ["html_notiz"]

    autocomplete_fields = ("lieferant", )

    ordering = ('-datum',)

    fieldsets = [
        ('Infos', {'fields': ['name', 'html_notiz']}),
        ('Lieferant', {'fields': ['lieferant']})
    ]

    inlines = [LieferungInlineProdukte, LieferungInlineProdukteAdd]

    save_on_top = True

    # Actions

    @admin.action(description="Lieferungen einlagern", permissions=["change"])
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

    actions = ["einlagern"]

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path('<path:object_id>/einlagern', self.admin_site.admin_view(views.lieferung_einlagern),
                 name='%s_%s_einlagern' % info),
        ]
        return my_urls + urls


@admin.register(Notiz)
class NotizenAdmin(CustomModelAdmin):
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

        return [
            ("Infos", {"fields": ["name", "beschrieb"]}),
            ("Daten", {"fields": ["erledigt", "priority"]}),
        ]

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
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

    # Save

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


class ProduktInlineKategorienInline(admin.TabularInline):
    model = Produkt.kategorien.through
    extra = 0

    autocomplete_fields = ("kategorie", )

    # Permissions

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Produkt)
class ProduktAdmin(CustomModelAdmin):
    def get_fieldsets(self, request, obj=None):
        return [
            ('Infos', {'fields': ['artikelnummer', 'name']}),
            ('Beschrieb', {
                'fields': ['kurzbeschrieb', 'beschrieb'],
                'classes': ["collapse start-open"]}),
            ('Daten', {'fields': [
                'mengenbezeichnung', 'verkaufspreis', 'mwstsatz', 'lagerbestand', 'soll_lagerbestand']}),
            ('Lieferant', {
                'fields': [
                    'lieferant', 'lieferant_preis', 'lieferant_artikelnummer', 'lieferant_url'
                ], 'classes': ["collapse start-open"]}),
            ('Aktion', {
                'fields': [
                    'aktion_von', 'aktion_bis', 'aktion_preis'
                ], 'classes': ["collapse start-open"]}),
            ('Links', {
                'fields': [
                    'datenblattlink', 'bildlink'
                ], 'classes': ["collapse"]}),
            ('Bemerkung / Notiz', {
                'fields': [
                    'bemerkung', 'html_notiz'] if obj else ['bemerkung'],
                'classes': ["collapse start-open"]})
        ]

    ordering = ('artikelnummer', 'name')

    list_display = ('artikelnummer', 'clean_name', 'clean_kurzbeschrieb',
                    'clean_beschrieb', 'preis', 'in_aktion', 'lagerbestand', 'bild', 'html_notiz')
    list_display_links = ('artikelnummer', 'in_aktion',)
    list_filter = ('lieferant', 'kategorien', 'lagerbestand')
    search_fields = ['artikelnummer', 'name', 'kurzbeschrieb',
                     'beschrieb', 'bemerkung', 'notiz__name', 'notiz__beschrieb']

    readonly_fields = ["html_notiz"]

    autocomplete_fields = ("lieferant", )

    inlines = (ProduktInlineKategorienInline,)

    save_on_top = True

    list_select_related = ["notiz"]

    # Actions

    @admin.action(description="Produkte von WooCommerce aktualisieren", permissions=["change"])
    def wc_update(self, request, queryset):
        result = WooCommerce.product_bulk_update(queryset.all())
        messages.success(request, ((
            '{} Produkte' if result[0] != 1 else 'Ein Produkt') + ' von WooCommerce aktualisiert!').format(result[0]))
        if result[1]:
            messages.error(request, ('Beim Import von ' + (
                '{} Produkten' if result[1] != 1 else 'einem Produkt') + ' von WooCommerce ist ein Fehler aufgetreten!').format(result[1]))

    @admin.action(description="Lagerbestand zurücksetzen", permissions=["change"])
    def lagerbestand_zuruecksetzen(self, request, queryset):
        for produkt in queryset.all():
            produkt.lagerbestand = 0
            produkt.save()
        messages.success(request, (('Lagerbestand von {} Produkten' if queryset.count(
        ) != 1 else 'Lagerbestand von einem Produkt') + ' zurückgesetzt!').format(queryset.count()))

    @admin.action(description="Aktion beenden", permissions=["change"])
    def aktion_beenden(self, request, queryset):
        for produkt in queryset.all():
            produkt.aktion_bis = datetime.now(utc)
            produkt.save()
        messages.success(request, (('Aktion von {} Produkten' if queryset.count(
        ) != 1 else 'Aktion von einem Produkt') + ' beendet!').format(queryset.count()))

    actions = ["wc_update", "lagerbestand_zuruecksetzen", "aktion_beenden"]

    # Save

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj:
            obj.show_stock_warning(request)


@admin.register(Zahlungsempfaenger)
class ZahlungsempfaengerAdmin(CustomModelAdmin):
    fieldsets = [
        ("Infos", {"fields": [
            "qriban", "logourl", "firmenname", "firmenuid"]}),
        ("Adresse", {"fields": [
            "adresszeile1", "adresszeile2", "land"]}),
        ("Daten", {"fields": [
            "email", "telefon", "webseite"]})
    ]

    list_display = ('firmenname', 'firmenuid', 'qriban')
    list_filter = ('land',)
    search_fields = ['firmenname', 'adresszeile1',
                     'adresszeile2', 'qriban', 'firmenuid']

    save_on_top = True

    # Save

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj and not obj.has_valid_qr_iban():
            messages.error(request, "Ungültige QR-IBAN!")
        if obj and not obj.has_valid_uid():
            messages.warning(request, "Ungültige UID!")


# Einstellungen

@admin.register(Einstellung)
class EinstellungenAdmin(CustomModelAdmin):
    list_display = ('name', 'inhalt')
    ordering = ('name',)

    search_fields = ['name', 'char', 'text', 'inte', 'floa', 'url', 'email']

    readonly_fields = ["id", "name"]

    hidden = True

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            ('Name', {'fields': ['name']}),
            ('Inhalt', {'fields':
                        ['char'] if obj.typ == 'char' else
                        ['text'] if obj.typ == 'text' else
                        ['boo'] if obj.typ == 'bool' else
                        ['inte'] if obj.typ == 'int' else
                        ['floa'] if obj.typ == 'float' else
                        ['url'] if obj.typ == 'url' else
                        ['email'] if obj.typ == 'email' else
                        ['json'] if obj.typ == 'json' else []
                        }),
        ]
        return fieldsets

    # Permissions

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
