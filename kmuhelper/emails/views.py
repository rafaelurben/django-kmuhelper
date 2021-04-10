from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, path, reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe

from kmuhelper.decorators import require_object
from kmuhelper.emails.models import EMail
from kmuhelper.utils import package_version, python_version

#####

@require_object(EMail, reverse_lazy("kmuhelper:info"))
def email_view(request, obj):
    t1 = request.GET.get("token", None)
    t2 = str(obj.token)

    if request.user.has_perm("kmuhelper.view_email") or (t1 == t2):
        return HttpResponse(obj.render(online=True))
    
    messages.error(request, "Du hast keinen Zugriff auf diese E-Mail!")
    return redirect(reverse("kmuhelper:info"))