from django.contrib.auth.decorators import login_required, permission_required
from django.urls import NoReverseMatch, reverse_lazy, reverse
from django.shortcuts import render
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.loader import get_template

from kmuhelper.utils import render_error

# Create your views here.


@login_required(login_url=reverse_lazy("admin:login"))
def home(request):
    grid = [
        [
            {
                "title": "Admin",
                "subtitle": "Volle Kontrolle über die Hauptfunktionen",
                "url": reverse("admin:app_list", kwargs={"app_label": "kmuhelper"}),
                "icon": "fas fa-key",
            },
            {
                "title": "E-Mails",
                "subtitle": "Verwaltung und Erstellung von E-Mails",
                "url": reverse("kmuhelper:email-index"),
                "icon": "fas fa-envelope-open",
            },
        ],
        [
            {
                "title": "App (Mobile)",
                "subtitle": "Eingeschränkte Verwaltung von Daten in verschiedenen Arbeitsschritten",
                "url": reverse("kmuhelper:app-mobile"),
                "icon": "fas fa-mobile-alt",
            },
            {
                "title": "App (Desktop)",
                "subtitle": "Eingeschränkte Verwaltung von Daten in verschiedenen Arbeitsschritten",
                "url": reverse("kmuhelper:app-desktop"),
                "icon": "fas fa-desktop",
            },
        ],
        [
            {
                "title": "Statistiken",
                "subtitle": "Diagramme und co.",
                "url": reverse("kmuhelper:stats"),
                "icon": "fas fa-chart-pie",
            },
            {
                "title": "Einstellungen",
                "subtitle": "Kleine Einstellungen für den KMUHelper",
                "url": reverse("admin:kmuhelper_einstellung_changelist"),
                "icon": "fas fa-cog",
            },
        ],
        [
            {
                "title": "Handbuch",
                "subtitle": "Dokumentation zum KMUHelper",
                "url": "https://rafaelurben.github.io/django-kmuhelper/manual/",
                "icon": "fas fa-book",
            },
        ]
    ]
    return render(request, "kmuhelper/home.html", {"has_permission": True, "grid": grid})


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
                            message=f"Vorlage '{templatename}' wurde nicht gefunden.")
    except TemplateSyntaxError as error:
        return render_error(request, status=400, 
                            message=f"Vorlage '{templatename}' enthält ungültige Syntax: {error}")
    except (NoReverseMatch) as error:
        return render_error(request, status=400, 
                            message=f"Er ist ein Fehler aufgetreten: {error}")
