from rich import print

from django.contrib import admin
from django.db import models

from kmuhelper.main.models import Bestellung
from kmuhelper.overrides import CustomModel


#############


class PaymentImport(CustomModel):
    title = models.CharField(
        verbose_name="Titel",
        max_length=50,
    )
    is_parsed = models.BooleanField(
        verbose_name="Verarbeitet?",
        default=False,
    )
    time_imported = models.DateTimeField(
        verbose_name="Importiert am",
        auto_now_add=True,
    )

    # Display

    # @admin.display(description="Anzahl Einträge")
    # def entrycount(self):
    #     if hasattr(self, 'entries'):
    #         return self.entries.count()

    @admin.display(description="Zahlungsimport", ordering='title')
    def __str__(self):
        return f"{self.title} ({self.pk})"

    # Methods

    def process(self, request):
        pass

    class Meta:
        verbose_name = "Zahlungsimport"
        verbose_name_plural = "Zahlungsimporte"


class PaymentImportEntry(models.Model):
    referenznummer = models.CharField(
        verbose_name="Referenznummer",
        max_length=50,
    )
    betrag = models.FloatField(
        verbose_name="Betrag",
    )

    class Meta:
        verbose_name = "Zahlungsimport-Eintrag"
        verbose_name = "Zahlungsimport-Einträge"
        default_permissions = ()

    objects = models.Manager()
