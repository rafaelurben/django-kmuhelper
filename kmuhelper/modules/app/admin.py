from functools import update_wrapper

from django.contrib import admin
from django.urls import path
from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe
from django.views.generic import RedirectView

from kmuhelper.modules.app.models import App_ToDo, App_Warenausgang, App_Zahlungseingang, App_Lagerbestand, App_Wareneingang
from kmuhelper.modules.main.admin import NotizenAdmin, BestellungsAdmin, LieferungenAdmin, ProduktAdmin
from kmuhelper.overrides import CustomModelAdmin

#######


class App_AdminBase(CustomModelAdmin):
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


@admin.register(App_ToDo)
class App_ToDoenAdmin(App_AdminBase, NotizenAdmin):
    list_editable = ["priority", "erledigt"]
    list_filter = ["priority"]

    ordering = ["-priority", "erstellt_am"]


@admin.register(App_Warenausgang)
class App_WarenausgangAdmin(App_AdminBase, BestellungsAdmin):
    list_display = ('id', 'info', 'trackingnummer',
                    'versendet', 'status', 'html_app_notiz')
    list_editable = ("trackingnummer", "versendet", "status")
    list_filter = ('status', 'bezahlt')

    ordering = ("bezahlt", "-datum")

    actions = ()


@admin.register(App_Zahlungseingang)
class App_ZahlungseingangAdmin(App_AdminBase, BestellungsAdmin):
    list_display = ('id', 'info', 'bezahlt', 'status',
                    'fix_summe', 'html_app_notiz')
    list_editable = ("bezahlt", "status")
    list_filter = ('status', 'versendet', 'zahlungsmethode')

    ordering = ("versendet", "-rechnungsdatum")

    actions = ()


@admin.register(App_Lagerbestand)
class App_LagerbestandAdmin(App_AdminBase, ProduktAdmin):
    list_display = ('nr', 'clean_name', 'lagerbestand',
                    'preis', 'bemerkung', 'html_app_notiz')
    list_display_links = ('nr',)
    list_editable = ["lagerbestand"]

    actions = ["lagerbestand_zuruecksetzen"]


@admin.register(App_Wareneingang)
class App_WareneingangenAdmin(App_AdminBase, LieferungenAdmin):
    list_display = ('name', 'datum', 'anzahlprodukte', 'html_app_notiz')
    list_filter = ()

#


modeladmins = [
    (App_ToDo, App_ToDoenAdmin),
    (App_Warenausgang, App_WarenausgangAdmin),
    (App_Zahlungseingang, App_ZahlungseingangAdmin),
    (App_Lagerbestand, App_LagerbestandAdmin),
    (App_Wareneingang, App_WareneingangenAdmin),
]
