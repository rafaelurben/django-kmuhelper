from django.contrib import admin

from kmuhelper.modules.api.models import ApiKey
from kmuhelper.overrides import CustomModelAdmin


@admin.register(ApiKey)
class ApiKeyAdmin(CustomModelAdmin):
    list_display = ['id', 'name', 'user', 'read', 'write', 'key_preview']
    list_filter = ["read", "write"]

    readonly_fields = ('key', )

    fieldsets = [
        ('Settings', {'fields': ('name', 'user', ('read', 'write'))}),
        ('Key', {'fields': ('key',), "classes": ('collapse',)})
    ]

    ordering = ('id', )

    hidden = True

#


modeladmins = [
    (ApiKey, ApiKeyAdmin),
]
