from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import gettext_lazy

from kmuhelper.modules.main.models import Order
from kmuhelper.overrides import CustomModel
from kmuhelper.utils import formatprice

_ = gettext_lazy


#############


class PaymentImport(CustomModel):
    PKFILL_WIDTH = 5

    time_imported = models.DateTimeField(
        verbose_name=_("Importiert am"),
        auto_now_add=True,
    )
    is_processed = models.BooleanField(
        verbose_name=_("Verarbeitet?"),
        default=False,
    )

    data_msgid = models.CharField(
        verbose_name=_("Nachrichtenid"),
        max_length=50,
    )
    data_creationdate = models.DateTimeField(verbose_name=_("Erstellt am"))

    # Display

    @admin.display(description=_("Anzahl Einträge"))
    def entrycount(self):
        if hasattr(self, "entries"):
            return self.entries.count()

    @admin.display(description=_("Zahlungsimport"))
    def __str__(self):
        return f"{self.time_imported} ({self.pk})"

    # Methods

    def get_processing_context(self):
        context = {
            "unknown": [],
            "notfound": [],
            "ready": [],
            "alreadypaid": [],
            "unclear": [],
        }
        for entry in self.entries.order_by("ref").all():
            oid = entry.order_id()
            data = {
                "payment": entry,
                "id": oid,
            }

            if oid is None:
                context["unknown"].append(entry)
            else:
                relatedpayments = (
                    PaymentImportEntry.objects.filter(
                        amount=entry.amount,
                        currency=entry.currency,
                        iban=entry.iban,
                        ref=entry.ref,
                    )
                    .order_by("valuedate")
                    .exclude(pk=entry.pk)
                )
                if relatedpayments.count() > 0:
                    data["relatedpayments"] = relatedpayments.all()

                try:
                    order = Order.objects.get(pk=oid)

                    data["order"] = order

                    if entry.currency == "CHF" and order.is_correct_payment(
                        entry.amount, entry.valuedate
                    ):
                        if order.is_paid:
                            context["alreadypaid"].append(data)
                        else:
                            context["ready"].append(data)
                    else:
                        if order.customer:
                            data["samecustomerorders"] = order.customer.orders.exclude(
                                id=order.id
                            ).filter(is_paid=False)
                        context["unclear"].append(data)
                except ObjectDoesNotExist:
                    context["notfound"].append(data)
        return context

    class Meta:
        verbose_name = _("Zahlungsimport")
        verbose_name_plural = _("Zahlungsimporte")

    ADMIN_ICON = "fa-solid fa-file-import"


class PaymentImportEntry(models.Model):
    parent = models.ForeignKey(
        to="PaymentImport",
        on_delete=models.CASCADE,
        related_name="entries",
    )

    ref = models.CharField(
        verbose_name=_("Referenznummer"),
        max_length=50,
        default="",
    )
    additionalref = models.CharField(
        verbose_name=_("Zusätzliche Referenz"),
        max_length=250,
        default="",
    )
    iban = models.CharField(
        verbose_name=_("IBAN"),
        max_length=22,
        default="",
    )
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=250,
        default="",
    )

    valuedate = models.DateField(
        verbose_name=_("Valuta"),
        null=True,
    )

    amount = models.FloatField(
        verbose_name=_("Betrag"),
    )
    currency = models.CharField(
        verbose_name=_("Währung"),
        max_length=10,
    )

    @admin.display(description=_("Betrag"), ordering="amount")
    def betrag(self):
        return formatprice(self.amount)

    @admin.display(description=_("ID"), ordering="ref")
    def order_id(self):
        if len(self.ref) == 27 and str(self.ref)[-5:-1] == "0000":
            return str(self.ref).lstrip("0")[:-5]
        return None

    @admin.display(description=_("Eintrag"))
    def __str__(self):
        return f"{self.currency} {self.amount} - {self.order_id()} - {self.name} ({self.pk})"

    class Meta:
        verbose_name = _("Zahlungsimport-Eintrag")
        verbose_name_plural = _("Zahlungsimport-Einträge")
        default_permissions = ()

    objects = models.Manager()
