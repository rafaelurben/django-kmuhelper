import datetime
import json

from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy
from kmuhelper.decorators import require_all_kmuhelper_perms
from kmuhelper.modules.main.models import OrderItem, Order
from kmuhelper.translations import langselect
from kmuhelper.utils import render_error

_ = gettext_lazy

#####


@login_required(login_url=reverse_lazy("kmuhelper:login"))
def stats(request):
    return render(request, "kmuhelper/stats/index.html", {"has_permission": True})


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["view_product", "view_order"])
def stats_products_price(request):
    if not Order.objects.exists():
        return render_error(
            request, status=400, message=_("Keine Bestellungen vorhanden.")
        )

    try:
        from_date = timezone.make_aware(
            datetime.datetime.strptime(str(request.GET.get("from")), "%Y-%m-%d")
        )
    except (ValueError, IndexError):
        from_date = Order.objects.order_by("date").first().date

    try:
        to_date = timezone.make_aware(
            datetime.datetime.strptime(str(request.GET.get("to")), "%Y-%m-%d")
        )
    except (ValueError, IndexError):
        to_date = Order.objects.order_by("date").last().date

    products_sold = {}

    for bp in (
        OrderItem.objects.filter(order__date__gte=from_date, order__date__lte=to_date)
        .order_by("order__date")
        .values("order__date", "quantity")
    ):
        d = datetime.date(
            year=bp["order__date"].year, month=bp["order__date"].month, day=1
        ).isoformat()
        if d in products_sold:
            products_sold[d] += bp["quantity"]
        else:
            products_sold[d] = bp["quantity"]

    products_sold = [{"date": date, "y": products_sold[date]} for date in products_sold]
    products_sold_data = json.dumps(products_sold, cls=DjangoJSONEncoder)

    money_income = {}

    for b in (
        Order.objects.filter(date__gte=from_date, date__lte=to_date)
        .order_by("date")
        .values("date", "cached_sum")
    ):
        d = datetime.date(year=b["date"].year, month=b["date"].month, day=1).isoformat()
        if d in money_income:
            money_income[d] += b["cached_sum"]
        else:
            money_income[d] = b["cached_sum"]

    money_income = [{"date": date, "y": money_income[date]} for date in money_income]
    money_income_data = json.dumps(money_income, cls=DjangoJSONEncoder)

    context = {
        "has_permission": True,
        "products_sold": products_sold_data,
        "money_income": money_income_data,
    }
    return render(request, "kmuhelper/stats/products_price.html", context)


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_all_kmuhelper_perms(["view_product", "view_order"])
def best_products(request):
    if not Order.objects.exists():
        return render_error(
            request, status=400, message=_("Keine Bestellungen vorhanden.")
        )

    try:
        if "max" in request.GET:
            max_count = int(request.GET.get("max"))
        else:
            max_count = 20
    except (ValueError, IndexError):
        max_count = 20

    try:
        from_date = timezone.make_aware(
            datetime.datetime.strptime(str(request.GET.get("from")), "%Y-%m-%d")
        )
    except (ValueError, IndexError):
        from_date = Order.objects.order_by("date").first().date

    try:
        to_date = timezone.make_aware(
            datetime.datetime.strptime(str(request.GET.get("to")), "%Y-%m-%d")
        )
    except (ValueError, IndexError):
        to_date = Order.objects.order_by("date").last().date

    products = {}

    for bp in (
        OrderItem.objects.filter(order__date__gte=from_date, order__date__lte=to_date)
        .order_by("linked_product__name")
        .values("linked_product__name", "name", "quantity")
    ):
        product_name = langselect(bp["linked_product__name"] or bp["name"])
        if product_name in products:
            products[product_name] += bp["quantity"]
        else:
            products[product_name] = bp["quantity"]

    products = sorted(products.items(), key=lambda x: x[1], reverse=True)
    products = products[:max_count] if len(products) > max_count else products

    context = {
        "has_permission": True,
        "product_names": [p[0] for p in products],
        "product_counts": [p[1] for p in products],
    }
    return render(request, "kmuhelper/stats/best_products.html", context)
