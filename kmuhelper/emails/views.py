from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, path, reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe

from kmuhelper.utils import package_version, python_version

from kmuhelper.emails.models import EMail

#####

def email_view(request, object_id):
    if EMail.objects.filter(id=object_id).exists():
        email = EMail.objects.get(id=object_id)
        t1 = request.GET.get("token", None)
        t2 = str(email.token)
        if request.user.has_perm("kmuhelper.view_email") or (t1 == t2):
            return HttpResponse(email.render(online=True))
        else:
            return HttpResponseBadRequest("Du hast keinen Zugriff auf diese E-Mail!")
    else:
        return HttpResponseBadRequest("E-Mail wurde nicht gefunden!")
