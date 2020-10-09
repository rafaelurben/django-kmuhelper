from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, path, reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe

from kmuhelper.utils import package_version, python_version

#####

@login_required(login_url=reverse_lazy("admin:login"))
def versions(request):
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
