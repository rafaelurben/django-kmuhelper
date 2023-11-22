from django import forms
from django.utils.translation import gettext_lazy

from kmuhelper.modules.settings.models import Setting
from kmuhelper.modules.settings.utils import set_db_setting

_ = gettext_lazy


class WooCommerceSettingsForm(forms.Form):
    fieldsets = [
        {
            "name": _("WooCommerce-Einstellungen"),
            "fields": ["wc-url", "wc-webhook-secret"],
            "classes": "wide",
        },
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for obj in Setting.objects.filter(id__in=["wc-url", "wc-webhook-secret"]):
            self.fields[obj.id] = obj.get_field()

    def save_settings(self):
        for key, value in self.cleaned_data.items():
            set_db_setting(key, value)
