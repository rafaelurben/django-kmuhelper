from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

@login_required(login_url=reverse_lazy("admin:login"))
def home(request):
    return render(request, "kmuhelper/home.html", {"has_permission": True})


@login_required(login_url=reverse_lazy("admin:login"))
def admin(request):
    return redirect(reverse("admin:app_list", kwargs={"app_label": "kmuhelper"}))

def _templatetest(request, templatename):
    return render(request, templatename, {})
