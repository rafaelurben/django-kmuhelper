from django.urls import path, re_path

from kmuhelper.modules.api import views

#######################

urlpatterns = [
    path('versions', views.versions, name="api-versions"),
    path('orders/unpaid', views.orders_unpaid, name="api-orders-unpaid"),
    path('orders/<int:object_id>/set-paid', views.orders_set_paid, name="api-orders-set-paid"),

    re_path('.*', views.not_found, name="api-not-found")
]
