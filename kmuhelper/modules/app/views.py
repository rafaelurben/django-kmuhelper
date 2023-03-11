from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe
from django.utils.translation import gettext

from kmuhelper.decorators import require_any_kmuhelper_perms, require_kmuhelper_module_perms
import kmuhelper.modules.config as config

_ = gettext

#####


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_kmuhelper_module_perms('app')
def app_mobile_main(request):
    return render(request, "kmuhelper/app/mobile/main.html", {})


@allow_iframe
@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_kmuhelper_module_perms('app')
def app_mobile_home(request):
    return render(request, "kmuhelper/app/mobile/home.html", {
        "has_permission": True,
    })


@allow_iframe
@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_kmuhelper_module_perms('app')
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
@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_kmuhelper_module_perms('app')
def app_desktop(request):
    return render(request, 'admin/kmuhelper/_special/app/app_index.html', config.get_module_home_context(request, 'app'))
