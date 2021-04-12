from django.contrib import admin
from django.urls import path

from kmuhelper.emails import views
from kmuhelper.emails.models import EMail, EMailAttachment
from kmuhelper.overwrites import CustomModelAdmin

#######


@admin.register(EMailAttachment)
class EMailAttachmentAdmin(CustomModelAdmin):
    list_display = ['filename', 'description', 'time_created', 'autocreated']

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
            path('<path:object_id>/download', self.admin_site.admin_view(views.emailattachment_download),
                 name='%s_%s_download' % info),
        ]
        return my_urls + urls


@admin.register(EMail)
class EMailAdmin(CustomModelAdmin):
    def get_fieldsets(self, request, obj=None):
        default = [
            ("Infos", {'fields': ['subject', 'to', 'typ']}),
            ('Inhalt', {'fields': ['html_template', 'html_context']}),
        ]

        if obj:
            return default + [
                ('Zeiten', {'fields': ['time_created', 'time_sent']}),
                ('Extra', {'fields': ['data']}),
            ]

        return default

    readonly_fields = ('time_created', 'time_sent')

    ordering = ('sent', '-time_sent', '-time_created')

    list_display = ('subject', 'to', 'typ',
                    'time_created', 'sent', 'time_sent')
    search_fields = ['subject', 'to']

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
]
