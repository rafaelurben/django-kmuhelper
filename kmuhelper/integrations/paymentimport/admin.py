from django.contrib import admin, messages
from django.urls import path

from kmuhelper.overrides import CustomModelAdmin
from kmuhelper.integrations.paymentimport.models import PaymentImport, PaymentImportEntry
from kmuhelper.integrations.paymentimport import views


class PaymentImportAdminEntryInline(admin.TabularInline):
    model = PaymentImportEntry
    extra = 0


@admin.register(PaymentImport)
class PaymentImportAdmin(CustomModelAdmin):
    readonly_fields = ('time_imported',)

    ordering = ('is_parsed',)

    list_display = ('title', 'time_imported', 'is_parsed',)
    list_filter = ('is_parsed',)

    # inlines = (PaymentImportAdminEntryInline, )

    save_on_top = True
    hidden = True

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path('upload', self.admin_site.admin_view(views.upload),
                 name="%s_%s_upload" % info),
            path('<path:object_id>/process', self.admin_site.admin_view(views.process),
                 name="%s_%s_process" % info),
        ]
        return my_urls + urls

#


modeladmins = [
    (PaymentImport, PaymentImportAdmin),
]
