from django.urls import path, include
from django.contrib.admin import site
from django.contrib.auth import views as auth_views
from django.conf import settings

from kmuhelper import admin
from kmuhelper import views
from kmuhelper import startup

#######################

app_name = 'kmuhelper'
urlpatterns = [
    path('',        views.home, name="home"),
    path('admin/',  views.admin, name="admin"),

    path('_templatetest/<path:templatename>', views._templatetest, name="_templatetest"),

    path('',        include('kmuhelper.main')),
    path('api/',    include('kmuhelper.api')),
    path('app/',    include('kmuhelper.app')),
    path('emails/', include('kmuhelper.emails')),
    path('stats/',  include('kmuhelper.stats')),
    path('wc/',     include('kmuhelper.integrations.woocommerce')),
]
