from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from kmuhelper.main.models import Einstellung, Geheime_Einstellung, Produkt, Kunde, Kategorie, Lieferant, Lieferung, Bestellung, Bestellungsposten
from kmuhelper.decorators import confirm_action

###############

# Create your views here.


@login_required(login_url=reverse_lazy("admin:login"))
@confirm_action("Lieferant zuordnen")
def lieferant_zuordnen(request, object_id):
    if Lieferant.objects.filter(id=int(object_id)).exists():
        count = Lieferant.objects.get(id=int(object_id)).zuordnen()
        messages.success(request, ('Lieferant wurde ' + (('{} neuen Produkten' if count > 1 else 'einem neuen Produkt')
                                                         if count != 0 else "keinem neuen Produkt") + ' zugeordnet!').format(count))
    else:
        messages.error(request, "Lieferant konnte nicht gefunden werden!")
    return redirect(reverse("admin:kmuhelper_lieferant_change", args=[object_id]))


@login_required(login_url=reverse_lazy("admin:login"))
@confirm_action("Lieferung einlagern")
def lieferung_einlagern(request, object_id):
    if Lieferung.objects.filter(id=int(object_id)).exists():
        if Lieferung.objects.get(id=int(object_id)).einlagern():
            messages.success(request, "Lieferung eingelagert!")
        else:
            messages.error(
                request, "Lieferung konnte nicht eingelagert werden!")
    else:
        messages.error(request, "Lieferung konnte nicht gefunden werden!")
    return redirect(reverse("admin:kmuhelper_lieferung_change", args=[object_id]))


@login_required(login_url=reverse_lazy("admin:login"))
@confirm_action("Registrierungsmail versenden")
def kunde_email_registriert(request, object_id):
    if Kunde.objects.filter(id=int(object_id)).exists():
        if Kunde.objects.get(id=int(object_id)).send_register_mail():
            messages.success(request, "Registrierungsmail gesendet!")
        else:
            messages.error(
                request, "Registrierungsmail konnte nicht gesendet werden!")
    else:
        messages.error(request, "Kunde konnte nicht gefunden werden!")
    return redirect(reverse("admin:kmuhelper_kunde_change", args=[object_id]))


@login_required(login_url=reverse_lazy("admin:login"))
def bestellung_pdf_ansehen(request, object_id):
    if Bestellung.objects.filter(id=int(object_id)).exists():
        obj = Bestellung.objects.get(id=int(object_id))
        lieferschein = bool("lieferschein" in dict(request.GET))
        digital = not bool("druck" in dict(request.GET))
        pdf = obj.get_pdf(lieferschein=lieferschein, digital=digital)
        return pdf
    else:
        messages.error(request, "Bestellung wurde nicht gefunden!")
        return redirect(reverse("admin:kmuhelper_bestellung_changelist"))


@login_required(login_url=reverse_lazy("admin:login"))
@confirm_action("Rechnung an Kunden per E-Mail senden")
def bestellung_pdf_an_kunden_senden(request, object_id):
    if Bestellung.objects.filter(id=int(object_id)).exists():
        if Bestellung.objects.get(id=int(object_id)).send_pdf_rechnung_to_customer():
            messages.success(request, "Rechnung an Kunden gesendet!")
        else:
            messages.error(
                request, "Rechnung konnte nicht an Kunden gesendet werden!")
    else:
        messages.error(request, "Bestellung konnte nicht gefunden werden!")
    return redirect(reverse("admin:kmuhelper_bestellung_change", args=[object_id]))


@login_required(login_url=reverse_lazy("admin:login"))
@confirm_action("Bestellung duplizieren")
def bestellung_duplizieren(request, object_id):
    if Bestellung.objects.filter(id=int(object_id)).exists():
        new = Bestellung.objects.get(id=int(object_id)).duplicate()
        messages.success(
            request, "Bestellung wurde dupliziert! HINWEIS: Dies ist die neu erstellte Bestellung!")
        return redirect(reverse("admin:kmuhelper_bestellung_change", args=[new.pk]))
    else:
        messages.error(request, "Bestellung konnte nicht gefunden werden!")
    return redirect(reverse("admin:kmuhelper_bestellung_change", args=[object_id]))


@login_required(login_url=reverse_lazy("admin:login"))
@confirm_action("Bestellung zu Lieferung kopieren")
def bestellung_zu_lieferung(request, object_id):
    if Bestellung.objects.filter(id=int(object_id)).exists():
        new = Bestellung.objects.get(id=int(object_id)).zu_lieferung()
        messages.success(
            request, "Bestellung wurde zu einer Lieferung kopiert!")
        return redirect(reverse("admin:kmuhelper_lieferung_change", args=[new.pk]))
    else:
        messages.error(request, "Bestellung konnte nicht gefunden werden!")
    return redirect(reverse("admin:kmuhelper_bestellung_change", args=[object_id]))


# Kunden-Entpunkte

def public_view_order(request, order_id, order_key):
    if Bestellung.objects.filter(id=int(order_id)).exists():
        obj = Bestellung.objects.get(id=int(order_id))
        lieferschein = bool("lieferschein" in dict(request.GET))
        digital = not bool("druck" in dict(request.GET))
        if str(obj.order_key) == order_key:
            return obj.get_pdf(lieferschein=lieferschein, digital=digital)
        else:
            return HttpResponse("Der Bestellungsschlüssel dieser Bestellung ist falsch!")
    else:
        return HttpResponse("Bestellung wurde nicht gefunden")
