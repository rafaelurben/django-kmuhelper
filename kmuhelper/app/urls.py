from django.urls import path
from django.conf import settings

from kmuhelper.app import views

#######################

urlpatterns = [
    path('', views.app_main, name="app-main"),
    path('home', views.app_home, name="app-home"),
    path('error', views.app_error, name="app-error"),
    path('index', views.app_index, name="app-index"),

    path('manifest.webmanifest', views.app_manifest, name="app-manifest"),
]
