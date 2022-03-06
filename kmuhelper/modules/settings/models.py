"Models for KMUHelper settings"

from django.db import models
from django.contrib import admin
from django.templatetags.static import static
from django.utils.html import mark_safe, urlize

from kmuhelper.overrides import CustomModel

EINSTELLUNGSTYPEN = [
    ("char", "Text"),
    ("text", "Mehrzeiliger Text"),
    ("bool", "Wahrheitswert"),
    ("int", "Zahl"),
    ("float", "Fliesskommazahl"),
    ("url", "Url"),
    ("email", "E-Mail"),
    ("json", "JSON Daten"),
]


class SettingsBase(CustomModel):
    """Base model for 'Einstellung' and 'Geheime_Einstellung'"""

    id = models.CharField(
        verbose_name="ID",
        max_length=50,
        primary_key=True,
    )
    typ = models.CharField(
        verbose_name="Typ",
        max_length=5,
        default="char",
        choices=EINSTELLUNGSTYPEN,
    )

    content_char = models.CharField(
        verbose_name="Inhalt (Text)",
        max_length=250,
        default="",
        blank=True,
    )
    content_text = models.TextField(
        verbose_name="Inhalt (Mehrzeiliger Text)",
        default="",
        blank=True,
    )
    content_bool = models.BooleanField(
        verbose_name="Inhalt (Wahrheitswert)",
        default=False,
        blank=True,
    )
    content_int = models.IntegerField(
        verbose_name="Inhalt (Zahl)",
        default=0,
        blank=True,
    )
    content_float = models.FloatField(
        verbose_name="Inhalt (Fliesskommazahl)",
        default=0.0,
        blank=True,
    )
    content_url = models.URLField(
        verbose_name="Inhalt (Url)",
        default="",
        blank=True,
    )
    content_email = models.EmailField(
        verbose_name="Inhalt (E-Mail)",
        default="",
        blank=True,
    )

    content_json = models.JSONField(
        verbose_name="Inhalt (JSON)",
        default=dict,
        blank=True,
        null=True,
    )

    @property
    @admin.display(description="Inhalt")
    def content_display(self):
        if self.typ == "bool":
            return mark_safe('<img src="'+static(f"admin/img/icon-{'yes' if self.content_bool else 'no'}.svg")+'" />')
        if self.typ == "url":
            return mark_safe(urlize(self.content_url))
        return self.content
    
    @property
    def content(self):
        return getattr(self, f"content_{self.typ}", "ERROR! Unbekannter Einstellungstyp! Bitte kontaktiere den Entwickler!")

    @content.setter
    def content(self, var):
        if hasattr(self, f"content_{self.typ}"):
            return setattr(self, f"content_{self.typ}", var)

    class Meta:
        abstract = True

    objects = models.Manager()


class Einstellung(SettingsBase):
    """Model representing an editable setting"""

    name = models.CharField(
        verbose_name="Name",
        max_length=200,
    )

    description = models.TextField(
        verbose_name="Beschreibung",
        blank=True,
        default="",
    )

    @admin.display(description="Einstellung")
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Einstellung"
        verbose_name_plural = "Einstellungen"

    objects = models.Manager()

    admin_icon = "fas fa-cog"


class Geheime_Einstellung(SettingsBase):
    """Model representing a hidden setting

    Hidden settings should only be edited through code and are not
    meant to be seen by the user.

    Example usage: WooCommerce authentication data"""

    @admin.display(description="Geheime Einstellung")
    def __str__(self):
        return self.id

    class Meta:
        verbose_name = "Geheime Einstellung"
        verbose_name_plural = "Geheime Einstellungen"
