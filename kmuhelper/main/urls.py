from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings

from kmuhelper.main import views

#######################

urlpatterns = [
    path('public/order/<int:object_id>/<order_key>/',
         views.public_view_order, name='public-view-order'),
]
