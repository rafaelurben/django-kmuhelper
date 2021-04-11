from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy

from kmuhelper.decorators import require_object
from kmuhelper.emails.models import EMail

#####


@require_object(EMail, reverse_lazy("kmuhelper:error"))
def email_view(request, obj):
    """Render an email for online viewing"""

    token_received = request.GET.get("token", None)
    token_stored = str(obj.token)

    if request.user.has_perm("kmuhelper.view_email") or (token_received == token_stored):
        return HttpResponse(obj.render(online=True))

    messages.error(request, "Du hast keinen Zugriff auf diese E-Mail!")
    return redirect(reverse("kmuhelper:error"))
