from django.urls import path, re_path

from kmuhelper.api import views

#######################

urlpatterns = [
    path('versions', views.versions, name="api-versions"),
    path('orders/unpaid', views.orders_unpaid, name="api-orders-unpaid"),

    re_path('.*', views.not_found, name="api-not-found")
]
