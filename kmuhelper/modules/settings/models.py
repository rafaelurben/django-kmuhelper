"Models for KMUHelper settings"

from django import forms
from django.contrib import admin
from django.db import models
from django.templatetags.static import static
from django.utils.html import mark_safe, urlize
from django.utils.translation import gettext_lazy
from kmuhelper.modules.settings.constants import SETTINGS
from kmuhelper.overrides import CustomModel

_ = gettext_lazy

SETTINGTYPES = [
    ("char", _("Text")),
    ("text", _("Mehrzeiliger Text")),
    ("bool", _("Wahrheitswert")),
    ("int", _("Zahl")),
    ("float", _("Fliesskommazahl")),
    ("url", _("Url")),
    ("email", _("E-Mail")),
    ("json", _("JSON Daten")),
]


class SettingBase(CustomModel):
    """Base model for 'Setting' and 'SettingHidden'"""

    id = models.CharField(
        verbose_name=_("ID"),
        max_length=50,
        primary_key=True,
    )
    typ = models.CharField(
        verbose_name=_("Typ"),
        max_length=5,
        default="char",
        choices=SETTINGTYPES,
    )

    content_char = models.CharField(
        verbose_name=_("Inhalt (Text)"),
        max_length=250,
        default="",
        blank=True,
    )
    content_text = models.TextField(
        verbose_name=_("Inhalt (Mehrzeiliger Text)"),
        default="",
        blank=True,
    )
    content_bool = models.BooleanField(
        verbose_name=_("Inhalt (Wahrheitswert)"),
        default=False,
        blank=True,
    )
    content_int = models.IntegerField(
        verbose_name=_("Inhalt (Zahl)"),
        default=0,
        blank=True,
    )
    content_float = models.FloatField(
        verbose_name=_("Inhalt (Fliesskommazahl)"),
        default=0.0,
        blank=True,
    )
    content_url = models.URLField(
        verbose_name=_("Inhalt (Url)"),
        default="",
        blank=True,
    )
    content_email = models.EmailField(
        verbose_name=_("Inhalt (E-Mail)"),
        default="",
        blank=True,
    )

    content_json = models.JSONField(
        verbose_name=_("Inhalt (JSON)"),
        default=dict,
        blank=True,
        null=True,
    )

    @property
    @admin.display(description=_("Inhalt"))
    def content_display(self):
        if self.typ == "bool":
            return mark_safe(
                '<img src="'
                + static(f"admin/img/icon-{'yes' if self.content_bool else 'no'}.svg")
                + '" />'
            )
        if self.typ == "url":
            return mark_safe(urlize(self.content_url))
        return self.content

    @property
    def content(self):
        return getattr(
            self,
            f"content_{self.typ}",
            _("ERROR! Unbekannter Einstellungstyp! Bitte kontaktiere den Entwickler!"),
        )

    @content.setter
    def content(self, var):
        if hasattr(self, f"content_{self.typ}"):
            return setattr(self, f"content_{self.typ}", var)

    class Meta:
        abstract = True

    objects = models.Manager()


class Setting(SettingBase):
    """Model representing an editable setting"""

    @property
    def info(self):
        "Get the info dict for this setting"
        return SETTINGS.get(self.id, {})

    @property
    @admin.display(description=_("Einstellung"))
    def name(self):
        s = self.info.get("name", _("(unbekannte Einstellung)"))
        return mark_safe(s)

    @property
    @admin.display(description=_("Beschreibung"))
    def description(self):
        s = self.info.get("description", _("(unbekannte Einstellung)"))
        s = s.replace("\n", "<br />")
        return mark_safe(s)

    def get_field(self):
        "Get the corresponding form field for this setting"

        opt = {
            "label": self.name,
            "required": False,
            "help_text": self.description,
            "initial": self.content,
        }

        if self.typ == "char":
            return forms.CharField(**opt)
        if self.typ == "text":
            return forms.CharField(widget=forms.Textarea, **opt)
        if self.typ == "bool":
            return forms.BooleanField(**opt)
        if self.typ == "int":
            return forms.IntegerField(**opt)
        if self.typ == "float":
            return forms.FloatField(**opt)
        if self.typ == "url":
            return forms.URLField(**opt)
        if self.typ == "email":
            return forms.EmailField(**opt)
        if self.typ == "json":
            return forms.JSONField(**opt)
        raise ValueError("Unknown setting type! Can't get field!")

    @admin.display(description=_("Einstellung"))
    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = _("Einstellung")
        verbose_name_plural = _("Einstellungen")
        default_permissions = ("change",)

    objects = models.Manager()

    ADMIN_ICON = "fa-solid fa-cog"


class SettingHidden(SettingBase):
    """Model representing a hidden setting

    Hidden settings should only be edited through code and are not
    meant to be seen by the user.

    Example usage: WooCommerce authentication data"""

    class Meta:
        verbose_name = _("Versteckte Einstellung")
        verbose_name_plural = _("Versteckte Einstellungen")
        default_permissions = ()
