from django.urls import path
from django.conf import settings

from kmuhelper.api import views

#######################

urlpatterns = [
    path('versions', views.versions, name="api-versions"),
]
