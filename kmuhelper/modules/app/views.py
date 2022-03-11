from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe

from kmuhelper.utils import custom_app_list
from kmuhelper.modules.app.models import App_ToDo, App_Warenausgang, App_Zahlungseingang, App_Lagerbestand, App_Wareneingang

#####


@login_required(login_url=reverse_lazy("admin:login"))
def app_mobile_main(request):
    return render(request, "kmuhelper/app/mobile/main.html", {})


@allow_iframe
@login_required(login_url=reverse_lazy("admin:login"))
def app_mobile_home(request):
    return render(request, "kmuhelper/app/mobile/home.html", {
        "has_permission": True,
    })


@allow_iframe
def app_mobile_error(request):
    return render(request, "kmuhelper/app/mobile/error.html", {
        "has_permission": True,
    })


def app_mobile_manifest(request):
    response = render(request, "kmuhelper/app/mobile/manifest.webmanifest", {})
    response['Content-Type'] = 'text/json'
    response["Service-Worker-Allowed"] = "/"
    return response


@allow_iframe
@login_required(login_url=reverse_lazy("admin:login"))
def app_desktop(request):
    return render(request, 'admin/kmuhelper/_special/app/app_index.html', {
        'app_label': 'kmuhelper',
        'app_list': custom_app_list(request, [App_ToDo, App_Lagerbestand, App_Warenausgang, App_Wareneingang, App_Zahlungseingang], "KMUHelper App", reverse("kmuhelper:app-desktop")),
        'has_permission': True,
        'is_nav_sidebar_enabled': False,
        'is_popup': False,
        'title': 'KMUHelper App',
    })
