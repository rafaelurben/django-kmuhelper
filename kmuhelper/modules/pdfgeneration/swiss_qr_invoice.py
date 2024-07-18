from django.utils.translation import pgettext
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Flowable

import kmuhelper.modules.main.mixins as mixins
import kmuhelper.modules.main.models as models
from kmuhelper.utils import formatprice


class QRInvoiceFlowable(Flowable):
    """A Flowable that draws a Swiss QR-Invoice."""

    def __init__(
        self,
        total,
        address,
        payment_receiver,
        billing_information,
        qr_reference_number="",
        unstructured_message="",
        add_cut_info=True,
    ):
        super().__init__()

        self.width = 210
        self.height = 110
        self._fixedWidth = 210
        self._fixedHeight = 110

        self.total: float = total
        self.address: mixins.Address = address
        self.payment_receiver: models.PaymentReceiver = payment_receiver
        self.billing_information: str = billing_information
        self.qr_reference_number: str = qr_reference_number
        self.unstructured_message: str = unstructured_message
        self.add_cut_info: bool = add_cut_info

    @classmethod
    def from_order(cls, order, add_cut_lines=True):
        elem = cls(
            total=order.cached_sum,
            address=order.addr_billing,
            payment_receiver=order.payment_receiver,
            billing_information=order.get_qr_billing_information(),
            qr_reference_number=order.get_qr_reference_number(),
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
        ln("S")
        # - - - Name
        ln(recv.invoice_name)
        # - - - StrtNmOrAdrLine1
        ln(recv.invoice_street)
        # - - - BldgNbOrAdrLine2
        ln(recv.invoice_street_nr)
        # - - - PstCd
        ln(recv.invoice_postcode)
        # - - - TwnNm
        ln(recv.invoice_city)
        # - - - Ctry (2-stelliger Landescode gemäss ISO 3166-1)
        ln(recv.invoice_country)

        # - UltmtCdtr (Endgültiger Zahlungsempfänger)
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
        ln(formatprice(self.total) if self.total != 0 else "")
        # - - Ccy
        ln("CHF")

        # - UltmtDbtr (Endgültiger Zahlungspflichtiger)
        if addr.is_empty():
            ln("\n\n\n\n\n\n")
        else:
            # - - AdrTp
            ln("S")
            # - - Name
            ln(addr.company or f"{addr.first_name} {addr.last_name}")
            # - - StrtNmOrAdrLine1
            ln(addr.address_1)
            # - - BldgNbOrAdrLine2
            # Version 2.3 of the specification allows the building number to be delivered in StrtNmOrAdrLine1 (above)
            ln()
            # - - PstCd
            ln(addr.postcode)
            # - - TwnNm
            ln(addr.city)
            # - - Ctry (2-stelliger Landescode gemäss ISO 3166-1)
            ln(addr.country)

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
        ref = self.qr_reference_number
        recv = self.payment_receiver

        addr = self.address
        empty_addr = addr.is_empty()
        total = format(self.total, ",.2f").replace(",", " ")
        empty_total = self.total == 0

        c: Canvas = self.canv
        c.saveState()

        # QR-Code

        qrpayload = self.get_swiss_qr_payload()
        qr_code = qr.QrCodeWidget(qrpayload, barLevel="M")
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

        # Common parts

        def _draw_corners(x, y, width, height):
            """Draw corners. X and y represent the top left coordinates."""
            COR_LEN = 3 * mm
            c.setLineWidth(0.75)

            p = c.beginPath()
            p.moveTo(x, y)  # top left
            p.lineTo(x + COR_LEN, y)
            p.moveTo(x + width - COR_LEN, y)
            p.lineTo(x + width, y)  # top right
            p.lineTo(x + width, y - COR_LEN)
            p.moveTo(x + width, y - height + COR_LEN)
            p.lineTo(x + width, y - height)  # bottom right
            p.lineTo(x + width - COR_LEN, y - height)
            p.moveTo(x + COR_LEN, y - height)
            p.lineTo(x, y - height)  # bottom left
            p.lineTo(x, y - height + COR_LEN)
            p.moveTo(x, y - COR_LEN)
            p.lineTo(x, y)  # top left

            c.drawPath(p, stroke=1, fill=0)

        def _write_title(_t, text, small=False):
            _t.setFont("Helvetica-Bold", 6 if small else 8)
            _t.textLine(text)
            _t.moveCursor(0, 2)
            _t.setFont("Helvetica", 8 if small else 10)

        def _write_creditor_and_reference(_t, small=False):
            _write_title(
                _t,
                pgettext(
                    "QR-Invoice / fixed by SIX group style guide", "Konto / Zahlbar an"
                ),
                small=small,
            )
            _t.textLine(recv.qriban if recv.mode == "QRR" else recv.iban)
            _t.textLine(recv.invoice_name)
            _t.textLine(f"{recv.invoice_street} {recv.invoice_street_nr}")
            _t.textLine(f"{recv.invoice_postcode} {recv.invoice_city}")
            _t.moveCursor(0, 9)
            if recv.mode == "QRR":
                _write_title(
                    _t,
                    pgettext("QR-Invoice / fixed by SIX group style guide", "Referenz"),
                    small=small,
                )
                _t.textLine(ref)
                _t.moveCursor(0, 9)

        def _write_additional_info(_t):
            _write_title(
                _t,
                pgettext(
                    "QR-Invoice / fixed by SIX group style guide",
                    "Zusätzliche Informationen",
                ),
            )
            _t.textLine(self.unstructured_message)
            _t.moveCursor(0, 9)

        def _write_debitor(_t, small=False):
            _write_title(
                _t,
                pgettext(
                    "QR-Invoice / fixed by SIX group style guide",
                    "Zahlbar durch (Name/Adresse)",
                )
                if empty_addr
                else pgettext(
                    "QR-Invoice / fixed by SIX group style guide", "Zahlbar durch"
                ),
                small=small,
            )
            if not empty_addr:
                _t.textLine(
                    addr["company"] or f"{addr['first_name']} {addr['last_name']}"
                )
                _t.textLine(addr["address_1"])
                _t.textLine(f"{addr['postcode']} {addr['city']}")

        # Überschriften

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

        # Empfangsschein / Bereich Betrag

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

        c.setFont("Helvetica", 8)
        c.drawString(5 * mm, 30 * mm, "CHF")
        if empty_total:
            _draw_corners(
                20 * mm, 32 * mm, 37 * mm, 10 * mm
            )  # Leerer Betrag (Empfangsschein); statt 30x10 hier 37x10 aus Design-Gründen
        else:
            c.drawString(20 * mm, 30 * mm, total)

        # Empfangsschein / Bereich Annahmestelle

        c.setFont("Helvetica-Bold", 6)
        c.drawRightString(
            57 * mm,
            17 * mm,
            pgettext("QR-Invoice / fixed by SIX group style guide", "Annahmestelle"),
        )

        # Empfangsschein / Bereich Angaben

        t = c.beginText(5 * mm, 90 * mm)
        _write_creditor_and_reference(t, small=True)
        _write_debitor(t, small=True)
        c.drawText(t)
        if empty_addr:
            _draw_corners(
                5 * mm,
                (59 if recv.mode == "QRR" else 68) * mm,
                52 * mm,
                20 * mm
                # this is a very hacky solution because t.getY() returns a wrong result and cannot be used
                # to determine the end of the text box
            )  # Leerer Zahlungspflichtiger

        # Zahlteil / Bereich Betrag

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
        if empty_total:
            _draw_corners(
                77 * mm, 31.5 * mm, 40 * mm, 15 * mm
            )  # Leerer Betrag (Zahlteil)
        else:
            c.drawString(87 * mm, 29 * mm, total)

        # Zahlteil / Bereich Angaben

        t = c.beginText(118 * mm, 97 * mm)
        _write_creditor_and_reference(t)
        _write_additional_info(t)
        _write_debitor(t)
        c.drawText(t)
        if empty_addr:
            _draw_corners(
                118 * mm,
                (48 if recv.mode == "QRR" else 60) * mm,
                65 * mm,
                25 * mm
                # this is a very hacky solution because t.getY() returns a wrong result and cannot be used
                # to determine the end of the text box
            )  # Leerer Zahlungspflichtiger

        # Zahlteil / Bereich Weitere Informationen

        # c.setFont("Helvetica-Bold", 7)
        # c.drawString(67*mm, 11*mm, "Name AV1:")
        # c.drawString(67*mm, 8*mm, "Name AV2:")
        #
        # c.setFont("Helvetica", 7)
        # c.drawString(82*mm, 11*mm, "Linie 1")
        # c.drawString(82*mm, 8*mm, "Linie 2")

        # DEBUG

        # self.debug()

        c.restoreState()

    def draw(self):
        self.canv.translate(-12 * mm, -12 * mm)
        self.draw_qr_invoice()
