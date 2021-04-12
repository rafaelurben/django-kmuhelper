from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy

from kmuhelper.decorators import require_object, confirm_action
from kmuhelper.emails.models import EMail

#####


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.send_email")
@require_object(EMail)
@confirm_action("E-Mail Nachricht senden")
def email_send(request, obj):
    success = obj.send()
    if success:
        messages.success(request, "E-Mail wurde versendet!")
    else:
        messages.error(request, "E-Mail konnte nicht gesendet werden!")
    return redirect(reverse("admin:kmuhelper_email_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.send_email")
@require_object(EMail)
@confirm_action("E-Mail Nachricht ERNEUT senden")
def email_resend(request, obj):
    success = obj.send()
    if success:
        messages.success(request, "E-Mail wurde erneut versendet!")
    else:
        messages.error(request, "E-Mail konnte nicht gesendet werden!")
    return redirect(reverse("admin:kmuhelper_email_change", args=[obj.pk]))


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.view_email")
@require_object(EMail)
def email_preview(request, obj):
    return HttpResponse(obj.render(online=True))


# Public views


@require_object(EMail, reverse_lazy("kmuhelper:error"))
def email_view(request, obj):
    """Render an email for online viewing"""

    token_received = request.GET.get("token", None)
    token_stored = str(obj.token)

    if request.user.has_perm("kmuhelper.view_email") or (token_received == token_stored):
        return HttpResponse(obj.render(online=True))

    messages.error(request, "Du hast keinen Zugriff auf diese E-Mail!")
    return redirect(reverse("kmuhelper:error"))
