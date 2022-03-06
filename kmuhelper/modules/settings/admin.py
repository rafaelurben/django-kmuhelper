from django.contrib import admin

from kmuhelper.modules.settings import models
from kmuhelper.overrides import CustomModelAdmin


@admin.register(models.Einstellung)
class EinstellungenAdmin(CustomModelAdmin):
    list_display = ('name', 'content_display')
    ordering = ('name',)

    search_fields = ['name', 'description']

    readonly_fields = ["id", "name", "description"]

    hidden = True

    def get_fields(self, request, obj=None):
        return ['description', f'content_{obj.typ}']

    # Permissions

    NO_ADD = True
    NO_DELETE = True


#

modeladmins = [
    (models.Einstellung, EinstellungenAdmin),
]
