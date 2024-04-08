from django.contrib import admin
from django.urls import path
from django.utils.translation import gettext_lazy

from kmuhelper.modules.integrations.paymentimport import views
from kmuhelper.modules.integrations.paymentimport.models import (
    PaymentImport,
    PaymentImportEntry,
)
from kmuhelper.overrides import CustomModelAdmin

_ = gettext_lazy


class PaymentImportAdminEntryInline(admin.TabularInline):
    model = PaymentImportEntry
    verbose_name = _("Eintrag")
    verbose_name_plural = _("Einträge")
    extra = 0

    fields = (
        "currency",
        "betrag",
        "ref",
        "order_id",
        "valuedate",
        "name",
        "iban",
        "additionalref",
    )
    readonly_fields = (
        "order_id",
        "betrag",
    )
    ordering = ("ref",)


@admin.register(PaymentImport)
class PaymentImportAdmin(CustomModelAdmin):
    readonly_fields = ("time_imported",)

    fieldsets = [
        ("Infos", {"fields": ["is_processed", "time_imported"]}),
        ("Daten", {"fields": ["data_msgid", "data_creationdate"]}),
    ]

    ordering = ("is_processed",)

    list_display = (
        "pkfill",
        "time_imported",
        "entrycount",
        "is_processed",
        "data_msgid",
    )
    list_filter = ("is_processed",)

    inlines = (PaymentImportAdminEntryInline,)

    save_on_top = True

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path(
                "upload/",
                self.admin_site.admin_view(views.upload),
                name="%s_%s_upload" % info,
            ),
            path(
                "<path:object_id>/process/",
                self.admin_site.admin_view(views.process),
                name="%s_%s_process" % info,
            ),
        ]
        return my_urls + urls

    # Permissions

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return obj is None


#


modeladmins = [
    (PaymentImport, PaymentImportAdmin),
]
