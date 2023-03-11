from django.contrib.auth.decorators import login_required, permission_required
from django.urls import NoReverseMatch, reverse_lazy, reverse
from django.shortcuts import render
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.loader import get_template
from django.utils.translation import gettext

import kmuhelper.modules.config as config
from kmuhelper.decorators import require_any_kmuhelper_perms
from kmuhelper.utils import render_error
from kmuhelper.constants import URL_MANUAL

_ = gettext

# Create your views here.


@login_required(login_url=reverse_lazy("admin:login"))
@require_any_kmuhelper_perms()
def home(request):
    grid = [
        [
            {
                "title": _("Admin"),
                "subtitle": _("Volle Kontrolle über die Hauptfunktionen"),
                "url": reverse("admin:app_list", kwargs={"app_label": "kmuhelper"}),
                "icon": "fas fa-key",
                "hidden": not config.user_has_module_permission(request.user, "main"),
            },
            {
                "title": _("E-Mails"),
                "subtitle": _("Verwaltung und Erstellung von E-Mails"),
                "url": reverse("kmuhelper:email-index"),
                "icon": "fas fa-envelope-open",
                "hidden": not config.user_has_module_permission(request.user, "emails"),
            },
        ],
        [
            {
                "title": _("App (Mobile)"),
                "subtitle": _("Eingeschränkte Verwaltung von Daten in verschiedenen Arbeitsschritten"),
                "url": reverse("kmuhelper:app-mobile"),
                "icon": "fas fa-mobile-alt",
                "hidden": not config.user_has_module_permission(request.user, "app"),
            },
            {
                "title": _("App (Desktop)"),
                "subtitle": _("Eingeschränkte Verwaltung von Daten in verschiedenen Arbeitsschritten"),
                "url": reverse("kmuhelper:app-desktop"),
                "icon": "fas fa-desktop",
                "hidden": not config.user_has_module_permission(request.user, "app"),
            },
        ],
        [
            {
                "title": _("Statistiken"),
                "subtitle": _("Diagramme und co."),
                "url": reverse("kmuhelper:stats"),
                "icon": "fas fa-chart-pie",
                "hidden": not config.user_has_module_permission(request.user, "main"),
            },
            {
                "title": _("Einstellungen"),
                "subtitle": _("Einstellungen für den KMUHelper"),
                "url": reverse("kmuhelper:settings"),
                "icon": "fas fa-cog",
                "hidden": not config.user_has_module_permission(request.user, "settings"),
            },
        ],
        [
            {
                "title": _("Handbuch"),
                "subtitle": _("Dokumentation zum KMUHelper"),
                "url": URL_MANUAL,
                "icon": "fas fa-book",
            },
        ]
    ]
    return render(request, "kmuhelper/home.html", {"has_permission": True, "grid": grid})


@require_any_kmuhelper_perms()
def error(request):
    return render_error(request)


@permission_required("is_superuser")
def _templatetest(request, templatename):
    """DEBUG: Test a template with given parameters"""

    try:
        get_template(templatename)
        return render(request, templatename, request.GET.dict())
    except TemplateDoesNotExist:
        return render_error(request, status=404, 
                            message=_("Vorlage %s wurde nicht gefunden.") % templatename)
    except TemplateSyntaxError as error:
        return render_error(request, status=400, 
                            message=_("Vorlage %(name)s enthält einen Syntaxfehler: %(error)s") % {
                                "name": templatename,
                                "error": error
                            })
    except (NoReverseMatch) as error:
        return render_error(request, status=400, 
                            message=_("Es ist ein Fehler aufgetreten: %s") % error)
