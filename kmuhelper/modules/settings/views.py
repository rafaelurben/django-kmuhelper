from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy, gettext

from kmuhelper.decorators import (
    require_any_kmuhelper_perms,
    require_all_kmuhelper_perms,
)
from kmuhelper.modules.settings.forms import SettingsForm

_ = gettext_lazy


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["change_setting"])
def settings_form(request):
    if request.method == "POST":
        form = SettingsForm(request.POST)
        if form.is_valid():
            form.save_settings()
            messages.success(request, gettext("Einstellungen gespeichert!"))
            # Redirect to prevent resending the form on reload
            return redirect("kmuhelper:settings")
    else:
        form = SettingsForm()

    return render(
        request, "kmuhelper/settings/form.html", {"form": form, "has_permission": True}
    )


@login_required(login_url=reverse_lazy("admin:login"))
@require_any_kmuhelper_perms()
def build_info(request):
    return render(request, "kmuhelper/settings/build_info.html")
