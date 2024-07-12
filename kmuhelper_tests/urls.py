from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("kmuhelper/", include("kmuhelper.urls")),
    path("admin/", admin.site.urls),
]
