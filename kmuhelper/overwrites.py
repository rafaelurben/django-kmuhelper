from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

class CustomModelAdmin(admin.ModelAdmin):
    """django.contrib.admin.ModelAdmin with custom overwrites"""

    def _get_obj_does_not_exist_redirect(self, request, opts, object_id):
        """Redirect to changelist page instead of admin home if object is not found"""

        super()._get_obj_does_not_exist_redirect(request, opts, object_id)
        info = self.model._meta.app_label, self.model._meta.model_name
        return redirect(reverse('admin:%s_%s_changelist' % info))
