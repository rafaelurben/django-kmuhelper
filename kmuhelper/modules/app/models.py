from django.contrib import admin
from django.db import models

from kmuhelper.modules.main.models import Notiz, Bestellung, Produkt, Lieferung

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

    admin_title = "ToDo-Liste"


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

    admin_title = "Warenausgang"
    admin_icon = "fas fa-box-open"


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

    admin_title = "Zahlungseingang"
    admin_icon = "fas fa-hand-holding-dollar"


class ToDoLagerbestand(Produkt):
    @admin.display(description="Preis")
    def preis(self, *args, **kwargs):
        return super().preis(*args, **kwargs)

    @admin.display(description="Nr.", ordering="artikelnummer")
    def nr(self):
        return self.artikelnummer

    class Meta:
        proxy = True
        verbose_name = "Produkt"
        verbose_name_plural = "Produkte"
        default_permissions = ('add', 'change', 'view')

    admin_title = "Lagerbestand"


class ToDoLieferungsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(eingelagert=False)


class ToDoLieferung(Lieferung):
    objects = ToDoLieferungsManager()

    class Meta:
        proxy = True
        verbose_name = "Lieferung"
        verbose_name_plural = "Lieferungen"
        default_permissions = ('add', 'change', 'view')

    admin_title = "Wareneingang"
