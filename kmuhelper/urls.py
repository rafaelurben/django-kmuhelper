from django.urls import path, include, re_path

from kmuhelper import views
from kmuhelper import startup

#######################

app_name = 'kmuhelper'
urlpatterns = [
    path('',        views.home, name="home"),

    # Developing tools
    path('_templatetest/<path:templatename>',
                    views._templatetest, name="_templatetest"),

    # Main modules
    path('',        include('kmuhelper.main')),
    path('api/',    include('kmuhelper.api')),
    path('app/',    include('kmuhelper.app')),
    path('emails/', include('kmuhelper.emails')),
    path('stats/',  include('kmuhelper.stats')),

    # Deprecated urls
    path('wc/',     include('kmuhelper.integrations.woocommerce')),

    # Integrations
    path('integrations/woocommerce/',
                    include('kmuhelper.integrations.woocommerce')),

    # 404 Not found
    re_path('^.*$', views.error)
]
