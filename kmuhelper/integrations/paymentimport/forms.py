from defusedxml.ElementTree import parse as parse_xml, ParseError

from rich import print

from django import forms
from django.contrib import messages
from django.core.validators import FileExtensionValidator
from django.shortcuts import redirect, reverse

from kmuhelper.integrations.paymentimport.models import PaymentImport, PaymentImportEntry


def log(string, *args):
    print("[deep_pink4][KMUHelper Paymentimport][/] -", string, *args)

#####


class CamtUploadForm(forms.Form):
    """Form for uploading and processing camt.054.001.02 files"""

    file = forms.FileField(
        label="XML-Datei",
        help_text="Die Datei muss nach dem camt.053.001.04 Standard aufgebaut sein und "
                  "Detailinformationen enthalten.",
        validators=[FileExtensionValidator(['xml'])],
    )

    def clean_file(self):
        file = self.cleaned_data.get("file")

        if file:
            try:
                tree = parse_xml(file)
                root = tree.getroot()
                msg = root.find('{*}BkToCstmrStmt')

                if 'camt.053.001.04' not in str(root.tag) or msg is None:
                    raise forms.ValidationError(
                        "Die Datei liegt nicht im korrekten Format vor!"
                    )

                self.cleaned_data["camt.053.001.04"] = msg
            except ParseError as error:
                raise forms.ValidationError(
                    f"Die Datei kann nicht verarbeitet werden! {error}"
                )

        return file

    def create_payment_import_and_redirect(self, request):
        msg = self.cleaned_data.get('camt.053.001.04')
        try:
            msgid = msg.find('./{*}GrpHdr/{*}MsgId').text
            creationdate = msg.find('./{*}GrpHdr/{*}CreDtTm').text
            log(
                f"Start processing - Message id: '{msgid}' - Creation date: '{creationdate}'")

            dbentry = PaymentImport.objects.create(
                data_msgid=msgid,
                data_creationdate=creationdate,
            )

            for entry in msg.findall('./{*}Stmt/{*}Ntry'):
                description = entry.find('{*}AddtlNtryInf').text
                iscredit = entry.find('{*}CdtDbtInd').text == 'CRDT'
                log(f"- Entry {iscredit} Description: '{description}'")
                if iscredit:
                    if description in ['Sammelbuchung QR-Rechnung mit QR-Referenz']:
                        for txdtls in entry.findall('./{*}NtryDtls/{*}TxDtls'):
                            _amt = txdtls.find('{*}Amt')
                            amount = _amt.text
                            currency = _amt.attrib.get('Ccy', 'CHF')
                            name = txdtls.find(
                                './{*}RltdPties/{*}Dbtr/{*}Nm').text
                            iban = txdtls.find(
                                './{*}RltdPties/{*}DbtrAcct/{*}Id/{*}IBAN').text
                            ref = txdtls.find(
                                './{*}RmtInf/{*}Strd/{*}CdtrRefInf/{*}Ref').text
                            log(f"- - {amount} {currency} '{name}' '{iban}' {ref}")

                            PaymentImportEntry.objects.create(
                                parent=dbentry,
                                name=name,
                                iban=iban,
                                ref=ref,
                                amount=float(amount),
                                currency=currency,
                            )

            return redirect(reverse('admin:kmuhelper_paymentimport_upload', args=[dbentry.pk]))
        except AttributeError as error:
            log(error)
            messages.error(
                request, f"Bei der Verarbeitung ist ein Fehler aufgetreten: {error}")
            return redirect(reverse('admin:kmuhelper_paymentimport_upload'))
