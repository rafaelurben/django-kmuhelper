from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext

import kmuhelper.modules.config as config
from kmuhelper.decorators import (
    require_kmuhelper_module_perms,
)

_ = gettext

#####


def app_redirect(request):
    return redirect(reverse("kmuhelper:app-index"))


def manifest_redirect(request):
    return redirect(reverse("kmuhelper:manifest"))


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_kmuhelper_module_perms("app")
def app_index(request):
    return render(
        request,
        "admin/kmuhelper/_special/app-index.html",
        config.get_module_home_context(request, "app"),
    )
