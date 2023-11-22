from django.urls import path

from kmuhelper.modules.settings import views

#######################

urlpatterns = [
    path("", views.settings_form, name="settings"),
    path("build-info", views.build_info, name="build-info"),
]
