from urllib.parse import urlencode

from django.contrib import admin
from django.db import models
from django.forms.models import model_to_dict
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _, gettext
from kmuhelper import widgets


class CustomModel(models.Model):
    """django.db.models.Model with custom overrides"""

    PKFILL_WIDTH = 6

    ADMIN_TITLE = None
    ADMIN_DESCRIPTION = None
    ADMIN_ICON = "fa-solid fa-circle-exclamation"

    IS_APP_MODEL = False
    NOTE_RELATION = None

    DICT_FIELDS = []
    DICT_EXCLUDE_FIELDS = []

    @admin.display(description="ID", ordering="pk")
    def pkfill(self, width=None):
        """Get the primary key of this object padded with zeros"""

        return str(self.pk).zfill(width or self.PKFILL_WIDTH)

    @property
    def to_dict(self):
        """Return the model fields as a dict"""

        exclude = self.DICT_EXCLUDE_FIELDS
        fields = self.DICT_FIELDS

        if fields:
            return model_to_dict(self, fields=fields, exclude=exclude)

        return model_to_dict(self, exclude=exclude)

    @property
    def to_query_string(self):
        """Return the model fields as a query string"""

        return urlencode(self.to_dict)

    @admin.display(description=_("🔗 Notiz"), ordering="linked_note")
    def linked_note_html(self):
        is_app = self.IS_APP_MODEL
        rel_name = self.NOTE_RELATION

        if rel_name is None:
            return None

        if hasattr(self, "linked_note"):
            if is_app:
                view_name = "admin:kmuhelper_app_todo_change"
            else:
                view_name = "admin:kmuhelper_note_change"

            link = reverse(view_name, kwargs={"object_id": self.linked_note.pk})
            text = gettext("Notiz #%d") % self.linked_note.pk
        else:
            if is_app:
                view_name = "admin:kmuhelper_app_todo_add"
            else:
                view_name = "admin:kmuhelper_note_add"

            link = reverse(view_name) + f"?from_{rel_name}={self.pk}"
            text = gettext("Notiz erstellen")
        return format_html('<a target="_blank" href="{}">{}</a>', link, text)

    class Meta:
        abstract = True


class CustomModelAdmin(admin.ModelAdmin):
    """django.contrib.admin.ModelAdmin with custom overrides"""

    HIDDEN = False

    formfield_overrides = {models.JSONField: {"widget": widgets.PrettyJSONWidget}}
    list_max_show_all = 1000

    def _get_obj_does_not_exist_redirect(self, request, opts, object_id):
        """Redirect to changelist page instead of admin home if object is not found"""

        super()._get_obj_does_not_exist_redirect(request, opts, object_id)
        info = self.model._meta.app_label, self.model._meta.model_name
        return redirect(reverse("admin:%s_%s_changelist" % info))

    def get_actions(self, request):
        """Make some action not always available"""

        actions = super().get_actions(request)
        if "wc_update" in actions:
            from kmuhelper.modules.integrations.woocommerce.utils import is_connected

            if not is_connected():
                del actions["wc_update"]
        return actions

    def has_module_permission(self, request):
        """Add option to hide model in default admin"""

        if self.HIDDEN:
            return {}

        return super().has_module_permission(request)

    # Readonly fields

    def get_readonly_fields(self, request, obj=None) -> tuple:
        if "unlock" in request.GET:
            return tuple(self.readonly_fields)
        return tuple(self.readonly_fields) + tuple(
            self.get_additional_readonly_fields(request, obj)
        )

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
        return tuple(self.readonly_fields) + tuple(
            self.get_additional_readonly_fields(request, obj)
        )

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
        return tuple(self.readonly_fields) + tuple(
            self.get_additional_readonly_fields(request, obj)
        )

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
