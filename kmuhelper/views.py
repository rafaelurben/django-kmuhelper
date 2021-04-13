from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse_lazy

from kmuhelper.utils import render_error

# Create your views here.


@login_required(login_url=reverse_lazy("admin:login"))
def home(request):
    return render(request, "kmuhelper/home.html", {"has_permission": True})


def error(request):
    return render_error(request)


def _templatetest(request, templatename):
    return render(request, templatename, {})
