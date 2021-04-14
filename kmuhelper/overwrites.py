from urllib.parse import urlencode

from django.contrib import admin
from django.db import models
from django.forms.models import model_to_dict
from django.shortcuts import redirect
from django.urls import reverse


class CustomModel(models.Model):
    """django.db.models.Model with custom overwrites"""

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
    """django.contrib.admin.ModelAdmin with custom overwrites"""

    def _get_obj_does_not_exist_redirect(self, request, opts, object_id):
        """Redirect to changelist page instead of admin home if object is not found"""

        super()._get_obj_does_not_exist_redirect(request, opts, object_id)
        info = self.model._meta.app_label, self.model._meta.model_name
        return redirect(reverse('admin:%s_%s_changelist' % info))
