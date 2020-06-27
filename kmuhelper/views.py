from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from urllib.parse import urlencode

from random import randint
from json import loads as loadjson

from .models import Einstellung, Geheime_Einstellung, Produkt, Kunde, Kategorie, Lieferung, Bestellung
from .apis import WooCommerce

# Create your views here.

@csrf_exempt
def wc_auth_key(request):
    JSON = loadjson(request.body)
    storeurl = request.headers.get("user-agent").split(";")[1].lstrip()

    url = Geheime_Einstellung.objects.get(id="wc-url")
    if url.inhalt.lstrip("https://").lstrip("http://").split("/")[0] == storeurl.lstrip("https://").lstrip("http://").split("/")[0]:
        key = Geheime_Einstellung.objects.get(id="wc-consumer_key")
        key.inhalt = JSON["consumer_key"]
        key.save()

        secret = Geheime_Einstellung.objects.get(id="wc-consumer_secret")
        secret.inhalt = JSON["consumer_secret"]
        secret.save()

        url = Einstellung.objects.get(id="wc-url")
        url.inhalt = "Bestätigt: "+storeurl+" (Änderungen an diesem Eintrag werden nur nach erneutem Verbinden angewendet!)"
        url.save()
    return HttpResponse("success")


@login_required(login_url="/admin/login")
def wc_auth_end(request):
    if request.GET["success"] == "1":
        messages.success(request,"WooCommerce erfolgreich verbunden!")
    else:
        messages.error(request,"WooCommerce konnte nicht verbunden werden!")
    return redirect("/admin/kmuhelper/")


@login_required(login_url="/admin/login")
def wc_auth_start(request):
    shopurl = Einstellung.objects.get(id="wc-url").inhalt
    kmuhelperurl = request.get_host()
    params = {
        "app_name": "KMUHelper",
        "scope": "read",
        "user_id": randint(100000,999999),
        "return_url": kmuhelperurl+"/kmuhelper/wc/auth/end",
        "callback_url": kmuhelperurl+"/kmuhelper/wc/auth/key"
    }
    query_string = urlencode(params)
    if not "https://" in shopurl and not "http://" in shopurl:
        shopurl = "https://"+shopurl

    return redirect("%s%s?%s" % (shopurl, '/wc-auth/v1/authorize', query_string))


@login_required(login_url="/admin/login")
def wc_import_products(request):
    count = WooCommerce.product_import()
    messages.success(request, (('{} neue Produkte' if count != 1 else 'Ein neues Produkt')+' von WooCommerce importiert!').format(count))
    return redirect("/admin/kmuhelper/produkt/")

@login_required(login_url="/admin/login")
def wc_import_customers(request):
    count = WooCommerce.customer_import()
    messages.success(request, (('{} neue Kunden' if count != 1 else 'Ein neuer Kunde')+' von WooCommerce importiert!').format(count))
    return redirect("/admin/kmuhelper/kunde/")

@login_required(login_url="/admin/login")
def wc_import_categories(request):
    count = WooCommerce.category_import()
    messages.success(request, (('{} neue Kategorien' if count != 1 else 'Eine neue Kategorie')+' von WooCommerce importiert!').format(count))
    return redirect("/admin/kmuhelper/kategorie/")

@login_required(login_url="/admin/login")
def wc_import_orders(request):
    count = WooCommerce.order_import()
    messages.success(request, (('{} neue Bestellungen' if count != 1 else 'Eine neue Bestellung')+' von WooCommerce importiert!').format(count))
    return redirect("/admin/kmuhelper/bestellung/")


@login_required(login_url="/admin/login")
def wc_update_product(request, object_id):
    product = WooCommerce.product_update(Produkt.objects.get(id=int(object_id)))
    messages.success(request, "Produkt aktualisiert: "+str(product))
    return redirect("/admin/kmuhelper/produkt/"+object_id)

@login_required(login_url="/admin/login")
def wc_update_customer(request, object_id):
    customer = WooCommerce.customer_update(Kunde.objects.get(id=int(object_id)))
    messages.success(request, "Kunde aktualisiert: "+str(customer))
    return redirect("/admin/kmuhelper/kunde/"+object_id)

@login_required(login_url="/admin/login")
def wc_update_category(request, object_id):
    category = WooCommerce.category_update(Kategorie.objects.get(id=int(object_id)))
    messages.success(request, "Kategorie aktualisiert: "+str(category))
    return redirect("/admin/kmuhelper/kategorie/"+object_id)

@login_required(login_url="/admin/login")
def wc_update_order(request, object_id):
    order = WooCommerce.order_update(Bestellung.objects.get(id=int(object_id)))
    messages.success(request, "Bestellung aktualisiert: "+str(order))
    return redirect("/admin/kmuhelper/bestellung/"+object_id)


@csrf_exempt
def wc_webhooks(request):
    if "x-wc-webhook-topic" in request.headers and "x-wc-webhook-source" in request.headers:
        erwartete_url = Geheime_Einstellung.objects.get(id="wc-url").inhalt.lstrip("https://").lstrip("http://").split("/")[0]
        erhaltene_url = request.headers["x-wc-webhook-source"].lstrip("https://").lstrip("http://").split("/")[0]
        if erhaltene_url == erwartete_url:
            print("[KMUHelper] - WooCommerce Webhook erhalten...")
            topic = request.headers["x-wc-webhook-topic"]
            obj = loadjson(request.body)
            if topic == "product.updated" or topic == "product.created":
                if Produkt.objects.filter(woocommerceid=obj["id"]).exists():
                    WooCommerce.product_update(Produkt.objects.get(woocommerceid=obj["id"]), obj)
                else:
                    WooCommerce.product_create(obj)
            elif topic == "customer.updated" or topic == "customer.created":
                if Kunde.objects.filter(woocommerceid=obj["id"]).exists():
                    WooCommerce.customer_update(Kunde.objects.get(woocommerceid=obj["id"]), obj)
                else:
                    WooCommerce.customer_create(obj)
            elif topic == "order.updated" or topic == "order.created":
                if Bestellung.objects.filter(woocommerceid=obj["id"]).exists():
                    WooCommerce.order_update(Bestellung.objects.get(woocommerceid=obj["id"]), obj)
                else:
                    WooCommerce.order_create(obj)
        else:
            print("[KMUHelper] - WooCommerce Webhook von einer falschen Webseite ignoriert! - Erwartet: '"+erwartete_url+"' - Erhalten: '"+erhaltene_url+"'")
            return HttpResponseBadRequest("Zugriff nicht gestattet!")
    return HttpResponse("Erfolgreich erhalten!")


@login_required(login_url="/admin/login")
def lieferung_einlagern(request, object_id):
    if Lieferung.objects.get(id=int(object_id)).einlagern():
        messages.success(request, "Lieferung eingelagert!")
    else:
        messages.error(request, "Lieferung konnte nicht eingelagert werden!")
    return redirect("/admin/kmuhelper/lieferung/"+object_id)

@login_required(login_url="/admin/login")
def kunde_email_registriert(request, object_id):
    Kunde.objects.get(id=int(object_id)).send_register_mail()
    messages.success(request, "Registrierungsmail gesendet!")
    return redirect("/admin/kmuhelper/kunde/"+object_id)


@login_required(login_url="/admin/login")
def bestellung_pdf_ansehen(request, object_id):
    obj = Bestellung.objects.get(id=int(object_id))
    lieferschein = bool("lieferschein" in dict(request.GET))
    digital = not bool("druck" in dict(request.GET))
    if obj:
        pdf = obj.get_pdf(lieferschein=lieferschein, digital=digital)
        return pdf
    else:
        messages.error(request, "Bestellung wurde nicht gefunden!")
        return redirect("/admin/kmuhelper/bestellung")

@login_required(login_url="/admin/login")
def bestellung_pdf_an_kunden_senden(request, object_id):
    obj = Bestellung.objects.get(id=int(object_id))
    if obj:
        if obj.send_pdf_rechnung_to_customer():
            messages.success(request, "Rechnung an Kunden gesendet!")
        else:
            messages.error(request, "Rechnung konnte nicht an Kunden gesendet werden!")
    return redirect("/admin/kmuhelper/bestellung/"+object_id)




##### Kunden-Entpunkte

def kunde_rechnung_ansehen(request, order_id, order_key):
    obj = Bestellung.objects.get(id=int(order_id))
    digital = not bool("druck" in dict(request.GET))
    if obj:
        if obj.order_key == order_key:
            return obj.get_pdf_rechnung(digital=digital)
        else:
            return HttpResponse("Der Bestellungsschlüssel dieser Bestellung ist falsch!")
    else:
        return HttpResponse("Bestellung wurde nicht gefunden")
