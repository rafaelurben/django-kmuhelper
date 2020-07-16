from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse, path
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe

from .models import ToDoNotiz, ToDoVersand, ToDoZahlungseingang, Lieferung

#####

def app_main(request):
    return render(request, "kmuhelper/app/main.html", {})

@allow_iframe
def app_home(request):
    return render(request, "kmuhelper/app/home.html", {})

#####

urlpatterns = [
    path('app/', app_main, name="app-main"),
    path('app/home', app_home, name="app-home"),
]
