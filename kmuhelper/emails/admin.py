from django.contrib import admin, messages
from datetime import datetime
from pytz import utc

from kmuhelper.emails.models import EMail

#######


@admin.register(EMail)
class EMailAdmin(admin.ModelAdmin):
    def get_fieldsets(self, request, obj=None):
        if obj:
            return [
                ("Infos", {'fields': ['subject', 'to', 'typ']}),
                ('Inhalt', {'fields': ['html_template', 'html_context']}),
                ('Zeiten', {'fields': ['time_created', 'time_sent']}),
                ('Extra', {'fields': ['data']}),
            ]
        else:
            return [
                ("Infos", {'fields': ['subject', 'to', 'typ']}),
                ('Inhalt', {'fields': ['html_template', 'html_context']}),
            ]

    readonly_fields = ('time_created', 'time_sent')

    ordering = ('time_sent', 'time_created',)

    list_display = ('subject', 'to', 'typ',
                    'time_created', 'time_sent', 'is_sent')
    search_fields = ['subject', 'to']

    def has_module_permission(self, request):
        return {}

#


modeladmins = [
    (EMail, EMailAdmin),
]
