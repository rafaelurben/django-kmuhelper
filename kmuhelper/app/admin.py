from django.contrib import admin, messages
from datetime import datetime
from pytz import utc

from kmuhelper.app.models import ToDoNotiz, ToDoVersand, ToDoZahlungseingang, ToDoLagerbestand, ToDoLieferung
from kmuhelper.main.admin import NotizenAdmin, BestellungsAdmin, LieferungenAdmin, ProduktAdmin
from kmuhelper.main.models import Ansprechpartner, Bestellung, Kategorie, Kosten, Kunde, Lieferant, Lieferung, Notiz, Produkt, Zahlungsempfaenger, Einstellung

from kmuhelper.utils import package_version, python_version
from kmuhelper.integrations.woocommerce import WooCommerce

#######


@admin.register(ToDoNotiz)
class ToDoNotizenAdmin(NotizenAdmin):
    list_editable = ["priority", "erledigt"]
    list_filter = ["priority"]

    ordering = ["-priority", "erstellt_am"]

    def has_module_permission(self, request):
        return {}

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        from django.urls import path
        from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe
        from functools import update_wrapper

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(allow_iframe(view))(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        return [
            path('', wrap(self.changelist_view),
                 name='%s_%s_changelist' % info),
            path('add/', wrap(self.add_view), name='%s_%s_add' % info),
            path('autocomplete/', wrap(self.autocomplete_view),
                 name='%s_%s_autocomplete' % info),
            # path('<path:object_id>/history/', wrap(self.history_view), name='%s_%s_history' % info),
            # path('<path:object_id>/delete/', wrap(self.delete_view), name='%s_%s_delete' % info),
            path('<path:object_id>/change/', wrap(self.change_view),
                 name='%s_%s_change' % info),
        ]


@admin.register(ToDoVersand)
class ToDoVersandAdmin(BestellungsAdmin):
    list_display = ('id', 'info', 'trackingnummer',
                    'versendet', 'status', 'html_todo_notiz')
    list_editable = ("trackingnummer", "versendet", "status")
    list_filter = ('status', 'bezahlt')

    ordering = ("bezahlt", "-datum")

    actions = ()

    def has_module_permission(self, request):
        return {}

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        from django.urls import path
        from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe
        from functools import update_wrapper

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(allow_iframe(view))(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        return [
            path('', wrap(self.changelist_view),
                 name='%s_%s_changelist' % info),
            path('add/', wrap(self.add_view), name='%s_%s_add' % info),
            path('autocomplete/', wrap(self.autocomplete_view),
                 name='%s_%s_autocomplete' % info),
            # path('<path:object_id>/history/', wrap(self.history_view), name='%s_%s_history' % info),
            # path('<path:object_id>/delete/', wrap(self.delete_view), name='%s_%s_delete' % info),
            path('<path:object_id>/change/', wrap(self.change_view),
                 name='%s_%s_change' % info),
        ]


@admin.register(ToDoZahlungseingang)
class ToDoZahlungseingangAdmin(BestellungsAdmin):
    list_display = ('id', 'info', 'bezahlt', 'status',
                    'fix_summe', 'html_todo_notiz')
    list_editable = ("bezahlt", "status")
    list_filter = ('status', 'versendet', 'zahlungsmethode')

    ordering = ("versendet", "-rechnungsdatum")

    actions = ()

    def has_module_permission(self, request):
        return {}

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        from django.urls import path
        from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe
        from functools import update_wrapper

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(allow_iframe(view))(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        return [
            path('', wrap(self.changelist_view),
                 name='%s_%s_changelist' % info),
            path('add/', wrap(self.add_view), name='%s_%s_add' % info),
            path('autocomplete/', wrap(self.autocomplete_view),
                 name='%s_%s_autocomplete' % info),
            # path('<path:object_id>/history/', wrap(self.history_view), name='%s_%s_history' % info),
            # path('<path:object_id>/delete/', wrap(self.delete_view), name='%s_%s_delete' % info),
            path('<path:object_id>/change/', wrap(self.change_view),
                 name='%s_%s_change' % info),
        ]


@admin.register(ToDoLagerbestand)
class ToDoLagerbestandAdmin(ProduktAdmin):
    list_display = ('nr', 'clean_name', 'lagerbestand',
                    'preis', 'bemerkung', 'html_todo_notiz')
    list_editable = ["lagerbestand"]

    actions = ["lagerbestand_zuruecksetzen"]

    def has_module_permission(self, request):
        return {}

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        from django.urls import path
        from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe
        from functools import update_wrapper

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(allow_iframe(view))(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        return [
            path('', wrap(self.changelist_view),
                 name='%s_%s_changelist' % info),
            path('add/', wrap(self.add_view), name='%s_%s_add' % info),
            path('autocomplete/', wrap(self.autocomplete_view),
                 name='%s_%s_autocomplete' % info),
            # path('<path:object_id>/history/', wrap(self.history_view), name='%s_%s_history' % info),
            # path('<path:object_id>/delete/', wrap(self.delete_view), name='%s_%s_delete' % info),
            path('<path:object_id>/change/', wrap(self.change_view),
                 name='%s_%s_change' % info),
        ]


@admin.register(ToDoLieferung)
class ToDoLieferungenAdmin(LieferungenAdmin):
    list_display = ('name', 'datum', 'anzahlprodukte', 'html_todo_notiz')
    list_filter = ()

    def has_module_permission(self, request):
        return {}

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        from django.urls import path
        from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe
        from functools import update_wrapper

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(allow_iframe(view))(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        return [
            path('', wrap(self.changelist_view),
                 name='%s_%s_changelist' % info),
            path('add/', wrap(self.add_view), name='%s_%s_add' % info),
            path('autocomplete/', wrap(self.autocomplete_view),
                 name='%s_%s_autocomplete' % info),
            # path('<path:object_id>/history/', wrap(self.history_view), name='%s_%s_history' % info),
            # path('<path:object_id>/delete/', wrap(self.delete_view), name='%s_%s_delete' % info),
            path('<path:object_id>/change/', wrap(self.change_view),
                 name='%s_%s_change' % info),
        ]

# 

modeladmins = [
    (ToDoNotiz, ToDoNotizenAdmin),
    (ToDoVersand, ToDoVersandAdmin),
    (ToDoZahlungseingang, ToDoZahlungseingangAdmin),
    (ToDoLagerbestand, ToDoLagerbestandAdmin),
    (ToDoLieferung, ToDoLieferungenAdmin),
]

