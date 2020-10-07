# pylint: disable=no-member

from django.db import models
from django.utils.html import mark_safe

from .models import Notiz, Bestellung, Produkt, Lieferung

#####

class ToDoNotizManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(erledigt=False)


class ToDoNotiz(Notiz):
    objects = ToDoNotizManager()

    class Meta:
        proxy = True
        verbose_name = "Notiz"
        verbose_name_plural = "Notizen"
        default_permissions = ('add', 'change', 'view')


class ToDoVersandManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(versendet=False)


class ToDoVersand(Bestellung):
    objects = ToDoVersandManager()

    class Meta:
        proxy = True
        verbose_name = "Bestellung"
        verbose_name_plural = "Bestellungen"
        default_permissions = ('add', 'change', 'view')


class ToDoZahlungseingangManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(bezahlt=False)


class ToDoZahlungseingang(Bestellung):
    objects = ToDoZahlungseingangManager()

    class Meta:
        proxy = True
        verbose_name = "Bestellung"
        verbose_name_plural = "Bestellung"
        default_permissions = ('add', 'change', 'view')


class ToDoLagerbestand(Produkt):
    def html_todo_notiz_erstellen(self):
        link = self.get_todo_notiz_link()
        return mark_safe('<a target="_blank" href="'+link+'">+ ToDo Notiz</a>')
    html_todo_notiz_erstellen.short_description = "ToDo Notiz Erstellen"

    def preis(self, *args, **kwargs):
        return super().preis(*args, **kwargs)
    preis.short_description = "Preis"

    def nr(self):
        return self.artikelnummer
    nr.short_description = "Nr."

    class Meta:
        proxy = True
        verbose_name = "Produkt"
        verbose_name_plural = "Produkte"
        default_permissions = ('add', 'change', 'view')


class ToDoLieferungsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(eingelagert=False)


class ToDoLieferung(Lieferung):
    def html_todo_notiz_erstellen(self):
        link = self.get_todo_notiz_link()
        return mark_safe('<a target="_blank" href="'+link+'">+ ToDo Notiz</a>')
    html_todo_notiz_erstellen.short_description = "ToDo Notiz Erstellen"

    objects = ToDoLieferungsManager()

    class Meta:
        proxy = True
        verbose_name = "Lieferung"
        verbose_name_plural = "Lieferungen"
        default_permissions = ('add', 'change', 'view')
