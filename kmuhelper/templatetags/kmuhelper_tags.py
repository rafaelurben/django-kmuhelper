from django import template
from kmuhelper.main.models import Geheime_Einstellung, Einstellung

register = template.Library()

##########

@register.simple_tag(takes_context=True, name="kmuhelper_woocommerce_connected")
def kmuhelper_woocommerce_connected(context):
    is_connected = bool(
        Geheime_Einstellung.objects.filter(id="wc-url").exists() and
        Geheime_Einstellung.objects.get(id="wc-url").inhalt
    )
    return is_connected


@register.simple_tag(takes_context=True, name="kmuhelper_email_show_buttons")
def kmuhelper_email_show_buttons(context):
    show = bool(
        Einstellung.objects.filter(id="email-show-buttons").exists() and
        Einstellung.objects.get(id="email-show-buttons").inhalt
    )
    return show


@register.filter
def kmuhelper_replace_start_url(value):
    value = value.replace('<a href="/admin/">Start</a>', '')
    value = value.replace('&rsaquo; <a href="/admin/kmuhelper/">KMUHelper</a>','<a href="/admin/kmuhelper/">KMUHelper Admin</a>')
    return value
