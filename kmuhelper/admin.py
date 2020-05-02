from django.contrib import admin, messages
from datetime import datetime
from pytz import utc

from .models import Ansprechpartner, Produkt, Kategorie, Lieferant, Lieferung, Kunde, Einstellung, Bestellung, Kosten, Zahlungsempfaenger
from .apis import WooCommerce

# Titel-Änderungen

admin.site.site_header = "Administration"
admin.site.site_title = "Admin"
admin.site.index_title = "Haupt-Administration"

# Register your models here.

@admin.register(Ansprechpartner)
class AnsprechpartnerAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Name", {'fields': ['name']}),
        ('Daten', {'fields': ['telefon','email']})
    ]

    ordering = ('name',)

    list_display = ('name', 'telefon', 'email')
    search_fields = ['name', 'telefon', 'email']



class BestellungInlineBestellungsposten(admin.TabularInline):
    model = Bestellung.produkte.through
    verbose_name = "Bestellungsposten"
    verbose_name_plural = "Bestellungsposten"
    extra = 0

    def has_change_permission(self, request, obj=None):
        return False if (obj and (obj.versendet or obj.bezahlt)) else True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False if (obj and (obj.versendet or obj.bezahlt)) else True

    def get_readonly_fields(self, request, obj=None):
        return ["zwischensumme","mwstsatz","produkt","produktpreis"]

    def get_fieldsets(self, request, obj=None):
        return [(None, {'fields': ['produkt','bemerkung','produktpreis','menge','mwstsatz','zwischensumme']})]

class BestellungInlineBestellungspostenAdd(admin.TabularInline):
    model = Bestellung.produkte.through
    verbose_name = "Bestellungsposten"
    verbose_name_plural = "Bestellungsposten hinzufügen"
    extra = 0

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False if (obj and (obj.versendet or obj.bezahlt)) else True

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return ["zwischensumme","mwstsatz","produktpreis"]

    def get_fieldsets(self, request, obj=None):
        return [(None, {'fields': ['produkt','bemerkung','menge']})]

class BestellungInlineBestellungskosten(admin.TabularInline):
    model = Bestellung.kosten.through
    verbose_name = "Bestellungskosten"
    verbose_name_plural = "Bestellungskosten"
    extra = 0

    def has_change_permission(self, request, obj=None):
        return False if (obj and (obj.versendet or obj.bezahlt)) else True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False if (obj and (obj.versendet or obj.bezahlt)) else True

    def get_readonly_fields(self, request, obj=None):
        return ["zwischensumme","versteuerbar","kosten"]

    def get_fieldsets(self, request, obj=None):
        return [(None, {'fields': ['kosten','bemerkung','versteuerbar','zwischensumme']})]

class BestellungInlineBestellungskostenAdd(admin.TabularInline):
    model = Bestellung.kosten.through
    verbose_name = "Bestellungskosten"
    verbose_name_plural = "Bestellungskosten hinzufügen"
    extra = 0

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False if (obj and (obj.versendet or obj.bezahlt)) else True

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return ["zwischensumme"]

    def get_fieldsets(self, request, obj=None):
        return [(None, {'fields': ['kosten','bemerkung']})]

@admin.register(Bestellung)
class BestellungsAdmin(admin.ModelAdmin):
    list_display = ('id','datum','kunde','status','zahlungsmethode','bezahlt','versendet','summe_gesamt')
    list_filter = ('status','bezahlt','versendet','zahlungsmethode')
    search_fields = ['name','beschrieb','notiz','kundennotiz']

    ordering = ("versendet","bezahlt","-datum")

    inlines = [BestellungInlineBestellungsposten, BestellungInlineBestellungspostenAdd, BestellungInlineBestellungskosten, BestellungInlineBestellungskostenAdd]

    def get_fieldsets(self, request, obj=None):
        if obj:
            return [
                (None, {'fields': ['zahlungsempfaenger','ansprechpartner']}),
                ('Infos', {'fields': ['name','datum','status']}),
                ('Lieferung', {'fields': ['versendet','trackingnummer']}),
                ('Bezahlung', {'fields': ['bezahlt','zahlungsmethode','summe','summe_mwst','summe_gesamt']}),
                ('Notizen', {'fields': ['kundennotiz','notiz'], 'classes': ["collapse"]}),
                ('Kunde', {'fields': ['kunde']}),
                ('Rechnungsadresse', {'fields': ['rechnungsadresse_vorname','rechnungsadresse_nachname','rechnungsadresse_firma','rechnungsadresse_adresszeile1','rechnungsadresse_adresszeile2','rechnungsadresse_plz','rechnungsadresse_ort','rechnungsadresse_kanton','rechnungsadresse_land','rechnungsadresse_email','rechnungsadresse_telefon'], 'classes': ["collapse"]}),
                ('Lieferadresse', {'fields': ['lieferadresse_vorname','lieferadresse_nachname','lieferadresse_firma','lieferadresse_adresszeile1','lieferadresse_adresszeile2','lieferadresse_plz','lieferadresse_ort','lieferadresse_kanton','lieferadresse_land'], 'classes': ["collapse"]})
            ]
        else:
            return [
                (None, {'fields': ['zahlungsempfaenger','ansprechpartner']}),
                ('Lieferung', {'fields': ['trackingnummer']}),
                ('Bezahlung', {'fields': ['bezahlt','zahlungsmethode']}),
                ('Notizen', {'fields': ['kundennotiz','notiz'], 'classes': ["collapse"]}),
                ('Kunde', {'fields': ['kunde']})
            ]

    def get_readonly_fields(self, request, obj=None):
        rechnungsadresse = ['rechnungsadresse_vorname','rechnungsadresse_nachname','rechnungsadresse_firma','rechnungsadresse_adresszeile1','rechnungsadresse_adresszeile2','rechnungsadresse_plz','rechnungsadresse_ort','rechnungsadresse_kanton','rechnungsadresse_land','rechnungsadresse_email','rechnungsadresse_telefon']
        lieferadresse = ['lieferadresse_vorname','lieferadresse_nachname','lieferadresse_firma','lieferadresse_adresszeile1','lieferadresse_adresszeile2','lieferadresse_plz','lieferadresse_ort','lieferadresse_kanton','lieferadresse_land']
        fields = ['name','trackinglink','datum','summe','summe_mwst','summe_gesamt']
        if obj:
            if obj.versendet:
                fields += ['versendet','trackingnummer']+lieferadresse
            if obj.bezahlt:
                fields += ['bezahlt','zahlungsmethode']+rechnungsadresse
            if obj.woocommerceid:
                fields += ["kundennotiz"]
        else:
            fields += ["status"]
        return fields

    change_form_template = 'admin/kmuhelper/bestellung_change_form.html'
    change_list_template = 'admin/kmuhelper/bestellung_change_list.html'

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
        messages.success(request, (('{} Bestellungen' if successcount != 1 else 'Eine Bestellung')+' als bezahlt markiert!').format(successcount))
        if errorcount:
            messages.error(request, ('Beim als bezahlt markieren von '+('{} Bestellungen' if errorcount != 1 else 'einer Bestellung')+' ist ein Fehler aufgetreten!').format(errorcount))
    als_bezahlt_markieren.short_description = "Als bezahlt markieren"

    actions = [als_bezahlt_markieren]



class KategorienInlineUntergeordneteKategorien(admin.TabularInline):
    model = Produkt.kategorien.through
    verbose_name = "Produkt in dieser Kategorie"
    verbose_name_plural = "Produkte in dieser Kategorie"
    extra = 0

@admin.register(Kategorie)
class KategorienAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Infos', {'fields': ['name','beschrieb','bildlink']}),
        ('Übergeordnete Kategorie', {'fields': ['uebergeordnete_kategorie']})
    ]

    list_display = ('name','beschrieb','uebergeordnete_kategorie','bild')
    search_fields = ['name','beschrieb']

    ordering = ("name","uebergeordnete_kategorie")

    inlines = [KategorienInlineUntergeordneteKategorien]

    actions = ["wc_update"]

    def wc_update(self, request, queryset):
        result = WooCommerce.category_bulk_update(queryset.all())
        messages.success(request, (('{} Kategorien' if result[0] != 1 else 'Eine Kategorie')+' von WooCommerce aktualisiert!').format(result[0]))
        if result[1]:
            messages.error(request, ('Beim Import von '+('{} Kategorien' if result[1] != 1 else 'einer Kategorie')+' von WooCommerce ist ein Fehler aufgetreten!').format(result[1]))
    wc_update.short_description = "Kategorien von WooCommerce aktualisieren"

    change_form_template = 'admin/kmuhelper/kategorie_change_form.html'
    change_list_template = 'admin/kmuhelper/kategorie_change_list.html'



@admin.register(Kosten)
class KostenAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ("name", "preis", "versteuerbar")})
    ]

    readonly_fields = ("preis","versteuerbar")



@admin.register(Kunde)
class KundenAdmin(admin.ModelAdmin):
    def get_fieldsets(self, request, obj=None):
        return [
            ('Infos', {'fields': ['vorname','nachname','email','benutzername','sprache']}),
            ('Rechnungsadresse', {'fields': [('rechnungsadresse_vorname','rechnungsadresse_nachname'),'rechnungsadresse_firma',('rechnungsadresse_adresszeile1','rechnungsadresse_adresszeile2'),('rechnungsadresse_plz','rechnungsadresse_ort'),('rechnungsadresse_kanton','rechnungsadresse_land'),('rechnungsadresse_email','rechnungsadresse_telefon')]}),
            ('Lieferadresse', {'fields': [('lieferadresse_vorname','lieferadresse_nachname'),'lieferadresse_firma',('lieferadresse_adresszeile1','lieferadresse_adresszeile2'),('lieferadresse_plz','lieferadresse_ort'),('lieferadresse_kanton','lieferadresse_land')], 'classes': ["collapse"]})
        ] if not obj else [
            ('Infos', {'fields': ['vorname','nachname','email','benutzername','sprache']}),
            ('Rechnungsadresse', {'fields': [('rechnungsadresse_vorname','rechnungsadresse_nachname'),'rechnungsadresse_firma',('rechnungsadresse_adresszeile1','rechnungsadresse_adresszeile2'),('rechnungsadresse_plz','rechnungsadresse_ort'),('rechnungsadresse_kanton','rechnungsadresse_land'),('rechnungsadresse_email','rechnungsadresse_telefon')]}),
            ('Lieferadresse', {'fields': [('lieferadresse_vorname','lieferadresse_nachname'),'lieferadresse_firma',('lieferadresse_adresszeile1','lieferadresse_adresszeile2'),('lieferadresse_plz','lieferadresse_ort'),('lieferadresse_kanton','lieferadresse_land')], 'classes': ["collapse"]}),
            ('Erweitert', {'fields': [('zusammenfuegen')], 'classes': ["collapse"]})
        ]

    ordering = ('nachname','vorname')

    list_display = ('id','nachname','vorname','email','avatar')
    search_fields = ['nachname','vorname','email','benutzername','rechnungsadresse_vorname','rechnungsadresse_nachname','rechnungsadresse_firma','rechnungsadresse_adresszeile1','rechnungsadresse_adresszeile2','rechnungsadresse_ort','rechnungsadresse_kanton','rechnungsadresse_plz','rechnungsadresse_land','rechnungsadresse_email','rechnungsadresse_telefon','lieferadresse_vorname','lieferadresse_nachname','lieferadresse_firma','lieferadresse_adresszeile1','lieferadresse_adresszeile2','lieferadresse_ort','lieferadresse_kanton','lieferadresse_kanton','lieferadresse_plz','lieferadresse_land']

    actions = ["wc_update"]


    def wc_update(self, request, queryset):
        result = WooCommerce.customer_bulk_update(queryset.all())
        messages.success(request, (('{} Kunden' if result[0] != 1 else 'Ein Kunde')+' von WooCommerce aktualisiert!').format(result[0]))
        if result[1]:
            messages.error(request, ('Beim Import von '+('{} Kunden' if result[1] != 1 else 'einem Kunden')+' von WooCommerce ist ein Fehler aufgetreten!').format(result[1]))
    wc_update.short_description = "Kunden von WooCommerce aktualisieren"

    change_form_template = 'admin/kmuhelper/kunde_change_form.html'
    change_list_template = 'admin/kmuhelper/kunde_change_list.html'



@admin.register(Lieferant)
class LieferantenAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Infos', {'fields': ['kuerzel','name']}),
        ('Firma', {'fields': ['webseite','telefon','email']}),
        ('Texte', {'fields': ['adresse','notiz'], 'classes': ["collapse"]}),
        ('Ansprechpartner', {'fields': ['ansprechpartner','ansprechpartnertel','ansprechpartnermail'], 'classes': ["collapse"]})
    ]

    ordering = ('kuerzel',)

    list_display = ('kuerzel','name','notiz')
    search_fields = ['kuerzel','name','adresse','notiz']



class LieferungInlineProdukte(admin.TabularInline):
    model = Lieferung.produkte.through
    verbose_name = "Produkt"
    verbose_name_plural = "Produkte"
    extra = 0

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
    list_display = ('name','datum','notiz','anzahlprodukte','eingelagert')
    ordering = ('name',)

    fieldsets = [
        ('Infos', {'fields': ['name','notiz']}),
        ('Lieferant', {'fields': ['lieferant']})
    ]

    inlines = [LieferungInlineProdukte]

    actions = ["einlagern"]

    def einlagern(self, request, queryset):
        successcount = 0
        errorcount = 0
        for lieferung in queryset.all():
            if lieferung.einlagern():
                successcount += 1
            else:
                errorcount += 1
        messages.success(request, (('{} Lieferungen' if successcount != 1 else 'Eine Lieferung')+' wurde eingelagert!').format(successcount))
        if errorcount:
            messages.error(request, ('Beim Einlagern von '+('{} Lieferungen' if errorcount != 1 else 'einer Lieferung')+' ist ein Fehler aufgetreten!').format(errorcount))
    einlagern.short_description = "Lieferungen einlagern"

    change_form_template = 'admin/kmuhelper/lieferung_change_form.html'



class ProduktInlineProduktkategorien(admin.TabularInline):
    model = Produkt.kategorien.through
    extra = 0

@admin.register(Produkt)
class ProduktAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Infos', {'fields': ['artikelnummer','name']}),
        ('Beschrieb', {'fields': ['kurzbeschrieb','beschrieb'], 'classes': ["collapse"]}),
        ('Daten', {'fields': ['mengenbezeichnung','verkaufspreis','mwstsatz','lagerbestand']}),
        ('Lieferant', {'fields': ['lieferant','lieferant_preis','lieferant_artikelnummer']}),
        ('Aktion', {'fields': ['aktion_von','aktion_bis','aktion_preis'], 'classes': ["collapse"]}),
        ('Links', {'fields': ['datenblattlink','bildlink'], 'classes': ["collapse"]}),
        ('Bemerkungen', {'fields': ['bemerkung'], 'classes': ["collapse"]}) #packlistenbemerkung
    ]

    ordering = ('artikelnummer','name')

    list_display = ('artikelnummer','clean_name','clean_kurzbeschrieb','clean_beschrieb','preis','in_aktion','lagerbestand','bild')
    list_filter = ('lieferant','kategorien','lagerbestand')
    search_fields = ['artikelnummer','name','kurzbeschrieb','beschrieb']

    inlines = (ProduktInlineProduktkategorien,)

    actions = ["wc_update","lagerbestand_zuruecksetzen","aktion_beenden"]

    def wc_update(self, request, queryset):
        result = WooCommerce.product_bulk_update(queryset.all())
        messages.success(request, (('{} Produkte' if result[0] != 1 else 'Ein Produkt')+' von WooCommerce aktualisiert!').format(result[0]))
        if result[1]:
            messages.error(request, ('Beim Import von '+('{} Produkten' if result[1] != 1 else 'einem Produkt')+' von WooCommerce ist ein Fehler aufgetreten!').format(result[1]))
    wc_update.short_description = "Produkte von WooCommerce aktualisieren"

    def lagerbestand_zuruecksetzen(self, request, queryset):
        for produkt in queryset.all():
            produkt.lagerbestand = 0
            produkt.save()
        messages.success(request, (('Lagerbestand von {} Produkten' if queryset.count() != 1 else 'Lagerbestand von einem Produkt')+' zurückgesetzt!').format(queryset.count()))
    lagerbestand_zuruecksetzen.short_description = "Lagerbestand zurücksetzen"

    def aktion_beenden(self, request, queryset):
        for produkt in queryset.all():
            produkt.aktion_bis = datetime.now(utc)
            produkt.save()
        messages.success(request, (('Aktion von {} Produkten' if queryset.count() != 1 else 'Aktion von einem Produkt')+' beendet!').format(queryset.count()))
    aktion_beenden.short_description = "Aktion beenden"


    change_form_template = 'admin/kmuhelper/produkt_change_form.html'
    change_list_template = 'admin/kmuhelper/produkt_change_list.html'



@admin.register(Zahlungsempfaenger)
class ZahlungsempfaengerAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Infos", {"fields": ["qriban","logourl","firmenname","firmenuid"]}),
        ("Adresse", {"fields": ["adresszeile1","adresszeile2","land"]}),
        ("Daten", {"fields": ["email","telefon","webseite"]})
    ]

    list_display = ('firmenname','firmenuid','qriban')
    list_filter = ('land',)
    search_fields = ['firmenname','adresszeile1','adresszeile2','qriban','firmenuid']



###################

@admin.register(Einstellung)
class EinstellungenAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ('name','inhalt')
    ordering = ('name',)

    fieldsets = [
        ('Name', {'fields': ['name']}),
        ('Inhalt', {'fields': ['inhalt']}),
    ]

    def get_readonly_fields(self, request, obj=None):
        return ["id","name"]

    change_list_template = 'admin/kmuhelper/einstellung_change_list.html'

################
