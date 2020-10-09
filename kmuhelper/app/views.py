from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse, path, reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe

#####

@login_required(login_url=reverse_lazy("admin:login"))
def app_main(request):
    return render(request, "kmuhelper/app/main.html", {})

@allow_iframe
@login_required(login_url=reverse_lazy("admin:login"))
def app_home(request):
    return render(request, "kmuhelper/app/home.html", {
        "has_permission": True,
    })

@allow_iframe
def app_error(request):
    return render(request, "kmuhelper/app/error.html", {
        "has_permission": True,
    })

@allow_iframe
@login_required(login_url=reverse_lazy("admin:login"))
def app_index(request):
    return render(request, 'admin/kmuhelper/app-todo/app_index.html', {
        'app_label': 'kmuhelper',
        'app_list': [{
            'app_label': 'kmuhelper',
            'app_url': reverse("kmuhelper:app-index"),
            'has_module_perms': True,
            'models': [
                {
                    'add_url': reverse("admin:kmuhelper_todonotiz_add"),
                    'admin_url': reverse("admin:kmuhelper_todonotiz_changelist"),
                    'name': 'ToDo-Liste',
                    'object_name': 'Notiz',
                    'perms': {
                        'add': request.user.has_perm("kmuhelper.add_todonotiz"),
                        'change': request.user.has_perm("kmuhelper.change_todonotiz"),
                        'delete': False,
                        'view': request.user.has_perm("kmuhelper.view_todonotiz")},
                    'view_only': False
                },
                {
                    'add_url': reverse("admin:kmuhelper_todoversand_add"),
                    'admin_url': reverse("admin:kmuhelper_todoversand_changelist"),
                    'name': 'Versand',
                    'object_name': 'Bestellung',
                    'perms': {
                        'add': request.user.has_perm("kmuhelper.add_todoversand"),
                        'change': request.user.has_perm("kmuhelper.change_todoversand"),
                        'delete': False,
                        'view': request.user.has_perm("kmuhelper.view_todoversand")},
                    'view_only': False
                },
                {
                    'add_url': reverse("admin:kmuhelper_todozahlungseingang_add"),
                    'admin_url': reverse("admin:kmuhelper_todozahlungseingang_changelist"),
                    'name': 'Zahlungseingang',
                    'object_name': 'Bestellung',
                    'perms': {
                        'add': request.user.has_perm("kmuhelper.add_todozahlungseingang"),
                        'change': request.user.has_perm("kmuhelper.change_todozahlungseingang"),
                        'delete': False,
                        'view': request.user.has_perm("kmuhelper.view_todozahlungseingang")},
                    'view_only': False
                },
                {
                    'add_url': reverse("admin:kmuhelper_todolagerbestand_add"),
                    'admin_url': reverse("admin:kmuhelper_todolagerbestand_changelist"),
                    'name': 'Lagerbestand',
                    'object_name': 'Produkt',
                    'perms': {
                        'add': request.user.has_perm("kmuhelper.add_todolagerbestand"),
                        'change': request.user.has_perm("kmuhelper.change_todolagerbestand"),
                        'delete': False,
                        'view': request.user.has_perm("kmuhelper.view_todolagerbestand")},
                    'view_only': False
                },
                {
                    'add_url': reverse("admin:kmuhelper_todolieferung_add"),
                    'admin_url': reverse("admin:kmuhelper_todolieferung_changelist"),
                    'name': 'Wareneingang',
                    'object_name': 'Lieferung',
                    'perms': {
                        'add': request.user.has_perm("kmuhelper.add_todolieferung"),
                        'change': request.user.has_perm("kmuhelper.change_todolieferung"),
                        'delete': False,
                        'view': request.user.has_perm("kmuhelper.view_todolieferung")},
                    'view_only': False
                },
            ],
            'name': 'KMUHelper App'
        }],
        'has_permission': True,
        'is_nav_sidebar_enabled': False,
        'is_popup': False,
        'title': 'KMUHelper App',
    })


def app_manifest(request):
    response = render(request, "kmuhelper/app/manifest.webmanifest", {})
    response['Content-Type'] = 'text/json'
    response["Service-Worker-Allowed"] = "/"
    return response


