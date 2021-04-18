import uuid

from functools import wraps
from django.http import JsonResponse

from kmuhelper.api.models import ApiKey


def _is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def protected(read=False, write=False, perms_required=()):
    """Decorator: Protect an api view from unauthorized access."""
    def decorator(function):
        @wraps(function)
        def wrap(request, *args, **kwargs):
            apikey = request.GET.get("apikey", None)

            if apikey:
                if _is_valid_uuid(apikey) and ApiKey.objects.filter(key=apikey).exists():
                    keyobject = ApiKey.objects.get(key=apikey)

                    if ((not read) or keyobject.read) and ((not write) or keyobject.write) and keyobject.has_perms(perms_required):
                        return function(request, *args, **kwargs)

                    return JsonResponse({
                        "error": "no-permission",
                        "message": "You do not have permission to access this endpoint! (authentication method: api key)"
                    }, status=403)

                return JsonResponse({
                    "error": "apikey-invalid",
                    "message": "Your api key is invalid!"
                }, status=403)

            if request.user.is_authenticated:
                if request.user.has_perms(perms_required):
                    return function(request, *args, **kwargs)

                return JsonResponse({
                    "error": "no-permission",
                    "message": "You do not have permission to access this endpoint! (authentication method: session)"
                }, status=403)

            return JsonResponse({
                "error": "not-authenticated",
                "message": "You must authenticate yourself to use this endpoint!"
            }, status=403)
        return wrap
    return decorator

# Shortcuts


def api_read(perms_required=()):
    """Decorator: Requires a read api key or a logged in user to access this view"""
    return protected(read=True, write=False, perms_required=perms_required)


def api_write(perms_required=()):
    """Decorator: Requires a write api key or a logged in user to access this view"""
    return protected(read=False, write=True, perms_required=perms_required)


def api_readwrite(perms_required=()):
    """Decorator: Requires a read/write api key or a logged in user to access this view"""
    return protected(read=True, write=True, perms_required=perms_required)
