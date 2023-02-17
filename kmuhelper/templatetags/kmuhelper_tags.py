from django import template
from django.urls import reverse
from django.apps import apps
from django.utils.html import format_html

from kmuhelper import settings
from kmuhelper.modules import config
from kmuhelper.modules.integrations.woocommerce.utils import is_connected as is_woocommerce_connected

register = template.Library()

##########

@register.simple_tag(name="kmuhelper_woocommerce_connected")
def kmuhelper_woocommerce_connected():
    return is_woocommerce_connected()


@register.simple_tag(name="kmuhelper_email_show_buttons")
def kmuhelper_email_show_buttons():
    show = bool(settings.get_db_setting("email-show-buttons"))
    return show

@register.simple_tag(name="get_admin_model", takes_context=True)
def get_admin_model(context, model_name=None):
    model = config.get_model_from_context(context, model_name)
    return model

@register.simple_tag(name="kmuhelper_branding", takes_context=True)
def kmuhelper_branding(context, module_name=None):
    module = config.get_module_from_context(context, module_name)

    url_home = reverse("kmuhelper:home")
    url_module = reverse(module.get('viewname'))

    return format_html('<h1 id="site-name"><a target="_top" href="{}">{}</a> | <a id="app-link" target="_top" href="{}">{}</a></h1>',
                       url_home, 'KMUHelper', url_module, module.get('title'))

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


@register.inclusion_tag('kmuhelper/_includes/pagechooser.html', takes_context=False)
def kmuhelper_pagechooser_from_model_list(model_list):
    griddata = []
    for model in model_list:
        try:
            dbmodel = apps.get_model('kmuhelper', model["object_name"])
        except LookupError:
            dbmodel = None
        griddata.append({
            "title": getattr(dbmodel, "admin_title", "") or model["name"],
            "url": model["admin_url"],
            "subtitle": getattr(dbmodel, "admin_description", ""),
            "icon": getattr(dbmodel, "admin_icon", "fa-solid fa-circle-exclamation"),
        })
    return {"griddata": [griddata], "pagechooserclass": "smallboxes"}


@register.inclusion_tag('kmuhelper/_includes/pagechooser.html', takes_context=False)
def kmuhelper_pagechooser(griddata, pagechooserclass=""):
    return {"griddata": griddata, "pagechooserclass": pagechooserclass}
