from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, path, reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe
from django.db import models

from kmuhelper.utils import package_version, python_version
from kmuhelper.models import Bestellung
from kmuhelper.api.decorators import api_read, api_write, api_readwrite

#####

def not_found(request):
    """"""

    return JsonResponse({
        "error": "endpoint-not-found",
        "message": "This endpoint does not exist!"
    })

#####

@api_read()
def versions(request):
    """Get the installed versions of some dependencies, their newest versions available and the current python version."""

    context = {
        "versions": {
            "Python": {"current": python_version(), "latest": "-", "uptodate": None},
        }
    }

    packages = ["Django", "django-kmuhelper", "gunicorn",
                "requests", "WooCommerce", "reportlab", "rich", "pytz"]

    for package in packages:
        context["versions"][package] = package_version(package)
    return JsonResponse(context)


@api_read()
def orders_unpaid(request):
    """Get sums of currently unpaid orders."""

    sum_unsent = Bestellung.objects.filter(bezahlt=False, versendet=False).aggregate(
        models.Sum('fix_summe'))["fix_summe__sum"]
    sum_sent = Bestellung.objects.filter(bezahlt=False, versendet=True).aggregate(
        models.Sum('fix_summe'))["fix_summe__sum"]

    context = {
        "orders_unpaid_sum": {
            "unsent": round(sum_unsent, 2),
            "sent": round(sum_sent, 2),
            "all": round(sum_unsent, 2)+round(sum_sent, 2)
        }
    }
    return JsonResponse(context)
