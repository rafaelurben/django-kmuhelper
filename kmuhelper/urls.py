from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings

from kmuhelper import views
from kmuhelper.main.models import Einstellung, Geheime_Einstellung

#####

from rich import print

prefix = "[deep_pink4][KMUHelper Urls][/] -"

def log(string, *args):
    print(prefix, string, *args)

# Einstellungen festlegen

try:
    Einstellung.objects.get_or_create(id="wc-url", typ="url", name="WooCommerce Shop-Url")
    Einstellung.objects.get_or_create(id="email-stock-warning-receiver", typ="email", name="E-Mail für Warnungen zum Lagerbestand")
    Einstellung.objects.get_or_create(id="email-show-buttons", typ="bool", name="E-Mail Knöpfe anzeigen")

    Geheime_Einstellung.objects.get_or_create(id="wc-consumer_key")
    Geheime_Einstellung.objects.get_or_create(id="wc-consumer_secret")
    Geheime_Einstellung.objects.get_or_create(id="wc-url")
except Exception as e:
    log("[urls.py] - Error while adding settings:", e)


#######################

app_name = 'kmuhelper'
urlpatterns = [
    path('', views.home, name="home"),
    path('admin/', views.admin, name="admin"),

    path('_templatetest/<path:templatename>', views._templatetest, name="_templatetest"),

    path('',        include('kmuhelper.main')),
    path('api/',    include('kmuhelper.api')),
    path('app/',    include('kmuhelper.app')),
    path('emails/', include('kmuhelper.emails')),
    path('stats/',  include('kmuhelper.stats')),
    path('wc/',     include('kmuhelper.integrations.woocommerce')),
]
