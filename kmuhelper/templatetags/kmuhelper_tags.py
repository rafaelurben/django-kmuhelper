from django import template
from django.apps import apps
from django.urls import reverse
from django.utils.html import format_html

from kmuhelper import settings, constants
from kmuhelper.modules import config
from kmuhelper.modules.integrations.woocommerce.utils import (
    is_connected as is_woocommerce_connected,
)

register = template.Library()

##########


@register.simple_tag(name="kmuhelper_woocommerce_connected")
def kmuhelper_woocommerce_connected():
    return is_woocommerce_connected()


@register.simple_tag(name="kmuhelper_has_module_permission", takes_context=True)
def kmuhelper_has_module_permission(context, module_name):
    return config.user_has_module_permission(context.get("user"), module_name)


@register.simple_tag(name="kmuhelper_email_show_buttons", takes_context=True)
def kmuhelper_email_show_buttons(context):
    show = bool(settings.get_db_setting("email-show-buttons"))
    return show and context.get("user").has_perm("kmuhelper.view_email")


@register.simple_tag(name="get_admin_model", takes_context=True)
def get_admin_model(context, model_name=None):
    model = config.get_model_from_context(context, model_name)
    return model


@register.simple_tag(name="get_admin_module", takes_context=True)
def get_admin_module(context, module_name=None):
    model = config.get_module_from_context(context, module_name)
    return model


@register.simple_tag(name="kmuhelper_branding", takes_context=True)
def kmuhelper_branding(context, module_name=None):
    module = config.get_module_from_context(context, module_name)

    url_home = reverse("kmuhelper:home")
    url_module = reverse(module.get("viewname"))

    return format_html(
        '<h1 id="site-name"><a target="_top" href="{}">{}</a> | <a id="app-link" target="_top" href="{}">{}</a></h1>',
        url_home,
        "KMUHelper",
        url_module,
        module.get("title"),
    )


@register.inclusion_tag("kmuhelper/_includes/pagechooser.html", takes_context=False)
def kmuhelper_pagechooser_from_model_list(model_list):
    griddata = []
    for model in model_list:
        try:
            dbmodel = apps.get_model("kmuhelper", model["object_name"])
        except LookupError:
            dbmodel = None
        griddata.append(
            {
                "title": getattr(dbmodel, "ADMIN_TITLE", "") or model["name"],
                "url": model["admin_url"],
                "subtitle": getattr(dbmodel, "ADMIN_DESCRIPTION", ""),
                "icon": getattr(
                    dbmodel, "ADMIN_ICON", "fa-solid fa-circle-exclamation"
                ),
            }
        )
    return {"griddata": [griddata], "pagechooserclass": "smallboxes"}


@register.inclusion_tag("kmuhelper/_includes/pagechooser.html", takes_context=False)
def kmuhelper_pagechooser(griddata, pagechooserclass=""):
    return {"griddata": griddata, "pagechooserclass": pagechooserclass}


@register.simple_tag(name="docs_url", takes_context=False)
def docs_url(path=""):
    return constants.URL_MANUAL + path
