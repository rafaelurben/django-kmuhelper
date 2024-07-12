import json
from random import randint
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.html import format_html
from django.utils.translation import gettext_lazy, gettext
from django.views.decorators.csrf import csrf_exempt
from rich import print

from kmuhelper import settings
from kmuhelper.decorators import (
    require_object,
    require_all_kmuhelper_perms,
    require_any_kmuhelper_perms,
    confirm_action,
)
from kmuhelper.modules.integrations.woocommerce.api import (
    WCGeneralAPI,
    WCCustomersAPI,
    WCOrdersAPI,
    WCProductsAPI,
    WCProductCategoriesAPI,
)
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
    shopurl = settings.get_db_setting("wc-url", None)

    if not shopurl or not shopurl.startswith("http"):
        messages.error(
            request,
            gettext("Please enter a valid WooCommerce URL, beginning with 'https://'!"),
        )
        return redirect(reverse("kmuhelper:wc-settings"))

    if not request.is_secure():
        # WooCommerce only accepts callback_urls via SSL
        messages.error(request, gettext("Setting up WooCommerce is only possible when connected via HTTPS!"))
        return redirect(reverse("kmuhelper:wc-settings"))

    params = {
        "app_name": "KMUHelper",
        "scope": "read",
        "user_id": randint(100000, 999999),
        "return_url": request.build_absolute_uri(reverse("kmuhelper:wc-auth-end")),
        "callback_url": request.build_absolute_uri(reverse("kmuhelper:wc-auth-key")),
    }
    query_string = urlencode(params)

    url = "%s%s?%s" % (shopurl, "/wc-auth/v1/authorize", query_string)
    return redirect(url)


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["change_setting"])
@confirm_action(_("Delete stored API credentials"))
def wc_auth_clear(request):
    wc_url = settings.get_secret_db_setting("wc-url")
    wc_consumer_key = settings.get_secret_db_setting("wc-consumer_key")

    if not wc_url or not wc_consumer_key:
        messages.warning(request, gettext("WooCommerce was not set up."))
    else:
        api_keys_url = (
            wc_url + "/wp-admin/admin.php?page=wc-settings&tab=advanced&section=keys"
        )

        settings.set_secret_db_setting("wc-url", "")
        settings.set_secret_db_setting("wc-consumer_key", "")
        settings.set_secret_db_setting("wc-consumer_secret", "")

        messages.success(
            request,
            format_html(
                '{} <a target="_blank" href="{}">{}</a> (Consumer key: {})',
                gettext("Credentials deleted! Please revoke your API key manually:"),
                api_keys_url,
                gettext("click here"),
                wc_consumer_key,
            ),
        )
    return redirect(reverse("kmuhelper:wc-settings"))


# Note: Change permission is required because the view redirects to the settings page
@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["change_setting"])
def wc_system_status(request):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        status = WCGeneralAPI().get_system_status()

        if status:
            messages.success(request, _("WooCommerce is connected and works!"))
        else:
            messages.error(request, _("WooCommerce doesn't seem to work!"))
    return redirect(reverse("kmuhelper:wc-settings"))


# Note: Change permission is required because the view redirects to the settings page
@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["change_setting"])
def wc_webhooks_status(request):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        current_host = "https://" + request.get_host()

        if current_host.endswith("localhost"):
            messages.error(
                request, gettext("Cannot check webhooks while on localhost!")
            )
            return redirect(reverse("kmuhelper:wc-settings"))

        delivery_url = current_host + reverse("kmuhelper:wc-webhooks")
        success, topics = WCGeneralAPI().get_enabled_webhooks_topics(delivery_url)

        if success:
            if topics:
                messages.success(
                    request,
                    gettext("%(count)d topic(s) have been set up correctly: %(topics)s")
                    % {"count": len(topics), "topics": ",".join(topics)},
                )
            else:
                messages.warning(request, _("No correctly setup webhooks detected!"))
        else:
            messages.error(request, _("Checking webhook status failed!"))
    return redirect(reverse("kmuhelper:wc-settings"))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["add_product"])
def wc_import_products(request):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        WCProductsAPI().import_all_objects_from_api(request=request)
    return redirect(reverse("admin:kmuhelper_product_changelist"))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["add_customer"])
def wc_import_customers(request):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        WCCustomersAPI().import_all_objects_from_api(request=request)
    return redirect(reverse("admin:kmuhelper_customer_changelist"))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["add_productcategory"])
def wc_import_categories(request):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        WCProductCategoriesAPI().import_all_objects_from_api(request=request)
    return redirect(reverse("admin:kmuhelper_productcategory_changelist"))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["add_order"])
def wc_import_orders(request):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        WCOrdersAPI().import_all_objects_from_api(request=request)
    return redirect(reverse("admin:kmuhelper_order_changelist"))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["change_product"])
@require_object(Product)
def wc_update_product(request, obj):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        try:
            WCProductsAPI().update_object_from_api(obj)
            messages.success(request, gettext("Product '%s' updated!") % str(obj))
        except Exception as e:
            messages.error(
                request,
                gettext("Product '%(name)s' update failed! %(error_msg)s")
                % {"name": str(obj), "error_msg": str(e)},
            )
    return redirect(reverse("admin:kmuhelper_product_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["change_customer"])
@require_object(Customer)
def wc_update_customer(request, obj):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        try:
            WCCustomersAPI().update_object_from_api(obj)
            messages.success(request, gettext("Customer '%s' updated!") % str(obj))
        except Exception as e:
            messages.error(
                request,
                gettext("Customer '%(name)s' update failed! %(error_msg)s")
                % {"name": str(obj), "error_msg": str(e)},
            )
    return redirect(reverse("admin:kmuhelper_customer_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["change_productcategory"])
@require_object(ProductCategory)
def wc_update_category(request, obj):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        try:
            WCProductCategoriesAPI().update_object_from_api(obj)
            messages.success(
                request, gettext("Product category '%s' updated!") % str(obj)
            )
        except Exception as e:
            messages.error(
                request,
                gettext("Product category '%(name)s' update failed! %(error_msg)s")
                % {"name": str(obj), "error_msg": str(e)},
            )
    return redirect(reverse("admin:kmuhelper_productcategory_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["change_order"])
@require_object(Order)
def wc_update_order(request, obj):
    if not is_connected():
        messages.error(request, NOT_CONNECTED_ERRMSG)
    else:
        try:
            WCOrdersAPI().update_object_from_api(obj)
            messages.success(request, gettext("Order '%s' updated!") % str(obj))
        except Exception as e:
            messages.error(
                request,
                gettext("Order '%(name)s' update failed! %(error_msg)s")
                % {"name": str(obj), "error_msg": str(e)},
            )
    return redirect(reverse("admin:kmuhelper_order_change", args=[obj.pk]))


@csrf_exempt
def wc_webhooks(request):
    """Endpoint for WooCommerce webhooks"""

    # 1. Check request method

    if request.method != "POST":
        messages.warning(
            request,
            gettext(
                "This endpoint is only available via POST and not meant to be used by humans!"
            ),
        )
        return render_error(request, status=405)

    # 2. Check if WooCommerce is connected

    if not is_connected():
        return JsonResponse(
            {
                "accepted": False,
                "reason": "Webhooks are currently disabled.",
            },
            status=418,
        )

    # 3. Check request source

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
                "reason": "Request was accepted but ignored because it doesn't contain any usable info!",
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

    # 4. Check request signature

    secret = settings.get_db_setting("wc-webhook-secret")

    if secret:
        if not ("x-wc-webhook-signature" in request.headers):
            log("[orange_red1]WooCommerce Webhook rejected (no signature)![/]")
            return JsonResponse(
                {
                    "accepted": False,
                    "reason": "No signature provided!",
                },
                status=403,
            )

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

    delivery_id = request.headers["x-wc-webhook-delivery-id"]
    topic = request.headers["x-wc-webhook-topic"]
    wc_obj = json.loads(request.body)
    wc_obj_id = wc_obj.get("id")

    log("Delivery ID: ", delivery_id)
    log("Topic: ", topic)
    log("Object ID: ", wc_obj_id)

    if not wc_obj_id:
        log("[orange_red1]Object ID was not provided - reporting to admins...[/]")
        mail_admins(
            "ERROR: WooCommerce Webhook without object ID received!",
            f"Delivery ID: {delivery_id}\nTopic: {topic}\nObject: {str(wc_obj)}",
        )
        return JsonResponse(
            {"accepted": False, "reason": "Object ID was not provided!"}, status=400
        )

    match topic:
        case "product.updated" | "product.created" | "product.restored":
            if Product.objects.filter(woocommerceid=wc_obj_id).exists():
                product = Product.objects.get(woocommerceid=wc_obj_id)
                WCProductsAPI().update_object_from_data(
                    product, wc_obj, is_create_event=(topic == "product.created")
                )
            else:
                WCProductsAPI().create_object_from_data(wc_obj)
        case "product.deleted":
            if Product.objects.filter(woocommerceid=wc_obj_id).exists():
                product = Product.objects.get(woocommerceid=wc_obj_id)
                WCProductsAPI().delete_object_from_data(product, wc_obj)
        case "customer.updated" | "customer.created" | "customer.restored":
            if Customer.objects.filter(woocommerceid=wc_obj_id).exists():
                customer = Customer.objects.get(woocommerceid=wc_obj_id)
                customer.woocommerce_deleted = False
                WCCustomersAPI().update_object_from_data(customer, wc_obj)
            else:
                WCCustomersAPI().create_object_from_data(wc_obj)
        case "customer.deleted":
            if Customer.objects.filter(woocommerceid=wc_obj_id).exists():
                customer = Customer.objects.get(woocommerceid=wc_obj_id)
                WCCustomersAPI().delete_object_from_data(customer, wc_obj)
        case "order.updated" | "order.created" | "order.restored":
            if Order.objects.filter(woocommerceid=wc_obj_id).exists():
                order = Order.objects.get(woocommerceid=wc_obj_id)
                order.woocommerce_deleted = False
                WCOrdersAPI().update_object_from_data(order, wc_obj)
            else:
                WCOrdersAPI().create_object_from_data(wc_obj)
        case "order.deleted":
            if Order.objects.filter(woocommerceid=wc_obj_id).exists():
                order = Order.objects.get(woocommerceid=wc_obj_id)
                WCOrdersAPI().delete_object_from_data(order, wc_obj)
        case _:
            log(f"[orange_red1]Unknown topic: '{topic}' - reporting to admins...")
            mail_admins(
                "ERROR: WooCommerce Webhook with unknown topic received!",
                f"Delivery ID: {delivery_id}\nTopic: {topic}\nObject: {str(wc_obj)}",
            )
            return JsonResponse(
                {"accepted": False, "message": "Topic not supported!"}, status=400
            )

    return JsonResponse(
        {"accepted": True, "message": "Successfully processed!"}, status=200
    )


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
            "kmuhelper_url": "https://" + request.get_host(),
            "wc_url": secreturl,
            "is_connected": is_connected(),
            "is_url_valid": test_wc_url(url),
        },
    )
