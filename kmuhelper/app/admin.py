from functools import update_wrapper

from django.contrib import admin
from django.urls import path
from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe
from django.views.generic import RedirectView

from kmuhelper.app.models import ToDoNotiz, ToDoVersand, ToDoZahlungseingang, ToDoLagerbestand, ToDoLieferung
from kmuhelper.main.admin import NotizenAdmin, BestellungsAdmin, LieferungenAdmin, ProduktAdmin
from kmuhelper.overrides import CustomModelAdmin

#######


class ToDoAdminBase(CustomModelAdmin):
    hidden = True

    # Permissions

    def has_delete_permission(self, request, obj=None):
        """Deactivate delete feature inside the app"""
        return False

    # Views

    def get_urls(self):
        """Overwrite"""

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(allow_iframe(view))(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        return [
            path('', wrap(self.changelist_view),
                 name='%s_%s_changelist' % info),
            path('add/', wrap(self.add_view),
                 name='%s_%s_add' % info),
            # path('<path:object_id>/history/', wrap(self.history_view),
            #      name='%s_%s_history' % info),
            # path('<path:object_id>/delete/', wrap(self.delete_view),
            #      name='%s_%s_delete' % info),
            path('<path:object_id>/change/', wrap(self.change_view),
                 name='%s_%s_change' % info),
            path('<path:object_id>/', wrap(RedirectView.as_view(
                pattern_name='%s:%s_%s_change' % (
                    (self.admin_site.name,) + info)
            ))),
        ]

#


@admin.register(ToDoNotiz)
class ToDoNotizenAdmin(ToDoAdminBase, NotizenAdmin):
    list_editable = ["priority", "erledigt"]
    list_filter = ["priority"]

    ordering = ["-priority", "erstellt_am"]


@admin.register(ToDoVersand)
class ToDoVersandAdmin(ToDoAdminBase, BestellungsAdmin):
    list_display = ('id', 'info', 'trackingnummer',
                    'versendet', 'status', 'html_todo_notiz')
    list_editable = ("trackingnummer", "versendet", "status")
    list_filter = ('status', 'bezahlt')

    ordering = ("bezahlt", "-datum")

    actions = ()


@admin.register(ToDoZahlungseingang)
class ToDoZahlungseingangAdmin(ToDoAdminBase, BestellungsAdmin):
    list_display = ('id', 'info', 'bezahlt', 'status',
                    'fix_summe', 'html_todo_notiz')
    list_editable = ("bezahlt", "status")
    list_filter = ('status', 'versendet', 'zahlungsmethode')

    ordering = ("versendet", "-rechnungsdatum")

    actions = ()


@admin.register(ToDoLagerbestand)
class ToDoLagerbestandAdmin(ToDoAdminBase, ProduktAdmin):
    list_display = ('nr', 'clean_name', 'lagerbestand',
                    'preis', 'bemerkung', 'html_todo_notiz')
    list_display_links = ('nr',)
    list_editable = ["lagerbestand"]

    actions = ["lagerbestand_zuruecksetzen"]


@admin.register(ToDoLieferung)
class ToDoLieferungenAdmin(ToDoAdminBase, LieferungenAdmin):
    list_display = ('name', 'datum', 'anzahlprodukte', 'html_todo_notiz')
    list_filter = ()

#


modeladmins = [
    (ToDoNotiz, ToDoNotizenAdmin),
    (ToDoVersand, ToDoVersandAdmin),
    (ToDoZahlungseingang, ToDoZahlungseingangAdmin),
    (ToDoLagerbestand, ToDoLagerbestandAdmin),
    (ToDoLieferung, ToDoLieferungenAdmin),
]
