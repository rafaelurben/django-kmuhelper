from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import include, path, reverse

urlpatterns = [
    path("kmuhelper/", include("kmuhelper.urls")),
    path("admin/", admin.site.urls),
]
