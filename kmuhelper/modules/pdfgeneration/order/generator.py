"""PDF creator for invoices and delivery notes"""

from datetime import datetime

from kmuhelper import settings
from kmuhelper.translations import autotranslate_quantity_description, autotranslate_kosten_name, langselect
from kmuhelper.utils import formatprice
from kmuhelper.modules.pdfgeneration.base import PDFGenerator

from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, TopPadder, Flowable
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import black
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import qr
from reportlab.graphics import renderPDF

from django.utils.translation import pgettext

style_default = ParagraphStyle("Normal", fontname="Helvetica")
style_bold = ParagraphStyle("Bold", fontname="Helvetica-Bold")

#####


class _PDFOrderPriceTable(Table):
    COLWIDTHS = [26*mm, 80*mm, 20*mm, 20*mm, 20*mm, 20*mm]

    @classmethod
    def from_order(cls, order, lang="de", show_payment_conditions=None):
        data = [(pgettext('Text on generated order PDF', "Art-Nr."),
                 pgettext('Text on generated order PDF', "Bezeichnung"),
                 pgettext('Text on generated order PDF', "Anzahl"),
                 pgettext('Text on generated order PDF', "Einheit"),
                 pgettext('Text on generated order PDF', "Preis"),
                 pgettext('Text on generated order PDF', "Total"))]

        # Products

        h_products = 0

        for bp in order.products.through.objects.filter(bestellung=order):
            subtotal_without_discount = bp.calc_subtotal_without_discount()
            data.append((
                bp.produkt.article_number,
                Paragraph(langselect(bp.produkt.name, lang)),
                str(bp.quantity),
                langselect(autotranslate_quantity_description(
                    bp.produkt.quantity_description), lang),
                formatprice(bp.product_price),
                formatprice(subtotal_without_discount)
            ))
            h_products += 1
            if bp.discount:
                data.append((
                    "",
                    "- "+pgettext('Text on generated order PDF', "Rabatt"),
                    str(bp.discount),
                    "%",
                    formatprice(subtotal_without_discount),
                    formatprice(bp.calc_discount())
                ))
                h_products += 1
            if bp.note:
                data.append((
                    "",
                    Paragraph(f"- <b>{bp.note}</b>"),
                    "",
                    "",
                    "",
                    ""
                ))
                h_products += 1

        # Costs

        h_costs = 0

        for bk in order.kosten.through.objects.filter(bestellung=order):
            data.append((
                "",
                Paragraph(langselect(autotranslate_kosten_name(bk.name), lang)),
                "",
                "",
                "",
                formatprice(bk.price)
            ))
            h_costs += 1
            if bk.discount:
                data.append((
                    "",
                    "- "+pgettext('Text on generated order PDF', "Rabatt"),
                    str(bk.discount),
                    "%",
                    formatprice(bk.calc_subtotal_without_discount()),
                    formatprice(bk.calc_discount())
                ))
                h_costs += 1
            if bk.note:
                data.append((
                    "",
                    Paragraph(f"- <b>{bk.note}</b>"),
                    "",
                    "",
                    "",
                    ""
                ))
                h_costs += 1

        # VAT

        h_vat = 0

        vat_dict = dict(order.get_vat_dict())
        for vat_rate in vat_dict:
            data.append((
                "",
                pgettext('Text on generated order PDF', "MwSt"),
                vat_rate,
                "%",
                formatprice(float(vat_dict[vat_rate])),
                formatprice(float(vat_dict[vat_rate]*(float(vat_rate)/100)))
            ))
            h_vat += 1

        # Total & Payment conditions

        if show_payment_conditions is None:
            show_payment_conditions = settings.get_db_setting(
                "print-payment-conditions", False)

        if show_payment_conditions:
            payconds = order.get_payment_conditions_data()
            totaltext = pgettext(
                'Text on generated order PDF', "Rechnungsbetrag, zahlbar netto innert %s Tagen") % payconds[-1]["days"]
        else:
            totaltext = pgettext('Text on generated order PDF', "Rechnungsbetrag")

        data.append((
            Paragraph(f"<b>{totaltext}</b>"),
            "",
            "",
            "CHF",
            "",
            formatprice(order.cached_sum),
        ))

        h_paycond = 0
        if show_payment_conditions:
            for paycond in payconds:
                if paycond["percent"] != 0.0:
                    data.append((
                        pgettext('Text on generated order PDF', "%(days)s Tage %(percent)s%% Skonto") % {"days": paycond["days"],
                                                                                   "percent": paycond["percent"]},
                        "",
                        "",
                        "CHF",
                        "",
                        formatprice(paycond["price"]),
                    ))
                    h_paycond += 1

        # Style

        style = [
            # Horizontal lines
            # Header
            ('LINEABOVE', (0, 0), (-1, 0), 1, black),
            # Header/Products divider
            ('LINEBELOW', (0, 0), (-1, 0), 1, black),
            # Products/Costs divider
            ('LINEBELOW', (0, h_products), (-1, h_products), 0.5, black),
            # Costs/VAT divider
            ('LINEBELOW', (0, h_products+h_costs),
             (-1, h_products+h_costs), 0.5, black),
            # VAT/Footer divider
            ('LINEBELOW', (0, h_products+h_costs+h_vat),
             (-1, h_products+h_costs+h_vat), 1, black),
            # Footer
            ('LINEBELOW', (0, -1), (-1, -1), 1, black),

            # Span for total line
            ('SPAN', (0, -1-h_paycond), (2, -1-h_paycond)),

            # Horizontal alignment (same for all rows)
            ('ALIGN', (-1, 0), (-1, -1), "RIGHT"),
            ('ALIGN', (-2, 0), (-2, -1), "RIGHT"),
            ('ALIGN', (-4, 0), (-4, -1), "RIGHT"),
            # Vertical alignment (same for whole table)
            ('VALIGN', (0, 0), (-1, -1), "TOP"),
            # Bold total line
            ('FONTNAME', (0, -1-h_paycond), (-1, -1-h_paycond), "Helvetica-Bold"),
        ]

        return cls(data, repeatRows=1, style=TableStyle(style), colWidths=cls.COLWIDTHS)


class _PDFOrderProductTable(Table):
    COLWIDTHS = [36*mm, 110*mm, 20*mm, 20*mm]

    @classmethod
    def from_order(cls, order, lang="de"):
        data = [(pgettext('Text on generated order PDF', "Art-Nr."),
                 pgettext('Text on generated order PDF', "Bezeichnung"),
                 pgettext('Text on generated order PDF', "Anzahl"),
                 pgettext('Text on generated order PDF', "Einheit"))]

        productcount = 0

        # Products

        for bp in order.products.through.objects.filter(bestellung=order):
            data.append((
                bp.produkt.article_number,
                Paragraph(langselect(bp.produkt.name, lang)),
                str(bp.quantity),
                langselect(autotranslate_quantity_description(
                    bp.produkt.quantity_description), lang),
            ))
            if bp.note:
                data.append((
                    "",
                    Paragraph(f"- <b>{bp.note}</b>"),
                    "",
                    ""
                ))

            productcount += bp.quantity

        # Total

        data.append((
            pgettext('Text on generated order PDF', "Anzahl Produkte"),
            "",
            str(productcount),
            ""
        ))

        style = TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, black),
            ('LINEBELOW', (0, 0), (-1, 0), 1, black),
            ('LINEABOVE', (0, -1), (-1, -1), 1, black),
            ('LINEBELOW', (0, -1), (-1, -1), 1, black),
            ('ALIGN', (1, -1), (1, -1), "CENTER"),
            ('FONTNAME', (0, -1), (-1, -1), "Helvetica-Bold"),
            ('VALIGN', (0, 0), (-1, -1), "TOP"),
        ])

        return cls(data, repeatRows=1, style=style, colWidths=cls.COLWIDTHS)


class _PDFOrderQrInvoice(Flowable):
    @classmethod
    def from_order(cls, order, add_cut_lines=True):
        elem = cls()
        elem.width = 210
        elem.height = 110
        elem._fixedWidth = 210
        elem._fixedHeight = 110
        elem.add_cut_info = add_cut_lines
        elem.order = order
        return elem

    def __repr__(self):
        return "QR-Invoice"

    def __str__(self):
        return "QR-Invoice"

    def debug(self):
        c = self.canv
        c.setStrokeColor("green")
        c.rect(5*mm, 5*mm, 52*mm, 95*mm)  # Empfangsschein
        c.rect(67*mm, 5*mm, 138*mm, 95*mm)  # Zahlteil
        c.rect(67*mm, 42*mm, 46*mm, 46*mm)  # QR-Code
        c.line(5*mm, 23*mm, 57*mm, 23*mm)
        c.line(5*mm, 37*mm, 57*mm, 37*mm)
        c.line(5*mm, 93*mm, 57*mm, 93*mm)
        c.line(67*mm, 93*mm, 118*mm, 93*mm)
        c.line(67*mm, 37*mm, 118*mm, 37*mm)
        c.line(67*mm, 15*mm, 205*mm, 15*mm)
        c.line(118*mm, 100*mm, 118*mm, 15*mm)
        c.setStrokeColor("black")

    def get_swiss_qr_payload(self):
        order = self.order
        recv = order.zahlungsempfaenger
        addr = order.addr_billing
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
        ln(recv.name)
        # - - - StrtNmOrAdrLine1
        ln(recv.address_1)
        # - - - BldgNbOrAdrLine2
        ln(recv.address_2)
        # - - - PstCd
        ln()
        # - - - TwnNm
        ln()
        # - - - Ctry (2-stelliger Landescode gemäss ISO 3166-1)
        ln(recv.country)

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
        ln(formatprice(order.cached_sum))
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
        ln(addr["postcode"]+" "+addr["city"])
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
            ln(order.referenznummer().replace(" ", ""))
        else:
            ln()
        # - - AddInf
        # - - - Ustrd
        ln(order.unstrukturierte_mitteilung())
        # - - - Trailer
        ln("EPD")
        # - - - StrdBkgInf
        ln(order.rechnungsinformationen())

        # - AltPmtInf
        # - - AltPmt
        # ln()
        # - - AltPmt
        # ln()

        return "\n".join(qrpayload)

    def draw_qr_invoice(self):
        order = self.order
        invoiceinfo = order.rechnungsinformationen()
        strdbkginf = (invoiceinfo[:len(invoiceinfo)//2],
                      invoiceinfo[len(invoiceinfo)//2:])
        ref = order.referenznummer()
        total = format(order.cached_sum, "08,.2f").replace(
            ",", " ").lstrip(" 0")
        recv = order.zahlungsempfaenger
        addr = order.addr_billing

        c = self.canv
        c.saveState()

        # QR-Code

        qrpayload = self.get_swiss_qr_payload()
        qr_code = qr.QrCodeWidget(qrpayload)
        qrbounds = qr_code.getBounds()
        qrwidth = qrbounds[2] - qrbounds[0]
        qrheight = qrbounds[3] - qrbounds[1]
        d = Drawing(
            52.2*mm, 52.2*mm, transform=[52.2*mm/qrwidth, 0, 0, 52.2*mm/qrheight, 0, 0])  # 46, 46
        d.add(qr_code)
        renderPDF.draw(d, c, 63.9*mm, 38.9*mm)  # 67, 42

        # Schweizerkreuz

        c.setFillColor("black")
        c.setStrokeColor("white")
        c.rect(86.5*mm, 61.5*mm, 7*mm, 7*mm, fill=1, stroke=1)
        c.setFillColor("white")
        c.rect(89.25*mm, 63*mm, 1.5*mm, 4*mm, fill=1, stroke=0)
        c.rect(88*mm, 64.25*mm, 4*mm, 1.5*mm, fill=1, stroke=0)

        c.setFillColor("black")
        c.setStrokeColor("black")

        # Begrenzungen Empfangsschein und Zahlteil und Abzutrennen-Hinweis

        if self.add_cut_info:
            c.line(0*mm, 105*mm, 210*mm, 105*mm)
            c.line(62*mm, 0*mm, 62*mm, 105*mm)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(
                105*mm, 107*mm, pgettext('QR-Invoice / fixed by SIX group style guide', "Vor der Einzahlung abzutrennen"))

        # Titel

        def titel(t, text, klein=False):
            t.setFont("Helvetica-Bold", 6 if klein else 8)
            t.textLine(text)
            t.moveCursor(0, 2)
            t.setFont("Helvetica", 8 if klein else 10)

        # Empfangsschein Angaben
        t = c.beginText(5*mm, 90*mm)
        titel(t, pgettext('QR-Invoice / fixed by SIX group style guide', "Konto / Zahlbar an"), True)
        t.textLine(recv.qriban if recv.mode == "QRR" else recv.iban)
        t.textLine(recv.name)
        t.textLine(recv.address_1)
        t.textLine(recv.address_2)
        t.moveCursor(0, 9)
        if recv.mode == "QRR":
            titel(t, pgettext('QR-Invoice / fixed by SIX group style guide', "Referenz"), True)
            t.textLine(ref)
            t.moveCursor(0, 9)
        titel(t, pgettext('QR-Invoice / fixed by SIX group style guide', "Zahlbar durch"), True)
        t.textLine(addr["company"] or f"{addr['first_name']} {addr['last_name']}")
        t.textLine(addr["address_1"])
        t.textLine(f"{addr['postcode']} {addr['city']}")
        c.drawText(t)

        # Zahlteil Angaben
        t = c.beginText(118*mm, 97*mm)
        titel(t, pgettext('QR-Invoice / fixed by SIX group style guide', "Konto / Zahlbar an"))
        t.textLine(recv.qriban if recv.mode == "QRR" else recv.iban)
        t.textLine(recv.name)
        t.textLine(recv.address_1)
        t.textLine(recv.address_2)
        t.moveCursor(0, 9)
        if recv.mode == "QRR":
            titel(t, pgettext('QR-Invoice / fixed by SIX group style guide', "Referenz"))
            t.textLine(ref)
            t.moveCursor(0, 9)
        titel(t, pgettext('QR-Invoice / fixed by SIX group style guide', "Zusätzliche Informationen"))
        t.textLine(order.unstrukturierte_mitteilung())
        t.textLine(strdbkginf[0])
        t.textLine(strdbkginf[1])
        t.moveCursor(0, 9)
        titel(t, pgettext('QR-Invoice / fixed by SIX group style guide', "Zahlbar durch"))
        t.textLine(addr["company"] or f"{addr['first_name']} {addr['last_name']}")
        t.textLine(addr["address_1"])
        t.textLine(f"{addr['postcode']} {addr['city']}")
        c.drawText(t)

        # Texte
        c.setFont("Helvetica-Bold", 11)
        c.drawString(5*mm, 97*mm, pgettext('QR-Invoice / fixed by SIX group style guide', "Empfangsschein"))
        c.drawString(67*mm, 97*mm, pgettext('QR-Invoice / fixed by SIX group style guide', "Zahlteil"))

        c.setFont("Helvetica-Bold", 6)
        c.drawString(5*mm, 33*mm, pgettext('QR-Invoice / fixed by SIX group style guide', "Währung"))
        c.drawString(20*mm, 33*mm, pgettext('QR-Invoice / fixed by SIX group style guide', "Betrag"))
        c.drawString(38*mm, 20*mm, pgettext('QR-Invoice / fixed by SIX group style guide', "Annahmestelle"))

        c.setFont("Helvetica", 8)
        c.drawString(5*mm, 30*mm, "CHF")
        c.drawString(20*mm, 30*mm, total)

        c.setFont("Helvetica-Bold", 8)
        c.drawString(67*mm, 33*mm, pgettext('QR-Invoice / fixed by SIX group style guide', "Währung"))
        c.drawString(87*mm, 33*mm, pgettext('QR-Invoice / fixed by SIX group style guide', "Betrag"))

        c.setFont("Helvetica", 10)
        c.drawString(67*mm, 29*mm, "CHF")
        c.drawString(87*mm, 29*mm, total)

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
        self.canv.translate(-12*mm, -12*mm)
        self.draw_qr_invoice()


class _PDFOrderHeader(Flowable):
    @classmethod
    def from_order(cls, order, title, is_delivery_note=False):
        elem = cls()
        elem.width = 210
        elem.height = 75
        elem._fixedWidth = 210
        elem._fixedHeight = 75

        elem.order = order
        elem.title = str(title)
        elem.is_delivery_note = is_delivery_note
        return elem

    def draw_header(self):
        order = self.order
        ze = order.zahlungsempfaenger

        c = self.canv
        c.saveState()

        # Logo
        if ze.logourl:
            c.drawImage(ImageReader(ze.logourl), 120*mm, 67*mm,
                        width=20*mm, height=-20*mm, mask="auto", anchor="nw")

        # Company name
        c.setFont("Helvetica-Bold", 14)
        c.drawString(12*mm, 64*mm, ze.name)

        # Company address
        t = c.beginText(12*mm, 57*mm)
        t.setFont("Helvetica", 10)
        t.textLine(ze.address_1)
        if ze.country == "CH":
            t.textLine(ze.address_2)
        else:
            t.textLine(f"{ze.country}-{ze.address_2}")
        c.drawText(t)

        # Company info: Title
        t = c.beginText(12*mm, 46*mm)
        t.setFont("Helvetica", 8)
        t.textLine(pgettext('Text on generated order PDF', "Tel."))
        t.textLine(pgettext('Text on generated order PDF', "E-Mail"))
        if ze.website:
            t.textLine(pgettext('Text on generated order PDF', "Web"))
        if ze.swiss_uid:
            t.textLine(pgettext('Text on generated order PDF', "MwSt"))
        c.drawText(t)

        # Company info: Content
        t = c.beginText(24*mm, 46*mm)
        t.setFont("Helvetica", 8)
        t.textLine(order.ansprechpartner.phone)
        t.textLine(order.ansprechpartner.email)
        if ze.website:
            t.textLine(ze.website)
        if ze.swiss_uid:
            t.textLine(ze.swiss_uid)
        c.drawText(t)

        # Customer/Order info: Title
        t = c.beginText(12*mm, 27*mm)
        t.setFont("Helvetica", 12)
        t.textLine(pgettext('Text on generated order PDF', "Ihre Kundennummer"))
        t.textLine(pgettext('Text on generated order PDF', "Bestellnummer"))
        t.textLine(pgettext('Text on generated order PDF', "Bestelldatum"))
        if self.is_delivery_note:
            t.textLine(pgettext('Text on generated order PDF', "Datum"))
        else:
            t.textLine(pgettext('Text on generated order PDF', "Rechnungsdatum"))
        c.drawText(t)

        # Customer/Order info: Content
        t = c.beginText(64*mm, 27*mm)
        t.setFont("Helvetica", 12)
        t.textLine(order.kunde.pkfill(9) if order.kunde else "-"*9)
        t.textLine(order.pkfill(9))
        t.textLine(order.date.strftime("%d.%m.%Y"))
        if self.is_delivery_note:
            t.textLine(datetime.now().date().strftime("%d.%m.%Y"))
        else:
            t.textLine(order.invoice_date.strftime("%d.%m.%Y"))
        c.drawText(t)

        # Customer address
        t = c.beginText(120*mm, 27*mm)
        t.setFont("Helvetica", 12)
        if self.is_delivery_note:
            addr = order.addr_shipping
        else:
            addr = order.addr_billing

        if addr["company"]:
            t.textLine(addr["company"])
        if addr["first_name"] or addr["last_name"]:
            t.textLine(f'{addr["first_name"]} {addr["last_name"]}'.strip())
        t.textLine(addr["address_1"])
        if addr["address_2"]:
            t.textLine(addr["address_2"])
        t.textLine(f'{addr["postcode"]} {addr["city"]}'.strip())

        c.drawText(t)

        # Title and date
        c.setFont("Helvetica-Bold", 10)
        c.drawString(12*mm, 0*mm, self.title)

        c.setFont("Helvetica", 10)
        if len(self.title) <= 23:
            c.drawString(64*mm, 0*mm, f'{order.date.year}-{order.pkfill(6)}' +
                         (f' (Online #{order.woocommerceid})' if order.woocommerceid else ''))
        else:
            c.drawString(120*mm, 0*mm, f'{order.date.year}-{order.pkfill(6)}' +
                         (f' (Online #{order.woocommerceid})' if order.woocommerceid else ''))

        c.restoreState()

    def draw(self):
        self.canv.translate(-12*mm, -40*mm)
        self.draw_header()


class PDFOrder(PDFGenerator):
    def __init__(self, order, title, *, text=None, lang=None, is_delivery_note=False, add_cut_lines=True, show_payment_conditions=None):
        order.cached_sum = order.calc_total()

        lang = lang or (order.kunde.language if order.kunde and order.kunde.language else "de")

        # Header
        elements = [
            _PDFOrderHeader.from_order(
                order, title=title, is_delivery_note=is_delivery_note),
            Spacer(1, 48*mm),
        ]

        # Custom text
        if text:
            elements += [
                Paragraph(text.replace("\n", "\n<br />")),
                Spacer(1, 10*mm),
            ]

        # Main body
        if is_delivery_note:
            elements += [
                _PDFOrderProductTable.from_order(order, lang=lang)
            ]
        else:
            elements += [
                _PDFOrderPriceTable.from_order(
                    order, lang=lang, show_payment_conditions=show_payment_conditions),
                Spacer(1, 65*mm),
                TopPadder(
                    _PDFOrderQrInvoice.from_order(
                        order, add_cut_lines=add_cut_lines
                    )
                ),
            ]

        # Set the elements
        self.elements = elements
