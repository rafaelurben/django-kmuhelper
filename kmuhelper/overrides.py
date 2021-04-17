from urllib.parse import urlencode

from django.contrib import admin
from django.db import models
from django.forms.models import model_to_dict
from django.shortcuts import redirect
from django.urls import reverse

from kmuhelper import widgets


class CustomModel(models.Model):
    """django.db.models.Model with custom overrides"""

    @property
    def to_dict(self):
        """Return the model fields as a dict"""

        exclude = getattr(self.__class__, "DICT_EXCLUDE_FIELDS", list())
        fields = getattr(self.__class__, "DICT_FIELDS", list())

        if fields:
            return model_to_dict(self, fields=fields, exclude=exclude)

        return model_to_dict(self, exclude=exclude)

    @property
    def to_query_string(self):
        """Return the model fields as a query string"""

        return urlencode(self.to_dict)

    class Meta:
        abstract = True


class CustomModelAdmin(admin.ModelAdmin):
    """django.contrib.admin.ModelAdmin with custom overrides"""

    formfield_overrides = {
        models.JSONField: {'widget': widgets.PrettyJSONWidget}
    }

    def _get_obj_does_not_exist_redirect(self, request, opts, object_id):
        """Redirect to changelist page instead of admin home if object is not found"""

        super()._get_obj_does_not_exist_redirect(request, opts, object_id)
        info = self.model._meta.app_label, self.model._meta.model_name
        return redirect(reverse('admin:%s_%s_changelist' % info))

    def get_actions(self, request):
        """Make some action not always available"""

        actions = super().get_actions(request)
        if 'wc_update' in actions:
            from kmuhelper.integrations.woocommerce.utils import is_connected as woocommerce_connected
            if not woocommerce_connected():
                del actions['wc_update']
        return actions

    def has_module_permission(self, request):
        """Add option to hide model in default admin"""

        if getattr(self.__class__, 'hidden', False):
            return {}

        return super().has_module_permission(request)
