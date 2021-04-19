from xml.etree.ElementTree import parse as parse_xml, ParseError

from rich import print

from django import forms
from django.contrib import messages
from django.core.validators import FileExtensionValidator
from django.shortcuts import redirect, reverse


def log(string, *args):
    print("[deep_pink4][KMUHelper Paymentimport][/] -", string, *args)

#####


class CamtUploadForm(forms.Form):
    """Form for uploading and processing camt.054.001.02 files"""

    file = forms.FileField(
        label="XML-Datei",
        help_text="Die Datei muss nach dem camt.054.001.02 Standard aufgebaut sein.",
        validators=[FileExtensionValidator(['xml'])],
    )

    def clean_file(self):
        file = self.cleaned_data.get("file")

        if file:
            try:
                tree = parse_xml(file)
                root = tree.getroot()
                msg = root.find('{*}BkToCstmrDbtCdtNtfctn')

                if 'camt.054.001.02' not in str(root.attrib) or msg is None:
                    raise forms.ValidationError(
                        "Die Datei liegt nicht im korrekten Format vor!"
                    )

                self.cleaned_data["camt.054.001.02"] = msg
            except ParseError:
                raise forms.ValidationError(
                    "Die Datei kann nicht verarbeitet werden!"
                )

        return file

    def create_payment_import_and_redirect(self, request):
        msg = self.cleaned_data.get('camt.054.001.02')
        try:
            log("Start processing", msg)
            for notif in msg.findall('{*}Ntfctn'):
                iban = notif.find('./{*}Acct/{*}Id/{*}IBAN').text
                log("Processing notification for account", iban)
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
                                _amt = txdtls.find(
                                    './{*}AmtDtls/{*}TxAmt/{*}Amt')
                                amount = _amt.text
                                currency = _amt.attrib.get('Ccy', 'CHF')
                                log(amount, currency)
            # TODO: Create PaymentImport and redirect to its change page
            return redirect(reverse('admin:kmuhelper_paymentimport_changelist'))
        except AttributeError as error:
            log(error)
            messages.error(request, f"Bei der Verarbeitung ist ein Fehler aufgetreten: {error}")
            return redirect(reverse('admin:kmuhelper_paymentimport_upload'))
