from functools import update_wrapper

from django.contrib import admin
from django.urls import path
from django.views.decorators.clickjacking import (
    xframe_options_sameorigin as allow_iframe,
)
from django.views.generic import RedirectView

from kmuhelper.modules.app.models import (
    App_ToDo,
    App_Shipping,
    App_IncomingPayments,
    App_Stock,
    App_Arrival,
)
from kmuhelper.modules.main.admin import (
    NoteAdmin,
    OrderAdmin,
    SupplyAdmin,
    ProductAdmin,
)
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
            path("", wrap(self.changelist_view), name="%s_%s_changelist" % info),
            path("add/", wrap(self.add_view), name="%s_%s_add" % info),
            # path('<path:object_id>/history/', wrap(self.history_view),
            #      name='%s_%s_history' % info),
            # path('<path:object_id>/delete/', wrap(self.delete_view),
            #      name='%s_%s_delete' % info),
            path(
                "<path:object_id>/change/",
                wrap(self.change_view),
                name="%s_%s_change" % info,
            ),
            path(
                "<path:object_id>/",
                wrap(
                    RedirectView.as_view(
                        pattern_name="%s:%s_%s_change"
                        % ((self.admin_site.name,) + info)
                    )
                ),
            ),
        ]


#


@admin.register(App_ToDo)
class App_ToDoAdmin(App_AdminBase, NoteAdmin):
    list_editable = ["priority", "done"]
    list_filter = ["priority"]

    ordering = ["-priority", "created_at"]


@admin.register(App_Shipping)
class App_ShippingAdmin(App_AdminBase, OrderAdmin):
    list_display = (
        "id",
        "info",
        "status",
        "shipped_on",
        "is_shipped",
        "tracking_number",
        "linked_note_html",
    )
    list_editable = ("shipped_on", "is_shipped", "status", "tracking_number")
    list_filter = ("status", "is_paid")

    ordering = ("is_paid", "-date")

    actions = ()


@admin.register(App_IncomingPayments)
class App_IncomingPaymentsAdmin(App_AdminBase, OrderAdmin):
    list_display = (
        "id",
        "info",
        "status",
        "paid_on",
        "is_paid",
        "display_cached_sum",
        "display_payment_conditions",
        "linked_note_html",
    )
    list_editable = ("paid_on", "is_paid", "status")
    list_filter = ("status", "is_shipped", "payment_method")

    ordering = (
        "status",
        "invoice_date",
    )

    actions = ()


@admin.register(App_Stock)
class App_StockAdmin(App_AdminBase, ProductAdmin):
    list_display = (
        "nr",
        "clean_name",
        "stock_current",
        "get_current_price",
        "note",
        "linked_note_html",
    )
    list_display_links = ("nr",)
    list_editable = ["stock_current"]

    actions = ["reset_stock"]


@admin.register(App_Arrival)
class App_ArrivalAdmin(App_AdminBase, SupplyAdmin):
    list_display = ("name", "date", "total_quantity", "linked_note_html")
    list_filter = ()


#


modeladmins = [
    (App_ToDo, App_ToDoAdmin),
    (App_Shipping, App_ShippingAdmin),
    (App_IncomingPayments, App_IncomingPaymentsAdmin),
    (App_Stock, App_StockAdmin),
    (App_Arrival, App_ArrivalAdmin),
]
