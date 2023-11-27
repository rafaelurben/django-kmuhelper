from django.contrib import admin
from django.db import models
from django.utils.translation import gettext_lazy

from kmuhelper.modules.main.models import Note, Order, Product, Supply

_ = gettext_lazy

#####


class App_ToDoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(done=False)


class App_ToDo(Note):
    IS_APP_MODEL = True

    objects = App_ToDoManager()

    class Meta:
        proxy = True
        verbose_name = _("Notiz")
        verbose_name_plural = _("Notizen")
        default_permissions = []

    admin_title = _("ToDo-Liste")
    admin_description = _("Unerledigten Notizen")


class App_ShippingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_shipped=False)


class App_Shipping(Order):
    IS_APP_MODEL = True

    objects = App_ShippingManager()

    class Meta:
        proxy = True
        verbose_name = _("Bestellung")
        verbose_name_plural = _("Bestellungen")
        default_permissions = []

    admin_title = _("Warenausgang")
    admin_description = _("Nicht versendete Bestellungen")
    admin_icon = "fas fa-box-open"


class App_IncomingPaymentsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_paid=False)


class App_IncomingPayments(Order):
    IS_APP_MODEL = True

    objects = App_IncomingPaymentsManager()

    class Meta:
        proxy = True
        verbose_name = _("Bestellung")
        verbose_name_plural = _("Bestellungen")
        default_permissions = []

    admin_title = _("Zahlungseingang")
    admin_description = _("Nicht bezahlte Bestellungen")
    admin_icon = "fas fa-hand-holding-dollar"


class App_Stock(Product):
    IS_APP_MODEL = True

    @admin.display(description=_("Preis"))
    def get_current_price(self, *args, **kwargs):
        return super().get_current_price(*args, **kwargs)

    @admin.display(description=_("Nr."), ordering="article_number")
    def nr(self):
        return self.article_number

    class Meta:
        proxy = True
        verbose_name = _("Produkt")
        verbose_name_plural = _("Produkte")
        default_permissions = []

    admin_title = _("Lagerbestand")
    admin_description = _("Alle Produkte im Lager")


class App_ArrivalManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_added_to_stock=False)


class App_Arrival(Supply):
    IS_APP_MODEL = True

    objects = App_ArrivalManager()

    class Meta:
        proxy = True
        verbose_name = _("Lieferung")
        verbose_name_plural = _("Lieferungen")
        default_permissions = []

    admin_title = _("Wareneingang")
    admin_description = _("Nicht eingelagerte Lieferungen")
