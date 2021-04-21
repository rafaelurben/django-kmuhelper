from rich import print

from django.contrib import admin, messages
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from django.utils.html import format_html, mark_safe

from kmuhelper.main.models import Bestellung
from kmuhelper.overrides import CustomModel
from kmuhelper.utils import formatprice


#############


class PaymentImport(CustomModel):
    time_imported = models.DateTimeField(
        verbose_name="Importiert am",
        auto_now_add=True,
    )
    is_processed = models.BooleanField(
        verbose_name="Verarbeitet?",
        default=False,
    )

    data_msgid = models.CharField(
        verbose_name="Nachrichtenid",
        max_length=50,
    )
    data_creationdate = models.DateTimeField(
        verbose_name="Erstellt am"
    )

    # Display

    @admin.display(description="Anzahl Einträge")
    def entrycount(self):
        if hasattr(self, 'entries'):
            return self.entries.count()

    @admin.display(description="Zahlungsimport")
    def __str__(self):
        return f"{self.time_imported} ({self.pk})"

    # Methods

    def get_processing_context(self):
        context = {
            'unknown': [],
            'notfound': [],
            'ready': [],
            'alreadypaid': [],
            'unclear': [],
        }
        for entry in self.entries.all():
            oid = entry.order_id()
            data = {
                'payment': entry,
                'id': oid,
            }
            if oid is None:
                context['unknown'].append(entry)
            else:
                try:
                    bestellung = Bestellung.objects.get(pk=oid)

                    data['order'] = bestellung

                    if bestellung.fix_summe == entry.amount and entry.currency == 'CHF':
                        if bestellung.bezahlt:
                            context['alreadypaid'].append(data)
                        else:
                            context['ready'].append(data)
                    else:
                        if bestellung.kunde:
                            data['relatedorders'] = bestellung.kunde.bestellungen.exclude(
                                id=bestellung.id).filter(bezahlt=False)
                        context['unclear'].append(data)
                except ObjectDoesNotExist:
                    context['notfound'].append(data)
        return context

    class Meta:
        verbose_name = "Zahlungsimport"
        verbose_name_plural = "Zahlungsimporte"


class PaymentImportEntry(models.Model):
    parent = models.ForeignKey(
        to='PaymentImport',
        on_delete=models.CASCADE,
        related_name='entries',
    )

    ref = models.CharField(
        verbose_name="Referenznummer",
        max_length=50,
    )
    iban = models.CharField(
        verbose_name="IBAN",
        max_length=22,
    )
    name = models.CharField(
        verbose_name="Name",
        max_length=100,
    )

    amount = models.FloatField(
        verbose_name="Betrag",
    )
    currency = models.CharField(
        verbose_name="Währung",
        max_length=10,
    )

    @admin.display(description="Betrag", ordering='amount')
    def betrag(self):
        return formatprice(self.amount)

    @admin.display(description="ID", ordering='ref')
    def order_id(self):
        if (
                len(self.ref) == 27 and
                str(self.ref)[-5:-1] == '0000'
        ):
            return str(self.ref).lstrip('0')[:-5]
        return None

    @admin.display(description="Eintrag")
    def __str__(self):
        return f"{self.currency} {self.amount} - {self.order_id()} - {self.name}"

    class Meta:
        verbose_name = "Zahlungsimport-Eintrag"
        verbose_name_plural = "Zahlungsimport-Einträge"
        default_permissions = ()

    objects = models.Manager()
