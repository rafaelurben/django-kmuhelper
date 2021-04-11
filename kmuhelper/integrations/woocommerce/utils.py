from kmuhelper.main.models import Geheime_Einstellung


def is_connected(context=None):
    return bool(
        Geheime_Einstellung.objects.filter(id="wc-url").exists() and
        Geheime_Einstellung.objects.get(id="wc-url").inhalt
    )
