from django.contrib import admin
from django.urls import path

from kmuhelper.modules.emails import views
from kmuhelper.modules.emails.models import EMail, EMailAttachment, Attachment, EMailTemplate
from kmuhelper.overrides import CustomModelAdmin, CustomTabularInline

#######


@admin.register(Attachment)
class AttachmentAdmin(CustomModelAdmin):
    list_display = ['filename', 'description',
                    'time_created', 'autocreated', 'id']
    list_display_links = ['filename']

    search_fields = ('filename', 'description', )

    ordering = ['-time_created']

    save_on_top = True

    hidden = True

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

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path('<path:object_id>/download/', self.admin_site.admin_view(views.attachment_download),
                 name='%s_%s_download' % info),
        ]
        return my_urls + urls


class EMailAdminAttachmentInline(CustomTabularInline):
    model = EMailAttachment
    verbose_name = "Anhang"
    verbose_name_plural = "Anhänge"
    extra = 0

    show_change_link = True

    autocomplete_fields = ('attachment', )

    # Permissions

    NO_CHANGE = True


@admin.register(EMail)
class EMailAdmin(CustomModelAdmin):
    def get_fieldsets(self, request, obj=None):
        default = [
            ('Infos', {
                'fields': ['subject', 'to']}),
            ('Zusätzliche Empfänger', {
                'fields': ['cc', 'bcc'],
                'classes': ['collapse']}),
            ('Inhalt', {
                'fields': ['html_template', 'text', 'html_context']}),
        ]

        if obj:
            return default + [
                ('Zeiten', {'fields': ['time_created', 'time_sent']}),
            ]

        return default

    readonly_fields = ('time_created', 'time_sent')

    ordering = ('sent', '-time_sent', '-time_created')

    list_display = ('subject', 'to', 'html_template',
                    'time_created', 'sent', 'time_sent')
    list_filter = ('html_template', 'sent')

    search_fields = ['subject', 'to', 'cc',
                     'bcc', 'html_context', 'text', 'notes']

    inlines = (EMailAdminAttachmentInline, )

    save_on_top = True

    hidden = True

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path('<path:object_id>/preview/', self.admin_site.admin_view(views.email_preview),
                 name='%s_%s_preview' % info),
            path('<path:object_id>/send/', self.admin_site.admin_view(views.email_send),
                 name='%s_%s_send' % info),
            path('<path:object_id>/resend/', self.admin_site.admin_view(views.email_resend),
                 name='%s_%s_resend' % info),
        ]
        return my_urls + urls

    # Custom save

    def save_model(self, request, obj, form, change):
        if obj:
            obj.is_valid(request)
        super().save_model(request, obj, form, change)


@admin.register(EMailTemplate)
class EMailTemplateAdmin(CustomModelAdmin):
    list_display = ['title', 'description', 'get_use_link']

    search_fields = ('title', 'description', )

    ordering = ['title']

    fieldsets = [
        ('Infos', {
            'fields': ['title', 'description']}),
        ('Inhalt', {
            'fields': ['mail_to', 'mail_subject', 'mail_text']}),
        ('Optionen', {
            'fields': ['mail_template', 'mail_context']}),
    ]

    save_on_top = True

    hidden = True

    # Views

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super().get_urls()

        my_urls = [
            path('savevars', self.admin_site.admin_view(views.emailtemplate_savevars),
                 name="%s_%s_savevars" % info),
            path('resetvars', self.admin_site.admin_view(views.emailtemplate_resetvars),
                 name="%s_%s_resetvars" % info),
            path('<path:object_id>/use/', self.admin_site.admin_view(views.emailtemplate_use),
                 name='%s_%s_use' % info),
        ]
        return my_urls + urls

#


modeladmins = [
    (EMail, EMailAdmin),
    (Attachment, AttachmentAdmin),
    (EMailTemplate, EMailTemplateAdmin),
]
