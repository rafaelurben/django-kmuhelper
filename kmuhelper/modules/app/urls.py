from django.urls import path

from kmuhelper.modules.app import views

#######################

urlpatterns = [
    path(
        "manifest.webmanifest",
        views.app_manifest,
        name="app-manifest",
    ),
    path("", views.app_index, name="app-index"),
    # Redirects for legacy URLs
    path("mobile/", views.app_redirect),
    path("desktop/", views.app_redirect),
]
