from django import template

from kmuhelper import settings
from kmuhelper.integrations.woocommerce.utils import is_connected as is_woocommerce_connected

register = template.Library()

##########

@register.simple_tag(takes_context=True, name="kmuhelper_woocommerce_connected")
def kmuhelper_woocommerce_connected(context=None):
    return is_woocommerce_connected()


@register.simple_tag(takes_context=True, name="kmuhelper_email_show_buttons")
def kmuhelper_email_show_buttons(context=None):
    show = bool(settings.get_db_setting("email-show-buttons"))
    return show


@register.filter
def kmuhelper_replace_start_url(value):
    value = value.replace('<a href="/admin/">Start</a>', '')
    value = value.replace('&rsaquo; <a href="/admin/kmuhelper/">KMUHelper</a>','<a href="/admin/kmuhelper/">KMUHelper Admin</a>')
    return value
