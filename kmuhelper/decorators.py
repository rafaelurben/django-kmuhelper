from functools import wraps

from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import redirect, render


def confirm_action(action_message):
    def decorator(function):
        @wraps(function)
        def wrap(request, *args, **kwargs):
            if request.method == "POST":
                return function(request, *args, **kwargs)
            return render(request, "admin/kmuhelper/_confirm.html", {"action": action_message})
        return wrap
    return decorator
