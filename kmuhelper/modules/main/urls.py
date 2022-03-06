from django.urls import path

from kmuhelper.modules.main import views

#######################

urlpatterns = [
    path('public/order/<int:object_id>/<order_key>/',
         views.public_view_order, name='public-view-order'),
]
