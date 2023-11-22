from django import forms

from kmuhelper.modules.settings.models import Setting
from kmuhelper.modules.settings.constants import SETTINGS_FIELDSETS
from kmuhelper.modules.settings.utils import set_db_setting


class SettingsForm(forms.Form):
    fieldsets = SETTINGS_FIELDSETS

    _fieldlist = []
    for fieldset in fieldsets:
        _fieldlist += fieldset["fields"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for obj in Setting.objects.filter(id__in=self._fieldlist):
            self.fields[obj.id] = obj.get_field()

    def save_settings(self):
        for key, value in self.cleaned_data.items():
            set_db_setting(key, value)
