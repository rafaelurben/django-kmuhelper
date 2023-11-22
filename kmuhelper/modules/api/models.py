import uuid

from django.db import models
from django.contrib import admin

from django.utils.translation import gettext_lazy, gettext

from kmuhelper import settings
from kmuhelper.overrides import CustomModel

_ = gettext_lazy


class ApiKey(CustomModel):
    """Model representing an api key"""

    key = models.UUIDField(
        verbose_name=_("Key"),
        default=uuid.uuid4,
        unique=True,
    )
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=100,
        default="",
        blank=True,
    )
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    read = models.BooleanField(
        verbose_name=_("Read permission?"),
        default=True,
    )
    write = models.BooleanField(
        verbose_name=_("Write permission?"),
        default=False,
    )

    objects = models.Manager()

    @admin.display(description=_("Api key"))
    def __str__(self):
        perms = (
            _("read")
            if self.read and not self.write
            else _("write")
            if self.write and not self.read
            else _("read/write")
            if self.read and self.write
            else _("UNUSABLE")
        )
        return f"{self.name} ({perms}; {self.user.username})"

    @admin.display(description=_("Key preview"))
    def key_preview(self):
        """Get the first and last letters of the key"""
        return str(self.key)[:4] + "..." + str(self.key)[-4:]

    def has_perm(self, *args, **kwargs):
        """Shortcut for self.user.has_perm"""
        return self.user.has_perm(*args, **kwargs)

    def has_perms(self, *args, **kwargs):
        """Shortcut for self.user.has_perms"""
        return self.user.has_perms(*args, **kwargs)

    class Meta:
        verbose_name = _("Api key")
        verbose_name_plural = _("Api keys")
