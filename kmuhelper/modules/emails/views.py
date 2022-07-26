from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy

from kmuhelper.decorators import require_object, confirm_action
from kmuhelper.modules.emails.models import EMail, Attachment, EMailTemplate
from kmuhelper.utils import render_error, custom_app_list

#####

# EMail views


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.send_email")
@require_object(EMail)
@confirm_action("E-Mail Nachricht senden")
def email_send(request, obj):
    if obj.is_valid():
        try:
            success = obj.send()
            if success:
                messages.success(request, "E-Mail wurde versendet!")
            else:
                messages.error(request, "E-Mail konnte nicht gesendet werden!")
        except FileNotFoundError:
            messages.error(request, "Eine Datei aus dem Anhang konnte nicht gefunden werden!")
    return redirect(reverse("admin:kmuhelper_email_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.send_email")
@require_object(EMail)
@confirm_action("E-Mail Nachricht ERNEUT senden")
def email_resend(request, obj):
    if obj.is_valid(request):
        try:
            success = obj.send()
            if success:
                messages.success(request, "E-Mail wurde erneut versendet!")
            else:
                messages.error(request, "E-Mail konnte nicht gesendet werden!")
        except FileNotFoundError:
            messages.error(request, "Eine Datei aus dem Anhang konnte nicht gefunden werden!")
    return redirect(reverse("admin:kmuhelper_email_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.view_email")
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

    if request.user.has_perm("kmuhelper.view_email") or (token_received == token_stored):
        if obj.is_valid():
            return HttpResponse(obj.render(online=True))

        messages.warning(
            request, "Diese E-Mail kann zurzeit leider nicht angezeigt werden.")
    else:
        messages.error(request, "Du hast keinen Zugriff auf diese E-Mail!")

    return render_error(request)


# EMailAttachment views


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.download_attachment")
@require_object(Attachment)
def attachment_download(request, obj):
    download = not "preview" in request.GET
    try:
        return obj.get_file_response(download=download)
    except FileNotFoundError:
        messages.error(request, "Datei wurde nicht gefunden!")
        return render_error(request)


# Public views


@require_object(Attachment, show_errorpage=True)
def attachment_view(request, obj):
    """Render an attachment for online viewing"""

    token_received = request.GET.get("token", None)
    token_stored = str(obj.token)

    if request.user.has_perm("kmuhelper.download_attachment") or (token_received == token_stored):
        download = "download" in request.GET
        try:
            return obj.get_file_response(download=download)
        except FileNotFoundError:
            messages.error(request, "Diese Datei ist leider nicht mehr verfügbar!")
    else:
        messages.error(request, "Du hast keinen Zugriff auf diesen E-Mail-Anhang!")

    return render_error(request)


# EMailTemplate Views


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required(["kmuhelper.view_emailtemplate"])
def emailtemplate_savevars(request):
    """Save variables into session for usage in template"""

    data = request.GET.dict()
    request.session["emailtemplate-vars"] = data

    messages.success(
        request, f"Folgende Daten wurden gespeichert, um die nächste Vorlage auszufüllen: {data}")
    return redirect(reverse("admin:kmuhelper_emailtemplate_changelist"))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required(["kmuhelper.view_emailtemplate"])
def emailtemplate_resetvars(request):
    """Reset saved session variables for email templates"""

    if "emailtemplate-vars" in request.session:
        del request.session["emailtemplate-vars"]

    messages.success(
        request, "Gespeicherte Daten wurden gelöscht!")
    return redirect(reverse("admin:kmuhelper_emailtemplate_changelist"))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required(["kmuhelper.view_emailtemplate", "kmuhelper.add_email"])
@require_object(EMailTemplate)
def emailtemplate_use(request, obj):
    """Use a template"""

    savedvars = request.session.pop("emailtemplate-vars", dict())
    requestvars = request.GET.dict()
    data = {**savedvars, **requestvars}

    mail = obj.create_mail(data)

    messages.success(
        request, f"Vorlage wurde mit folgenden Daten ausgefüllt: {data}")
    return redirect(reverse("admin:kmuhelper_email_change", args=[mail.pk]))


# Custom fake admin

@login_required(login_url=reverse_lazy("admin:login"))
def email_index(request):
    return render(request, 'admin/kmuhelper/_special/emails/app_index.html', {
        'app_label': 'kmuhelper',
        'app_list': custom_app_list(request, [EMail, EMailTemplate, Attachment], "KMUHelper E-Mails", reverse('kmuhelper:email-index')),
        'has_permission': True,
        'is_nav_sidebar_enabled': False,
        'is_popup': False,
        'title': 'KMUHelper E-Mails',
    })
