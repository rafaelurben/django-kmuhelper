# pylint: disable=no-member

from django.urls import path
from django.conf import settings

from kmuhelper.integrations.woocommerce import views

#######################

urlpatterns = [
    path('auth/start', views.wc_auth_start, name="wc-auth-start"),
    path('auth/end', views.wc_auth_end, name="wc-auth-end"),
    path('auth/key', views.wc_auth_key, name="wc-auth-key"),
    path('import/products', views.wc_import_products, name="wc-import-products"),
    path('import/customers', views.wc_import_customers, name="wc-import-customers"),
    path('import/categories', views.wc_import_categories, name="wc-import-categories"),
    path('import/orders', views.wc_import_orders, name="wc-import-orders"),
    path('update/product/<object_id>', views.wc_update_product, name="wc-update-product"),
    path('update/customer/<object_id>', views.wc_update_customer, name="wc-update-customer"),
    path('update/category/<object_id>', views.wc_update_category, name="wc-update-category"),
    path('update/order/<object_id>', views.wc_update_order, name="wc-update-order"),
    
    path('webhooks', views.wc_webhooks, name="wc-webhooks"),
]
