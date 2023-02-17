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

from django.utils.translation import gettext_lazy, gettext, ngettext

from kmuhelper import settings
from kmuhelper.decorators import require_object
from kmuhelper.modules.main.models import Product, Customer, ProductCategory, Order
from kmuhelper.modules.integrations.woocommerce.api import WooCommerce
from kmuhelper.modules.integrations.woocommerce.utils import is_connected
from kmuhelper.utils import render_error

_ = gettext_lazy

def log(string, *args):
    print("[deep_pink4][KMUHelper][/] -", string, *args)
 
NOT_CONNECTED_ERRMSG = _("WooCommerce wurde scheinbar nicht richtig verbunden!")

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
        messages.success(request, gettext("WooCommerce erfolgreich verbunden!"))
    else:
        messages.error(request, gettext("WooCommerce konnte nicht verbunden werden!"))
    return redirect(reverse('kmuhelper:settings'))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.change_setting")
def wc_auth_start(request):
    shopurl = settings.get_db_setting("wc-url", "Bestätigt")

    if not shopurl or not shopurl.startswith("http"):
        messages.error(request, gettext("Please enter a valid WooCommerce URL in the settings, beginning with 'http'!"))
        return redirect(reverse('kmuhelper:settings'))

    kmuhelperurl = request.get_host()
    params = {
        "app_name": "KMUHelper",
        "scope": "read",
        "user_id": randint(100000, 999999),
        "return_url": kmuhelperurl + reverse("kmuhelper:wc-auth-end"),
        "callback_url": kmuhelperurl + reverse("kmuhelper:wc-auth-key")
    }
    query_string = urlencode(params)

    url = "%s%s?%s" % (shopurl, '/wc-auth/v1/authorize', query_string)
    return redirect(url)


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.add_product")
def wc_import_products(request):
    if not is_connected():
        messages.error(
            request, NOT_CONNECTED_ERRMSG)
    else:
        count = WooCommerce.product_import()
        messages.success(request, ngettext(
            '%d new product has been imported from WooCommerce!',
            '%d new products have been imported from WooCommerce!',
            count
        ))
    return redirect(reverse("admin:kmuhelper_product_changelist"))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.add_customer")
def wc_import_customers(request):
    if not is_connected():
        messages.error(
            request, NOT_CONNECTED_ERRMSG)
    else:
        count = WooCommerce.customer_import()
        messages.success(request, ngettext(
            '%d new customer has been imported from WooCommerce!',
            '%d new customers have been imported from WooCommerce!',
            count
        ))
    return redirect(reverse("admin:kmuhelper_customer_changelist"))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.add_productcategory")
def wc_import_categories(request):
    if not is_connected():
        messages.error(
            request, NOT_CONNECTED_ERRMSG)
    else:
        count = WooCommerce.category_import()
        messages.success(request, ngettext(
            '%d new product category has been imported from WooCommerce!',
            '%d new product categories have been imported from WooCommerce!',
            count
        ))
    return redirect(reverse("admin:kmuhelper_productcategory_changelist"))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.add_order")
def wc_import_orders(request):
    if not is_connected():
        messages.error(
            request, NOT_CONNECTED_ERRMSG)
    else:
        count = WooCommerce.order_import()
        messages.success(request, ngettext(
            '%d new order has been imported from WooCommerce!',
            '%d new orders have been imported from WooCommerce!',
            count
        ))
    return redirect(reverse("admin:kmuhelper_order_changelist"))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.change_product")
@require_object(Product)
def wc_update_product(request, obj):
    if not is_connected():
        messages.error(
            request, NOT_CONNECTED_ERRMSG)
    else:
        product = WooCommerce.product_update(obj)
        messages.success(request, gettext("Product '%s' updated!") % str(product))
    return redirect(reverse("admin:kmuhelper_product_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.change_customer")
@require_object(Customer)
def wc_update_customer(request, obj):
    if not is_connected():
        messages.error(
            request, NOT_CONNECTED_ERRMSG)
    else:
        customer = WooCommerce.customer_update(obj)
        messages.success(request, gettext("Customer '%s' updated!") % str(customer))
    return redirect(reverse("admin:kmuhelper_customer_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.change_productcategory")
@require_object(ProductCategory)
def wc_update_category(request, obj):
    if not is_connected():
        messages.error(
            request, NOT_CONNECTED_ERRMSG)
    else:
        category = WooCommerce.category_update(obj)
        messages.success(request, gettext("Product category '%s' updated!") % str(category))
    return redirect(reverse("admin:kmuhelper_productcategory_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.change_order")
@require_object(Order)
def wc_update_order(request, obj):
    if not is_connected():
        messages.error(
            request, NOT_CONNECTED_ERRMSG)
    else:
        order = WooCommerce.order_update(obj)
        messages.success(request, gettext("Order '%s' updated!") % str(order))
    return redirect(reverse("admin:kmuhelper_order_change", args=[obj.pk]))


@csrf_exempt
def wc_webhooks(request):
    if request.method != "POST":
        messages.warning(request, gettext("This endpoint is only available via POST and not meant to be used by humans!"))
        return render_error(request, status=405)

    if not ("x-wc-webhook-topic" in request.headers and "x-wc-webhook-source" in request.headers):
        return JsonResponse({
            "accepted": True,
            "info": "Request was accepted but ignored because it doesn't contain any usable info!"
        }, status=202)

    stored_url = settings.get_secret_db_setting("wc-url").lstrip(
        "https://").lstrip("http://").split("/")[0]
    received_url = request.headers["x-wc-webhook-source"].lstrip(
        "https://").lstrip("http://").split("/")[0]

    if not received_url == stored_url:
        log("[orange_red1]WooCommerce Webhook ignored (unexpected domain)![/] " +
            "- Expected:", stored_url, "- Received:", received_url)
        return JsonResponse({
            "accepted": False,
            "reason": "Unknown domain!",
        }, status=403)

    ## TODO: Check if the webhook is valid (e.g. by checking the signature)
    ## https://woocommerce.github.io/woocommerce-rest-api-docs/#webhooks

    log("WooCommerce Webhook received...")

    topic = request.headers["x-wc-webhook-topic"]
    obj = json.loads(request.body)
    if topic in ("product.updated", "product.created"):
        if Product.objects.filter(woocommerceid=obj["id"]).exists():
            WooCommerce.product_update(
                Product.objects.get(woocommerceid=obj["id"]), obj)
        else:
            WooCommerce.product_create(obj)
    elif topic == "product.deleted":
        if Product.objects.filter(woocommerceid=obj["id"]).exists():
            product = Product.objects.get(woocommerceid=obj["id"])
            product.woocommerceid = 0
            product.save()
    elif topic in ("customer.updated", "customer.created"):
        if Customer.objects.filter(woocommerceid=obj["id"]).exists():
            WooCommerce.customer_update(
                Customer.objects.get(woocommerceid=obj["id"]), obj)
        else:
            WooCommerce.customer_create(obj)
    elif topic == "customer.deleted":
        if Customer.objects.filter(woocommerceid=obj["id"]).exists():
            customer = Customer.objects.get(woocommerceid=obj["id"])
            customer.woocommerceid = 0
            customer.save()
    elif topic in ("order.updated", "order.created"):
        if Order.objects.filter(woocommerceid=obj["id"]).exists():
            WooCommerce.order_update(
                Order.objects.get(woocommerceid=obj["id"]), obj)
        else:
            WooCommerce.order_create(obj)
    elif topic == "order.deleted":
        if Order.objects.filter(woocommerceid=obj["id"]).exists():
            order = Order.objects.get(woocommerceid=obj["id"])
            order.woocommerceid = 0
            order.save()
    else:
        log(f"[orange_red1]Unbekanntes Thema: '{topic}'")

    return JsonResponse({"accepted": True})
