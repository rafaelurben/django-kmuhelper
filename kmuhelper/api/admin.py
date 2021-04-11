from django.contrib import admin

from kmuhelper.api.models import ApiKey
from kmuhelper.overwrites import CustomModelAdmin

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

    # Permissions

    def has_module_permission(self, request):
        """Hide model in default admin"""
        return {}

#


modeladmins = [
    (ApiKey, ApiKeyAdmin),
]
