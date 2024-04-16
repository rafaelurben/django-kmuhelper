from django.contrib import admin
from django.urls import reverse, NoReverseMatch
from django.utils.html import format_html
from django.utils.translation import gettext_lazy
from kmuhelper.modules.log.models import AdminLogEntry
from kmuhelper.overrides import CustomModelAdmin

_ = gettext_lazy


@admin.register(AdminLogEntry)
class AdminLogEntryAdmin(CustomModelAdmin):
    HIDDEN = True

    list_filter = [
        "action_flag",
        "action_time",
        ("content_type", admin.RelatedOnlyFieldListFilter),
        "user",
    ]
    list_display = [
        "action_time",
        "content_type_display",
        "object_id_display",
        "object_repr",
        "action_flag",
        "action_display",
        "user_display",
    ]

    search_fields = ["object_id", "object_repr", "change_message"]

    ordering = ["-action_time"]

    date_hierarchy = "action_time"

    @admin.display(description=_("Typ"), ordering="content_type")
    def content_type_display(self, obj):
        if obj.content_type is None:
            return None
        try:
            url = reverse(
                "admin:{}_{}_changelist".format(
                    obj.content_type.app_label, obj.content_type.model
                )
            )
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.content_type.name,
            )
        except NoReverseMatch:
            return obj.content_type.name

    @admin.display(description=_("ID"), ordering="object_id")
    def object_id_display(self, obj):
        url = obj.get_admin_url()
        if url:
            return format_html(
                '<a href="{}">#{}</a>',
                obj.get_admin_url(),
                obj.object_id,
            )
        else:
            return f"#{obj.object_id}"

    @admin.display(description=_("Aktion"))
    def action_display(self, obj):
        return obj.get_change_message()

    @admin.display(description=_("Benutzer"), ordering="user_id")
    def user_display(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse("admin:auth_user_change", args=(obj.user_id,)),
            str(obj.user),
        )

    # Permissions

    NO_CHANGE = True
    NO_ADD = True
    NO_DELETE = True


#

modeladmins = [
    (AdminLogEntry, AdminLogEntryAdmin),
]
