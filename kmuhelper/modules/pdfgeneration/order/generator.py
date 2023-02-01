"""PDF creator for invoices and delivery notes"""

from datetime import datetime

from kmuhelper import settings
from kmuhelper.translations import autotranslate_mengenbezeichnung, autotranslate_kosten_name, langselect
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

from django.utils import translation
_ = translation.gettext

style_default = ParagraphStyle("Normal", fontname="Helvetica")
style_bold = ParagraphStyle("Bold", fontname="Helvetica-Bold")

#####


class _PDFOrderPriceTable(Table):
    COLWIDTHS = [26*mm, 80*mm, 20*mm, 20*mm, 20*mm, 20*mm]

    @classmethod
    def from_order(cls, order, lang="de", show_payment_conditions=None):
        data = [(_("Art-Nr."), _("Bezeichnung"), _("Anzahl"),
                 _("Einheit"), _("Preis"), _("Total"))]

        # Products

        h_products = 0

        for bp in order.produkte.through.objects.filter(bestellung=order):
            zwsumohnerabatt = bp.zwischensumme_ohne_rabatt()
            data.append((
                bp.produkt.artikelnummer,
                Paragraph(langselect(bp.produkt.name, lang)),
                str(bp.menge),
                langselect(autotranslate_mengenbezeichnung(bp.produkt.mengenbezeichnung), lang),
                formatprice(bp.produktpreis),
                formatprice(zwsumohnerabatt)
            ))
            h_products += 1
            if bp.rabatt:
                data.append((
                    "",
                    "- "+_("Rabatt"),
                    str(bp.rabatt),
                    "%",
                    formatprice(zwsumohnerabatt),
                    formatprice(bp.nur_rabatt())
                ))
                h_products += 1
            if bp.bemerkung:
                data.append((
                    "",
                    Paragraph(f"- <b>{bp.bemerkung}</b>"),
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
                formatprice(bk.preis)
            ))
            h_costs += 1
            if bk.rabatt:
                data.append((
                    "",
                    "- "+_("Rabatt"),
                    str(bk.rabatt),
                    "%",
                    formatprice(bk.zwischensumme_ohne_rabatt()),
                    formatprice(bk.nur_rabatt())
                ))
                h_costs += 1
            if bk.bemerkung:
                data.append((
                    "",
                    Paragraph(f"- <b>{bk.bemerkung}</b>"),
                    "",
                    "",
                    "",
                    ""
                ))
                h_costs += 1

        # VAT

        h_vat = 0

        mwstdict = dict(order.mwstdict())
        for mwstsatz in mwstdict:
            data.append((
                "",
                _("MwSt"),
                mwstsatz,
                "%",
                formatprice(float(mwstdict[mwstsatz])),
                formatprice(float(mwstdict[mwstsatz]*(float(mwstsatz)/100)))
            ))
            h_vat += 1

        # Total & Payment conditions

        if show_payment_conditions is None:
            show_payment_conditions = settings.get_db_setting(
                "print-payment-conditions", False)

        if show_payment_conditions:
            payconds = order.get_paymentconditions()
            totaltext = _("Rechnungsbetrag, zahlbar netto innert %s Tagen") % payconds[-1]["days"]
        else:
            totaltext = _("Rechnungsbetrag")

        data.append((
            Paragraph(f"<b>{totaltext}</b>"),
            "",
            "",
            "CHF",
            "",
            formatprice(order.fix_summe),
        ))

        h_paycond = 0
        if show_payment_conditions:
            for paycond in payconds:
                if paycond["percent"] != 0.0:
                    data.append((
                        _("%(days)s Tage %(percent)s%% Skonto") % {"days": paycond["days"],
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
            ('LINEBELOW', (0, h_products+h_costs), (-1, h_products+h_costs), 0.5, black),
            # VAT/Footer divider
            ('LINEBELOW', (0, h_products+h_costs+h_vat), (-1, h_products+h_costs+h_vat), 1, black),
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
        data = [(_("Art-Nr."), _("Bezeichnung"), _("Anzahl"), _("Einheit"))]

        productcount = 0

        # Products

        for bp in order.produkte.through.objects.filter(bestellung=order):
            data.append((
                bp.produkt.artikelnummer,
                Paragraph(langselect(bp.produkt.name, lang)),
                str(bp.menge),
                langselect(autotranslate_mengenbezeichnung(bp.produkt.mengenbezeichnung), lang),
            ))
            if bp.bemerkung:
                data.append((
                    "",
                    Paragraph(f"- <b>{bp.bemerkung}</b>"),
                    "",
                    ""
                ))

            productcount += bp.menge

        # Total

        data.append((
            _("Anzahl Produkte"),
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
        addr = order.rechnungsadresse
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
        ln(recv.firmenname)
        # - - - StrtNmOrAdrLine1
        ln(recv.adresszeile1)
        # - - - BldgNbOrAdrLine2
        ln(recv.adresszeile2)
        # - - - PstCd
        ln()
        # - - - TwnNm
        ln()
        # - - - Ctry (2-stelliger Landescode gemäss ISO 3166-1)
        ln(recv.land)

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
        ln(formatprice(order.fix_summe))
        # - - Ccy
        ln("CHF")

        # - UltmtDbtr (Entgültiger Zahlungspflichtiger)
        # - - AdrTp
        ln("K")
        # - - Name
        ln(addr["firma"] or f"{addr['vorname']} {addr['nachname']}")
        # - - StrtNmOrAdrLine1
        ln(addr["adresszeile1"])
        # - - BldgNbOrAdrLine2
        ln(addr["plz"]+" "+addr["ort"])
        # - - PstCd
        ln()
        # - - TwnNm
        ln()
        # - - Ctry (2-stelliger Landescode gemäss ISO 3166-1)
        ln(addr["land"])

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

        ## - AltPmtInf
        ## - - AltPmt
        # ln()
        ## - - AltPmt
        # ln()

        return "\n".join(qrpayload)

    def draw_qr_invoice(self):
        order = self.order
        invoiceinfo = order.rechnungsinformationen()
        strdbkginf = (invoiceinfo[:len(invoiceinfo)//2], invoiceinfo[len(invoiceinfo)//2:])
        ref = order.referenznummer()
        total = format(order.fix_summe, "08,.2f").replace(",", " ").lstrip(" 0")
        recv = order.zahlungsempfaenger
        addr = order.rechnungsadresse

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
                105*mm, 107*mm, _("Vor der Einzahlung abzutrennen"))

        # Titel

        def titel(t, text, klein=False):
            t.setFont("Helvetica-Bold", 6 if klein else 8)
            t.textLine(text)
            t.moveCursor(0, 2)
            t.setFont("Helvetica", 8 if klein else 10)

        # Empfangsschein Angaben
        t = c.beginText(5*mm, 90*mm)
        titel(t, _("Konto / Zahlbar an"), True)
        t.textLine(recv.qriban if recv.mode == "QRR" else recv.iban)
        t.textLine(recv.firmenname)
        t.textLine(recv.adresszeile1)
        t.textLine(recv.adresszeile2)
        t.moveCursor(0, 9)
        if recv.mode == "QRR":
            titel(t, _("Referenz"), True)
            t.textLine(ref)
            t.moveCursor(0, 9)
        titel(t, _("Zahlbar durch"), True)
        t.textLine(addr["firma"] or f"{addr['vorname']} {addr['nachname']}")
        t.textLine(addr["adresszeile1"])
        t.textLine(f"{addr['plz']} {addr['ort']}")
        c.drawText(t)

        # Zahlteil Angaben
        t = c.beginText(118*mm, 97*mm)
        titel(t, _("Konto / Zahlbar an"))
        t.textLine(recv.qriban if recv.mode == "QRR" else recv.iban)
        t.textLine(recv.firmenname)
        t.textLine(recv.adresszeile1)
        t.textLine(recv.adresszeile2)
        t.moveCursor(0, 9)
        if recv.mode == "QRR":
            titel(t, _("Referenz"))
            t.textLine(ref)
            t.moveCursor(0, 9)
        titel(t, _("Zusätzliche Informationen"))
        t.textLine(order.unstrukturierte_mitteilung())
        t.textLine(strdbkginf[0])
        t.textLine(strdbkginf[1])
        t.moveCursor(0, 9)
        titel(t, _("Zahlbar durch"))
        t.textLine(addr["firma"] or f"{addr['vorname']} {addr['nachname']}")
        t.textLine(addr["adresszeile1"])
        t.textLine(f"{addr['plz']} {addr['ort']}")
        c.drawText(t)

        # Texte
        c.setFont("Helvetica-Bold", 11)
        c.drawString(5*mm, 97*mm, _("Empfangsschein"))
        c.drawString(67*mm, 97*mm, _("Zahlteil"))

        c.setFont("Helvetica-Bold", 6)
        c.drawString(5*mm, 33*mm, _("Währung"))
        c.drawString(20*mm, 33*mm, _("Betrag"))
        c.drawString(38*mm, 20*mm, _("Annahmestelle"))

        c.setFont("Helvetica", 8)
        c.drawString(5*mm, 30*mm, "CHF")
        c.drawString(20*mm, 30*mm, total)

        c.setFont("Helvetica-Bold", 8)
        c.drawString(67*mm, 33*mm, _("Währung"))
        c.drawString(87*mm, 33*mm, _("Betrag"))

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
        c.drawString(12*mm, 64*mm, ze.firmenname)

        # Company address
        t = c.beginText(12*mm, 57*mm)
        t.setFont("Helvetica", 10)
        t.textLine(ze.adresszeile1)
        if ze.land == "CH":
            t.textLine(ze.adresszeile2)
        else:
            t.textLine(f"{ze.land}-{ze.adresszeile2}")
        c.drawText(t)

        # Company info: Title
        t = c.beginText(12*mm, 46*mm)
        t.setFont("Helvetica", 8)
        t.textLine(_("Tel."))
        t.textLine(_("E-Mail"))
        if ze.webseite:
            t.textLine(_("Web"))
        if ze.firmenuid:
            t.textLine(_("MwSt"))
        c.drawText(t)

        # Company info: Content
        t = c.beginText(24*mm, 46*mm)
        t.setFont("Helvetica", 8)
        t.textLine(order.ansprechpartner.telefon)
        t.textLine(order.ansprechpartner.email)
        if ze.webseite:
            t.textLine(ze.webseite)
        if ze.firmenuid:
            t.textLine(ze.firmenuid)
        c.drawText(t)

        # Customer/Order info: Title
        t = c.beginText(12*mm, 27*mm)
        t.setFont("Helvetica", 12)
        t.textLine(_("Ihre Kundennummer"))
        t.textLine(_("Bestellnummer"))
        t.textLine(_("Bestelldatum"))
        if self.is_delivery_note:
            t.textLine(_("Datum"))
        else:
            t.textLine(_("Rechnungsdatum"))
        c.drawText(t)

        # Customer/Order info: Content
        t = c.beginText(64*mm, 27*mm)
        t.setFont("Helvetica", 12)
        t.textLine(order.kunde.pkfill(9) if order.kunde else "-"*9)
        t.textLine(order.pkfill(9))
        t.textLine(order.datum.strftime("%d.%m.%Y"))
        if self.is_delivery_note:
            t.textLine(datetime.now().date().strftime("%d.%m.%Y"))
        else:
            t.textLine(order.rechnungsdatum.strftime("%d.%m.%Y"))
        c.drawText(t)

        # Customer address
        t = c.beginText(120*mm, 27*mm)
        t.setFont("Helvetica", 12)
        if self.is_delivery_note:
            addr = order.lieferadresse
        else:
            addr = order.rechnungsadresse

        if addr["firma"]:
            t.textLine(addr["firma"])
        if addr["vorname"] or addr["nachname"]:
            t.textLine(f'{addr["vorname"]} {addr["nachname"]}'.strip())
        t.textLine(addr["adresszeile1"])
        if addr["adresszeile2"]:
            t.textLine(addr["adresszeile2"])
        t.textLine(f'{addr["plz"]} {addr["ort"]}'.strip())

        c.drawText(t)

        # Title and date
        c.setFont("Helvetica-Bold", 10)
        c.drawString(12*mm, 0*mm, self.title)

        c.setFont("Helvetica", 10)
        if len(self.title) <= 23:
            c.drawString(64*mm, 0*mm, f'{order.datum.year}-{order.pkfill(6)}' +
                         (f' (Online #{order.woocommerceid})' if order.woocommerceid else ''))
        else:
            c.drawString(120*mm, 0*mm, f'{order.datum.year}-{order.pkfill(6)}' +
                         (f' (Online #{order.woocommerceid})' if order.woocommerceid else ''))

        c.restoreState()

    def draw(self):
        self.canv.translate(-12*mm, -40*mm)
        self.draw_header()


class PDFOrder(PDFGenerator):
    def __init__(self, order, title, *, text=None, is_delivery_note=False, add_cut_lines=True, show_payment_conditions=None):
        order.fix_summe = order.summe_gesamt()

        lang = order.kunde.sprache if order.kunde and order.kunde.sprache else "de"

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
                _PDFOrderPriceTable.from_order(order, lang=lang, show_payment_conditions=show_payment_conditions),
                Spacer(1, 65*mm),
                TopPadder(
                    _PDFOrderQrInvoice.from_order(
                        order, add_cut_lines=add_cut_lines
                    )
                ),
            ]

        # Set the elements
        self.elements = elements
