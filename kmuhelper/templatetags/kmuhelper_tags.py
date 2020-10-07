# pylint: disable=no-member

from django import template
from ..models import Geheime_Einstellung

register = template.Library()


@register.simple_tag(takes_context=True, name="kmuhelper_woocommerce_connected")
def kmuhelper_woocommerce_connected(context):
    is_connected = bool(
        Geheime_Einstellung.objects.filter(id="wc-url").exists() and
        Geheime_Einstellung.objects.get(id="wc-url").inhalt
    )
    return is_connected


@register.filter
def replace_start_url(value):
    value = value.replace('<a href="/admin/">Start</a>', '')
    value = value.replace('&rsaquo; <a href="/admin/kmuhelper/">KMUHelper</a>','<a href="/admin/kmuhelper/">KMUHelper Admin</a>')
    return value
