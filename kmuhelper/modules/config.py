# KMUHelper modules configuration

from django.apps import apps
from django.shortcuts import reverse
from django.utils.translation import gettext_lazy

_ = gettext_lazy

MODULES = {
    "home": {
        "title": _("Home"),
        "viewname": "kmuhelper:home",
        "model_names": [],
    },
    "main": {
        "title": _("Admin"),
        "viewname": "kmuhelper:main-index",
        "model_names": [
            "ContactPerson",
            "Order",
            "Fee",
            "Customer",
            "Supplier",
            "Supply",
            "Note",
            "Product",
            "ProductCategory",
            "PaymentReceiver",
            "PaymentImport",
        ],
    },
    "emails": {
        "title": _("E-Mails"),
        "viewname": "kmuhelper:email-index",
        "model_names": [
            "EMailTemplate",
            "EMail",
            "Attachment",
        ],
    },
    "app": {
        "title": _("App"),
        "viewname": "kmuhelper:app-index",
        "model_names": [
            "App_ToDo",
            "App_Stock",
            "App_Shipping",
            "App_Arrival",
            "App_IncomingPayments",
        ],
    },
    "settings": {
        "title": _("Einstellungen"),
        "viewname": "kmuhelper:settings",
        "model_names": [
            "Setting",
        ],
    },
    "stats": {
        "title": _("Statistiken"),
        "viewname": "kmuhelper:stats",
        "model_names": [],
    },
    "log": {
        "title": _("Log"),
        "viewname": "kmuhelper:log",
        "model_names": [
            "AdminLogEntry",
        ],
    },
}

MODULE_ASSOCIATIONS = {}


# Utils


def get_model(model_name):
    return apps.get_model("kmuhelper", model_name)


def get_models(model_names):
    models = [get_model(model_name) for model_name in model_names]
    return models


def __load():
    for module_name, module in MODULES.items():
        for model in get_models(module.get("model_names")):
            MODULE_ASSOCIATIONS[model._meta.model_name] = module_name


def get_model_from_context(context, model_name=None):
    if model_name is None:
        model_opts = context.get("opts", None)
        if model_opts is None:
            return None
        model_name = model_opts.model_name
    return get_model(model_name)


def get_module_from_context(context, module_name=None):
    if module_name is None:
        model_opts = context.get("opts", None)
        if model_opts is None:
            module_name = "main"
        else:
            model_name = model_opts.model_name

            if MODULE_ASSOCIATIONS == {}:
                __load()

            module_name = MODULE_ASSOCIATIONS.get(model_name, "main")
    return MODULES.get(module_name)


def get_module_home_context(request, module_name):
    module = MODULES.get(module_name)
    return {
        "app_label": "kmuhelper",
        "app_list": [
            {
                "app_label": "kmuhelper",
                "app_url": reverse(module.get("viewname")),
                "has_module_perms": True,
                "models": [
                    {
                        "add_url": reverse(
                            f"admin:kmuhelper_{model._meta.model_name}_add"
                        ),
                        "admin_url": reverse(
                            f"admin:kmuhelper_{model._meta.model_name}_changelist"
                        ),
                        "name": model._meta.verbose_name_plural,
                        "object_name": model._meta.model_name,
                        "perms": {
                            "add": request.user.has_perm(
                                f"kmuhelper.add_{model._meta.model_name}"
                            ),
                            "change": request.user.has_perm(
                                f"kmuhelper.change_{model._meta.model_name}"
                            ),
                            "delete": request.user.has_perm(
                                f"kmuhelper.delete_{model._meta.model_name}"
                            ),
                            "view": request.user.has_perm(
                                f"kmuhelper.view_{model._meta.model_name}"
                            ),
                        },
                        "view_only": not request.user.has_perm(
                            f"kmuhelper.change_{model._meta.model_name}"
                        ),
                    }
                    for model in get_models(module.get("model_names"))
                    if (
                        request.user.has_perm(
                            f"kmuhelper.view_{model._meta.model_name}"
                        )
                        or request.user.has_perm(
                            f"kmuhelper.change_{model._meta.model_name}"
                        )
                    )
                ],
                "name": module.get("title"),
            }
        ],
        "has_permission": True,
        "is_nav_sidebar_enabled": False,
        "is_popup": False,
        "title": module.get("full_title"),
    }


def user_has_module_permission(user, module_name):
    module = MODULES.get(module_name)
    for model_name in module.get("model_names"):
        name = model_name.lower()
        if user.has_perm(f"kmuhelper.view_{name}") or user.has_perm(
            f"kmuhelper.change_{name}"
        ):
            return True
    return False
