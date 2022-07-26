from urllib.parse import urlencode

from django.contrib import admin
from django.db import models
from django.forms.models import model_to_dict
from django.shortcuts import redirect
from django.urls import reverse

from kmuhelper import widgets


class CustomModel(models.Model):
    """django.db.models.Model with custom overrides"""

    def pkfill(self, width=6):
        """Get the primary key of this object padded with zeros"""

        return str(self.pk).zfill(width)

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
            from kmuhelper.modules.integrations.woocommerce.utils import is_connected
            if not is_connected():
                del actions['wc_update']
        return actions

    def has_module_permission(self, request):
        """Add option to hide model in default admin"""

        if getattr(self.__class__, 'hidden', False):
            return {}

        return super().has_module_permission(request)

    # Readonly fields

    def get_readonly_fields(self, request, obj=None) -> tuple:
        if "unlock" in request.GET:
            return tuple(self.readonly_fields)
        return tuple(self.readonly_fields) + tuple(self.get_additional_readonly_fields(request, obj))

    def get_additional_readonly_fields(self, request, obj=None) -> list:
        return []

    # Permissions

    NO_CHANGE = False

    def has_change_permission(self, request, obj=None):
        return False if self.NO_CHANGE else super().has_change_permission(request, obj)

    NO_ADD = False

    def has_add_permission(self, request):
        return False if self.NO_ADD else super().has_add_permission(request)

    NO_DELETE = False

    def has_delete_permission(self, request, obj=None):
        return False if self.NO_DELETE else super().has_delete_permission(request, obj)

    NO_VIEW = False

    def has_view_permission(self, request, obj=None):
        return False if self.NO_VIEW else super().has_view_permission(request, obj)


class CustomTabularInline(admin.TabularInline):
    """django.contrib.admin.TabularInline with custom overrides"""

    # Readonly fields

    def get_readonly_fields(self, request, obj=None) -> tuple:
        if "unlock" in request.GET:
            return tuple(self.readonly_fields)
        return tuple(self.readonly_fields) + tuple(self.get_additional_readonly_fields(request, obj))

    def get_additional_readonly_fields(self, request, obj=None) -> list:
        return []

    # Permissions

    NO_CHANGE = False

    def has_change_permission(self, request, obj=None):
        return False if self.NO_CHANGE else super().has_change_permission(request, obj)

    NO_ADD = False

    def has_add_permission(self, request, obj=None):
        return False if self.NO_ADD else super().has_add_permission(request, obj)

    NO_DELETE = False

    def has_delete_permission(self, request, obj=None):
        return False if self.NO_DELETE else super().has_delete_permission(request, obj)

    NO_VIEW = False

    def has_view_permission(self, request, obj=None):
        return False if self.NO_VIEW else super().has_view_permission(request, obj)


class CustomStackedInline(admin.StackedInline):
    """django.contrib.admin.StackedInline with custom overrides"""

    # Readonly fields

    def get_readonly_fields(self, request, obj=None) -> tuple:
        if "unlock" in request.GET:
            return tuple(self.readonly_fields)
        return tuple(self.readonly_fields) + tuple(self.get_additional_readonly_fields(request, obj))

    def get_additional_readonly_fields(self, request, obj=None) -> list:
        return []

    # Permissions

    NO_CHANGE = False

    def has_change_permission(self, request, obj=None):
        return False if self.NO_CHANGE else super().has_change_permission(request, obj)

    NO_ADD = False

    def has_add_permission(self, request, obj=None):
        return False if self.NO_ADD else super().has_add_permission(request, obj)

    NO_DELETE = False

    def has_delete_permission(self, request, obj=None):
        return False if self.NO_DELETE else super().has_delete_permission(request, obj)

    NO_VIEW = False

    def has_view_permission(self, request, obj=None):
        return False if self.NO_VIEW else super().has_view_permission(request, obj)
