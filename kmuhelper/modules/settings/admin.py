from django.contrib import admin

from kmuhelper.modules.settings import models
from kmuhelper.overrides import CustomModelAdmin


@admin.register(models.Setting)
class SettingAdmin(CustomModelAdmin):
    list_display = ("name", "content_display")
    ordering = ("id",)

    search_fields = []

    readonly_fields = ["id", "name", "description"]

    HIDDEN = True

    def get_fields(self, request, obj=None):
        return ["description", f"content_{obj.typ}"]

    # Permissions

    NO_ADD = True
    NO_DELETE = True


#

modeladmins = [
    (models.Setting, SettingAdmin),
]
