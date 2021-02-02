from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings

from kmuhelper.main import views

#######################

urlpatterns = [
    path('kunde/<object_id>/email-registriert', views.kunde_email_registriert, name='kunde-email-registriert'),
    path('lieferant/<object_id>/zuordnen', views.lieferant_zuordnen, name='lieferant-zuordnen'),
    path('lieferung/<object_id>/einlagern', views.lieferung_einlagern, name='lieferung-einlagern'),
    path('bestellung/<object_id>/pdf', views.bestellung_pdf_ansehen, name='bestellung-pdf-ansehen'),
    path('bestellung/<object_id>/pdf/ankundensenden', views.bestellung_pdf_an_kunden_senden, name='bestellung-pdf-an-kunden-senden'),

    path('public/order/<order_id>/<order_key>/', views.public_view_order, name='public-view-order'),
]


