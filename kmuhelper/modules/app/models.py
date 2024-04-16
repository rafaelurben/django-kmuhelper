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

    ADMIN_TITLE = _("ToDo-Liste")
    ADMIN_DESCRIPTION = _("Unerledigten Notizen")


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

    ADMIN_TITLE = _("Warenausgang")
    ADMIN_DESCRIPTION = _("Nicht versendete Bestellungen")
    ADMIN_ICON = "fa-solid fa-box-open"


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

    ADMIN_TITLE = _("Zahlungseingang")
    ADMIN_DESCRIPTION = _("Nicht bezahlte Bestellungen")
    ADMIN_ICON = "fa-solid fa-hand-holding-dollar"


class App_Stock(Product):
    IS_APP_MODEL = True

    display_current_price = Product.display_current_price
    display_article_number = Product.display_article_number

    class Meta:
        proxy = True
        verbose_name = _("Produkt")
        verbose_name_plural = _("Produkte")
        default_permissions = []

    ADMIN_TITLE = _("Lagerbestand")
    ADMIN_DESCRIPTION = _("Alle Produkte im Lager")


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

    ADMIN_TITLE = _("Wareneingang")
    ADMIN_DESCRIPTION = _("Nicht eingelagerte Lieferungen")
