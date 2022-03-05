"Models for KMUHelper settings"

from django.db import models
from django.contrib import admin

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

    char = models.CharField(
        verbose_name="Inhalt (Text)",
        max_length=250,
        default="",
        blank=True,
    )
    text = models.TextField(
        verbose_name="Inhalt (Mehrzeiliger Text)",
        default="",
        blank=True,
    )
    boo = models.BooleanField(
        verbose_name="Inhalt (Wahrheitswert)",
        default=False,
        blank=True,
    )
    inte = models.IntegerField(
        verbose_name="Inhalt (Zahl)",
        default=0,
        blank=True,
    )
    floa = models.FloatField(
        verbose_name="Inhalt (Fliesskommazahl)",
        default=0.0,
        blank=True,
    )
    url = models.URLField(
        verbose_name="Inhalt (Url)",
        default="",
        blank=True,
    )
    email = models.EmailField(
        verbose_name="Inhalt (E-Mail)",
        default="",
        blank=True,
    )

    json = models.JSONField(
        verbose_name="Inhalt (JSON)",
        default=dict,
        blank=True,
        null=True,
    )

    @property
    @admin.display(description="Inhalt")
    def inhalt(self):
        if self.typ == "char":
            return self.char
        if self.typ == "text":
            return self.text
        if self.typ == "bool":
            return self.boo
        if self.typ == "int":
            return self.inte
        if self.typ == "float":
            return self.floa
        if self.typ == "url":
            return self.url
        if self.typ == "email":
            return self.email
        if self.typ == "json":
            return self.json

    @inhalt.setter
    def inhalt(self, var):
        if self.typ == "char":
            self.char = var
        elif self.typ == "text":
            self.text = var
        elif self.typ == "bool":
            self.boo = var
        elif self.typ == "int":
            self.inte = var
        elif self.typ == "float":
            self.floa = var
        elif self.typ == "url":
            self.url = var
        elif self.typ == "email":
            self.email = var
        elif self.typ == "json":
            self.json = var

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
