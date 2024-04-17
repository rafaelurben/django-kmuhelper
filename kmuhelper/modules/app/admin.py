from django.contrib import admin

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
    HIDDEN = True


@admin.register(App_ToDo)
class App_ToDoAdmin(App_AdminBase, NoteAdmin):
    list_display = ["pkfill", "name", "description", "priority", "done", "created_at"]
    list_editable = ["priority", "done"]
    list_filter = ["priority"]

    ordering = ["-priority", "created_at"]


@admin.register(App_Shipping)
class App_ShippingAdmin(App_AdminBase, OrderAdmin):
    list_display = [
        "pkfill",
        "info",
        "status",
        "shipped_on",
        "is_shipped",
        "tracking_number",
        "linked_note_html",
    ]
    list_editable = ["shipped_on", "is_shipped", "status", "tracking_number"]
    list_filter = ["status", "is_paid"]

    ordering = ["is_paid", "-date"]

    actions = []


@admin.register(App_IncomingPayments)
class App_IncomingPaymentsAdmin(App_AdminBase, OrderAdmin):
    list_display = [
        "pkfill",
        "info",
        "status",
        "paid_on",
        "is_paid",
        "display_cached_sum",
        "display_payment_conditions",
        "linked_note_html",
    ]
    list_editable = ["paid_on", "is_paid", "status"]
    list_filter = ["status", "is_shipped", "payment_method"]

    ordering = [
        "status",
        "invoice_date",
    ]

    actions = []


@admin.register(App_Stock)
class App_StockAdmin(App_AdminBase, ProductAdmin):
    list_display = [
        "pkfill",
        "display_article_number",
        "clean_name",
        "stock_current",
        "stock_target",
        "display_current_price",
        "note",
        "linked_note_html",
    ]
    list_editable = ["stock_current", "stock_target"]

    actions = ["reset_stock"]


@admin.register(App_Arrival)
class App_ArrivalAdmin(App_AdminBase, SupplyAdmin):
    list_display = ["pkfill", "name", "date", "total_quantity", "linked_note_html"]
    list_filter = []


#


modeladmins = [
    (App_ToDo, App_ToDoAdmin),
    (App_Shipping, App_ShippingAdmin),
    (App_IncomingPayments, App_IncomingPaymentsAdmin),
    (App_Stock, App_StockAdmin),
    (App_Arrival, App_ArrivalAdmin),
]
