from django.urls import path
from django.conf import settings

from kmuhelper.emails import views

#######################

urlpatterns = [
    path('<object_id>/view', views.email_view, name="email-view"),
]
