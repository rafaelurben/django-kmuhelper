from django import forms

from kmuhelper.modules.settings.models import Einstellung
from kmuhelper.modules.settings.constants import SETTINGS, SETTINGS_FIELDSETS
from kmuhelper.modules.settings.utils import get_db_setting, set_db_setting

class SettingsForm(forms.Form):
    fieldsets = SETTINGS_FIELDSETS
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for obj in Einstellung.objects.all():
            if obj.id in SETTINGS:
                self.fields[obj.id] = obj.get_field()

    def save_settings(self):
        for key, value in self.cleaned_data.items():
            if key in SETTINGS:
                set_db_setting(key, value)
