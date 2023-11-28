import json
from random import randint
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy, gettext, ngettext
from django.views.decorators.csrf import csrf_exempt
from rich import print

from kmuhelper import settings
from kmuhelper.decorators import (
    require_object,
    require_all_kmuhelper_perms,
    require_any_kmuhelper_perms,
)
from kmuhelper.modules.integrations.woocommerce.api import WooCommerce
from kmuhelper.modules.integrations.woocommerce.forms import WooCommerceSettingsForm
from kmuhelper.modules.integrations.woocommerce.utils import (
    is_connected,
    base64_hmac_sha256,
    random_secret,
    test_wc_url,
)
from kmuhelper.modules.main.models import Product, Customer, ProductCategory, Order
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

        storedomain = storeurl.lstrip("https://").lstrip("http://").split("/")[0]
        saveddomain = savedurl.lstrip("https://").lstrip("http://").split("/")[0]

        if saveddomain == storedomain:
            settings.set_secret_db_setting("wc-url", storeurl)
            settings.set_secret_db_setting("wc-consumer_key", data["consumer_key"])
            settings.set_secret_db_setting(
                "wc-consumer_secret", data["consumer_secret"]
            )

            return JsonResponse({"success": True}, status=200)

        return JsonResponse({"success": False, "reason": "Unknown URL!"}, status=401)
    except KeyError:
        return JsonResponse({"success": False, "reason": "Useless data!"}, status=400)


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_any_kmuhelper_perms()
def wc_auth_end(request):
    if request.GET.get("success") == "1":
        messages.success(request, gettext("WooCommerce erfolgreich verbunden!"))
    else:
        messages.error(request, gettext("WooCommerce konnte nicht verbunden werden!"))
    return redirect(reverse("kmuhelper:wc-settings"))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["change_setting"])
def wc_auth_start(request):
    shopurl = settings.get_db_setting("wc-url", "Bestätigt")

    if not shopurl or not shopurl.startswith("http"):
        messages.error(
            request,
            gettext("Please enter a valid WooCommerce URL, beginning with 'https://'!"),
        )
        return redirect(reverse("kmuhelper:wc-settings"))

    kmuhelperurl = request.get_host()
    params = {
        "app_name": "KMUHelper",
        "scope": "read",
        "user_id": randint(100000, 999999),
        "return_url": kmuhelperurl + reverse("kmuhelper:wc-auth-end"),
        "callback_url": kmuhelperurl + reverse("kmuhelper:wc-auth-key"),
    }
    query_string = urlencode(params)

    url = "%s%s?%s" % (shopurl, "/wc-auth/v1/authorize", query_string)
    return redirect(url)


# Note: Change permission is required because the view redirects to the settings page
@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["change_setting"])
def wc_system_status(request):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        status = WooCommerce.get_system_status()

        if status:
            messages.success(request, _("WooCommerce is connected and works!"))
        else:
            messages.error(request, _("WooCommerce doesn't seem to work!"))
    return redirect(reverse("kmuhelper:wc-settings"))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["add_product"])
def wc_import_products(request):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        count = WooCommerce.product_import()
        messages.success(
            request,
            ngettext(
                "%d new product has been imported from WooCommerce!",
                "%d new products have been imported from WooCommerce!",
                count,
            )
            % count,
        )
    return redirect(reverse("admin:kmuhelper_product_changelist"))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["add_customer"])
def wc_import_customers(request):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        count = WooCommerce.customer_import()
        messages.success(
            request,
            ngettext(
                "%d new customer has been imported from WooCommerce!",
                "%d new customers have been imported from WooCommerce!",
                count,
            )
            % count,
        )
    return redirect(reverse("admin:kmuhelper_customer_changelist"))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["add_productcategory"])
def wc_import_categories(request):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        count = WooCommerce.category_import()
        messages.success(
            request,
            ngettext(
                "%d new product category has been imported from WooCommerce!",
                "%d new product categories have been imported from WooCommerce!",
                count,
            )
            % count,
        )
    return redirect(reverse("admin:kmuhelper_productcategory_changelist"))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["add_order"])
def wc_import_orders(request):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        count = WooCommerce.order_import()
        messages.success(
            request,
            ngettext(
                "%d new order has been imported from WooCommerce!",
                "%d new orders have been imported from WooCommerce!",
                count,
            )
            % count,
        )
    return redirect(reverse("admin:kmuhelper_order_changelist"))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["change_product"])
@require_object(Product)
def wc_update_product(request, obj):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        product = WooCommerce.product_update(obj)
        messages.success(request, gettext("Product '%s' updated!") % str(product))
    return redirect(reverse("admin:kmuhelper_product_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["change_customer"])
@require_object(Customer)
def wc_update_customer(request, obj):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        customer = WooCommerce.customer_update(obj)
        messages.success(request, gettext("Customer '%s' updated!") % str(customer))
    return redirect(reverse("admin:kmuhelper_customer_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["change_productcategory"])
@require_object(ProductCategory)
def wc_update_category(request, obj):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        category = WooCommerce.category_update(obj)
        messages.success(
            request, gettext("Product category '%s' updated!") % str(category)
        )
    return redirect(reverse("admin:kmuhelper_productcategory_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["change_order"])
@require_object(Order)
def wc_update_order(request, obj):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        order = WooCommerce.order_update(obj)
        messages.success(request, gettext("Order '%s' updated!") % str(order))
    return redirect(reverse("admin:kmuhelper_order_change", args=[obj.pk]))


@csrf_exempt
def wc_webhooks(request):
    "Endpoint for WooCommerce webhooks"

    # 1. Check request method

    if request.method != "POST":
        messages.warning(
            request,
            gettext(
                "This endpoint is only available via POST and not meant to be used by humans!"
            ),
        )
        return render_error(request, status=405)

    # 2. Check request source

    if not (
        "x-wc-webhook-topic" in request.headers
        and "x-wc-webhook-source" in request.headers
    ):
        log(
            "[orange_red1]WooCommerce Webhook accepted but ignored (no usable headers)![/] "
            + "(Might be a test request from WooCommerce)"
        )
        return JsonResponse(
            {
                "accepted": True,
                "info": "Request was accepted but ignored because it doesn't contain any usable info!",
            },
            status=200,
        )

    stored_url = (
        settings.get_secret_db_setting("wc-url")
        .lstrip("https://")
        .lstrip("http://")
        .split("/")[0]
    )
    received_url = (
        request.headers["x-wc-webhook-source"]
        .lstrip("https://")
        .lstrip("http://")
        .split("/")[0]
    )

    if not received_url == stored_url:
        log(
            "[orange_red1]WooCommerce Webhook rejected (unexpected domain)![/] "
            + "- Expected:",
            stored_url,
            "- Received:",
            received_url,
        )
        return JsonResponse(
            {
                "accepted": False,
                "reason": "Unknown domain!",
            },
            status=403,
        )

    # 3. Check request signature

    if not ("x-wc-webhook-signature" in request.headers):
        log("[orange_red1]WooCommerce Webhook rejected (no signature)![/]")
        return JsonResponse(
            {
                "accepted": False,
                "reason": "Invalid signature!",
            },
            status=403,
        )

    secret = settings.get_db_setting("wc-webhook-secret")

    if secret:
        received_signature = bytes(
            request.headers["x-wc-webhook-signature"], encoding="utf-8"
        )
        expected_signature = base64_hmac_sha256(str(secret).encode(), request.body)

        if received_signature == expected_signature:
            log("[green]WooCommerce Webhook signature check successful![/]")
        else:
            log(
                "[orange_red1]WooCommerce Webhook signature check failed![/] "
                + "- Expected:",
                expected_signature,
                "- Received:",
                received_signature,
            )
            return JsonResponse(
                {
                    "accepted": False,
                    "reason": "Signature mismatch!",
                },
                status=403,
            )

    else:
        log(
            "[orange_red1]Skipped WooCommerce Webhook signature check (no secret available)![/]"
        )

    # Do stuff

    log("WooCommerce Webhook is being processed...")

    topic = request.headers["x-wc-webhook-topic"]
    obj = json.loads(request.body)
    if topic in ("product.updated", "product.created"):
        if Product.objects.filter(woocommerceid=obj["id"]).exists():
            WooCommerce.product_update(
                Product.objects.get(woocommerceid=obj["id"]), obj
            )
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
                Customer.objects.get(woocommerceid=obj["id"]), obj
            )
        else:
            WooCommerce.customer_create(obj)
    elif topic == "customer.deleted":
        if Customer.objects.filter(woocommerceid=obj["id"]).exists():
            customer = Customer.objects.get(woocommerceid=obj["id"])
            customer.woocommerceid = 0
            customer.save()
    elif topic in ("order.updated", "order.created"):
        if Order.objects.filter(woocommerceid=obj["id"]).exists():
            WooCommerce.order_update(Order.objects.get(woocommerceid=obj["id"]), obj)
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


# Settings


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["change_setting"])
def wc_settings(request):
    if request.method == "POST":
        form = WooCommerceSettingsForm(request.POST)
        if form.is_valid():
            form.save_settings()
            messages.success(request, gettext("Einstellungen gespeichert!"))
            # Redirect to prevent resending the form on reload
            return redirect("kmuhelper:wc-settings")
    else:
        form = WooCommerceSettingsForm()

    secreturl = settings.get_secret_db_setting("wc-url", None)
    url = settings.get_db_setting("wc-url", None)

    return render(
        request,
        "kmuhelper/integrations/woocommerce/settings.html",
        {
            "form": form,
            "has_permission": True,
            "random_secret": random_secret(),
            "kmuhelper_url": request.get_host(),
            "wc_url": secreturl,
            "is_connected": is_connected(),
            "is_url_valid": test_wc_url(url),
        },
    )
