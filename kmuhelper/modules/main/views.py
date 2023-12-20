from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy

from kmuhelper.decorators import (
    confirm_action,
    require_object,
    require_all_kmuhelper_perms,
)
from kmuhelper.modules.main.models import Customer, Supplier, Supply, Order

_ = gettext_lazy

# Create your views here.


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["change_product", "view_supplier"])
@require_object(Supplier)
@confirm_action(_("Lieferant allen Produkten ohne Lieferant zuordnen"))
def supplier_assign(request, obj):
    count = obj.assign()
    if count == 1:
        messages.success(request, _("Lieferant wurde einem neuen Produkt zugeordnet!"))
    elif count == 0:
        messages.success(request, _("Lieferant wurde keinem neuen Produkt zugeordnet!"))
    else:
        messages.success(
            request,
            _("Lieferant wurde %d neuen Produkten einem neuen Produkt zugeordnet!")
            % count,
        )
    return redirect(reverse("admin:kmuhelper_supplier_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["change_product", "view_supply"])
@require_object(Supply)
@confirm_action(_("Lieferung einlagern"))
def supply_add_to_stock(request, obj):
    if obj.add_to_stock():
        messages.success(request, _("Lieferung eingelagert!"))
    else:
        messages.error(request, _("Lieferung konnte nicht eingelagert werden!"))
    return redirect(reverse("admin:kmuhelper_supply_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["add_email", "view_customer", "change_customer"])
@require_object(Customer)
def create_customer_email_registered(request, obj):
    mail = obj.create_email_registered()
    messages.success(request, _("E-Mail wurde generiert!"))
    return redirect(reverse("admin:kmuhelper_email_change", args=[mail.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["view_customer", "add_order"])
@require_object(Customer)
def create_customer_order(request, obj):
    order = Order.objects.create(customer=obj)
    messages.success(request, _("Bestellung wurde erstellt!"))
    return redirect(reverse("admin:kmuhelper_order_change", args=[order.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["add_email", "view_order", "change_order"])
@require_object(Order)
def create_order_email_invoice(request, obj):
    mail = obj.create_email_invoice()
    messages.success(request, _("E-Mail wurde generiert!"))
    return redirect(reverse("admin:kmuhelper_email_change", args=[mail.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required(["add_email", "view_order", "change_order"])
@require_object(Order)
def create_order_email_shipped(request, obj):
    mail = obj.create_email_shipped()
    messages.success(request, _("E-Mail wurde generiert!"))
    return redirect(reverse("admin:kmuhelper_email_change", args=[mail.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["add_order", "view_order"])
@require_object(Order)
@confirm_action(_("Bestellung duplizieren"))
def duplicate_order(request, obj):
    new = obj.duplicate()
    messages.success(
        request,
        _(
            "Bestellung wurde dupliziert! HINWEIS: Dies ist die neu erstellte Bestellung!"
        ),
    )
    return redirect(reverse("admin:kmuhelper_order_change", args=[new.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["add_supply", "view_order"])
@require_object(Order)
@confirm_action(_("Bestellung zu Lieferung kopieren"))
def copy_order_to_supply(request, obj):
    new = obj.copy_to_supply()
    messages.success(request, _("Bestellung wurde zu einer Lieferung kopiert!"))
    return redirect(reverse("admin:kmuhelper_supply_change", args=[new.pk]))


def index(request):
    return redirect(reverse("admin:app_list", args=["kmuhelper"]))
