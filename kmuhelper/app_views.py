from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse, path, reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe

from .models import ToDoNotiz, ToDoVersand, ToDoZahlungseingang, ToDoLagerbestand, Lieferung

#####

@login_required(login_url=reverse_lazy("admin:login"))
def app_main(request):
    return render(request, "kmuhelper/app/main.html", {})

@allow_iframe
@login_required(login_url=reverse_lazy("admin:login"))
def app_home(request):
    return render(request, "kmuhelper/app/home.html", {
        "has_permission": True,
    })

@allow_iframe
def app_error(request):
    return render(request, "kmuhelper/app/error.html", {
        "has_permission": True,
    })

def app_manifest(request):
    response = render(request, "kmuhelper/app/manifest.webmanifest", {})
    response['Content-Type'] = 'text/json'
    response["Service-Worker-Allowed"] = "/"
    return response

#####

urlpatterns = [
    path('app/', app_main, name="app-main"),
    path('app/home', app_home, name="app-home"),
    path('app/error', app_error, name="app-error"),
    path('app/manifest.webmanifest', app_manifest, name="app-manifest"),
]
