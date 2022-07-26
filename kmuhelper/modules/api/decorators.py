import uuid

from functools import wraps

from kmuhelper.modules.api.constants import (
    NO_PERMISSION_APIKEY, APIKEY_INVALID, NO_PERMISSION_SESSION, NOT_AUTHENTICATED, OBJ_NOT_FOUND
)
from kmuhelper.modules.api.models import ApiKey
from kmuhelper.decorators import require_object as original_require_object


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

                    return NO_PERMISSION_APIKEY

                return APIKEY_INVALID

            if request.user.is_authenticated:
                if request.user.has_perms(perms_required):
                    return function(request, *args, **kwargs)

                return NO_PERMISSION_SESSION

            return NOT_AUTHENTICATED
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


def require_object(model):
    """Decorator: Requires an object with gived ID and passes it to the view"""
    return original_require_object(model, custom_response=OBJ_NOT_FOUND)
