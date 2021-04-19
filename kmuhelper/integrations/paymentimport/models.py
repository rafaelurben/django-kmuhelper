from xml.etree.ElementTree import parse as parse_xml
from rich import print

from django.contrib import admin
from django.core.validators import FileExtensionValidator
from django.db import models

from kmuhelper.main.models import Bestellung
from kmuhelper.overrides import CustomModel


def log(string, *args):
    print("[deep_pink4][KMUHelper Paymentimport][/] -", string, *args)

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

    xmlfile = models.FileField(
        verbose_name="Datei",
        upload_to="paymentimport/",
        validators=[FileExtensionValidator(['xml'])],
    )



    @admin.display(description="Anzahl Einträge")
    def entrycount(self):
        if hasattr(self, 'entries'):
            return self.entries.count()

    @admin.display(description="Zahlungsimport", ordering='title')
    def __str__(self):
        return f"{self.title} ({self.pk})"

    # Methods

    def parse(self, request=None):
        try:
            tree = parse_xml(self.xmlfile)
            root = tree.getroot()
            msg = root.find('{*}BkToCstmrDbtCdtNtfctn')
            log("Start parsing...")
            for notif in msg.findall('{*}Ntfctn'):
                iban = notif.find('./{*}Acct/{*}Id/{*}IBAN').text
                log("Parsing notification for account", iban)
                for entry in notif.findall('{*}Ntry'):
                    ispositive = entry.find('{*}CdtDbtInd').text == 'DBIT'
                    # _amt = entry.find('{*}Amt')
                    # amount = _amt.text
                    # currency = _amt.attrib.get('Ccy', 'CHF')
                    # if ispositive:
                    #     log("Saving positive", amount, currency)
                    # else:
                    #     log("Skipping negative:", amount, currency)
                    if ispositive:
                        for ntrydtls in entry.findall('{*}NtryDtls'):
                            for txdtls in ntrydtls.findall('{*}TxDtls'):
                                log(txdtls)
                                log(txdtls.find('{*}AmtDtls'))
                                _amt = txdtls.find('./{*}AmtDtls/{*}TxAmt/{*}Amt')
                                amount = _amt.text
                                currency = _amt.attrib.get('Ccy', 'CHF')
                                log(amount, currency)

            return True
        except AttributeError as error:
            log(error)
            return False

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

    objects = models.Manager()
