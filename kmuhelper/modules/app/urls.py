from django.urls import path

from kmuhelper.modules.app import views

#######################

urlpatterns = [
    path('mobile/', views.app_mobile_main, name="app-mobile"),
    path('mobile/home', views.app_mobile_home, name="app-mobile-home"),
    path('mobile/error', views.app_mobile_error, name="app-mobile-error"),

    path('mobile/manifest.webmanifest', views.app_mobile_manifest, name="app-mobile-manifest"),

    path('desktop/', views.app_desktop, name="app-desktop"),
]
