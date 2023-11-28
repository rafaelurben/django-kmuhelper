from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy, gettext

import kmuhelper.modules.config as config
from kmuhelper.decorators import (
    require_object,
    confirm_action,
    require_all_kmuhelper_perms,
    require_kmuhelper_module_perms,
)
from kmuhelper.modules.emails.models import EMail, Attachment, EMailTemplate
from kmuhelper.utils import render_error

_ = gettext_lazy

#####

# EMail views


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["send_email"])
@require_object(EMail)
@confirm_action(_("E-Mail-Nachricht senden"))
def email_send(request, obj):
    if obj.is_valid():
        try:
            success = obj.send()
            if success:
                messages.success(request, gettext("E-Mail wurde versendet!"))
            else:
                messages.error(request, gettext("E-Mail konnte nicht gesendet werden!"))
        except FileNotFoundError:
            messages.error(
                request,
                gettext("Eine Datei aus dem Anhang konnte nicht gefunden werden!"),
            )
    return redirect(reverse("admin:kmuhelper_email_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["send_email"])
@require_object(EMail)
@confirm_action(_("E-Mail Nachricht ERNEUT senden"))
def email_resend(request, obj):
    if obj.is_valid(request):
        try:
            success = obj.send()
            if success:
                messages.success(request, gettext("E-Mail wurde erneut versendet!"))
            else:
                messages.error(request, gettext("E-Mail konnte nicht gesendet werden!"))
        except FileNotFoundError:
            messages.error(
                request,
                gettext("Eine Datei aus dem Anhang konnte nicht gefunden werden!"),
            )
    return redirect(reverse("admin:kmuhelper_email_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["view_email"])
@require_object(EMail)
def email_preview(request, obj):
    if obj.is_valid(request):
        return HttpResponse(obj.render(online=True))
    return redirect(reverse("admin:kmuhelper_email_change", args=[obj.pk]))


# Public views


@require_object(EMail, show_errorpage=True)
def email_view(request, obj):
    """Render an email for online viewing"""

    token_received = request.GET.get("token", None)
    token_stored = str(obj.token)

    if request.user.has_perm("kmuhelper.view_email") or (
        token_received == token_stored
    ):
        if obj.is_valid():
            return HttpResponse(obj.render(online=True))

        messages.warning(
            request, gettext("Diese E-Mail kann zurzeit leider nicht angezeigt werden.")
        )
    else:
        messages.error(request, gettext("Du hast keinen Zugriff auf diese E-Mail!"))

    return render_error(request)


# EMailAttachment views


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["download_attachment"])
@require_object(Attachment)
def attachment_download(request, obj):
    download = not "preview" in request.GET
    try:
        return obj.get_file_response(download=download)
    except FileNotFoundError:
        messages.error(request, gettext("Datei wurde nicht gefunden!"))
        return render_error(request)


# Public views


@require_object(Attachment, show_errorpage=True)
def attachment_view(request, obj):
    """Render an attachment for online viewing"""

    token_received = request.GET.get("token", None)
    token_stored = str(obj.token)

    if request.user.has_perm("kmuhelper.download_attachment") or (
        token_received == token_stored
    ):
        download = "download" in request.GET
        try:
            return obj.get_file_response(download=download)
        except FileNotFoundError:
            messages.error(
                request, gettext("Diese Datei ist leider nicht mehr verfügbar!")
            )
    else:
        messages.error(
            request, gettext("Du hast keinen Zugriff auf diesen E-Mail-Anhang!")
        )

    return render_error(request)


# EMailTemplate Views


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["view_emailtemplate"])
def emailtemplate_savevars(request):
    """Save variables into session for usage in template"""

    data = request.GET.dict()
    request.session["kmuhelper_emailtemplate_vars"] = data

    messages.success(
        request,
        gettext(
            "Daten wurden erfolgreich zwischengespeichert, um die nächste Vorlage auszufüllen."
        ),
    )
    return redirect(reverse("admin:kmuhelper_emailtemplate_changelist"))


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["view_emailtemplate"])
def emailtemplate_resetvars(request):
    """Reset saved session variables for email templates"""

    if "kmuhelper_emailtemplate_vars" in request.session:
        del request.session["kmuhelper_emailtemplate_vars"]

    messages.success(request, _("Gespeicherte Daten wurden gelöscht!"))
    return redirect(reverse("admin:kmuhelper_emailtemplate_changelist"))


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["view_emailtemplate", "add_email"])
@require_object(EMailTemplate)
def emailtemplate_use(request, obj):
    """Use a template"""

    savedvars = request.session.pop("kmuhelper_emailtemplate_vars", dict())
    requestvars = request.GET.dict()
    data = {**savedvars, **requestvars}

    mail = obj.create_mail(data)

    messages.success(
        request, _("Vorlage wurde mit folgenden Daten ausgefüllt: %s") % data
    )
    return redirect(reverse("admin:kmuhelper_email_change", args=[mail.pk]))


# Custom fake admin


@login_required(login_url=reverse_lazy("kmuhelper:login"))
@require_kmuhelper_module_perms("emails")
def email_index(request):
    return render(
        request,
        "admin/kmuhelper/_special/email-index.html",
        config.get_module_home_context(request, "emails"),
    )
