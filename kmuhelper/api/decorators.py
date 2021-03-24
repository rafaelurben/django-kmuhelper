from functools import wraps
from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import redirect

from kmuhelper.api.models import ApiKey

import uuid

def _is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

def protected(read=False, write=False, perms_required=[]):
    def decorator(function):
        @wraps(function)
        def wrap(request, *args, **kwargs):
            apikey = request.GET.get("apikey", None)
            if apikey:
                if _is_valid_uuid(apikey) and ApiKey.objects.filter(key=apikey).exists():
                    keyobject = ApiKey.objects.get(key=apikey)
                    if ((not read) or keyobject.read) and ((not write) or keyobject.write) and keyobject.has_perms(perms_required):
                        return function(request, *args, **kwargs)
                    else:
                        return JsonResponse({
                            "error": "no-permission",
                            "message": "You do not have permission to access this endpoint! (authentication method: api key)"
                        })
                else:
                    return JsonResponse({
                        "error": "apikey-invalid",
                        "message": "Your api key is invalid!"
                    })
            elif request.user.is_authenticated:
                if request.user.has_perms(perms_required):
                    return function(request, *args, **kwargs)
                else:
                    return JsonResponse({
                        "error": "no-permission",
                        "message": "You do not have permission to access this endpoint! (authentication method: session)"
                    })
            else:
                return JsonResponse({
                    "error": "not-authenticated",
                    "message": "You must authenticate yourself to use this endpoint!"
                })
        return wrap
    return decorator

# Shortcuts

def api_read(perms_required=[]):
    return protected(read=True, write=False, perms_required=perms_required) 

def api_write(perms_required=[]):
    return protected(read=False, write=True, perms_required=perms_required)

def api_readwrite(perms_required=[]):
    return protected(read=True, write=True, perms_required=perms_required)
