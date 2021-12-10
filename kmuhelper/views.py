from django.contrib.auth.decorators import login_required, permission_required
from django.urls import NoReverseMatch
from django.shortcuts import render
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.loader import get_template
from django.urls import reverse_lazy

from kmuhelper.utils import render_error

# Create your views here.


@login_required(login_url=reverse_lazy("admin:login"))
def home(request):
    return render(request, "kmuhelper/home.html", {"has_permission": True})


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
