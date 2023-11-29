from django.urls import path, include, re_path

from kmuhelper import startup  # noqa
from kmuhelper import views

#######################

app_name = "kmuhelper"
urlpatterns = [
    path("", views.home, name="home"),
    path("manifest.json", views.manifest, name="manifest"),
    path("login", views.login, name="login"),
    # Developing tools
    path(
        "_templatetest/<path:templatename>", views._templatetest, name="_templatetest"
    ),
    # Main modules
    path("main/", include("kmuhelper.modules.main")),
    path("api/", include("kmuhelper.modules.api")),
    path("app/", include("kmuhelper.modules.app")),
    path("emails/", include("kmuhelper.modules.emails")),
    path("stats/", include("kmuhelper.modules.stats")),
    path("settings/", include("kmuhelper.modules.settings")),
    # Deprecated urls
    path("wc/", include("kmuhelper.modules.integrations.woocommerce")),
    # Integrations
    path(
        "integrations/woocommerce/",
        include("kmuhelper.modules.integrations.woocommerce"),
    ),
    # 404 Not found
    re_path("^.*$", views.error),
]
