from django.contrib import admin
from django.urls import path

from kmuhelper.emails import views
from kmuhelper.emails.models import EMail, EMailAttachment, Attachment
from kmuhelper.overwrites import CustomModelAdmin

#######


@admin.register(Attachment)
class AttachmentAdmin(CustomModelAdmin):
    list_display = ['filename', 'description', 'time_created', 'autocreated']

    search_fields = ('filename', 'description', )

    ordering = ['-time_created']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['time_created', 'file', 'autocreated']

        return ['time_created', 'autocreated']

    def get_fieldsets(self, request, obj=None):
        default = [
            ('Datei', {'fields': ['filename', 'file']}),
            ('Infos', {'fields': ['description']})
        ]

        if obj:
            return default + [
                ('Daten', {'fields': ['autocreated', 'time_created']}),
            ]

        return default

    # Permissions

    def has_module_permission(self, request):
        """Hide model in default admin"""
        return {}

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path('<path:object_id>/download', self.admin_site.admin_view(views.attachment_download),
                 name='%s_%s_download' % info),
        ]
        return my_urls + urls


class EMailAdminAttachmentInline(admin.TabularInline):
    model = EMailAttachment
    verbose_name = "Anhang"
    verbose_name_plural = "Anhänge"
    extra = 0

    show_change_link = True

    autocomplete_fields = ('attachment', )

    # Permissions

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(EMail)
class EMailAdmin(CustomModelAdmin):
    def get_fieldsets(self, request, obj=None):
        default = [
            ('Infos', {
                'fields': ['subject', 'typ']}),
            ('Empfänger', {
                'fields': ['to', 'cc', 'bcc'],
                'classes': ['collapse']}),
            ('Inhalt', {
                'fields': ['html_template', 'html_context']}),
        ]

        if obj:
            return default + [
                ('Zeiten', {'fields': ['time_created', 'time_sent']}),
            ]

        return default

    readonly_fields = ('time_created', 'time_sent')

    ordering = ('sent', '-time_sent', '-time_created')

    list_display = ('subject', 'to', 'cc', 'bcc', 'typ',
                    'time_created', 'sent', 'time_sent')
    list_filter = ('typ', 'sent')

    search_fields = ['subject', 'to', 'cc', 'bcc', 'html_context']

    inlines = (EMailAdminAttachmentInline, )

    # Permissions

    def has_module_permission(self, request):
        """Hide model in default admin"""
        return {}

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path('<path:object_id>/preview', self.admin_site.admin_view(views.email_preview),
                 name='%s_%s_preview' % info),
            path('<path:object_id>/send', self.admin_site.admin_view(views.email_send),
                 name='%s_%s_send' % info),
            path('<path:object_id>/resend', self.admin_site.admin_view(views.email_resend),
                 name='%s_%s_resend' % info),
        ]
        return my_urls + urls

#


modeladmins = [
    (EMail, EMailAdmin),
    (Attachment, AttachmentAdmin),
]
