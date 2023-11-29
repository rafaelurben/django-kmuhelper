from django.urls import path

from kmuhelper.modules.app import views

#######################

urlpatterns = [
    path("", views.app_index, name="app-index"),
    # Redirects for legacy URLs
    path("manifest.webmanifest", views.manifest_redirect),
    path("mobile/", views.app_redirect),
    path("desktop/", views.app_redirect),
]
