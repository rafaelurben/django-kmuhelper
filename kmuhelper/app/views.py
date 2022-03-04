from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe

from kmuhelper.utils import custom_app_list
from kmuhelper.app.models import ToDoNotiz, ToDoVersand, ToDoZahlungseingang, ToDoLagerbestand, ToDoLieferung

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


@allow_iframe
@login_required(login_url=reverse_lazy("admin:login"))
def app_index(request):
    return render(request, 'admin/kmuhelper/_special/app/app_index.html', {
        'app_label': 'kmuhelper',
        'app_list': custom_app_list(request, [ToDoNotiz, ToDoVersand, ToDoZahlungseingang, ToDoLagerbestand, ToDoLieferung], "KMUHelper App", reverse("kmuhelper:app-index")),
        'has_permission': True,
        'is_nav_sidebar_enabled': False,
        'is_popup': False,
        'title': 'KMUHelper App',
    })


def app_manifest(request):
    response = render(request, "kmuhelper/app/manifest.webmanifest", {})
    response['Content-Type'] = 'text/json'
    response["Service-Worker-Allowed"] = "/"
    return response
