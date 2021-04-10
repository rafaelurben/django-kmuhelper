from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings

from kmuhelper.main import views

#######################

urlpatterns = [
    path('kunde/<int:object_id>/email-registriert',
         views.kunde_email_registriert, name='kunde-email-registriert'),
    path('lieferant/<int:object_id>/zuordnen',
         views.lieferant_zuordnen, name='lieferant-zuordnen'),
    path('lieferung/<int:object_id>/einlagern',
         views.lieferung_einlagern, name='lieferung-einlagern'),
    path('bestellung/<int:object_id>/pdf',
         views.bestellung_pdf_ansehen, name='bestellung-pdf-ansehen'),
    path('bestellung/<int:object_id>/pdf/ankundensenden',
         views.bestellung_pdf_an_kunden_senden, name='bestellung-pdf-an-kunden-senden'),
    path('bestellung/<int:object_id>/duplizieren',
         views.bestellung_duplizieren, name='bestellung-duplizieren'),
    path('bestellung/<int:object_id>/zu-lieferung',
         views.bestellung_zu_lieferung, name='bestellung-zu-lieferung'),

    path('public/order/<int:object_id>/<order_key>/',
         views.public_view_order, name='public-view-order'),
]
