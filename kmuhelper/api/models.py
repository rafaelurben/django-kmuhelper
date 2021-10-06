import uuid

from django.db import models
from django.contrib import admin

from kmuhelper import settings
from kmuhelper.overrides import CustomModel


class ApiKey(CustomModel):
    """Model representing an api key"""

    key = models.UUIDField(
        verbose_name="Key",
        default=uuid.uuid4,
        unique=True,
    )
    name = models.CharField(
        verbose_name="Name",
        max_length=100,
        default="",
        blank=True,
    )
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    read = models.BooleanField(
        verbose_name="Read permission?",
        default=True,
    )
    write = models.BooleanField(
        verbose_name="Write permission?",
        default=False,
    )

    objects = models.Manager()

    @admin.display(description="Api key")
    def __str__(self):
        perms = "read" if self.read and not self.write else "write" if self.write and not self.read else "read/write" if self.read and self.write else "UNUSABLE"
        return f"{self.name} ({perms}; {self.user.username})"

    @admin.display(description="Key preview")
    def key_preview(self):
        """Get the first and last letters of the key"""
        return str(self.key)[:4]+"..."+str(self.key)[-4:]

    def has_perm(self, *args, **kwargs):
        """Shortcut for self.user.has_perm"""
        return self.user.has_perm(*args, **kwargs)

    def has_perms(self, *args, **kwargs):
        """Shortcut for self.user.has_perms"""
        return self.user.has_perms(*args, **kwargs)

    class Meta:
        verbose_name = "Api key"
        verbose_name_plural = "Api keys"
