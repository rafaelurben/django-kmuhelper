import json

from urllib.parse import urlencode
from random import randint
from rich import print

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt

from kmuhelper import settings
from kmuhelper.decorators import require_object
from kmuhelper.modules.main.models import Produkt, Kunde, Kategorie, Bestellung
from kmuhelper.modules.integrations.woocommerce.api import WooCommerce
from kmuhelper.modules.integrations.woocommerce.utils import is_connected
from kmuhelper.utils import render_error


def log(string, *args):
    print("[deep_pink4][KMUHelper][/] -", string, *args)

#####


@csrf_exempt
def wc_auth_key(request):
    """Endpoint for receiving the keys from WooCommerce"""

    try:
        data = json.loads(request.body)
        storeurl = request.headers.get("user-agent").split(";")[1].lstrip()
        savedurl = settings.get_db_setting("wc-url")

        storedomain = storeurl.lstrip(
            "https://").lstrip("http://").split("/")[0]
        saveddomain = savedurl.lstrip(
            "https://").lstrip("http://").split("/")[0]

        if saveddomain == storedomain:
            settings.set_secret_db_setting(
                "wc-url",
                storeurl)
            settings.set_secret_db_setting(
                "wc-consumer_key",
                data["consumer_key"])
            settings.set_secret_db_setting(
                "wc-consumer_secret",
                data["consumer_secret"])

            settings.set_db_setting(
                "wc-url",
                "Bestätigt: " + storeurl +
                " (Änderungen werden nur nach erneutem Verbinden angewendet!)")
            return JsonResponse({"success": True}, status=200)

        return JsonResponse({"success": False, "reason": "Unknown URL!"}, status=401)
    except KeyError:
        return JsonResponse({"success": False, "reason": "Useless data!"}, status=400)


@login_required(login_url=reverse_lazy("admin:login"))
def wc_auth_end(request):
    if request.GET.get("success") == "1":
        messages.success(request, "WooCommerce erfolgreich verbunden!")
    else:
        messages.error(request, "WooCommerce konnte nicht verbunden werden!")
    return redirect(reverse('admin:kmuhelper_einstellung_changelist'))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.change_einstellung")
def wc_auth_start(request):
    shopurl = settings.get_db_setting("wc-url", "Bestätigt")

    if "Bestätigt" in shopurl or not shopurl:
        messages.error(
            request, "Bitte gib zuerst eine gültige Url ein, bevor du WooCommerce (neu) verbinden kannst!")
        return redirect(reverse('admin:kmuhelper_einstellung_changelist'))

    kmuhelperurl = request.get_host()
    params = {
        "app_name": "KMUHelper",
        "scope": "read",
        "user_id": randint(100000, 999999),
        "return_url": kmuhelperurl + reverse("kmuhelper:wc-auth-end"),
        "callback_url": kmuhelperurl + reverse("kmuhelper:wc-auth-key")
    }
    query_string = urlencode(params)

    if "https://" not in shopurl and "http://" not in shopurl:
        shopurl = "https://" + shopurl

    url = "%s%s?%s" % (shopurl, '/wc-auth/v1/authorize', query_string)
    return redirect(url)


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.add_produkt")
def wc_import_products(request):
    if not is_connected():
        messages.error(
            request, "WooCommerce wurde scheinbar nicht richtig verbunden!")
    else:
        count = WooCommerce.product_import()
        messages.success(request, (('{} neue Produkte' if count !=
                                    1 else 'Ein neues Produkt') + ' von WooCommerce importiert!').format(count))
    return redirect(reverse("admin:kmuhelper_produkt_changelist"))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.add_kunde")
def wc_import_customers(request):
    if not is_connected():
        messages.error(
            request, "WooCommerce wurde scheinbar nicht richtig verbunden!")
    else:
        count = WooCommerce.customer_import()
        messages.success(request, (('{} neue Kunden' if count !=
                                    1 else 'Ein neuer Kunde') + ' von WooCommerce importiert!').format(count))
    return redirect(reverse("admin:kmuhelper_kunde_changelist"))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.add_kategorie")
def wc_import_categories(request):
    if not is_connected():
        messages.error(
            request, "WooCommerce wurde scheinbar nicht richtig verbunden!")
    else:
        count = WooCommerce.category_import()
        messages.success(request, (('{} neue Kategorien' if count !=
                                    1 else 'Eine neue Kategorie') + ' von WooCommerce importiert!').format(count))
    return redirect(reverse("admin:kmuhelper_kategorie_changelist"))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.add_bestellung")
def wc_import_orders(request):
    if not is_connected():
        messages.error(
            request, "WooCommerce wurde scheinbar nicht richtig verbunden!")
    else:
        count = WooCommerce.order_import()
        messages.success(request, (('{} neue Bestellungen' if count !=
                                    1 else 'Eine neue Bestellung') + ' von WooCommerce importiert!').format(count))
    return redirect(reverse("admin:kmuhelper_bestellung_changelist"))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.change_produkt")
@require_object(Produkt)
def wc_update_product(request, obj):
    if not is_connected():
        messages.error(
            request, "WooCommerce wurde scheinbar nicht richtig verbunden!")
    else:
        product = WooCommerce.product_update(obj)
        messages.success(request, "Produkt aktualisiert: " + str(product))
    return redirect(reverse("admin:kmuhelper_produkt_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.change_kunde")
@require_object(Kunde)
def wc_update_customer(request, obj):
    if not is_connected():
        messages.error(
            request, "WooCommerce wurde scheinbar nicht richtig verbunden!")
    else:
        customer = WooCommerce.customer_update(obj)
        messages.success(request, "Kunde aktualisiert: " + str(customer))
    return redirect(reverse("admin:kmuhelper_kunde_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.change_kategorie")
@require_object(Kategorie)
def wc_update_category(request, obj):
    if not is_connected():
        messages.error(
            request, "WooCommerce wurde scheinbar nicht richtig verbunden!")
    else:
        category = WooCommerce.category_update(obj)
        messages.success(request, "Kategorie aktualisiert: " + str(category))
    return redirect(reverse("admin:kmuhelper_kategorie_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.change_bestellung")
@require_object(Bestellung)
def wc_update_order(request, obj):
    if not is_connected():
        messages.error(
            request, "WooCommerce wurde scheinbar nicht richtig verbunden!")
    else:
        order = WooCommerce.order_update(obj)
        messages.success(request, "Bestellung aktualisiert: " + str(order))
    return redirect(reverse("admin:kmuhelper_bestellung_change", args=[obj.pk]))


@csrf_exempt
def wc_webhooks(request):
    if request.method != "POST":
        messages.warning(request, "Dieser Endpunkt ist für Bots reserviert!")
        return render_error(request, status=405)

    if not ("x-wc-webhook-topic" in request.headers and "x-wc-webhook-source" in request.headers):
        return JsonResponse({
            "accepted": True,
            "info": "Request was accepted but ignored because it doesn't contain any usable info!"
        }, status=202)

    erwartete_url = settings.get_secret_db_setting("wc-url").lstrip(
        "https://").lstrip("http://").split("/")[0]
    erhaltene_url = request.headers["x-wc-webhook-source"].lstrip(
        "https://").lstrip("http://").split("/")[0]

    if not erhaltene_url == erwartete_url:
        log("[orange_red1]WooCommerce Webhook von einer falschen Webseite ignoriert![/] " +
            "- Erwartet:", erwartete_url, "- Erhalten:", erhaltene_url)
        return JsonResponse({
            "accepted": False,
            "reason": "Unknown domain!",
        }, status=403)

    log("WooCommerce Webhook erhalten...")

    topic = request.headers["x-wc-webhook-topic"]
    obj = json.loads(request.body)
    if topic in ("product.updated", "product.created"):
        if Produkt.objects.filter(woocommerceid=obj["id"]).exists():
            WooCommerce.product_update(
                Produkt.objects.get(woocommerceid=obj["id"]), obj)
        else:
            WooCommerce.product_create(obj)
    elif topic == "product.deleted":
        if Produkt.objects.filter(woocommerceid=obj["id"]).exists():
            product = Produkt.objects.get(woocommerceid=obj["id"])
            product.woocommerceid = 0
            product.save()
    elif topic in ("customer.updated", "customer.created"):
        if Kunde.objects.filter(woocommerceid=obj["id"]).exists():
            WooCommerce.customer_update(
                Kunde.objects.get(woocommerceid=obj["id"]), obj)
        else:
            WooCommerce.customer_create(obj)
    elif topic == "customer.deleted":
        if Kunde.objects.filter(woocommerceid=obj["id"]).exists():
            customer = Kunde.objects.get(woocommerceid=obj["id"])
            customer.woocommerceid = 0
            customer.save()
    elif topic in ("order.updated", "order.created"):
        if Bestellung.objects.filter(woocommerceid=obj["id"]).exists():
            WooCommerce.order_update(
                Bestellung.objects.get(woocommerceid=obj["id"]), obj)
        else:
            WooCommerce.order_create(obj)
    elif topic == "order.deleted":
        if Bestellung.objects.filter(woocommerceid=obj["id"]).exists():
            order = Bestellung.objects.get(woocommerceid=obj["id"])
            order.woocommerceid = 0
            order.save()
    else:
        log(f"[orange_red1]Unbekanntes Thema: '{topic}'")

    return JsonResponse({"accepted": True})
