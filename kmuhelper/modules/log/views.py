from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse_lazy


@login_required(login_url=reverse_lazy("admin:login"))
def log_redirect(request):
    return redirect("admin:kmuhelper_adminlogentry_changelist")
