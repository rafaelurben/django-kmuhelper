from reportlab.platypus import Flowable
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import qr
from reportlab.graphics import renderPDF

from django.utils.translation import pgettext

from kmuhelper.utils import formatprice
import kmuhelper.modules.main.models as models


class QRInvoiceFlowable(Flowable):
    "A Flowable that draws a Swiss QR-Invoice."

    def __init__(
        self,
        total,
        address,
        payment_receiver,
        billing_information,
        qr_refernce_number="",
        unstructured_message="",
        add_cut_info=True,
    ):
        self.width = 210
        self.height = 110
        self._fixedWidth = 210
        self._fixedHeight = 110

        self.total: float = total
        self.address: dict = address
        self.payment_receiver: models.PaymentReceiver = payment_receiver
        self.billing_information: str = billing_information
        self.qr_reference_number: str = qr_refernce_number
        self.unstructured_message: str = unstructured_message
        self.add_cut_info: bool = add_cut_info

    @classmethod
    def from_order(cls, order, add_cut_lines=True):
        elem = cls(
            total=order.cached_sum,
            address=order.addr_billing,
            payment_receiver=order.payment_receiver,
            billing_information=order.get_qr_billing_information(),
            qr_refernce_number=order.get_qr_reference_number(),
            unstructured_message=order.get_unstructured_message(),
            add_cut_info=add_cut_lines,
        )

        return elem

    def __repr__(self):
        return "QR-Invoice"

    def __str__(self):
        return "QR-Invoice"

    def debug(self):
        c = self.canv
        c.setStrokeColor("green")
        c.rect(5 * mm, 5 * mm, 52 * mm, 95 * mm)  # Empfangsschein
        c.rect(67 * mm, 5 * mm, 138 * mm, 95 * mm)  # Zahlteil
        c.rect(67 * mm, 42 * mm, 46 * mm, 46 * mm)  # QR-Code
        c.line(5 * mm, 23 * mm, 57 * mm, 23 * mm)
        c.line(5 * mm, 37 * mm, 57 * mm, 37 * mm)
        c.line(5 * mm, 93 * mm, 57 * mm, 93 * mm)
        c.line(67 * mm, 93 * mm, 118 * mm, 93 * mm)
        c.line(67 * mm, 37 * mm, 118 * mm, 37 * mm)
        c.line(67 * mm, 15 * mm, 205 * mm, 15 * mm)
        c.line(118 * mm, 100 * mm, 118 * mm, 15 * mm)
        c.setStrokeColor("black")

    def get_swiss_qr_payload(self):
        recv = self.payment_receiver
        addr = self.address
        qrpayload = []

        def ln(text=""):
            qrpayload.append(text)

        # QRCH
        # - Header
        # - - QRType
        ln("SPC")
        # - - Version
        ln("0200")
        # - - Coding
        ln("1")

        # - CdtrInf (Empfänger)
        # - - IBAN
        if recv.mode == "QRR":
            ln(recv.qriban.replace(" ", ""))
        else:
            ln(recv.iban.replace(" ", ""))
        # - - Cdtr
        # - - - AdrTp
        ln("K")
        # - - - Name
        ln(recv.invoice_name)
        # - - - StrtNmOrAdrLine1
        ln(recv.invoice_address_1)
        # - - - BldgNbOrAdrLine2
        ln(recv.invoice_address_2)
        # - - - PstCd
        ln()
        # - - - TwnNm
        ln()
        # - - - Ctry (2-stelliger Landescode gemäss ISO 3166-1)
        ln(recv.invoice_country)

        # - UltmtCdtr (Entgültiger Zahlungsempfänger)
        # - - AdrTp
        ln()
        # - - Name
        ln()
        # - - StrtNmOrAdrLine1
        ln()
        # - - BldgNbOrAdrLine2
        ln()
        # - - PstCd
        ln()
        # - - TwnNm
        ln()
        # - - Ctry (2-stelliger Landescode gemäss ISO 3166-1)
        ln()

        # - CcyAmt
        # - - Amt
        ln(formatprice(self.total))
        # - - Ccy
        ln("CHF")

        # - UltmtDbtr (Entgültiger Zahlungspflichtiger)
        # - - AdrTp
        ln("K")
        # - - Name
        ln(addr["company"] or f"{addr['first_name']} {addr['last_name']}")
        # - - StrtNmOrAdrLine1
        ln(addr["address_1"])
        # - - BldgNbOrAdrLine2
        ln(addr["postcode"] + " " + addr["city"])
        # - - PstCd
        ln()
        # - - TwnNm
        ln()
        # - - Ctry (2-stelliger Landescode gemäss ISO 3166-1)
        ln(addr["country"])

        # - RmtIn
        # - - TP
        ln(recv.mode)
        # - - Ref
        if recv.mode == "QRR":
            ln(self.qr_reference_number.replace(" ", ""))
        else:
            ln()
        # - - AddInf
        # - - - Ustrd
        ln(self.unstructured_message)
        # - - - Trailer
        ln("EPD")
        # - - - StrdBkgInf
        ln(self.billing_information)

        # - AltPmtInf
        # - - AltPmt
        # ln()
        # - - AltPmt
        # ln()

        return "\n".join(qrpayload)

    def draw_qr_invoice(self):
        billing_info = self.billing_information
        ref = self.qr_reference_number
        total = format(self.total, ",.2f").replace(",", " ")
        recv = self.payment_receiver
        addr = self.address

        c = self.canv
        c.saveState()

        # QR-Code

        qrpayload = self.get_swiss_qr_payload()
        qr_code = qr.QrCodeWidget(qrpayload)
        qrbounds = qr_code.getBounds()
        qrwidth = qrbounds[2] - qrbounds[0]
        qrheight = qrbounds[3] - qrbounds[1]
        d = Drawing(
            52.2 * mm,
            52.2 * mm,
            transform=[52.2 * mm / qrwidth, 0, 0, 52.2 * mm / qrheight, 0, 0],
        )  # 46, 46
        d.add(qr_code)
        renderPDF.draw(d, c, 63.9 * mm, 38.9 * mm)  # 67, 42

        # Schweizerkreuz

        c.setFillColor("black")
        c.setStrokeColor("white")
        c.rect(86.5 * mm, 61.5 * mm, 7 * mm, 7 * mm, fill=1, stroke=1)
        c.setFillColor("white")
        c.rect(89.25 * mm, 63 * mm, 1.5 * mm, 4 * mm, fill=1, stroke=0)
        c.rect(88 * mm, 64.25 * mm, 4 * mm, 1.5 * mm, fill=1, stroke=0)

        c.setFillColor("black")
        c.setStrokeColor("black")

        # Begrenzungen Empfangsschein und Zahlteil und Abzutrennen-Hinweis

        if self.add_cut_info:
            c.line(0 * mm, 105 * mm, 210 * mm, 105 * mm)
            c.line(62 * mm, 0 * mm, 62 * mm, 105 * mm)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(
                105 * mm,
                107 * mm,
                pgettext(
                    "QR-Invoice / fixed by SIX group style guide",
                    "Vor der Einzahlung abzutrennen",
                ),
            )

        # Titel

        def titel(t, text, klein=False):
            t.setFont("Helvetica-Bold", 6 if klein else 8)
            t.textLine(text)
            t.moveCursor(0, 2)
            t.setFont("Helvetica", 8 if klein else 10)

        # Empfangsschein Angaben
        t = c.beginText(5 * mm, 90 * mm)
        titel(
            t,
            pgettext(
                "QR-Invoice / fixed by SIX group style guide", "Konto / Zahlbar an"
            ),
            True,
        )
        t.textLine(recv.qriban if recv.mode == "QRR" else recv.iban)
        t.textLine(recv.invoice_name)
        t.textLine(recv.invoice_address_1)
        t.textLine(recv.invoice_address_2)
        t.moveCursor(0, 9)
        if recv.mode == "QRR":
            titel(
                t,
                pgettext("QR-Invoice / fixed by SIX group style guide", "Referenz"),
                True,
            )
            t.textLine(ref)
            t.moveCursor(0, 9)
        titel(
            t,
            pgettext("QR-Invoice / fixed by SIX group style guide", "Zahlbar durch"),
            True,
        )
        t.textLine(addr["company"] or f"{addr['first_name']} {addr['last_name']}")
        t.textLine(addr["address_1"])
        t.textLine(f"{addr['postcode']} {addr['city']}")
        c.drawText(t)

        # Zahlteil Angaben
        t = c.beginText(118 * mm, 97 * mm)
        titel(
            t,
            pgettext(
                "QR-Invoice / fixed by SIX group style guide", "Konto / Zahlbar an"
            ),
        )
        t.textLine(recv.qriban if recv.mode == "QRR" else recv.iban)
        t.textLine(recv.invoice_name)
        t.textLine(recv.invoice_address_1)
        t.textLine(recv.invoice_address_2)
        t.moveCursor(0, 9)
        if recv.mode == "QRR":
            titel(
                t, pgettext("QR-Invoice / fixed by SIX group style guide", "Referenz")
            )
            t.textLine(ref)
            t.moveCursor(0, 9)
        titel(
            t,
            pgettext(
                "QR-Invoice / fixed by SIX group style guide",
                "Zusätzliche Informationen",
            ),
        )
        t.textLine(self.unstructured_message)
        # Note: The billing information was originally printed on the
        #       invoice but is now exclusively included in the QR code.
        #       Reason: It's not human readable and just confusing.
        # t.textLine(billing_info[:len(billing_info)//2)
        # t.textLine(billing_info[len(billing_info)//2:])
        t.moveCursor(0, 9)
        titel(
            t, pgettext("QR-Invoice / fixed by SIX group style guide", "Zahlbar durch")
        )
        t.textLine(addr["company"] or f"{addr['first_name']} {addr['last_name']}")
        t.textLine(addr["address_1"])
        t.textLine(f"{addr['postcode']} {addr['city']}")
        c.drawText(t)

        # Texte
        c.setFont("Helvetica-Bold", 11)
        c.drawString(
            5 * mm,
            97 * mm,
            pgettext("QR-Invoice / fixed by SIX group style guide", "Empfangsschein"),
        )
        c.drawString(
            67 * mm,
            97 * mm,
            pgettext("QR-Invoice / fixed by SIX group style guide", "Zahlteil"),
        )

        c.setFont("Helvetica-Bold", 6)
        c.drawString(
            5 * mm,
            33 * mm,
            pgettext("QR-Invoice / fixed by SIX group style guide", "Währung"),
        )
        c.drawString(
            20 * mm,
            33 * mm,
            pgettext("QR-Invoice / fixed by SIX group style guide", "Betrag"),
        )
        c.drawString(
            38 * mm,
            20 * mm,
            pgettext("QR-Invoice / fixed by SIX group style guide", "Annahmestelle"),
        )

        c.setFont("Helvetica", 8)
        c.drawString(5 * mm, 30 * mm, "CHF")
        c.drawString(20 * mm, 30 * mm, total)

        c.setFont("Helvetica-Bold", 8)
        c.drawString(
            67 * mm,
            33 * mm,
            pgettext("QR-Invoice / fixed by SIX group style guide", "Währung"),
        )
        c.drawString(
            87 * mm,
            33 * mm,
            pgettext("QR-Invoice / fixed by SIX group style guide", "Betrag"),
        )

        c.setFont("Helvetica", 10)
        c.drawString(67 * mm, 29 * mm, "CHF")
        c.drawString(87 * mm, 29 * mm, total)

        # c.setFont("Helvetica-Bold", 7)
        # c.drawString(67*mm, 11*mm, "Name AV1:")
        # c.drawString(67*mm, 8*mm, "Name AV2:")
        #
        # c.setFont("Helvetica", 7)
        # c.drawString(82*mm, 11*mm, "Linie 1")
        # c.drawString(82*mm, 8*mm, "Linie 2")

        # if settings.DEBUG:
        # self.debug()

        c.restoreState()

    def draw(self):
        self.canv.translate(-12 * mm, -12 * mm)
        self.draw_qr_invoice()
