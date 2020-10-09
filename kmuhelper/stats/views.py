from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, path, reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe

from kmuhelper.utils import package_version, python_version
from kmuhelper.models import Bestellungsposten, Bestellung

import datetime
import json

#####

def stats(request):
    return render(request, "kmuhelper/stats/index.html", {})


def stats_products_price(request):
    products_sold = {}

    for bp in Bestellungsposten.objects.filter().order_by("bestellung__datum").values("bestellung__datum", "menge"):
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

    for b in Bestellung.objects.filter().order_by("datum").values("datum", "fix_summe"):
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
