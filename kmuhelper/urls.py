from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings

from . import views
from .app_views import urlpatterns as app_urlpatterns

# Standardwerte laden
try:
    from .models import Einstellung, Geheime_Einstellung
    Einstellung.objects.get_or_create(id="wc-url", typ="url", name="WooCommerce Shop-Url")[0]

    Geheime_Einstellung.objects.get_or_create(id="wc-consumer_key")
    Geheime_Einstellung.objects.get_or_create(id="wc-consumer_secret")
    Geheime_Einstellung.objects.get_or_create(id="wc-url")
except:
    pass


#######################

app_name = 'kmuhelper'
urlpatterns = [
    path('wc/auth/start', views.wc_auth_start, name="wc-auth-start"),
    path('wc/auth/end', views.wc_auth_end, name="wc-auth-end"),
    path('wc/auth/key', views.wc_auth_key, name="wc-auth-key"),
    path('wc/import/products', views.wc_import_products, name="wc-import-products"),
    path('wc/import/customers', views.wc_import_customers, name="wc-import-customers"),
    path('wc/import/categories', views.wc_import_categories, name="wc-import-categories"),
    path('wc/import/orders', views.wc_import_orders, name="wc-import-orders"),
    path('wc/update/product/<object_id>', views.wc_update_product, name="wc-update-product"),
    path('wc/update/customer/<object_id>', views.wc_update_customer, name="wc-update-customer"),
    path('wc/update/category/<object_id>', views.wc_update_category, name="wc-update-category"),
    path('wc/update/order/<object_id>', views.wc_update_order, name="wc-update-order"),
    path('wc/webhooks', views.wc_webhooks, name="wc-webhooks"),
    path('kunde/<object_id>/email-registriert', views.kunde_email_registriert, name='kunde-email-registriert'),
    path('lieferant/<object_id>/zuordnen', views.lieferant_zuordnen, name='lieferant-zuordnen'),
    path('lieferung/<object_id>/einlagern', views.lieferung_einlagern, name='lieferung-einlagern'),
    path('bestellung/<object_id>/pdf', views.bestellung_pdf_ansehen, name='bestellung-pdf-ansehen'),
    path('bestellung/<object_id>/pdf/ankundensenden', views.bestellung_pdf_an_kunden_senden, name='bestellung-pdf-an-kunden-senden'),

    path('kunde/bestellung/<order_id>/<order_key>/', views.kunde_rechnung_ansehen, name='kunde-rechnung-ansehen'),
] + app_urlpatterns
