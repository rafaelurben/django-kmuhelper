from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse, path
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from .models import ToDoNotiz, ToDoVersand, ToDoZahlungseingang, Lieferung

#####

def home(request):
    return render(request, "kmuhelper/app/home.html", {})

#####

urlpatterns = [
    path('app/', home, name="app-home"),
]
