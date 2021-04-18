from django import template
from django.urls import reverse

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
def kmuhelper_breadcrumbs(value, args=None):
    url_admin_kmuhelper = reverse(
        'admin:app_list', kwargs={'app_label': 'kmuhelper'})

    if args is None:
        title = "KMUHelper Admin"
        url = url_admin_kmuhelper
    else:
        title, viewname = args.split('|')
        url = reverse(viewname)

    value = "</a>".join(value.split(f'<a href="{url_admin_kmuhelper}">')[
                        1].split("</a>")[1::])
    value = f'<div id="breadcrumbs" class="breadcrumbs"><a href="{url}">{title}</a>' + value
    return value
