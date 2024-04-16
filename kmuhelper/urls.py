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
    path("main/", include("kmuhelper.modules.main.urls")),
    path("api/", include("kmuhelper.modules.api.urls")),
    path("app/", include("kmuhelper.modules.app.urls")),
    path("emails/", include("kmuhelper.modules.emails.urls")),
    path("stats/", include("kmuhelper.modules.stats.urls")),
    path("settings/", include("kmuhelper.modules.settings.urls")),
    path("log", include("kmuhelper.modules.log.urls")),
    # Integrations
    path(
        "integrations/woocommerce/",
        include("kmuhelper.modules.integrations.woocommerce.urls"),
    ),
    # 404 Not found
    re_path("^.*$", views.error),
]
