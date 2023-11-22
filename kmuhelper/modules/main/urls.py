from django.urls import path

from kmuhelper.modules.main import views

#######################

urlpatterns = [
    path("", views.index, name="main-index"),
]
