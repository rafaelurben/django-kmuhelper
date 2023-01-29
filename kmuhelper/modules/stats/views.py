import datetime
import json

from django.contrib.auth.decorators import login_required, permission_required
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone

from kmuhelper.utils import render_error
from kmuhelper.translations import langselect
from kmuhelper.modules.main.models import Bestellungsposten, Bestellung


#####


@login_required(login_url=reverse_lazy("admin:login"))
def stats(request):
    return render(request, "kmuhelper/stats/index.html", {"has_permission": True})


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.view_produkt")
def stats_products_price(request):
    if not Bestellung.objects.exists():
        return render_error(request, status=400,
                            message="Keine Bestellungen vorhanden.")

    try:
        from_date = timezone.make_aware(datetime.datetime.strptime(
            str(request.GET.get("from")), "%Y-%m-%d"))
    except (ValueError, IndexError):
        from_date = Bestellung.objects.order_by("datum").first().datum

    try:
        to_date = timezone.make_aware(datetime.datetime.strptime(
            str(request.GET.get("to")), "%Y-%m-%d"))
    except (ValueError, IndexError):
        to_date = Bestellung.objects.order_by("datum").last().datum

    products_sold = {}

    for bp in Bestellungsposten.objects.filter(bestellung__datum__gte=from_date, bestellung__datum__lte=to_date).order_by("bestellung__datum").values("bestellung__datum", "menge"):
        d = datetime.date(year=bp["bestellung__datum"].year,
                          month=bp["bestellung__datum"].month, day=1).isoformat()
        if d in products_sold:
            products_sold[d] += bp["menge"]
        else:
            products_sold[d] = bp["menge"]

    products_sold = [{"date": date, "y": products_sold[date]}
                     for date in products_sold]
    products_sold_data = json.dumps(products_sold, cls=DjangoJSONEncoder)

    money_income = {}

    for b in Bestellung.objects.filter(datum__gte=from_date, datum__lte=to_date).order_by("datum").values("datum", "fix_summe"):
        d = datetime.date(year=b["datum"].year,
                          month=b["datum"].month, day=1).isoformat()
        if d in money_income:
            money_income[d] += b["fix_summe"]
        else:
            money_income[d] = b["fix_summe"]

    money_income = [{"date": date, "y": money_income[date]}
                    for date in money_income]
    money_income_data = json.dumps(money_income, cls=DjangoJSONEncoder)

    context = {
        "has_permission": True,
        "products_sold": products_sold_data,
        "money_income": money_income_data,
    }
    return render(request, "kmuhelper/stats/products_price.html", context)


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.view_produkt")
def best_products(request):
    if not Bestellung.objects.exists():
        return render_error(request, status=400,
                            message="Keine Bestellungen vorhanden.")

    try:
        if "max" in request.GET:
            max_count = int(request.GET.get("max"))
        else:
            max_count = 20
    except (ValueError, IndexError):
        max_count = 20

    try:
        from_date = timezone.make_aware(datetime.datetime.strptime(
            str(request.GET.get("from")), "%Y-%m-%d"))
    except (ValueError, IndexError):
        from_date = Bestellung.objects.order_by("datum").first().datum

    try:
        to_date=timezone.make_aware(datetime.datetime.strptime(
            str(request.GET.get("to")), "%Y-%m-%d"))
    except (ValueError, IndexError):
        to_date = Bestellung.objects.order_by("datum").last().datum

    products = {}

    for bp in Bestellungsposten.objects.filter(bestellung__datum__gte=from_date, bestellung__datum__lte=to_date).order_by("produkt__name").values("produkt__name", "menge"):
        if bp["produkt__name"] in products:
            products[langselect(bp["produkt__name"])] += bp["menge"]
        else:
            products[langselect(bp["produkt__name"])] = bp["menge"]

    products = sorted(products.items(), key=lambda x: x[1], reverse=True)
    products = products[:max_count] if len(products) > max_count else products

    context = {
        "has_permission": True,
        "product_names": [p[0] for p in products],
        "product_counts": [p[1] for p in products],
    }
    return render(request, "kmuhelper/stats/best_products.html", context)
