from django.contrib import admin, messages

from kmuhelper.overrides import CustomModelAdmin
from kmuhelper.integrations.paymentimport.models import PaymentImport, PaymentImportEntry


class PaymentImportAdminEntryInline(admin.TabularInline):
    model = PaymentImportEntry
    extra = 0


@admin.register(PaymentImport)
class PaymentImportAdmin(CustomModelAdmin):
    readonly_fields = ('time_imported',)

    ordering = ('is_parsed',)

    list_display = ('title', 'time_imported', 'is_parsed', 'entrycount',)
    list_filter = ('is_parsed',)

    # inlines = (PaymentImportAdminEntryInline, )

    save_on_top = True

    hidden = True

    def get_fieldsets(self, request, obj=None):
        if obj:
            return []

        return [
            (None, {'fields': ['title', 'xmlfile']})
        ]

    # Custom save

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not obj.is_parsed:
            if not obj.parse(request):
                messages.error(request, "Datei konnte nicht verarbeitet werden!")


#


modeladmins = [
    (PaymentImport, PaymentImportAdmin),
]
