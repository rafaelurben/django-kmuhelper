from functools import wraps

from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect, render


def confirm_action(action_message):
    """Decorator to show a confirm page where the user has to confirm an action before executing it."""

    def decorator(function):
        @wraps(function)
        def wrap(request, *args, **kwargs):
            if request.method == "POST":
                return function(request, *args, **kwargs)
            return render(request, "admin/kmuhelper/_confirm.html", {"action": action_message})
        return wrap
    return decorator


def require_object(model, redirect_url=None):
    """Decorator to only call the view if an object with the given id exists and automatically pass it instead of the id."""

    def decorator(function):
        @wraps(function)
        def wrap(request, object_id, *args, **kwargs):
            if model.objects.filter(pk=int(object_id)).exists():
                obj = model.objects.get(pk=int(object_id))
                return function(request, obj, *args, **kwargs)

            messages.warning(
                request, f'{model._meta.verbose_name} mit ID "{object_id}" wurde nicht gefunden!')
            return redirect(redirect_url or reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"))
        return wrap
    return decorator
