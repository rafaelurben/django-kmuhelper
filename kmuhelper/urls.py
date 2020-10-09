from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings

from kmuhelper import views
from kmuhelper.models import Einstellung, Geheime_Einstellung

# Standardwerte laden
try:
    Einstellung.objects.get_or_create(id="wc-url", typ="url", name="WooCommerce Shop-Url")[0]

    Geheime_Einstellung.objects.get_or_create(id="wc-consumer_key")
    Geheime_Einstellung.objects.get_or_create(id="wc-consumer_secret")
    Geheime_Einstellung.objects.get_or_create(id="wc-url")
except:
    pass


#######################

app_name = 'kmuhelper'
urlpatterns = [
    path('', views.home, name="home"),
    path('admin', views.admin, name="admin"),
    
    path('kunde/<object_id>/email-registriert', views.kunde_email_registriert, name='kunde-email-registriert'),
    path('lieferant/<object_id>/zuordnen', views.lieferant_zuordnen, name='lieferant-zuordnen'),
    path('lieferung/<object_id>/einlagern', views.lieferung_einlagern, name='lieferung-einlagern'),
    path('bestellung/<object_id>/pdf', views.bestellung_pdf_ansehen, name='bestellung-pdf-ansehen'),
    path('bestellung/<object_id>/pdf/ankundensenden', views.bestellung_pdf_an_kunden_senden, name='bestellung-pdf-an-kunden-senden'),

    path('kunde/bestellung/<order_id>/<order_key>/', views.kunde_rechnung_ansehen, name='kunde-rechnung-ansehen'),

    path('api/',    include('kmuhelper.api')),
    path('app/',    include('kmuhelper.app')),
    path('stats/',  include('kmuhelper.stats')),
    path('wc/',     include('kmuhelper.integrations.woocommerce')),
]
