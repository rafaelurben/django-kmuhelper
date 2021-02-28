from django.urls import path
from django.conf import settings

from kmuhelper.api import views

#######################

urlpatterns = [
    path('errors/not-authenticated', views.not_authenticated, name="api-not-authenticated"),

    path('versions', views.versions, name="api-versions"),
    path('orders/unpaid', views.orders_unpaid, name="api-orders-unpaid"),
]
