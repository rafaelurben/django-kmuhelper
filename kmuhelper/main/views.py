from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy

from kmuhelper.main.models import Kunde, Lieferant, Lieferung, Bestellung
from kmuhelper.decorators import confirm_action, require_object

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
@permission_required("kmuhelper.add_email")
@require_object(Kunde)
@confirm_action("Registrierungsmail versenden")
def kunde_email_registriert(request, obj):
    if obj.send_register_mail():
        messages.success(request, "Registrierungsmail gesendet!")
    else:
        messages.error(
            request, "Registrierungsmail konnte nicht gesendet werden!")
    return redirect(reverse("admin:kmuhelper_kunde_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.view_bestellung")
@require_object(Bestellung)
def bestellung_pdf_ansehen(request, obj):
    lieferschein = bool("lieferschein" in dict(request.GET))
    digital = not bool("druck" in dict(request.GET))
    pdf = obj.get_pdf(lieferschein=lieferschein, digital=digital)
    return pdf


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.add_email")
@require_object(Bestellung)
@confirm_action("Rechnung an Kunden per E-Mail senden")
def bestellung_pdf_an_kunden_senden(request, obj):
    if obj.send_pdf_rechnung_to_customer():
        messages.success(request, "Rechnung an Kunden gesendet!")
    else:
        messages.error(
            request, "Rechnung konnte nicht an Kunden gesendet werden!")
    return redirect(reverse("admin:kmuhelper_bestellung_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.add_bestellung")
@require_object(Bestellung)
@confirm_action("Bestellung duplizieren")
def bestellung_duplizieren(request, obj):
    new = obj.duplicate()
    messages.success(
        request, "Bestellung wurde dupliziert! HINWEIS: Dies ist die neu erstellte Bestellung!")
    return redirect(reverse("admin:kmuhelper_bestellung_change", args=[new.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.add_lieferung")
@require_object(Bestellung)
@confirm_action("Bestellung zu Lieferung kopieren")
def bestellung_zu_lieferung(request, obj):
    new = obj.zu_lieferung()
    messages.success(
        request, "Bestellung wurde zu einer Lieferung kopiert!")
    return redirect(reverse("admin:kmuhelper_lieferung_change", args=[new.pk]))


# Kunden-Entpunkte

@require_object(Bestellung, reverse_lazy("kmuhelper:info"))
def public_view_order(request, obj, order_key):
    lieferschein = bool("lieferschein" in dict(request.GET))
    digital = not bool("druck" in dict(request.GET))

    if str(obj.order_key) == order_key:
        return obj.get_pdf(lieferschein=lieferschein, digital=digital)

    messages.error(
        request, "Der Bestellungsschlüssel dieser Bestellung stimmt nicht überein.")
    return redirect(reverse("kmuhelper:info"))
