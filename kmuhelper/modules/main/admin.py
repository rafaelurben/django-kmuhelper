from django.contrib import admin, messages
from django.db.models import Count
from django.urls import path
from django.utils import timezone
from django.utils.translation import gettext_lazy, ngettext

from kmuhelper import constants
from kmuhelper.modules.integrations.woocommerce import WooCommerce
from kmuhelper.modules.main import views
from kmuhelper.modules.main.models import (
    ContactPerson,
    Order,
    ProductCategory,
    Fee,
    Customer,
    Supplier,
    Supply,
    Note,
    Product,
    PaymentReceiver,
)
from kmuhelper.modules.pdfgeneration.order import views as pdf_order_views
from kmuhelper.overrides import (
    CustomModelAdmin,
    CustomTabularInline,
    CustomStackedInline,
)

_ = gettext_lazy

#######


@admin.register(ContactPerson)
class ContactPersonAdmin(CustomModelAdmin):
    fieldsets = [
        (_("Name"), {"fields": ["name"]}),
        (_("Kontaktinformationen"), {"fields": ["phone", "email"]}),
        (_("Optionen"), {"fields": ["is_default"]}),
    ]

    ordering = ("name",)

    list_display = ("name", "phone", "email", "is_default")
    search_fields = ["name", "phone", "email"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.is_default:
            ContactPerson.objects.filter(is_default=True).exclude(pk=obj.pk).update(
                is_default=False
            )


class OrderAdminOrderItemInline(CustomTabularInline):
    model = Order.products.through
    verbose_name = _("Bestellungsposten")
    verbose_name_plural = _("Bestellungsposten")
    extra = 0

    fields = (
        "product",
        "note",
        "product_price",
        "quantity",
        "discount",
        "display_subtotal",
        "display_vat_rate",
    )

    readonly_fields = (
        "display_subtotal",
        "display_vat_rate",
        "product",
    )

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
        return (
            False
            if (obj and (obj.is_shipped or obj.is_paid))
            else super().has_delete_permission(request, obj)
        )

    # Custom queryset

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("product")


class OrderAdminOrderItemInlineAdd(CustomTabularInline):
    model = Order.products.through
    verbose_name = _("Bestellungsposten")
    verbose_name_plural = _("Bestellungsposten hinzufügen")
    extra = 0

    autocomplete_fields = ("product",)

    fieldsets = [(None, {"fields": ["product", "note", "quantity", "discount"]})]

    # Permissions

    NO_CHANGE = True
    NO_DELETE = True
    NO_VIEW = True

    def has_add_permission(self, request, obj=None):
        return (
            False
            if (obj and (obj.is_shipped or obj.is_paid))
            else super().has_add_permission(request, obj)
        )


class OrderAdminOrderFeeInline(CustomTabularInline):
    model = Order.fees.through
    verbose_name = _("Bestellungskosten")
    verbose_name_plural = _("Bestellungskosten")
    extra = 0

    fields = (
        "linked_fee",
        "name",
        "price",
        "discount",
        "note",
        "display_subtotal",
        "vat_rate",
    )

    readonly_fields = (
        "linked_fee",
        "display_subtotal",
    )

    def get_additional_readonly_fields(self, request, obj=None):
        if obj and obj.is_paid:
            return ["price", "vat_rate", "discount"]
        return []

    # Permissions

    def has_add_permission(self, request, obj=None):
        return (
            False if (obj and obj.is_paid) else super().has_add_permission(request, obj)
        )

    def has_delete_permission(self, request, obj=None):
        return (
            False
            if (obj and obj.is_paid)
            else super().has_delete_permission(request, obj)
        )

    # Custom queryset

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("linked_fee")


class OrderAdminOrderFeeInlineImport(CustomTabularInline):
    model = Order.fees.through
    verbose_name = _("Bestellungskosten")
    verbose_name_plural = _("Bestellungskosten importieren")
    extra = 0

    autocomplete_fields = ("linked_fee",)

    fields = (
        "linked_fee",
        "note",
        "discount",
    )

    # Permissions

    NO_CHANGE = True
    NO_DELETE = True
    NO_VIEW = True

    def has_add_permission(self, request, obj=None):
        return (
            False if (obj and obj.is_paid) else super().has_add_permission(request, obj)
        )


@admin.register(Order)
class OrderAdmin(CustomModelAdmin):
    list_display = (
        "id",
        "date",
        "customer",
        "status",
        "payment_method",
        "is_shipped",
        "is_paid",
        "display_cached_sum",
        "linked_note_html",
    )
    list_filter = (
        "status",
        "is_paid",
        "is_shipped",
        "payment_method",
        "payment_receiver",
        "contact_person",
    )
    search_fields = (
        [
            "id",
            "date",
            "linked_note__name",
            "linked_note__description",
            "customer_note",
            "tracking_number",
        ]
        + constants.ADDR_BILLING_FIELDS
        + constants.ADDR_SHIPPING_FIELDS
    )

    ordering = ("is_shipped", "is_paid", "-date")

    autocomplete_fields = (
        "customer",
        "payment_receiver",
        "contact_person",
    )

    save_on_top = True

    list_select_related = ["customer", "linked_note"]

    date_hierarchy = "date"

    def get_fieldsets(self, request, obj=None):
        if obj:
            return [
                (
                    _("Einstellungen"),
                    {"fields": ["payment_receiver", "contact_person"]},
                ),
                (_("Infos"), {"fields": ["name", "date", "status"]}),
                (_("Kunde"), {"fields": ["customer"]}),
                (
                    _("Lieferung"),
                    {"fields": [("shipped_on", "is_shipped"), "tracking_number"]},
                ),
                (
                    _("Bezahlungsoptionen"),
                    {
                        "fields": [
                            "payment_method",
                            "invoice_date",
                            "payment_conditions",
                            "payment_purpose",
                        ]
                    },
                ),
                (
                    _("Bezahlung"),
                    {
                        "fields": [
                            ("display_total_breakdown", "display_payment_conditions"),
                            ("paid_on", "is_paid"),
                        ]
                    },
                ),
                (
                    _("Notizen & Texte"),
                    {
                        "fields": ["customer_note", "linked_note_html"],
                        "classes": ["collapse start-open"],
                    },
                ),
                (
                    _("Rechnungsadresse"),
                    {
                        "fields": constants.ADDR_BILLING_FIELDS
                        if obj.is_paid
                        else constants.ADDR_BILLING_FIELDS_CATEGORIZED,
                        "classes": ["collapse start-open addr-billing-fieldset"],
                    },
                ),
                (
                    _("Lieferadresse"),
                    {
                        "fields": constants.ADDR_SHIPPING_FIELDS
                        if obj.is_shipped
                        else constants.ADDR_SHIPPING_FIELDS_CATEGORIZED,
                        "classes": ["collapse start-open addr-shipping-fieldset"],
                    },
                ),
            ]

        return [
            (_("Einstellungen"), {"fields": ["payment_receiver", "contact_person"]}),
            (_("Infos"), {"fields": ["status"]}),
            (_("Kunde"), {"fields": ["customer"]}),
            (
                _("Bezahlungsoptionen"),
                {
                    "fields": [
                        "payment_method",
                        "invoice_date",
                        "payment_conditions",
                        "payment_purpose",
                    ],
                    "classes": ["collapse start-open"],
                },
            ),
            (
                _("Notizen & Texte"),
                {"fields": ["customer_note"], "classes": ["collapse start-open"]},
            ),
        ]

    readonly_fields = (
        "linked_note_html",
        "name",
        "tracking_link",
        "display_total_breakdown",
        "display_payment_conditions",
    )

    def get_additional_readonly_fields(self, request, obj=None):
        fields = []
        if obj:
            if obj.is_shipped:
                fields += [
                    "is_shipped"
                ] + constants.ADDR_SHIPPING_FIELDS_WITHOUT_CONTACT
            if obj.is_paid:
                fields += [
                    "is_paid",
                    "payment_method",
                    "invoice_date",
                    "payment_conditions",
                ] + constants.ADDR_BILLING_FIELDS_WITHOUT_CONTACT
            if obj.woocommerceid:
                fields += ["customer_note"]
        return fields

    def get_inlines(self, request, obj=None):
        inlines = [OrderAdminOrderItemInline]
        if request.user.has_perm("kmuhelper.view_product"):
            inlines += [OrderAdminOrderItemInlineAdd]
        inlines += [OrderAdminOrderFeeInline]
        if request.user.has_perm("kmuhelper.view_fee"):
            inlines += [OrderAdminOrderFeeInlineImport]
        return inlines

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
        messages.success(
            request,
            ngettext(
                "%d Bestellung wurde als bezahlt markiert.",
                "%d Bestellungen wurden als bezahlt markiert.",
                successcount,
            ),
        )
        if errorcount:
            messages.warning(
                request,
                ngettext(
                    "%d Bestellung war bereits als bezahlt markiert.",
                    "%d Bestellungen waren bereits als bezahlt markiert.",
                    errorcount,
                ),
            )

    @admin.action(
        description=_("Bestellungen von WooCommerce aktualisieren"),
        permissions=["change"],
    )
    def wc_update(self, request, queryset):
        successcount, errorcount = WooCommerce.order_bulk_update(queryset.all())
        messages.success(
            request,
            ngettext(
                "%d Bestellung wurde von WooCommerce aktualisiert.",
                "%d Bestellungen wurden von WooCommerce aktualisiert.",
                successcount,
            ),
        )
        if errorcount:
            messages.error(
                request,
                ngettext(
                    "%d Bestellung konnte nicht von WooCommerce aktualisiert werden.",
                    "%d Bestellungen konnten nicht von WooCommerce aktualisiert werden.",
                    errorcount,
                ),
            )

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
            path(
                "<path:object_id>/pdf/",
                self.admin_site.admin_view(pdf_order_views.order_view_pdf),
                name="%s_%s_pdf" % info,
            ),
            path(
                "<path:object_id>/pdf/form",
                self.admin_site.admin_view(pdf_order_views.order_create_pdf_form),
                name="%s_%s_pdf_form" % info,
            ),
            path(
                "<path:object_id>/email/invoice/",
                self.admin_site.admin_view(views.create_order_email_invoice),
                name="%s_%s_email_invoice" % info,
            ),
            path(
                "<path:object_id>/email/shipped/",
                self.admin_site.admin_view(views.create_order_email_shipped),
                name="%s_%s_email_shipped" % info,
            ),
            path(
                "<path:object_id>/duplicate/",
                self.admin_site.admin_view(views.duplicate_order),
                name="%s_%s_duplicate" % info,
            ),
            path(
                "<path:object_id>/return/",
                self.admin_site.admin_view(views.copy_order_to_supply),
                name="%s_%s_copy_to_supply" % info,
            ),
        ]
        return my_urls + urls


@admin.register(Fee)
class FeeAdmin(CustomModelAdmin):
    list_display = ["clean_name", "price", "vat_rate"]

    search_fields = ("name", "price")

    ordering = (
        "price",
        "vat_rate",
    )

    fieldsets = [(None, {"fields": ("name", "price", "vat_rate")})]


class CustomerAdminOrderInline(CustomTabularInline):
    model = Order
    verbose_name = _("Bestellung")
    verbose_name_plural = _("Bestellungen")
    extra = 0

    show_change_link = True

    ordering = ("-date",)

    fields = (
        "pk",
        "date",
        "display_cached_sum",
        "is_shipped",
        "is_paid",
        "display_paid_after",
    )
    readonly_fields = ("pk", "display_paid_after", "display_cached_sum")

    # Custom queryset

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("customer")

    # Permissions

    NO_CHANGE = True
    NO_ADD = True
    NO_DELETE = True


@admin.register(Customer)
class CustomerAdmin(CustomModelAdmin):
    def get_fieldsets(self, request, obj=None):
        default = [
            (
                _("Infos"),
                {"fields": ["first_name", "last_name", "company", "email", "language"]},
            ),
            (
                _("Rechnungsadresse"),
                {
                    "fields": constants.ADDR_BILLING_FIELDS_CATEGORIZED,
                    "classes": ["addr-billing-fieldset"],
                },
            ),
            (
                _("Lieferadresse"),
                {
                    "fields": constants.ADDR_SHIPPING_FIELDS_CATEGORIZED,
                    "classes": ["addr-shipping-fieldset"],
                },
            ),
        ]

        if obj:
            return default + [
                (_("Diverses"), {"fields": ["website", "note", "linked_note_html"]}),
                (_("Erweitert"), {"fields": ["combine_with"], "classes": ["collapse"]}),
            ]

        return default + [(_("Diverses"), {"fields": ["website", "note"]})]

    ordering = ("addr_billing_postcode", "company", "last_name", "first_name")

    list_display = (
        "id",
        "company",
        "last_name",
        "first_name",
        "addr_billing_postcode",
        "addr_billing_city",
        "email",
        "avatar",
        "linked_note_html",
    )
    search_fields = (
        [
            "id",
            "last_name",
            "first_name",
            "company",
            "email",
            "username",
            "website",
            "linked_note__name",
            "linked_note__description",
        ]
        + constants.ADDR_BILLING_FIELDS
        + constants.ADDR_SHIPPING_FIELDS
    )

    readonly_fields = ["linked_note_html"]

    list_select_related = ["linked_note"]

    autocomplete_fields = ["combine_with"]

    inlines = [CustomerAdminOrderInline]

    save_on_top = True

    # Actions

    @admin.action(
        description=_("Kunden von WooCommerce aktualisieren"), permissions=["change"]
    )
    def wc_update(self, request, queryset):
        successcount, errorcount = WooCommerce.customer_bulk_update(queryset.all())
        messages.success(
            request,
            ngettext(
                "%d Kunde wurde von WooCommerce aktualisiert.",
                "%d Kunden wurden von WooCommerce aktualisiert.",
                successcount,
            ),
        )
        if errorcount:
            messages.error(
                request,
                ngettext(
                    "%d Kunde konnte nicht von WooCommerce aktualisiert werden.",
                    "%d Kunden konnten nicht von WooCommerce aktualisiert werden.",
                    errorcount,
                ),
            )

    actions = ["wc_update"]

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path(
                "<path:object_id>/email/registered/",
                self.admin_site.admin_view(views.create_customer_email_registered),
                name="%s_%s_email_registered" % info,
            ),
            path(
                "<path:object_id>/create-order",
                self.admin_site.admin_view(views.create_customer_order),
                name="%s_%s_create_order" % info,
            ),
        ]
        return my_urls + urls


@admin.register(Supplier)
class SupplierAdmin(CustomModelAdmin):
    fieldsets = [
        (_("Infos"), {"fields": ["abbreviation", "name"]}),
        (_("Firma"), {"fields": ["website", "phone", "email", "address"]}),
        (
            _("Ansprechpartner"),
            {
                "fields": [
                    "contact_person_name",
                    "contact_person_phone",
                    "contact_person_email",
                ],
                "classes": ["collapse", "start-open"],
            },
        ),
        (_("Notiz"), {"fields": ["note"], "classes": ["collapse", "start-open"]}),
    ]

    ordering = ("abbreviation",)

    list_display = ("abbreviation", "name", "note")
    search_fields = ["abbreviation", "name", "address", "note"]

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path(
                "<path:object_id>/assign/",
                self.admin_site.admin_view(views.supplier_assign),
                name="%s_%s_assign" % info,
            ),
        ]
        return my_urls + urls


class SupplyInlineSupplyItem(CustomTabularInline):
    model = Supply.products.through
    verbose_name = _("Produkt")
    verbose_name_plural = _("Produkte")
    extra = 0

    readonly_fields = ("product",)

    fields = (
        "product",
        "quantity",
    )

    # Permissions

    NO_ADD = True

    def has_change_permission(self, request, obj=None):
        return (
            False
            if obj and obj.is_added_to_stock
            else super().has_change_permission(request, obj)
        )

    def has_delete_permission(self, request, obj=None):
        return (
            False
            if obj and obj.is_added_to_stock
            else super().has_delete_permission(request, obj)
        )


class SupplyInlineProductsAdd(CustomTabularInline):
    model = Supply.products.through
    verbose_name = _("Produkt")
    verbose_name_plural = _("Produkte hinzufügen")
    extra = 0

    autocomplete_fields = ("product",)

    fields = (
        "product",
        "quantity",
    )

    # Permissions

    NO_VIEW = True
    NO_CHANGE = True
    NO_DELETE = True

    def has_add_permission(self, request, obj=None):
        if not (
            request.user.has_perm("kmuhelper.view_product")
            or request.user.has_perm("kmuhelper.change_product")
        ):
            return False
        return (
            False
            if obj and obj.is_added_to_stock
            else super().has_add_permission(request, obj)
        )


@admin.register(Supply)
class SupplyAdmin(CustomModelAdmin):
    list_display = (
        "name",
        "date",
        "total_quantity",
        "supplier",
        "is_added_to_stock",
        "linked_note_html",
    )
    list_filter = (
        "is_added_to_stock",
        "supplier",
    )

    search_fields = [
        "name",
        "date",
        "supplier__name",
        "supplier__abbreviation",
        "linked_note__name",
        "linked_note__description",
    ]

    readonly_fields = ["linked_note_html"]

    autocomplete_fields = ("supplier",)

    ordering = ("-date",)

    fieldsets = [
        (_("Infos"), {"fields": ["name", "linked_note_html"]}),
        (_("Lieferant"), {"fields": ["supplier"]}),
    ]

    inlines = [SupplyInlineSupplyItem, SupplyInlineProductsAdd]

    save_on_top = True

    list_select_related = (
        "supplier",
        "linked_note",
    )

    # Actions

    @admin.action(description=_("Lieferungen einlagern"), permissions=["change"])
    def add_to_stock(self, request, queryset):
        successcount = 0
        errorcount = 0
        for supply in queryset.all():
            if supply.add_to_stock():
                successcount += 1
            else:
                errorcount += 1
        messages.success(
            request,
            ngettext(
                "%d Lieferung wurde als eingelagert markiert.",
                "%d Lieferungen wurden als eingelagert markiert.",
                successcount,
            ),
        )
        if errorcount:
            messages.error(
                request,
                ngettext(
                    "%d Lieferung konnte nicht eingelagert werden.",
                    "%d Lieferungen konnten nicht eingelagert werden.",
                    errorcount,
                ),
            )

    actions = ["add_to_stock"]

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path(
                "<path:object_id>/add_to_stock/",
                self.admin_site.admin_view(views.supply_add_to_stock),
                name="%s_%s_add_to_stock" % info,
            ),
        ]
        return my_urls + urls


@admin.register(Note)
class NoteAdmin(CustomModelAdmin):
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
            form.base_fields["description"].initial = ""
            if "from_order" in request.GET:
                pk = request.GET.get("from_order")
                t = _("Bestellung #%s") % pk
                form.base_fields["name"].initial = t
                form.base_fields["description"].initial += f"\n\n[{t}]"
            if "from_product" in request.GET:
                pk = request.GET.get("from_product")
                t = _("Produkt #%s") % pk
                form.base_fields["name"].initial = t
                form.base_fields["description"].initial += f"\n\n[{t}]"
            if "from_customer" in request.GET:
                pk = request.GET.get("from_customer")
                t = _("Kunde #%s") % pk
                form.base_fields["name"].initial = t
                form.base_fields["description"].initial += f"\n\n[{t}]"
            if "from_supply" in request.GET:
                pk = request.GET.get("from_supply")
                t = _("Lieferung #%s") % pk
                form.base_fields["name"].initial = t
                form.base_fields["description"].initial += f"\n\n[{t}]"
        return form

    # Save

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            if "from_order" in request.GET:
                pk = request.GET["from_order"]
                if Order.objects.filter(pk=pk).exists():
                    order = Order.objects.get(pk=pk)
                    obj.linked_order = order
                    obj.save()
                    messages.info(
                        request,
                        _("Bestellung #%s wurde mit dieser Notiz verknüpft.") % pk,
                    )
                else:
                    messages.warning(
                        request,
                        _(
                            "Bestellung #%s konnte nicht gefunden werden. Die Notiz wurde trotzdem erstellt."
                        )
                        % pk,
                    )
            if "from_product" in request.GET:
                pk = request.GET["from_product"]
                if Product.objects.filter(pk=pk).exists():
                    product = Product.objects.get(pk=pk)
                    obj.linked_product = product
                    obj.save()
                    messages.info(
                        request, _("Produkt #%s wurde mit dieser Notiz verknüpft.") % pk
                    )
                else:
                    messages.warning(
                        request,
                        _(
                            "Produkt #%s konnte nicht gefunden werden. Die Notiz wurde trotzdem erstellt."
                        )
                        % pk,
                    )
            if "from_customer" in request.GET:
                pk = request.GET["from_customer"]
                if Customer.objects.filter(pk=pk).exists():
                    customer = Customer.objects.get(pk=pk)
                    obj.linked_customer = customer
                    obj.save()
                    messages.info(
                        request, _("Kunde #%s wurde mit dieser Notiz verknüpft.") % pk
                    )
                else:
                    messages.warning(
                        request,
                        _(
                            "Kunde #%s konnte nicht gefunden werden. Die Notiz wurde trotzdem erstellt."
                        )
                        % pk,
                    )
            if "from_supply" in request.GET:
                pk = request.GET["from_supply"]
                if Supply.objects.filter(pk=pk).exists():
                    supply = Supply.objects.get(pk=pk)
                    obj.linked_supply = supply
                    obj.save()
                    messages.info(
                        request,
                        _("Lieferung #%s wurde mit dieser Notiz verknüpft.") % pk,
                    )
                else:
                    messages.warning(
                        request,
                        _(
                            "Lieferung #%s konnte nicht gefunden werden. Die Notiz wurde trotzdem erstellt."
                        )
                        % pk,
                    )


class ProductAdminProductCategoryInline(CustomTabularInline):
    model = Product.categories.through
    extra = 0

    autocomplete_fields = ("category",)

    # Custom queryset

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("category", "product")

    # Permissions

    NO_CHANGE = True

    def has_add_permission(self, request, obj=None):
        if not request.user.has_perm("kmuhelper.view_productcategory"):
            return False
        return super().has_add_permission(request, obj)


@admin.register(Product)
class ProductAdmin(CustomModelAdmin):
    def get_fieldsets(self, request, obj=None):
        return [
            (_("Infos"), {"fields": ["article_number", "name"]}),
            (
                _("Beschrieb"),
                {
                    "fields": ["short_description", "description"],
                    "classes": ["collapse start-open"],
                },
            ),
            (
                _("Daten"),
                {
                    "fields": [
                        "quantity_description",
                        "selling_price",
                        "vat_rate",
                        "stock_current",
                        "stock_target",
                    ]
                },
            ),
            (
                _("Lieferant"),
                {
                    "fields": [
                        "supplier",
                        "supplier_price",
                        "supplier_article_number",
                        "supplier_url",
                    ],
                    "classes": ["collapse start-open"],
                },
            ),
            (
                _("Aktion"),
                {
                    "fields": ["sale_from", "sale_to", "sale_price"],
                    "classes": ["collapse start-open"],
                },
            ),
            (
                _("Links"),
                {"fields": ["datasheet_url", "image_url"], "classes": ["collapse"]},
            ),
            (
                _("Bemerkung / Notiz"),
                {
                    "fields": ["note", "linked_note_html"] if obj else ["note"],
                    "classes": ["collapse start-open"],
                },
            ),
        ]

    ordering = ("article_number", "name")

    list_display = (
        "article_number",
        "clean_name",
        "clean_short_description",
        "clean_description",
        "get_current_price",
        "is_on_sale",
        "stock_current",
        "html_image",
        "linked_note_html",
    )
    list_display_links = (
        "article_number",
        "is_on_sale",
    )
    list_filter = ("supplier", "categories", "stock_current")
    search_fields = [
        "article_number",
        "name",
        "short_description",
        "description",
        "note",
        "linked_note__name",
        "linked_note__description",
    ]

    readonly_fields = ["linked_note_html"]

    autocomplete_fields = ("supplier",)

    inlines = (ProductAdminProductCategoryInline,)

    save_on_top = True

    list_select_related = ["linked_note"]

    # Actions

    @admin.action(
        description=_("Produkte von WooCommerce aktualisieren"), permissions=["change"]
    )
    def wc_update(self, request, queryset):
        successcount, errorcount = WooCommerce.product_bulk_update(queryset.all())
        messages.success(
            request,
            ngettext(
                "%d Produkt wurde von WooCommerce aktualisiert.",
                "%d Produkte wurden von WooCommerce aktualisiert.",
                successcount,
            ),
        )
        if errorcount:
            messages.error(
                request,
                ngettext(
                    "%d Produkt konnte nicht von WooCommerce aktualisiert werden.",
                    "%d Produkte konnten nicht von WooCommerce aktualisiert werden.",
                    errorcount,
                ),
            )

    @admin.action(description=_("Lagerbestand zurücksetzen"), permissions=["change"])
    def reset_stock(self, request, queryset):
        for product in queryset.all():
            product.stock_current = 0
            product.save()
        messages.success(
            request,
            ngettext(
                "Lagerbestand von %d Produkt zurückgesetzt.",
                "Lagerbestand von %d Produkten zurückgesetzt.",
                queryset.count(),
            ),
        )

    @admin.action(description=_("Aktion beenden"), permissions=["change"])
    def end_sale(self, request, queryset):
        for product in queryset.all():
            product.sale_to = timezone.now()
            product.save()
        messages.success(
            request,
            ngettext(
                "Aktion von %d Produkt beendet.",
                "Aktion von %d Produkten beendet.",
                queryset.count(),
            ),
        )

    actions = ["wc_update", "reset_stock", "end_sale"]

    # Save

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj:
            obj.show_stock_warning(request)


class ProductCategoryAdminProductInline(CustomStackedInline):
    model = Product.categories.through
    verbose_name = _("Produkt in dieser Kategorie")
    verbose_name_plural = _("Produkte in dieser Kategorie")
    extra = 0

    autocomplete_fields = ("product",)

    # Custom queryset

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("category", "product")

    # Permissions

    NO_CHANGE = True

    def has_add_permission(self, request, obj=None):
        if not (
            request.user.has_perm("kmuhelper.view_product")
            or request.user.has_perm("kmuhelper.change_product")
        ):
            return False
        return super().has_add_permission(request, obj)


@admin.register(ProductCategory)
class ProductCategoryAdmin(CustomModelAdmin):
    fieldsets = [
        (_("Infos"), {"fields": ["name", "description", "image_url"]}),
        (_("Übergeordnete Kategorie"), {"fields": ["parent_category"]}),
    ]

    list_display = (
        "clean_name",
        "clean_description",
        "parent_category",
        "html_image",
        "total_quantity",
    )
    search_fields = ["name", "description"]

    ordering = ("parent_category", "name")

    inlines = [ProductCategoryAdminProductInline]

    list_select_related = ("parent_category",)

    autocomplete_fields = ("parent_category",)

    # Custom queryset

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(total_quantity=Count("products"))

    # Actions

    @admin.action(
        description=_("Kategorien von WooCommerce aktualisieren"),
        permissions=["change"],
    )
    def wc_update(self, request, queryset):
        successcount, errorcount = WooCommerce.category_bulk_update(queryset.all())
        messages.success(
            request,
            ngettext(
                "%d Kategorie wurde von WooCommerce aktualisiert.",
                "%d Kategorien wurden von WooCommerce aktualisiert.",
                successcount,
            ),
        )
        if errorcount:
            messages.error(
                request,
                ngettext(
                    "%d Kategorie konnte nicht von WooCommerce aktualisiert werden.",
                    "%d Kategorien konnten nicht von WooCommerce aktualisiert werden.",
                    errorcount,
                ),
            )

    actions = ["wc_update"]


@admin.register(PaymentReceiver)
class PaymentReceiverAdmin(CustomModelAdmin):
    fieldsets = [
        (None, {"fields": ["internal_name"]}),
        (
            _("Anzeigeinformationen"),
            {"fields": ["display_name", "display_address_1", "display_address_2"]},
        ),
        (_("Zahlungsinformationen"), {"fields": ["mode", "qriban", "iban"]}),
        (
            _("Rechnungsadresse"),
            {
                "fields": [
                    "invoice_name",
                    "invoice_address_1",
                    "invoice_address_2",
                    "invoice_country",
                ]
            },
        ),
        (_("Optionen"), {"fields": ["invoice_display_mode", "is_default"]}),
        (
            _("Weitere Informationen & Darstellung"),
            {"fields": ["swiss_uid", "website", "logourl"]},
        ),
    ]

    list_display = (
        "admin_name",
        "mode",
        "active_iban",
        "invoice_display_mode",
        "is_default",
    )
    list_filter = (
        "mode",
        "invoice_country",
        "invoice_display_mode",
    )
    search_fields = [
        "internal_name",
        "display_name",
        "display_address_1",
        "display_address_2",
        "invoice_name",
        "invoice_address_1",
        "invoice_address_2",
        "invoice_country",
        "swiss_uid",
        "website",
        "logourl",
        "qriban",
        "iban",
    ]

    save_on_top = True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.is_default:
            PaymentReceiver.objects.filter(is_default=True).exclude(pk=obj.pk).update(
                is_default=False
            )


modeladmins = [
    (ContactPerson, ContactPersonAdmin),
    (Order, OrderAdmin),
    (ProductCategory, ProductCategoryAdmin),
    (Fee, FeeAdmin),
    (Customer, CustomerAdmin),
    (Supplier, SupplierAdmin),
    (Supply, SupplyAdmin),
    (Note, NoteAdmin),
    (Product, ProductAdmin),
    (PaymentReceiver, PaymentReceiverAdmin),
]
