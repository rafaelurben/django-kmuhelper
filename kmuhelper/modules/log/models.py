from django.contrib.admin.models import LogEntry
from django.db import models
from django.utils.translation import gettext_lazy

_ = gettext_lazy


class AdminLogEntryManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("content_type", "user")
            .filter(content_type__app_label="kmuhelper")
        )


class AdminLogEntry(LogEntry):
    objects = AdminLogEntryManager()

    admin_icon = "fa-solid fa-clock-rotate-left"

    class Meta:
        proxy = True
        verbose_name = _("Admin-Logeintrag")
        verbose_name_plural = _("Admin-Logeinträge")
