from django.urls import path

from kmuhelper.modules.log import views

#######################

urlpatterns = [
    path("", views.log_redirect, name="log"),
]
