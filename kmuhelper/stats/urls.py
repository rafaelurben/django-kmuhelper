from django.urls import path
from django.conf import settings

from kmuhelper.stats import views

#######################

urlpatterns = [
    path('', views.stats, name='stats'),

    path('products-price', views.stats_products_price, name='stats-products-price'),
    path('best-products', views.best_products, name='stats-best-products'),
]
