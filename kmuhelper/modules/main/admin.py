from datetime import datetime

from django.contrib import admin, messages
from django.db.models import Count
from django.urls import path
from django.utils import timezone
from django.utils.translation import gettext_lazy, gettext, ngettext

from kmuhelper import constants
from kmuhelper.modules.integrations.woocommerce import WooCommerce
from kmuhelper.modules.main import views
from kmuhelper.modules.main.models import (
    Ansprechpartner, Bestellung, Produktkategorie, Kosten, Kunde,
    Lieferant, Lieferung, Notiz, Produkt, Zahlungsempfaenger
)
from kmuhelper.overrides import CustomModelAdmin, CustomTabularInline, CustomStackedInline

_ = gettext_lazy

#######


@admin.register(Ansprechpartner)
class AnsprechpartnerAdmin(CustomModelAdmin):
    fieldsets = [
        ("Name", {'fields': ['name']}),
        ('Daten', {'fields': ['phone', 'email']})
    ]

    ordering = ('name',)

    list_display = ('name', 'phone', 'email')
    search_fields = ['name', 'phone', 'email']


class BestellungInlineBestellungsposten(CustomTabularInline):
    model = Bestellung.products.through
    verbose_name = _("Bestellungsposten")
    verbose_name_plural = _("Bestellungsposten")
    extra = 0

    fields = ('produkt', 'note', 'product_price', 'quantity', 'discount', 'display_subtotal', 'display_vat_rate',)

    readonly_fields = ('display_subtotal', 'display_vat_rate', 'produkt',)

    def get_additional_readonly_fields(self, request, obj=None):
        fields = ["product_price"]
        if obj and (obj.is_shipped or obj.is_paid):
            fields += ["quantity"]
        if obj and obj.is_paid:
            fields += ["discount"]
        return fields

    # Permissions

    NO_ADD = True

    def has_delete_permission(self, request, obj=None):
        return False if (obj and (obj.is_shipped or obj.is_paid)) else super().has_delete_permission(request, obj)

    # Custom queryset
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('produkt')

class BestellungInlineBestellungspostenAdd(CustomTabularInline):
    model = Bestellung.products.through
    verbose_name = _("Bestellungsposten")
    verbose_name_plural = _("Bestellungsposten hinzufügen")
    extra = 0

    autocomplete_fields = ("produkt",)

    fieldsets = [
        (None, {'fields': ['produkt', 'note', 'quantity', 'discount']})
    ]

    # Permissions

    NO_CHANGE = True
    NO_DELETE = True
    NO_VIEW = True

    def has_add_permission(self, request, obj=None):
        return False if (obj and (obj.is_shipped or obj.is_paid)) else super().has_add_permission(request, obj)


class BestellungInlineBestellungskosten(CustomTabularInline):
    model = Bestellung.kosten.through
    verbose_name = _("Bestellungskosten")
    verbose_name_plural = _("Bestellungskosten")
    extra = 0

    fields = ('kosten', 'name', 'price', 'discount', 'note', 'display_subtotal', 'vat_rate')

    readonly_fields = ('kosten', 'display_subtotal',)

    def get_additional_readonly_fields(self, request, obj=None):
        if obj and obj.is_paid:
            return ['price', 'vat_rate', 'discount']
        return []

    # Permissions

    def has_add_permission(self, request, obj=None):
        return False if (obj and obj.is_paid) else super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False if (obj and obj.is_paid) else super().has_delete_permission(request, obj)

    # Custom queryset
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('kosten')


class BestellungInlineBestellungskostenImport(CustomTabularInline):
    model = Bestellung.kosten.through
    verbose_name = _("Bestellungskosten")
    verbose_name_plural = _("Bestellungskosten importieren")
    extra = 0

    autocomplete_fields = ("kosten",)

    fields = ('kosten', 'note', 'discount',)

    # Permissions

    NO_CHANGE = True
    NO_DELETE = True
    NO_VIEW = True

    def has_add_permission(self, request, obj=None):
        return False if (obj and obj.is_paid) else super().has_add_permission(request, obj)


@admin.register(Bestellung)
class BestellungsAdmin(CustomModelAdmin):
    list_display = ('id', 'date', 'customer', 'status', 'payment_method',
                    'is_shipped', 'is_paid', 'display_cached_sum', 'linked_note_html')
    list_filter = ('status', 'is_paid', 'is_shipped', 'payment_method', 'payment_receiver', 'contact_person')
    search_fields = ['id', 'date', 'linked_note__name', 'linked_note__description', 'customer_note',
                     'tracking_number'] + constants.ADDR_BILLING_FIELDS + constants.ADDR_SHIPPING_FIELDS

    ordering = ("is_shipped", "is_paid", "-date")

    inlines = [BestellungInlineBestellungsposten, BestellungInlineBestellungspostenAdd,
               BestellungInlineBestellungskosten, BestellungInlineBestellungskostenImport]

    autocomplete_fields = ("customer", "payment_receiver", "contact_person", )

    save_on_top = True

    list_select_related = ["customer", "linked_note"]

    date_hierarchy = "date"

    def get_fieldsets(self, request, obj=None):
        if obj:
            return [
                (_('Einstellungen'), {
                    'fields': ['payment_receiver', 'contact_person']
                }),
                (_('Infos'), {'fields': ['name', 'date', 'status']}),
                (_('Kunde'), {'fields': ['customer']}),
                (_('Lieferung'), {'fields': [('shipped_on', 'is_shipped'), 'tracking_number']}),
                (_('Bezahlungsoptionen'), {
                    'fields': ['payment_method', 'invoice_date', 'payment_conditions']
                }),
                (_('Bezahlung'), {
                    'fields': [('display_total_breakdown', 'display_payment_conditions'), ('paid_on', 'is_paid')]
                }),
                (_('Notizen & Texte'), {
                    'fields': ['customer_note', 'linked_note_html'],
                    'classes': ["collapse start-open"]}),
                (_('Rechnungsadresse'), {
                    'fields': constants.ADDR_BILLING_FIELDS if obj.is_paid else constants.ADDR_BILLING_FIELDS_CATEGORIZED,
                    'classes': ["collapse default-open"]}),
                (_('Lieferadresse'), {
                    'fields': constants.ADDR_SHIPPING_FIELDS if obj.is_shipped else constants.ADDR_SHIPPING_FIELDS_CATEGORIZED,
                    'classes': ["collapse start-open"]})
            ]

        return [
            (_('Einstellungen'), {'fields': [
                'payment_receiver', 'contact_person']}),
            (_('Infos'), {'fields': ['status']}),
            (_('Kunde'), {'fields': ['customer']}),
            (_('Bezahlungsoptionen'), {
                'fields': ['payment_method', 'invoice_date', 'payment_conditions'],
                'classes': ["collapse start-open"]}),
            (_('Notizen & Texte'), {
                'fields': ['customer_note'],
                'classes': ["collapse start-open"]}),
        ]

    readonly_fields = ('linked_note_html', 'name', 'tracking_link', 'display_total_breakdown', 'display_payment_conditions')

    def get_additional_readonly_fields(self, request, obj=None):
        fields = []
        if obj:
            if obj.is_shipped:
                fields += ['is_shipped'] + \
                    constants.ADDR_SHIPPING_FIELDS_WITHOUT_CONTACT
            if obj.is_paid:
                fields += ['is_paid', 'payment_method', 'invoice_date', 'payment_conditions'] + \
                    constants.ADDR_BILLING_FIELDS_WITHOUT_CONTACT
            if obj.woocommerceid:
                fields += ["customer_note"]
        return fields

    # Actions

    @admin.action(description=_("Als bezahlt markieren"), permissions=["change"])
    def mark_as_paid(self, request, queryset):
        successcount = 0
        errorcount = 0
        for order in queryset.all():
            if order.is_paid:
                errorcount += 1
            else:
                order.is_paid = True
                if order.is_shipped:
                    order.status = "completed"
                order.save()
                successcount += 1
        messages.success(request, ngettext(
            '%d Bestellung wurde als bezahlt markiert.',
            '%d Bestellungen wurden als bezahlt markiert.',
            successcount
        ))
        if errorcount:
            messages.warning(request, ngettext(
                '%d Bestellung war bereits als bezahlt markiert.',
                '%d Bestellungen waren bereits als bezahlt markiert.',
                errorcount
            ))

    @admin.action(description=_("Bestellungen von WooCommerce aktualisieren"), permissions=["change"])
    def wc_update(self, request, queryset):
        successcount, errorcount = WooCommerce.order_bulk_update(queryset.all())
        messages.success(request, ngettext(
            '%d Bestellung wurde von WooCommerce aktualisiert.',
            '%d Bestellungen wurden von WooCommerce aktualisiert.',
            successcount
        ))
        if errorcount:
            messages.error(request, ngettext(
                '%d Bestellung konnte nicht von WooCommerce aktualisiert werden.',
                '%d Bestellungen konnten nicht von WooCommerce aktualisiert werden.',
                errorcount
            ))

    actions = [mark_as_paid, wc_update]

    # Save

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # stock warnings
        if obj:
            for product in obj.products.all():
                product.show_stock_warning(request)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        form.instance.second_save()

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path('<path:object_id>/pdf/', self.admin_site.admin_view(views.order_view_pdf),
                 name='%s_%s_pdf' % info),
            path('<path:object_id>/pdf/form', self.admin_site.admin_view(views.order_create_pdf_form),
                 name='%s_%s_pdf_form' % info),
            path('<path:object_id>/email/invoice/', self.admin_site.admin_view(views.create_order_email_invoice),
                 name='%s_%s_email_invoice' % info),
            path('<path:object_id>/email/shipped/', self.admin_site.admin_view(views.create_order_email_shipped),
                 name='%s_%s_email_shipped' % info),
            path('<path:object_id>/duplicate/', self.admin_site.admin_view(views.duplicate_order),
                 name='%s_%s_duplicate' % info),
            path('<path:object_id>/return/', self.admin_site.admin_view(views.copy_order_to_delivery),
                 name='%s_%s_copy_to_delivery' % info),
        ]
        return my_urls + urls


@admin.register(Kosten)
class KostenAdmin(CustomModelAdmin):
    list_display = ["clean_name", "price", "vat_rate"]

    search_fields = ('name', 'price')

    ordering = ('price', 'vat_rate',)

    fieldsets = [
        (None, {"fields": ("name", "price", "vat_rate")})
    ]


class KundenAdminBestellungsInline(CustomTabularInline):
    model = Bestellung
    verbose_name = _("Bestellung")
    verbose_name_plural = _("Bestellungen")
    extra = 0

    show_change_link = True

    ordering = ('-date', )

    fields = ('pk', 'date', 'display_cached_sum', 'is_shipped', 'is_paid', 'display_paid_after')
    readonly_fields = ('pk', 'display_paid_after', 'display_cached_sum')

    # Custom queryset
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('customer')

    # Permissions

    NO_CHANGE = True
    NO_ADD = True
    NO_DELETE = True


@admin.register(Kunde)
class KundenAdmin(CustomModelAdmin):
    def get_fieldsets(self, request, obj=None):
        default = [
            (_('Infos'), {'fields': [
                'first_name', 'last_name', 'company', 'email', 'language']}),
            (_('Rechnungsadresse'), {
                'fields': constants.ADDR_BILLING_FIELDS_CATEGORIZED}),
            (_('Lieferadresse'), {
                'fields': constants.ADDR_SHIPPING_FIELDS_CATEGORIZED,
                'classes': ["collapse start-open"]}),
        ]

        if obj:
            return default + [
                (_('Diverses'), {
                    'fields': [
                        'website', 'note', 'linked_note_html'
                    ]}),
                (_('Erweitert'), {
                    'fields': [
                        'combine_with'
                    ], 'classes': ["collapse"]})
            ]

        return default + [
            (_('Diverses'), {'fields': ['website', 'note']})
        ]

    ordering = ('addr_billing_postcode', 'company', 'last_name', 'first_name')

    list_display = ('id', 'company', 'last_name', 'first_name', 'addr_billing_postcode',
                    'addr_billing_city', 'email', 'avatar', 'linked_note_html')
    search_fields = ['id', 'last_name', 'first_name', 'company', 'email', 'username', 'website',
                     'linked_note__name', 'linked_note__description'] + constants.ADDR_BILLING_FIELDS + constants.ADDR_SHIPPING_FIELDS

    readonly_fields = ["linked_note_html"]

    list_select_related = ["linked_note"]

    autocomplete_fields = ["combine_with"]

    inlines = [KundenAdminBestellungsInline]

    save_on_top = True

    # Actions

    @admin.action(description=_("Kunden von WooCommerce aktualisieren"), permissions=["change"])
    def wc_update(self, request, queryset):
        successcount, errorcount = WooCommerce.customer_bulk_update(queryset.all())
        messages.success(request, ngettext(
            '%d Kunde wurde von WooCommerce aktualisiert.',
            '%d Kunden wurden von WooCommerce aktualisiert.',
            successcount
        ))
        if errorcount:
            messages.error(request, ngettext(
                '%d Kunde konnte nicht von WooCommerce aktualisiert werden.',
                '%d Kunden konnten nicht von WooCommerce aktualisiert werden.',
                errorcount
            ))

    actions = ["wc_update"]

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path('<path:object_id>/email/registered/', self.admin_site.admin_view(views.create_customer_email_registered),
                 name='%s_%s_email_registered' % info),
        ]
        return my_urls + urls


@admin.register(Lieferant)
class LieferantenAdmin(CustomModelAdmin):
    fieldsets = [
        (_('Infos'), {'fields': ['abbreviation', 'name']}),
        (_('Firma'), {'fields': ['website', 'phone', 'email', 'address']}),
        (_('Ansprechpartner'), {
            'fields': [
                'contact_person_name', 'contact_person_phone', 'contact_person_email'
            ],
            'classes': ["collapse", "start-open"]}),
        (_('Notiz'), {
            'fields': ['note'],
            'classes': ["collapse", "start-open"]}),
    ]

    ordering = ('abbreviation',)

    list_display = ('abbreviation', 'name', 'note')
    search_fields = ['abbreviation', 'name', 'address', 'note']

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path('<path:object_id>/zuordnen/', self.admin_site.admin_view(views.lieferant_zuordnen),
                 name='%s_%s_zuordnen' % info),
        ]
        return my_urls + urls


class LieferungInlineProdukte(CustomTabularInline):
    model = Lieferung.products.through
    verbose_name = _("Produkt")
    verbose_name_plural = _("Produkte")
    extra = 0

    readonly_fields = ("produkt",)

    fields = ("produkt", "quantity",)

    # Permissions

    NO_ADD = True

    def has_change_permission(self, request, obj=None):
        return False if obj and obj.is_added_to_stock else super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False if obj and obj.is_added_to_stock else super().has_delete_permission(request, obj)


class LieferungInlineProdukteAdd(CustomTabularInline):
    model = Lieferung.products.through
    verbose_name = _("Produkt")
    verbose_name_plural = _("Produkte hinzufügen")
    extra = 0

    autocomplete_fields = ("produkt",)

    fields = ("produkt", "quantity",)

    # Permissions

    NO_VIEW = True
    NO_CHANGE = True
    NO_DELETE = True

    def has_add_permission(self, request, obj=None):
        return False if obj and obj.is_added_to_stock else super().has_add_permission(request, obj)


@admin.register(Lieferung)
class LieferungenAdmin(CustomModelAdmin):
    list_display = ('name', 'date', 'total_quantity',
                    'lieferant', 'is_added_to_stock', 'linked_note_html')
    list_filter = ("is_added_to_stock", "lieferant", )

    search_fields = ["name", "date", "lieferant__name", "lieferant__abbreviation",
                     "linked_note__name", "linked_note__description"]

    readonly_fields = ["linked_note_html"]

    autocomplete_fields = ("lieferant", )

    ordering = ('-date',)

    fieldsets = [
        (_('Infos'), {'fields': ['name', 'linked_note_html']}),
        (_('Lieferant'), {'fields': ['lieferant']})
    ]

    inlines = [LieferungInlineProdukte, LieferungInlineProdukteAdd]

    save_on_top = True

    list_select_related = ("lieferant", "linked_note", )

    # Actions

    @admin.action(description=_("Lieferungen einlagern"), permissions=["change"])
    def einlagern(self, request, queryset):
        successcount = 0
        errorcount = 0
        for lieferung in queryset.all():
            if lieferung.einlagern():
                successcount += 1
            else:
                errorcount += 1
        messages.success(request, ngettext(
            '%d Lieferung wurde als eingelagert markiert.',
            '%d Lieferungen wurden als eingelagert markiert.',
            successcount
        ))
        if errorcount:
            messages.error(request, ngettext(
                '%d Lieferung konnte nicht eingelagert werden.',
                '%d Lieferungen konnten nicht eingelagert werden.',
                errorcount
            ))

    actions = ["einlagern"]

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path('<path:object_id>/einlagern/', self.admin_site.admin_view(views.lieferung_einlagern),
                 name='%s_%s_einlagern' % info),
        ]
        return my_urls + urls


@admin.register(Notiz)
class NotizenAdmin(CustomModelAdmin):
    list_display = ["name", "description", "priority", "done", "created_at"]
    list_filter = ["done", "priority"]

    readonly_fields = ["links"]

    ordering = ["done", "-priority", "created_at"]

    search_fields = ("name", "description")

    def get_fieldsets(self, request, obj=None):
        if obj:
            return [
                (_("Infos"), {"fields": ["name", "description"]}),
                (_("Daten"), {"fields": ["done", "priority"]}),
                (_("Verknüpfungen"), {"fields": ["links"]}),
            ]

        return [
            (_("Infos"), {"fields": ["name", "description"]}),
            (_("Daten"), {"fields": ["done", "priority"]}),
        ]

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        if obj is None:
            form.base_fields['description'].initial = ""
            if "from_order" in request.GET:
                pk = request.GET.get("from_order")
                t = _('Bestellung #%d') % pk
                form.base_fields['name'].initial = t
                form.base_fields['description'].initial += f'\n\n[{t}]'
            if "from_product" in request.GET:
                pk = request.GET.get("from_product")
                t = _('Produkt #%d') % pk
                form.base_fields['name'].initial = t
                form.base_fields['description'].initial += f'\n\n[{t}]'
            if "from_customer" in request.GET:
                pk = request.GET.get("from_customer")
                t = _('Kunde #%d') % pk
                form.base_fields['name'].initial = t
                form.base_fields['description'].initial += f'\n\n[{t}]'
            if "from_delivery" in request.GET:
                pk = request.GET.get("from_delivery")
                t = _('Lieferung #%d') % pk
                form.base_fields['name'].initial = t
                form.base_fields['description'].initial += f'\n\n[{t}]'
        return form

    # Save

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            if "from_order" in request.GET:
                pk = request.GET["from_order"]
                if Bestellung.objects.filter(pk=pk).exists():
                    order = Bestellung.objects.get(pk=pk)
                    obj.linked_order = order
                    obj.save()
                    messages.info(
                        request, _("Bestellung #%s wurde mit dieser Notiz verknüpft.") % pk)
                else:
                    messages.warning(
                        request, _("Bestellung #%s konnte nicht gefunden werden. Die Notiz wurde trotzdem erstellt.") % pk)
            if "from_product" in request.GET:
                pk = request.GET["from_product"]
                if Produkt.objects.filter(pk=pk).exists():
                    product = Produkt.objects.get(pk=pk)
                    obj.linked_product = product
                    obj.save()
                    messages.info(
                        request, _("Produkt #%s wurde mit dieser Notiz verknüpft.") % pk)
                else:
                    messages.warning(
                        request, _("Produkt #%s konnte nicht gefunden werden. Die Notiz wurde trotzdem erstellt.") % pk)
            if "from_customer" in request.GET:
                pk = request.GET["from_customer"]
                if Kunde.objects.filter(pk=pk).exists():
                    customer = Kunde.objects.get(pk=pk)
                    obj.linked_customer = customer
                    obj.save()
                    messages.info(request, _("Kunde #%s wurde mit dieser Notiz verknüpft.") % pk)
                else:
                    messages.warning(
                        request, _("Kunde #%s konnte nicht gefunden werden. Die Notiz wurde trotzdem erstellt.") % pk)
            if "from_delivery" in request.GET:
                pk = request.GET["from_delivery"]
                if Lieferung.objects.filter(pk=pk).exists():
                    delivery = Lieferung.objects.get(pk=pk)
                    obj.linked_delivery = delivery
                    obj.save()
                    messages.info(request, _("Lieferung #%s wurde mit dieser Notiz verknüpft.") % pk)
                else:
                    messages.warning(
                        request, _("Lieferung #%s konnte nicht gefunden werden. Die Notiz wurde trotzdem erstellt.") % pk)


class ProduktInlineKategorienInline(CustomTabularInline):
    model = Produkt.categories.through
    extra = 0

    autocomplete_fields = ("kategorie", )

    # Custom queryset
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('kategorie', 'produkt')

    # Permissions

    NO_CHANGE = True


@admin.register(Produkt)
class ProduktAdmin(CustomModelAdmin):
    def get_fieldsets(self, request, obj=None):
        return [
            (_('Infos'), {'fields': ['article_number', 'name']}),
            (_('Beschrieb'), {
                'fields': ['short_description', 'description'],
                'classes': ["collapse start-open"]}),
            (_('Daten'), {'fields': [
                'quantity_description', 'selling_price', 'vat_rate', 'lagerbestand', 'soll_lagerbestand']}),
            (_('Lieferant'), {
                'fields': [
                    'lieferant', 'lieferant_preis', 'lieferant_article_number', 'lieferant_url'
                ], 'classes': ["collapse start-open"]}),
            (_('Aktion'), {
                'fields': [
                    'sale_from', 'sale_to', 'sale_price'
                ], 'classes': ["collapse start-open"]}),
            (_('Links'), {
                'fields': [
                    'datasheet_url', 'image_url'
                ], 'classes': ["collapse"]}),
            (_('Bemerkung / Notiz'), {
                'fields': [
                    'note', 'linked_note_html'] if obj else ['note'],
                'classes': ["collapse start-open"]})
        ]

    ordering = ('article_number', 'name')

    list_display = ('article_number', 'clean_name', 'clean_short_description',
                    'clean_description', 'get_current_price', 'is_on_sale', 'lagerbestand', 'html_image', 'linked_note_html')
    list_display_links = ('article_number', 'is_on_sale',)
    list_filter = ('lieferant', 'categories', 'lagerbestand')
    search_fields = ['article_number', 'name', 'short_description',
                     'description', 'note', 'linked_note__name', 'linked_note__description']

    readonly_fields = ["linked_note_html"]

    autocomplete_fields = ("lieferant", )

    inlines = (ProduktInlineKategorienInline,)

    save_on_top = True

    list_select_related = ["linked_note"]

    # Actions

    @admin.action(description=_("Produkte von WooCommerce aktualisieren"), permissions=["change"])
    def wc_update(self, request, queryset):
        successcount, errorcount = WooCommerce.product_bulk_update(queryset.all())
        messages.success(request, ngettext(
            '%d Produkt wurde von WooCommerce aktualisiert.',
            '%d Produkte wurden von WooCommerce aktualisiert.',
            successcount
        ))
        if errorcount:
            messages.error(request, ngettext(
                '%d Produkt konnte nicht von WooCommerce aktualisiert werden.',
                '%d Produkte konnten nicht von WooCommerce aktualisiert werden.',
                errorcount
            ))

    @admin.action(description=_("Lagerbestand zurücksetzen"), permissions=["change"])
    def lagerbestand_zuruecksetzen(self, request, queryset):
        for produkt in queryset.all():
            produkt.lagerbestand = 0
            produkt.save()
        messages.success(request, ngettext(
            'Lagerbestand von %d Produkt zurückgesetzt.',
            'Lagerbestand von %d Produkten zurückgesetzt.',
            queryset.count()
        ))

    @admin.action(description=_("Aktion beenden"), permissions=["change"])
    def end_sale(self, request, queryset):
        for produkt in queryset.all():
            produkt.sale_to = timezone.now()
            produkt.save()
        messages.success(request, ngettext(
            'Aktion von %d Produkt beendet.',
            'Aktion von %d Produkten beendet.',
            queryset.count()
        ))

    actions = ["wc_update", "lagerbestand_zuruecksetzen", "end_sale"]

    # Save

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj:
            obj.show_stock_warning(request)


class ProduktkategorienAdminProduktInline(CustomStackedInline):
    model = Produkt.categories.through
    verbose_name = _("Produkt in dieser Kategorie")
    verbose_name_plural = _("Produkte in dieser Kategorie")
    extra = 0

    autocomplete_fields = ("produkt", )

    # Custom queryset
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('kategorie', 'produkt')

    # Permissions

    NO_CHANGE = True


@admin.register(Produktkategorie)
class ProduktkategorienAdmin(CustomModelAdmin):
    fieldsets = [
        (_('Infos'), {'fields': ['name', 'description', 'image_url']}),
        (_('Übergeordnete Kategorie'), {'fields': ['parent_category']})
    ]

    list_display = ('clean_name', 'clean_description',
                    'parent_category', 'html_image', 'total_quantity')
    search_fields = ['name', 'description']

    ordering = ("parent_category", "name")

    inlines = [ProduktkategorienAdminProduktInline]

    list_select_related = ("parent_category",)

    autocomplete_fields = ("parent_category", )

    # Custom queryset
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(total_quantity=Count('products'))

    # Actions

    @admin.action(description=_("Kategorien von WooCommerce aktualisieren"), permissions=["change"])
    def wc_update(self, request, queryset):
        successcount, errorcount = WooCommerce.category_bulk_update(queryset.all())
        messages.success(request, ngettext(
            '%d Kategorie wurde von WooCommerce aktualisiert.',
            '%d Kategorien wurden von WooCommerce aktualisiert.',
            successcount
        ))
        if errorcount:
            messages.error(request, ngettext(
                '%d Kategorie konnte nicht von WooCommerce aktualisiert werden.',
                '%d Kategorien konnten nicht von WooCommerce aktualisiert werden.',
                errorcount
            ))

    actions = ["wc_update"]


@admin.register(Zahlungsempfaenger)
class ZahlungsempfaengerAdmin(CustomModelAdmin):
    fieldsets = [
        (_("Infos"), {
            "fields": ["name", "swiss_uid", "logourl", "website"]
        }),
        (_("Adresse"), {
            "fields": ["address_1", "address_2", "country"]
        }),
        (_("Zahlungsdetails"), {
            "fields": ["mode", "qriban", "iban"]
        }),
        (_("Kontaktdaten"), {
            "fields": ["email", "phone"],
            "classes": ["collapse"]
        })
    ]

    list_display = ('name', 'swiss_uid', 'mode', 'qriban', 'iban')
    list_filter = ('mode',)
    search_fields = ['name', 'address_1',
                     'address_2', 'qriban', 'iban', 'swiss_uid']

    save_on_top = True

    # Save

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj:
            if obj.mode == "QRR" and not obj.has_valid_qr_iban():
                messages.error(request, _("Ungültige QR-IBAN!"))
            if obj.mode == "NON" and not obj.has_valid_iban():
                messages.error(request, _("Ungültige IBAN!"))
            if obj.swiss_uid and not obj.has_valid_uid():
                messages.warning(request, _("Ungültige UID!"))


modeladmins = [
    (Ansprechpartner, AnsprechpartnerAdmin),
    (Bestellung, BestellungsAdmin),
    (Produktkategorie, ProduktkategorienAdmin),
    (Kosten, KostenAdmin),
    (Kunde, KundenAdmin),
    (Lieferant, LieferantenAdmin),
    (Lieferung, LieferungenAdmin),
    (Notiz, NotizenAdmin),
    (Produkt, ProduktAdmin),
    (Zahlungsempfaenger, ZahlungsempfaengerAdmin),
]
