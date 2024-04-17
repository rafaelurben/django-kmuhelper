from django.urls import path

from kmuhelper.modules.integrations.woocommerce import views

#######################

urlpatterns = [
    path("auth/start", views.wc_auth_start, name="wc-auth-start"),
    path("auth/end", views.wc_auth_end, name="wc-auth-end"),
    path("auth/key", views.wc_auth_key, name="wc-auth-key"),
    path("auth/clear", views.wc_auth_clear, name="wc-auth-clear"),
    path("import/products", views.wc_import_products, name="wc-import-products"),
    path("import/customers", views.wc_import_customers, name="wc-import-customers"),
    path("import/categories", views.wc_import_categories, name="wc-import-categories"),
    path("import/orders", views.wc_import_orders, name="wc-import-orders"),
    path(
        "update/product/<int:object_id>",
        views.wc_update_product,
        name="wc-update-product",
    ),
    path(
        "update/customer/<int:object_id>",
        views.wc_update_customer,
        name="wc-update-customer",
    ),
    path(
        "update/category/<int:object_id>",
        views.wc_update_category,
        name="wc-update-category",
    ),
    path("update/order/<int:object_id>", views.wc_update_order, name="wc-update-order"),
    path("webhooks", views.wc_webhooks, name="wc-webhooks"),
    # User Interface
    path("settings", views.wc_settings, name="wc-settings"),
    path("system-status", views.wc_system_status, name="wc-system-status"),
    path("webhooks-status", views.wc_webhooks_status, name="wc-webhooks-status"),
]
