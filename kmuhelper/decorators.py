from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, PermissionDenied
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext

import kmuhelper.modules.config as config
from kmuhelper.utils import render_error

_ = gettext


def confirm_action(action_message):
    """Decorator to show a confirm page where the user has to
    confirm an action before executing it."""

    def decorator(function):
        @wraps(function)
        def wrap(request, *args, **kwargs):
            if request.method == "POST":
                return function(request, *args, **kwargs)
            return render(
                request, "admin/kmuhelper/_confirm.html", {"action": action_message}
            )

        return wrap

    return decorator


def require_object(
    model,
    redirect_url=None,
    raise_404=False,
    show_errorpage=False,
    custom_response=None,
):
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
                request,
                _("%(name)s with ID %(id)s was not found!")
                % {"name": model._meta.verbose_name, "id": object_id},
            )

            if raise_404:
                raise Http404

            if show_errorpage:
                return render_error(request)

            return redirect(
                redirect_url
                or reverse(
                    f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"
                )
            )

        return wrap

    return decorator


def require_all_kmuhelper_perms(
    permissions_required=[], login_url=None, raise_exception=True
):
    """
    Decorator for views that checks whether a user has ALL of the given kmuhelper
    permission enabled, redirecting to the log-in page if necessary.
    If the raise_exception parameter is given the PermissionDenied exception
    is raised.
    """

    def check_perms(user):
        if isinstance(permissions_required, str):
            perms = [permissions_required]
        else:
            perms = permissions_required

        perms = [f"kmuhelper.{perm}" if not "." in perm else perm for perm in perms]

        # First check if the user has the permission (even anon users)
        if user.has_perms(perms):
            return True
        # In case the 403 handler should be called raise the exception
        if raise_exception:
            raise PermissionDenied
        # As the last resort, show the login form
        return False

    return user_passes_test(check_perms, login_url=login_url)


def require_any_kmuhelper_perms(permissions=[], login_url=None, raise_exception=True):
    """
    Decorator for views that checks whether a user has ANY (of the given) kmuhelper
    permission enabled, redirecting to the log-in page if necessary.
    If the raise_exception parameter is given the PermissionDenied exception
    is raised.
    """

    def check_perms(user):
        if isinstance(permissions, str):
            perms = [permissions]
        else:
            perms = permissions

        # First check if the user has any kmuhelper permission
        if user.has_module_perms("kmuhelper"):
            # If no permissions are given, the user has access
            if not perms:
                return True

            # Check if the user has any of the given permissions
            for perm in perms:
                if user.has_perm(f"kmuhelper.{perm}" if not "." in perm else perm):
                    return True

        # In case the 403 handler should be called raise the exception
        if raise_exception:
            raise PermissionDenied
        # As the last resort, show the login form
        return False

    return user_passes_test(check_perms, login_url=login_url)


def require_kmuhelper_module_perms(module_name, login_url=None, raise_exception=True):
    """
    Decorator for views that checks whether a user has permissions for a kmuhelper
    module, redirecting to the log-in page if necessary.
    If the raise_exception parameter is given the PermissionDenied exception
    is raised.
    """

    def check_perms(user):
        # First check if the user has the permission (even anon users)
        if config.user_has_module_permission(user, module_name):
            return True

        # In case the 403 handler should be called raise the exception
        if raise_exception:
            raise PermissionDenied
        # As the last resort, show the login form
        return False

    return user_passes_test(check_perms, login_url=login_url)
