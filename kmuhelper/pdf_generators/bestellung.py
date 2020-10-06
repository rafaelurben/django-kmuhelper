from io import BytesIO

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import green, white, black
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, BaseDocTemplate, SimpleDocTemplate, Frame, PageTemplate, TopPadder, Flowable

from ..utils import clean, formatprice

from django.utils import translation
_ = translation.gettext

#####

class PriceTable(Table):
    def __init__(self, bestellung):
        sprache = bestellung.kunde.sprache if bestellung.kunde and bestellung.kunde.sprache else "de"

        data = [(_("Art-Nr."),_("Bezeichnung"),_("Anzahl"),_("Einheit"),_("Preis"),_("Total"))]

        style_default = ParagraphStyle("Normal",fontname="Helvetica")
        style_bold = ParagraphStyle("Bold",fontname="Helvetica-Bold")


        for bp in bestellung.produkte.through.objects.filter(bestellung=bestellung):  # Produkte
            data.append((
                bp.produkt.artikelnummer,
                Paragraph(clean(bp.produkt.name, sprache), style_default),
                str(bp.menge),
                clean(bp.produkt.mengenbezeichnung, sprache),
                formatprice(bp.produktpreis),
                formatprice(bp.zwischensumme_ohne_rabatt())
            ))
            if bp.rabatt:
                data.append((
                    "",
                    "- "+_("Rabatt"),
                    str(bp.rabatt),
                    "%",
                    formatprice(bp.zwischensumme_ohne_rabatt()),
                    formatprice(bp.nur_rabatt())
                ))
            if bp.bemerkung:
                data.append((
                    "",
                    Paragraph("- "+bp.bemerkung, style_bold),
                    "",
                    "",
                    "",
                    ""
                ))

        kostenzeilen = 0

        for bk in bestellung.kosten.through.objects.filter(bestellung=bestellung):  # Kosten
            data.append((
                "",
                Paragraph(clean(bk.kosten.name, sprache), style_default),
                "1",
                bk.kosten.mengenbezeichnung,
                formatprice(bk.kosten.preis),
                formatprice(bk.kosten.preis)
            ))
            kostenzeilen += 1
            if bk.rabatt:
                data.append((
                    "",
                    "- "+_("Rabatt"),
                    str(bk.rabatt),
                    "%",
                    formatprice(bk.zwischensumme_ohne_rabatt()),
                    formatprice(bk.nur_rabatt())
                ))
                kostenzeilen += 1
            if bk.bemerkung:
                data.append((
                    "",
                    Paragraph("- "+bk.bemerkung, style_bold),
                    "",
                    "",
                    "",
                    ""
                ))
                kostenzeilen += 1

        mwstdict = dict(bestellung.mwstdict())
        for mwstsatz in mwstdict:  # Mehrwertsteuer
            data.append((
                "",
                _("MwSt"),
                mwstsatz,
                "%",
                formatprice(float(mwstdict[mwstsatz])),
                formatprice(float(mwstdict[mwstsatz]*(float(mwstsatz)/100)))
            ))
            kostenzeilen += 1

        data.append((  # Total
            _("RECHNUNGSBETRAG"),
            "",
            "",
            "CHF",
            "",
            formatprice(bestellung.summe_gesamt())
        ))

        style = [
            ('LINEABOVE', (0,0), (-1,0), 1, black),
            ('LINEBELOW', (0,0), (-1,0), 1, black),
            ('LINEABOVE', (0,-1-kostenzeilen), (-1,-1-kostenzeilen), 0.5, black),
            ('LINEABOVE', (0,-1), (-1,-1), 1, black),
            ('LINEBELOW', (0,-1), (-1,-1), 1, black),
            ('ALIGN', (-1, 0), (-1, -1), "RIGHT"),
            ('ALIGN', (-2, 0), (-2, -1), "RIGHT"),
            ('ALIGN', (-4, 0), (-4, -1), "RIGHT"),
            ('ALIGN', (1, -1), (1, -1), "CENTER"),
            ('FONTNAME', (0, -1), (-1, -1), "Helvetica-Bold"),
            ('VALIGN', (0, 0), (-1, -1), "TOP"),
        ]

        Table.__init__(self, data, repeatRows=1, style=TableStyle(style), colWidths=[26*mm,80*mm,20*mm,20*mm,20*mm,20*mm])

class ProductTable(Table):
    def __init__(self, bestellung):
        sprache = bestellung.kunde.sprache if bestellung.kunde and bestellung.kunde.sprache else "de"

        data = [(_("Art-Nr."),_("Bezeichnung"),_("Anzahl"),_("Einheit"))]

        style_default = ParagraphStyle("Normal",fontname="Helvetica")
        style_bold = ParagraphStyle("Bold",fontname="Helvetica-Bold")

        produktanzahl = 0

        for bp in bestellung.produkte.through.objects.filter(bestellung=bestellung):  # Produkte
            data.append((
                bp.produkt.artikelnummer,
                Paragraph(clean(bp.produkt.name, sprache), style_default),
                str(bp.menge),
                clean(bp.produkt.mengenbezeichnung, sprache),
            ))
            if bp.bemerkung:
                data.append((
                    "",
                    "- "+Paragraph(bp.bemerkung, style_bold),
                    "",
                    ""
                ))

            produktanzahl += bp.menge

        data.append((  # Total
            _("ANZAHL PRODUKTE"),
            "",
            str(produktanzahl),
            ""
        ))

        style = [
            ('LINEABOVE', (0,0), (-1,0), 1, black),
            ('LINEBELOW', (0,0), (-1,0), 1, black),
            ('LINEABOVE', (0,-1), (-1,-1), 1, black),
            ('LINEBELOW', (0,-1), (-1,-1), 1, black),
            ('ALIGN', (1, -1), (1, -1), "CENTER"),
            ('FONTNAME', (0, -1), (-1, -1), "Helvetica-Bold"),
            ('VALIGN', (0, 0), (-1, -1), "TOP"),
        ]

        Table.__init__(self, data, repeatRows=1, style=TableStyle(style), colWidths=[36*mm,110*mm,20*mm,20*mm])

class QrInvoice(Flowable):
    def __init__(self, bestellung, digital=True):
        Flowable.__init__(self)
        self.width = 210
        self.height = 110
        self._fixedWidth = 210
        self._fixedHeight = 110
        self.digital = digital
        self.bestellung = bestellung

    def __repr__(self):
        return "QR-Invoice"

    def __str__(self):
        return "QR-Invoice"

    def debug(self):
        c = self.canv
        c.setStrokeColor("green")
        c.rect(5*mm,5*mm,52*mm,95*mm) # Empfangsschein
        c.rect(67*mm,5*mm,138*mm,95*mm) # Zahlteil
        c.rect(67*mm,42*mm,46*mm,46*mm) # QR-Code
        c.line(5*mm,23*mm,57*mm,23*mm)
        c.line(5*mm,37*mm,57*mm,37*mm)
        c.line(5*mm,93*mm,57*mm,93*mm)
        c.line(67*mm,93*mm,118*mm,93*mm)
        c.line(67*mm,37*mm,118*mm,37*mm)
        c.line(67*mm,15*mm,205*mm,15*mm)
        c.line(118*mm,100*mm,118*mm,15*mm)
        c.setStrokeColor("black")

    def get_swiss_qr_payload(self):
        bestellung = self.bestellung
        ze = bestellung.zahlungsempfaenger
        qrpayload = []

        def ln(text=""):
            qrpayload.append(text)

        #QRCH
            #Header
                #QRType
        ln("SPC")
                #Version
        ln("0200")
                #Coding
        ln("1")
            #CdtrInf (Empfänger)
                #IBAN
        ln(ze.qriban.replace(" ",""))
                #Cdtr
                    #AdrTp
        ln("K")
                    #Name
        ln(ze.firmenname)
                    #StrtNmOrAdrLine1
        ln(ze.adresszeile1)
                    #BldgNbOrAdrLine2
        ln(ze.adresszeile2)
                    #PstCd
        ln()
                    #TwnNm
        ln()
                    #Ctry (2-stelliger Landescode gemäss ISO 3166-1)
        ln(ze.land)
            #UltmtCdtr (Entgültiger Zahlungsempfänger)
                #AdrTp
        ln()
                #Name
        ln()
                #StrtNmOrAdrLine1
        ln()
                #BldgNbOrAdrLine2
        ln()
                #PstCd
        ln()
                #TwnNm
        ln()
                #Ctry (2-stelliger Landescode gemäss ISO 3166-1)
        ln()
            #CcyAmt
                #Amt
        ln("{:.2f}".format(bestellung.summe_gesamt()))
                #Ccy
        ln("CHF")
            #UltmtDbtr (Entgültiger Zahlungspflichtiger)
                #AdrTp
        ln("K")
                #Name
        ln((bestellung.rechnungsadresse_vorname+" "+bestellung.rechnungsadresse_nachname) if not bestellung.rechnungsadresse_firma else bestellung.rechnungsadresse_firma)
                #StrtNmOrAdrLine1
        ln(bestellung.rechnungsadresse_adresszeile1)
                #BldgNbOrAdrLine2
        ln(bestellung.rechnungsadresse_plz+" "+bestellung.rechnungsadresse_ort)
                #PstCd
        ln()
                #TwnNm
        ln()
                #Ctry (2-stelliger Landescode gemäss ISO 3166-1)
        ln(bestellung.rechnungsadresse_land)
            #RmtIn
                #TP
        ln("QRR")
                #Ref
        ln(bestellung.referenznummer().replace(" ",""))
                #AddInf
                    #Ustrd
        ln(str(bestellung.datum.strftime("%d.%m.%Y")))
                    #Trailer
        ln("EPD")
                    #StrdBkgInf
        ln(bestellung.rechnungsinformationen())
            #AltPmtInf
                #AltPmt
        #ln()
                #AltPmt
        #ln()

        return "\n".join(qrpayload)

    def draw_qr_invoice(self):
        bestellung = self.bestellung
        bestelldatum = str(bestellung.datum.strftime("%d.%m.%Y"))
        rechnungsinformationen = bestellung.rechnungsinformationen().split("/31/")
        referenznummer = bestellung.referenznummer()
        gesamtsumme = format(bestellung.summe_gesamt(),"08,.2f").replace(","," ").lstrip(" 0")
        ze = bestellung.zahlungsempfaenger

        c = self.canv
        c.saveState()

        # QR-Code

        qrpayload = self.get_swiss_qr_payload()
        qr_code = qr.QrCodeWidget(qrpayload)
        qrbounds = qr_code.getBounds()
        qrwidth = qrbounds[2] - qrbounds[0]
        qrheight = qrbounds[3] - qrbounds[1]
        d = Drawing(52.2*mm, 52.2*mm, transform=[52.2*mm/qrwidth,0,0,52.2*mm/qrheight,0,0]) # 46, 46
        d.add(qr_code)
        renderPDF.draw(d, c, 63.9*mm, 38.9*mm) # 67, 42

        # Schweizerkreuz

        c.setFillColor("black")
        c.setStrokeColor("white")
        c.rect(86.5*mm,61.5*mm,7*mm,7*mm,fill=1,stroke=1)
        c.setFillColor("white")
        c.rect(89.25*mm,63*mm,1.5*mm,4*mm,fill=1,stroke=0)
        c.rect(88*mm,64.25*mm,4*mm,1.5*mm,fill=1,stroke=0)

        c.setFillColor("black")
        c.setStrokeColor("black")

        # Begrenzungen Empfangsschein und Zahlteil und Abzutrennen-Hinweis

        if self.digital:
            c.line(0*mm,105*mm,210*mm,105*mm)
            c.line(62*mm,0*mm,62*mm,105*mm)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(105*mm, 107*mm, _("Vor der Einzahlung abzutrennen"))

        # Titel

        def titel(t, text, klein=False):
            t.setFont("Helvetica-Bold", 6 if klein else 8)
            t.textLine(text)
            t.moveCursor(0,2)
            t.setFont("Helvetica", 8 if klein else 10)

        # Empfangsschein Angaben
        t = c.beginText(5*mm,90*mm)
        titel(t,_("Konto / Zahlbar an"),True)
        t.textLine(ze.qriban)
        t.textLine(ze.firmenname)
        t.textLine(ze.adresszeile1)
        t.textLine(ze.adresszeile2)
        t.moveCursor(0,9)
        titel(t,_("Referenz"),True)
        t.textLine(referenznummer)
        t.moveCursor(0,9)
        titel(t,_("Zahlbar durch"),True)
        t.textLine((bestellung.rechnungsadresse_vorname+" "+bestellung.rechnungsadresse_nachname) if not bestellung.rechnungsadresse_firma else bestellung.rechnungsadresse_firma)
        t.textLine(bestellung.rechnungsadresse_adresszeile1)
        t.textLine(bestellung.rechnungsadresse_plz+" "+bestellung.rechnungsadresse_ort)
        c.drawText(t)

        # Zahlteil Angaben
        t = c.beginText(118*mm,97*mm)
        titel(t,_("Konto / Zahlbar an"))
        t.textLine(ze.qriban)
        t.textLine(ze.firmenname)
        t.textLine(ze.adresszeile1)
        t.textLine(ze.adresszeile2)
        t.moveCursor(0,9)
        titel(t,_("Referenz"))
        t.textLine(referenznummer)
        t.moveCursor(0,9)
        titel(t,_("Zusätzliche Informationen"))
        t.textLine(bestelldatum)
        t.textLine(rechnungsinformationen[0])
        t.textLine("/31/"+rechnungsinformationen[1])
        t.moveCursor(0,9)
        titel(t,_("Zahlbar durch"))
        t.textLine((bestellung.rechnungsadresse_vorname+" "+bestellung.rechnungsadresse_nachname) if not bestellung.rechnungsadresse_firma else bestellung.rechnungsadresse_firma)
        t.textLine(bestellung.rechnungsadresse_adresszeile1)
        t.textLine(bestellung.rechnungsadresse_plz+" "+bestellung.rechnungsadresse_ort)
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
        c.drawString(20*mm, 30*mm, gesamtsumme)

        c.setFont("Helvetica-Bold", 8)
        c.drawString(67*mm, 33*mm, _("Währung"))
        c.drawString(87*mm, 33*mm, _("Betrag"))

        c.setFont("Helvetica", 10)
        c.drawString(67*mm, 29*mm, "CHF")
        c.drawString(87*mm, 29*mm, gesamtsumme)

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
        self.canv.translate(-12*mm,-12*mm)
        self.draw_qr_invoice()

class Header(Flowable):
    def __init__(self, bestellung, lieferschein=False):
        Flowable.__init__(self)
        self.width = 210
        self.height = 75
        self._fixedWidth = 210
        self._fixedHeight = 75
        self.lieferschein = lieferschein
        self.bestellung = bestellung

    def __repr__(self):
        return "QR-Invoice"

    def __str__(self):
        return "QR-Invoice"

    def draw_header(self):
        bestellung = self.bestellung
        bestelldatum = str(bestellung.datum.strftime("%d.%m.%Y"))
        ze = bestellung.zahlungsempfaenger

        c = self.canv
        c.saveState()

        # Logo
        if ze.logourl:
            c.drawImage(ImageReader(ze.logourl), 120*mm, 67*mm, width=20*mm, height=-20*mm, mask="auto", anchor="nw")

        # Firmenname
        c.setFont("Helvetica-Bold", 14)
        c.drawString(12*mm, 64*mm, ze.firmenname)

        # Firmenadresse
        t = c.beginText(12*mm, 57*mm)
        t.setFont("Helvetica", 10)
        t.textLine(ze.adresszeile1)
        t.textLine((ze.land+"-" if not ze.land == "CH" else "")+ze.adresszeile2)
        c.drawText(t)

        # Firmendaten: Texte
        t = c.beginText(12*mm, 46*mm)
        t.setFont("Helvetica", 8)
        t.textLine(_("Tel."))
        t.textLine(_("E-Mail"))
        t.textLine(_("Web"))
        t.textLine(_("MwSt"))
        c.drawText(t)

        # Firmendaten: Inhalt
        t = c.beginText(24*mm, 46*mm)
        t.setFont("Helvetica", 8)
        t.textLine(bestellung.ansprechpartner.telefon)
        t.textLine(bestellung.ansprechpartner.email)
        t.textLine(ze.webseite)
        t.textLine(ze.firmenuid)
        c.drawText(t)

        # Rechnungsdaten: Texte
        t = c.beginText(12*mm, 27*mm)
        t.setFont("Helvetica", 12)
        t.textLine(_("Ihr/e Ansprechpartner/in"))
        t.textLine(_("Ihre Bestellung vom"))
        t.textLine(_("Ihre Kundennummer"))
        c.drawText(t)

        # Rechnungsdaten: Inhalt
        t = c.beginText(64*mm, 27*mm)
        t.setFont("Helvetica", 12)
        t.textLine(bestellung.ansprechpartner.name)
        t.textLine(bestelldatum)
        t.textLine(str(bestellung.kunde.pk).zfill(6) if bestellung.kunde else "n.a.")
        c.drawText(t)

        # Kundenadresse
        t = c.beginText(120*mm, 27*mm)
        t.setFont("Helvetica", 12)
        if self.lieferschein:
            if bestellung.lieferadresse_firma:
                t.textLine(bestellung.lieferadresse_firma)
            if bestellung.lieferadresse_vorname or bestellung.lieferadresse_nachname:
                t.textLine((bestellung.lieferadresse_vorname+" " if bestellung.lieferadresse_vorname else "")+(bestellung.lieferadresse_nachname or ""))
            t.textLine(bestellung.lieferadresse_adresszeile1)
            if bestellung.lieferadresse_adresszeile2:
                t.textLine(bestellung.lieferadresse_adresszeile2)
            t.textLine(bestellung.lieferadresse_plz+" "+bestellung.lieferadresse_ort)
            c.drawText(t)
        else:
            if bestellung.rechnungsadresse_firma:
                t.textLine(bestellung.rechnungsadresse_firma)
            if bestellung.rechnungsadresse_vorname or bestellung.rechnungsadresse_nachname:
                t.textLine((bestellung.rechnungsadresse_vorname+" " if bestellung.rechnungsadresse_vorname else "")+(bestellung.rechnungsadresse_nachname or ""))
            t.textLine(bestellung.rechnungsadresse_adresszeile1)
            if bestellung.rechnungsadresse_adresszeile2:
                t.textLine(bestellung.rechnungsadresse_adresszeile2)
            t.textLine(bestellung.rechnungsadresse_plz+" "+bestellung.rechnungsadresse_ort)
            c.drawText(t)

        # Rechnung
        c.setFont("Helvetica-Bold", 10)
        if self.lieferschein:
            c.drawString(12*mm, 0*mm, _("LIEFERSCHEIN"))
        else:
            c.drawString(12*mm, 0*mm, _("RECHNUNG"))
        c.setFont("Helvetica", 10)
        c.drawString(64*mm, 0*mm, (bestellung.datum.strftime("%Y")+"-"+str(bestellung.pk).zfill(6)+(" (Online #"+str(bestellung.woocommerceid)+")" if bestellung.woocommerceid else "")))

        c.restoreState()

    def draw(self):
        self.canv.translate(-12*mm,-40*mm)
        self.draw_header()

def pdf_bestellung(bestellung, lieferschein=False, digital:bool=True):
    sprache = bestellung.kunde.sprache if bestellung.kunde and bestellung.kunde.sprache else "de"

    cur_language = translation.get_language()
    translation.activate(sprache)

    #####

    def get_buffer(bestellung, lieferschein, digital):
        buffer = BytesIO()

        doc = SimpleDocTemplate(buffer, rightMargin=10*mm, leftMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)
        if lieferschein:
            elements = [Header(bestellung, lieferschein=True), Spacer(1,48*mm), ProductTable(bestellung)]
        else:
            elements = [Header(bestellung, lieferschein=False), Spacer(1,48*mm), PriceTable(bestellung), Spacer(1,65*mm), TopPadder(QrInvoice(bestellung, digital))]
        doc.build(elements)
        buffer.seek(0)
        return buffer

    # def get_buffer_old(bestellung):
    #     buffer = BytesIO()
    #
    #     template = PageTemplate(id="empty", pagesize=A4, frames=[Frame(10*mm, 10*mm, 190*mm, 277*mm)])
    #     doc = BaseDocTemplate(buffer, pagesize=A4, pageTemplates=[template])
    #     elements = [Header(bestellung, lieferschein=True), Spacer(1,48*mm), PriceTable(bestellung), Spacer(1,65*mm), TopPadder(QrInvoice(bestellung, digital))]
    #     doc.build(elements)
    #     buffer.seek(0)
    #     return buffer

    #####

    buffer = get_buffer(bestellung, lieferschein=lieferschein, digital=digital)

    translation.activate(cur_language)

    return buffer
