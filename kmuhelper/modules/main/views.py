from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy

from kmuhelper.modules.main.models import Kunde, Lieferant, Lieferung, Bestellung
from kmuhelper.decorators import confirm_action, require_object
from kmuhelper.utils import render_error

# Other views

from kmuhelper.modules.pdfgeneration.order.views import order_view_pdf, order_create_pdf_form

###############

# Create your views here.


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.change_produkt")
@require_object(Lieferant)
@confirm_action("Lieferant allen Produkten ohne Lieferant zuordnen")
def lieferant_zuordnen(request, obj):
    count = obj.zuordnen()
    if count == 1:
        messages.success(
            request, 'Lieferant wurde einem neuen Produkt zugeordnet!')
    elif count == 0:
        messages.success(
            request, 'Lieferant wurde keinem neuen Produkt zugeordnet!')
    else:
        messages.success(
            request, f'Lieferant wurde {count} neuen Produkten einem neuen Produkt zugeordnet!')
    return redirect(reverse("admin:kmuhelper_lieferant_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.change_produkt")
@require_object(Lieferung)
@confirm_action("Lieferung einlagern")
def lieferung_einlagern(request, obj):
    if obj.einlagern():
        messages.success(request, "Lieferung eingelagert!")
    else:
        messages.error(
            request, "Lieferung konnte nicht eingelagert werden!")
    return redirect(reverse("admin:kmuhelper_lieferung_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required(
    ["kmuhelper.add_email", "kmuhelper.view_kunde", "kmuhelper.change_kunde"]
)
@require_object(Kunde)
def kunde_email_registriert(request, obj):
    mail = obj.create_email_registered()
    messages.success(request, "E-Mail wurde generiert!")
    return redirect(reverse("admin:kmuhelper_email_change", args=[mail.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required(
    ["kmuhelper.add_email", "kmuhelper.view_bestellung", "kmuhelper.change_bestellung"]
)
@require_object(Bestellung)
def create_order_email_invoice(request, obj):
    mail = obj.create_email_invoice()
    messages.success(request, "E-Mail wurde generiert!")
    return redirect(reverse("admin:kmuhelper_email_change", args=[mail.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required(
    ["kmuhelper.add_email", "kmuhelper.view_bestellung", "kmuhelper.change_bestellung"]
)
@require_object(Bestellung)
def create_order_email_shipped(request, obj):
    mail = obj.create_email_shipped()
    messages.success(request, "E-Mail wurde generiert!")
    return redirect(reverse("admin:kmuhelper_email_change", args=[mail.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.add_bestellung")
@require_object(Bestellung)
@confirm_action("Bestellung duplizieren")
def duplicate_order(request, obj):
    new = obj.duplicate()
    messages.success(
        request, "Bestellung wurde dupliziert! HINWEIS: Dies ist die neu erstellte Bestellung!")
    return redirect(reverse("admin:kmuhelper_bestellung_change", args=[new.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.add_lieferung")
@require_object(Bestellung)
@confirm_action("Bestellung zu Lieferung kopieren")
def copy_order_to_delivery(request, obj):
    new = obj.copy_to_delivery()
    messages.success(
        request, "Bestellung wurde zu einer Lieferung kopiert!")
    return redirect(reverse("admin:kmuhelper_lieferung_change", args=[new.pk]))

