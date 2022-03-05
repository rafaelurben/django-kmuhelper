from django.contrib import admin

from kmuhelper.settings import models
from kmuhelper.overrides import CustomModelAdmin


@admin.register(models.Einstellung)
class EinstellungenAdmin(CustomModelAdmin):
    list_display = ('name', 'inhalt')
    ordering = ('name',)

    search_fields = ['name', 'description', 'char',
                     'text', 'inte', 'floa', 'url', 'email']

    readonly_fields = ["id", "name", "description"]

    hidden = True

    def get_fields(self, request, obj=None):
        return ['description'] + (
            ['char'] if obj.typ == 'char' else
            ['text'] if obj.typ == 'text' else
            ['boo'] if obj.typ == 'bool' else
            ['inte'] if obj.typ == 'int' else
            ['floa'] if obj.typ == 'float' else
            ['url'] if obj.typ == 'url' else
            ['email'] if obj.typ == 'email' else
            ['json'] if obj.typ == 'json' else []
        )

    # Permissions

    NO_ADD = True
    NO_DELETE = True


#

modeladmins = [
    (models.Einstellung, EinstellungenAdmin),
]
