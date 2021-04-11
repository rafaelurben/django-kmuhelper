from django.contrib import admin

from kmuhelper.emails.models import EMail
from kmuhelper.overwrites import CustomModelAdmin

#######


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

    ordering = ('time_sent', 'time_created',)

    list_display = ('subject', 'to', 'typ',
                    'time_created', 'time_sent', 'is_sent')
    search_fields = ['subject', 'to']

    # Permissions

    def has_module_permission(self, request):
        """Hide model in default admin"""
        return {}

#


modeladmins = [
    (EMail, EMailAdmin),
]
