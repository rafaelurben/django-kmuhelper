from django.contrib import admin

from kmuhelper.integrations.xmlimport.models import XMLFile, XMLFileEntry

@admin.register(XMLFile)
class XMLFileAdmin(admin.ModelAdmin):
    list_display = ()
    list_filter = ()

    def has_module_permission(self, request):
        return {}

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        from django.urls import path
        from django.views.decorators.clickjacking import xframe_options_sameorigin as allow_iframe
        from functools import update_wrapper

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(allow_iframe(view))(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        return [
            path('', wrap(self.changelist_view),
                 name='%s_%s_changelist' % info),
            path('add/', wrap(self.add_view), 
                 name='%s_%s_add' % info),
            path('autocomplete/', wrap(self.autocomplete_view),
                 name='%s_%s_autocomplete' % info),
            path('<path:object_id>/history/', wrap(self.history_view), 
                 name='%s_%s_history' % info),
            path('<path:object_id>/delete/', wrap(self.delete_view), 
                 name='%s_%s_delete' % info),
            path('<path:object_id>/change/', wrap(self.change_view),
                 name='%s_%s_change' % info),
        ]


#

modeladmins = [
    (XMLFile, XMLFileAdmin),
]
