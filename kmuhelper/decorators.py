from functools import wraps

from django.contrib import messages
from django.http import Http404
from django.urls import reverse
from django.shortcuts import redirect, render

from kmuhelper.utils import render_error


def confirm_action(action_message):
    """Decorator to show a confirm page where the user has to 
    confirm an action before executing it."""

    def decorator(function):
        @wraps(function)
        def wrap(request, *args, **kwargs):
            if request.method == "POST":
                return function(request, *args, **kwargs)
            return render(request, "admin/kmuhelper/_confirm.html", {"action": action_message})
        return wrap
    return decorator


def require_object(model, redirect_url=None, raise_404=False, show_errorpage=False, custom_response=None):
    """Decorator to only call the view if an object with the given id exists
    and automatically pass it instead of the id."""

    def decorator(function):
        @wraps(function)
        def wrap(request, object_id, *args, **kwargs):
            if model.objects.filter(pk=int(object_id)).exists():
                obj = model.objects.get(pk=int(object_id))
                return function(request, obj, *args, **kwargs)

            if custom_response:
                return custom_response

            messages.warning(
                request, f'{model._meta.verbose_name} mit ID "{object_id}" wurde nicht gefunden!')

            if raise_404:
                raise Http404

            if show_errorpage:
                return render_error(request)

            return redirect(redirect_url or reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"))
        return wrap
    return decorator
