from django.http import HttpResponse, FileResponse
from django.conf import settings
from django.core import mail
from django.template.loader import get_template

from datetime import datetime
from io import BytesIO
import os

################

def translate(id, language="de"):
    translations = {
        "de": {
            "rechnung_header_ansprechpartner":      "Ihr/e Ansprechpartner/in",
            "rechnung_header_bestellungvom":        "Ihre Bestellung vom",
            "rechnung_header_kundennummer":         "Ihre Kundennummer",
            "rechnung_header_rechnung":             "RECHNUNG",

            "rechnung_tabelle_artnr":               "Art-Nr.",
            "rechnung_tabelle_bezeichnung":         "Bezeichnung",
            "rechnung_tabelle_anzahl":              "Anzahl",
            "rechnung_tabelle_einheit":             "Einheit",
            "rechnung_tabelle_preis":               "Preis",
            "rechnung_tabelle_total":               "Total",
            "rechnung_tabelle_mwst":                "MwSt",
            "rechnung_tabelle_gesamttotal":         "RECHNUNGSBETRAG",

            "rechnung_qr_zahlteil":                 "Zahlteil",
            "rechnung_qr_kontozahlbaran":           "Konto / Zahlbar an",
            "rechnung_qr_referenz":                 "Referenz",
            "rechnung_qr_zusätzlicheinformationen": "Zusätzliche Informationen",
            "rechnung_qr_weitereiinformationen":    "Weitere Informationen",
            "rechnung_qr_währung":                  "Währung",
            "rechnung_qr_betrag":                   "Betrag",
            "rechnung_qr_empfangsschein":           "Empfangsschein",
            "rechnung_qr_annahmestelle":            "Annahmestelle",
            "rechnung_qr_abtrennen":                "Vor der Einzahlung abzutrennen",
            "rechnung_qr_zahlbardurch":             "Zahlbar durch",
            "rechnung_qr_zahlbardurchnameadresse":  "Zahlbar durch (Name/Adresse)",
            "rechnung_qr_zugunsten":                "Zugunsten",
        },
        "fr": {
            "rechnung_header_ansprechpartner":      "Votre interlocuteur",
            "rechnung_header_bestellungvom":        "Votre commande du",
            "rechnung_header_kundennummer":         "Ihre Kundennummer",
            "rechnung_header_rechnung":             "FACTURE",

            "rechnung_tabelle_artnr":               "Art-Nr.",
            "rechnung_tabelle_bezeichnung":         "Appellation",
            "rechnung_tabelle_anzahl":              "Quantité",
            "rechnung_tabelle_einheit":             "Unité",
            "rechnung_tabelle_preis":               "Prix",
            "rechnung_tabelle_total":               "Total",
            "rechnung_tabelle_mwst":                "TVA",
            "rechnung_tabelle_gesamttotal":         "MONTANT DE LA FACTURE",

            "rechnung_qr_zahlteil":                 "Section paiement",
            "rechnung_qr_kontozahlbaran":           "Compte / Payable à",
            "rechnung_qr_referenz":                 "Référence",
            "rechnung_qr_zusätzlicheinformationen": "Informations additionnelles",
            "rechnung_qr_weitereiinformationen":    "Informations supplémentaires",
            "rechnung_qr_währung":                  "Monnaie",
            "rechnung_qr_betrag":                   "Montant",
            "rechnung_qr_empfangsschein":           "Récépissé",
            "rechnung_qr_annahmestelle":            "Point de dépôt",
            "rechnung_qr_abtrennen":                "A détacher avant le versement",
            "rechnung_qr_zahlbardurch":             "Payable par",
            "rechnung_qr_zahlbardurchnameadresse":  "Payable par (nom/adresse)",
            "rechnung_qr_zugunsten":                "En faveur de",
        },
        "it": {
            "rechnung_header_ansprechpartner":      "La Sua controparte",
            "rechnung_header_bestellungvom":        "La Sua ordinazione del",
            "rechnung_header_kundennummer":         "Il Suo codice cliente",
            "rechnung_header_rechnung":             "FATTURA",

            "rechnung_tabelle_artnr":               "Articolo n.",
            "rechnung_tabelle_bezeichnung":         "Denominazione",
            "rechnung_tabelle_anzahl":              "Quantità",
            "rechnung_tabelle_einheit":             "Unità",
            "rechnung_tabelle_preis":               "Prezzo",
            "rechnung_tabelle_total":               "Totale",
            "rechnung_tabelle_mwst":                "IVA",
            "rechnung_tabelle_gesamttotal":         "IMPORTO DELLA FATTURA",

            "rechnung_qr_zahlteil":                 "Sezione pagamento",
            "rechnung_qr_kontozahlbaran":           "Conto / Pagabile a",
            "rechnung_qr_referenz":                 "Riferimento",
            "rechnung_qr_zusätzlicheinformationen": "Informazioni aggiuntive",
            "rechnung_qr_weitereiinformationen":    "Informazioni supplementari",
            "rechnung_qr_währung":                  "Valuta",
            "rechnung_qr_betrag":                   "Importo",
            "rechnung_qr_empfangsschein":           "Ricevuta",
            "rechnung_qr_annahmestelle":            "Punto di accettazione",
            "rechnung_qr_abtrennen":                "Da staccare prima del versamento",
            "rechnung_qr_zahlbardurch":             "Pagabile da",
            "rechnung_qr_zahlbardurchnameadresse":  "Pagabile da (nome/indirizzo)",
            "rechnung_qr_zugunsten":                "A favore di",
        },
        "en": {
            "rechnung_header_ansprechpartner":      "Your contact",
            "rechnung_header_bestellungvom":        "Date of your order",
            "rechnung_header_kundennummer":         "Your customer number",
            "rechnung_header_rechnung":             "INVOICE",

            "rechnung_tabelle_artnr":               "Item No.",
            "rechnung_tabelle_bezeichnung":         "Name",
            "rechnung_tabelle_anzahl":              "Quantity",
            "rechnung_tabelle_einheit":             "Unit",
            "rechnung_tabelle_preis":               "Price",
            "rechnung_tabelle_total":               "Total",
            "rechnung_tabelle_mwst":                "VAT",
            "rechnung_tabelle_gesamttotal":         "INVOICE AMOUNT",

            "rechnung_qr_zahlteil":                 "Payment part",
            "rechnung_qr_kontozahlbaran":           "Account / Payable to",
            "rechnung_qr_referenz":                 "Reference",
            "rechnung_qr_zusätzlicheinformationen": "Additional information",
            "rechnung_qr_weitereiinformationen":    "Further information",
            "rechnung_qr_währung":                  "Currency",
            "rechnung_qr_betrag":                   "Amount",
            "rechnung_qr_empfangsschein":           "Receipt",
            "rechnung_qr_annahmestelle":            "Acceptance point",
            "rechnung_qr_abtrennen":                "Separate before paying in",
            "rechnung_qr_zahlbardurch":             "Payable by",
            "rechnung_qr_zahlbardurchnameadresse":  "Payable by (name/address)",
            "rechnung_qr_zugunsten":                "In favour of",
        },
    }

    return translations[language][id] if (language in translations and id in translations[language]) else (translations["de"][id] if id in translations["de"] else "")

def runden(preis):
    return float("{:.2f}".format(float(round(round(preis / 0.05) * 0.05, 2))))

def formatprice(preis):
    return "{:.2f}".format(float(preis))

def clean(string, lang="de"):
    if "[:"+lang+"]" in string:
        return string.split("[:"+lang+"]")[1].split("[:")[0]
    elif "[:de]" in string:
        return string.split("[:de]")[1].split("[:")[0]
    else:
        return string

###############

def send_mail(subject:str, to:str, template_name:str, context:dict={}, headers:dict={}, bcc:list=[]):
    html_message = get_template("kmuhelper/emails/"+template_name).render(context)

    msg = mail.EmailMessage(
        subject=subject,
        body=html_message,
        to=[to],
        headers=headers,
        bcc=bcc
    )

    msg.content_subtype = "html"

    return bool(msg.send())

def send_pdf(subject:str, to:str, template_name:str, pdf:BytesIO, pdf_filename:str="file.pdf", context:dict={}, headers:dict={}, bcc:list=[]):
    html_message = get_template("kmuhelper/emails/"+template_name).render(context)

    msg = mail.EmailMessage(
        subject=subject,
        body=html_message,
        to=[to],
        headers=headers,
        bcc=bcc
    )

    msg.content_subtype = "html"
    msg.attach(filename=pdf_filename, content=pdf.read(), mimetype="application/pdf")

    return bool(msg.send())

###############

def modulo10rekursiv(strNummer):
    intTabelle = [
        [0,9,4,6,8,2,7,1,3,5],
        [9,4,6,8,2,7,1,3,5,0],
        [4,6,8,2,7,1,3,5,0,9],
        [6,8,2,7,1,3,5,0,9,4],
        [8,2,7,1,3,5,0,9,4,6],
        [2,7,1,3,5,0,9,4,6,8],
        [7,1,3,5,0,9,4,6,8,2],
        [1,3,5,0,9,4,6,8,2,7],
        [3,5,0,9,4,6,8,2,7,1],
        [5,0,9,4,6,8,2,7,1,3],
    ]
    strNummer = strNummer.replace(" ","")
    uebertrag = 0
    for num in strNummer:
        uebertrag = intTabelle[uebertrag][int(num)]
    return [0,9,8,7,6,5,4,3,2,1][uebertrag]

###############

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import pink, green, brown, white, black, gray
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, BaseDocTemplate, SimpleDocTemplate, Frame, PageTemplate, TopPadder, Flowable

#####


def pdf_rechnung(bestellung, digital:bool=True, mahnung:bool=False):
    sprache = bestellung.kunde.sprache if bestellung.kunde and bestellung.kunde.sprache else "de"
    bestelldatum = str(bestellung.datum.strftime("%d.%m.%Y"))
    ze = bestellung.zahlungsempfaenger

    def draw_header(c, doc=None):
        c.saveState()

        # Logo
        c.drawImage(ImageReader(ze.logourl), 120*mm, 260*mm, height=27.5*mm, width=27.5*mm, mask="auto")

        # Firmenname
        c.setFont("Helvetica-Bold", 14)
        c.drawString(12*mm, 284*mm, ze.firmenname)

        # Firmenadresse
        t = c.beginText(12*mm, 277*mm)
        t.setFont("Helvetica", 10)
        t.textLine(ze.adresszeile1)
        t.textLine((ze.land+"-" if not ze.land == "CH" else "")+ze.adresszeile2)
        c.drawText(t)

        # Firmendaten: Texte
        t = c.beginText(12*mm, 266*mm)
        t.setFont("Helvetica", 8)
        t.textLine("Tel.")
        t.textLine("E-Mail")
        t.textLine("Web")
        t.textLine("MwSt")
        c.drawText(t)

        # Firmendaten: Inhalt
        t = c.beginText(24*mm, 266*mm)
        t.setFont("Helvetica", 8)
        t.textLine(bestellung.ansprechpartner.telefon)
        t.textLine(bestellung.ansprechpartner.email)
        t.textLine(ze.webseite)
        t.textLine(ze.firmenuid)
        c.drawText(t)

        # Rechnungsdaten: Texte
        t = c.beginText(12*mm, 247*mm)
        t.setFont("Helvetica", 12)
        t.textLine(translate("rechnung_header_ansprechpartner", sprache))
        t.textLine(translate("rechnung_header_bestellungvom", sprache))
        t.textLine(translate("rechnung_header_kundennummer", sprache))
        c.drawText(t)

        # Rechnungsdaten: Inhalt
        t = c.beginText(64*mm, 247*mm)
        t.setFont("Helvetica", 12)
        t.textLine(bestellung.ansprechpartner.name)
        t.textLine(bestelldatum)
        t.textLine(str(bestellung.kunde.pk).zfill(6) if bestellung.kunde else "n.a.")
        c.drawText(t)

        # Kundenadresse
        t = c.beginText(120*mm, 247*mm)
        t.setFont("Helvetica", 12)
        if bestellung.rechnungsadresse_firma:
            t.textLine(bestellung.rechnungsadresse_firma)
        if bestellung.rechnungsadresse_vorname or bestellung.rechnungsadresse_nachname:
            t.textLine(bestellung.rechnungsadresse_vorname+" "+bestellung.rechnungsadresse_nachname)
        t.textLine(bestellung.rechnungsadresse_adresszeile1)
        if bestellung.rechnungsadresse_adresszeile2:
            t.textLine(bestellung.rechnungsadresse_adresszeile2)
        t.textLine(bestellung.rechnungsadresse_plz+" "+bestellung.rechnungsadresse_ort)
        c.drawText(t)

        # Rechnung
        c.setFont("Helvetica-Bold", 10)
        c.drawString(12*mm, 220*mm, translate("rechnung_header_rechnung", sprache))
        c.setFont("Helvetica", 10)
        c.drawString(64*mm, 220*mm, (bestellung.datum.strftime("%Y")+"-"+str(bestellung.pk).zfill(6)+(" (Online Nr. "+str(bestellung.woocommerceid)+")" if bestellung.woocommerceid else "")))

        c.restoreState()

    def draw_qr_invoice(c, doc=None):
        def debug(c):
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

        def get_swiss_qr_payload(bestellung):
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

        c.saveState()

        # QR-Code

        qrpayload = get_swiss_qr_payload(bestellung)
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

        if digital:
            c.line(0*mm,105*mm,210*mm,105*mm)
            c.line(62*mm,0*mm,62*mm,105*mm)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(105*mm, 107*mm, translate("rechnung_qr_abtrennen", sprache))

        # Titel

        def titel(t, text, klein=False):
            t.setFont("Helvetica-Bold", 6 if klein else 8)
            t.textLine(text)
            t.moveCursor(0,2)
            t.setFont("Helvetica", 8 if klein else 10)

        # Empfangsschein Angaben
        t = c.beginText(5*mm,90*mm)
        titel(t,translate("rechnung_qr_kontozahlbaran", sprache),True)
        t.textLine(ze.qriban)
        t.textLine(ze.firmenname)
        t.textLine(ze.adresszeile1)
        t.textLine(ze.adresszeile2)
        t.moveCursor(0,9)
        titel(t,translate("rechnung_qr_referenz", sprache),True)
        t.textLine(bestellung.referenznummer())
        t.moveCursor(0,9)
        titel(t,translate("rechnung_qr_zahlbardurch", sprache),True)
        t.textLine((bestellung.rechnungsadresse_vorname+" "+bestellung.rechnungsadresse_nachname) if not bestellung.rechnungsadresse_firma else bestellung.rechnungsadresse_firma)
        t.textLine(bestellung.rechnungsadresse_adresszeile1)
        t.textLine(bestellung.rechnungsadresse_plz+" "+bestellung.rechnungsadresse_ort)
        c.drawText(t)

        # Zahlteil Angaben
        t = c.beginText(118*mm,97*mm)
        titel(t,translate("rechnung_qr_kontozahlbaran", sprache))
        t.textLine(ze.qriban)
        t.textLine(ze.firmenname)
        t.textLine(ze.adresszeile1)
        t.textLine(ze.adresszeile2)
        t.moveCursor(0,9)
        titel(t,translate("rechnung_qr_referenz", sprache))
        t.textLine(bestellung.referenznummer())
        t.moveCursor(0,9)
        titel(t,translate("rechnung_qr_zusätzlicheinformationen", sprache))
        t.textLine(bestelldatum)
        t.textLine(bestellung.rechnungsinformationen().split("/31/")[0]+"/31/")
        t.textLine(bestellung.rechnungsinformationen().split("/31/")[1])
        t.moveCursor(0,9)
        titel(t,translate("rechnung_qr_zahlbardurch", sprache))
        t.textLine((bestellung.rechnungsadresse_vorname+" "+bestellung.rechnungsadresse_nachname) if not bestellung.rechnungsadresse_firma else bestellung.rechnungsadresse_firma)
        t.textLine(bestellung.rechnungsadresse_adresszeile1)
        t.textLine(bestellung.rechnungsadresse_plz+" "+bestellung.rechnungsadresse_ort)
        c.drawText(t)

        # Texte
        c.setFont("Helvetica-Bold", 11)
        c.drawString(5*mm, 97*mm, translate("rechnung_qr_empfangsschein", sprache))
        c.drawString(67*mm, 97*mm, translate("rechnung_qr_zahlteil", sprache))

        c.setFont("Helvetica-Bold", 6)
        c.drawString(5*mm, 33*mm, translate("rechnung_qr_währung", sprache))
        c.drawString(20*mm, 33*mm, translate("rechnung_qr_betrag", sprache))
        c.drawString(38*mm, 20*mm, translate("rechnung_qr_annahmestelle", sprache))

        c.setFont("Helvetica", 8)
        c.drawString(5*mm, 30*mm, "CHF")
        c.drawString(20*mm, 30*mm, format(bestellung.summe_gesamt(),"08,.2f").replace(","," ").lstrip(" 0"))

        c.setFont("Helvetica-Bold", 8)
        c.drawString(67*mm, 33*mm, translate("rechnung_qr_währung", sprache))
        c.drawString(87*mm, 33*mm, translate("rechnung_qr_betrag", sprache))

        c.setFont("Helvetica", 10)
        c.drawString(67*mm, 29*mm, "CHF")
        c.drawString(87*mm, 29*mm, format(bestellung.summe_gesamt(),"08,.2f").replace(","," ").lstrip(" 0"))

        # c.setFont("Helvetica-Bold", 7)
        # c.drawString(67*mm, 11*mm, "Name AV1:")
        # c.drawString(67*mm, 8*mm, "Name AV2:")
        #
        # c.setFont("Helvetica", 7)
        # c.drawString(82*mm, 11*mm, "Linie 1")
        # c.drawString(82*mm, 8*mm, "Linie 2")

        #if settings.DEBUG:
            #debug(c)

        c.restoreState()

    def draw_header_and_invoice(c, doc=None):
        draw_header(c,doc)
        draw_qr_invoice(c,doc)

    def get_table():
        data = [(translate("rechnung_tabelle_artnr", sprache),translate("rechnung_tabelle_bezeichnung", sprache),translate("rechnung_tabelle_anzahl", sprache),translate("rechnung_tabelle_einheit", sprache),translate("rechnung_tabelle_preis", sprache),translate("rechnung_tabelle_total", sprache))]

        style_default = ParagraphStyle("Normal",fontname="Helvetica")
        style_bold = ParagraphStyle("Bold",fontname="Helvetica-Bold")


        for bp in bestellung.produkte.through.objects.filter(bestellung=bestellung):  # Produkte
            data.append((
                bp.produkt.artikelnummer,
                Paragraph(clean(bp.produkt.name, sprache), style_default),
                str(bp.menge),
                clean(bp.produkt.mengenbezeichnung, sprache),
                formatprice(bp.produktpreis),
                formatprice(bp.zwischensumme())
            ))
            if bp.bemerkung:
                data.append((
                    "",
                    Paragraph(bp.bemerkung, style_bold),
                    "",
                    "",
                    "",
                    ""
                ))

        k = 0

        for bk in bestellung.kosten.through.objects.filter(bestellung=bestellung):  # Kosten
            data.append((
                "",
                Paragraph(clean(bk.kosten.name, sprache), style_default),
                "",
                "",
                "",
                formatprice(bk.kosten.preis)
            ))
            k += 1
            if bk.bemerkung:
                data.append((
                    "",
                    Paragraph(bk.bemerkung, style_bold),
                    "",
                    "",
                    "",
                    ""
                ))
                k += 1

        mwstdict = bestellung.mwstdict()
        for mwstsatz in mwstdict:  # Mehrwertsteuer
            data.append((
                "",
                translate("rechnung_tabelle_mwst", sprache),
                mwstsatz,
                "%",
                formatprice(float(mwstdict[mwstsatz])),
                formatprice(float(mwstdict[mwstsatz]*(float(mwstsatz)/100)))
            ))
            k += 1

        data.append((  # Total
            translate("rechnung_tabelle_gesamttotal", sprache),
            "",
            "",
            "CHF",
            "",
            formatprice(bestellung.summe_gesamt())
        ))

        style = [
            ('LINEABOVE', (0,0), (-1,0), 1, black),
            ('LINEBELOW', (0,0), (-1,0), 1, black),
            ('LINEABOVE', (0,-1-k), (-1,-1-k), 0.5, black),
            ('LINEABOVE', (0,-1), (-1,-1), 1, black),
            ('LINEBELOW', (0,-1), (-1,-1), 1, black),
            ('ALIGN', (-1, 0), (-1, -1), "RIGHT"),
            ('ALIGN', (-2, 0), (-2, -1), "RIGHT"),
            ('ALIGN', (1, -1), (1, -1), "CENTER"),
            ('FONTNAME', (0, -1), (-1, -1), "Helvetica-Bold"),
            ('VALIGN', (0, 0), (-1, -1), "TOP"),
        ]


        return Table(data, repeatRows=1, style=TableStyle(style), colWidths=[26*mm,80*mm,20*mm,20*mm,20*mm,20*mm])

    #####

    template_header_and_invoice =   PageTemplate(id="header_and_invoice",   pagesize=A4, frames=[Frame(10*mm, 10*mm, 190*mm, 205*mm)], onPage=draw_header_and_invoice)
    template_invoiceonly        =   PageTemplate(id="invoiceonly",          pagesize=A4, frames=[Frame(10*mm, 10*mm, 190*mm, 277*mm)], onPage=draw_qr_invoice)
    template_tableonly          =   PageTemplate(id="tableonly",            pagesize=A4, frames=[Frame(10*mm, 10*mm, 190*mm, 277*mm)],                      autoNextPageTemplate=True)
    template_headeronly         =   PageTemplate(id="headeronly",           pagesize=A4, frames=[Frame(10*mm, 10*mm, 190*mm, 205*mm)], onPage=draw_header,  autoNextPageTemplate=True)

    #####

    # def get_buffer_v1():
    #     buffer = BytesIO()
    #
    #     doc = SimpleDocTemplate(buffer, rightMargin=10*mm, leftMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)
    #     elements = [Spacer(1,75*mm), get_table(), Spacer(210*mm,108*mm)]
    #     doc.build(elements, onFirstPage=draw_header)
    #     buffer.seek(0)
    #     return buffer
    #
    # def get_buffer_v2():
    #     buffer = BytesIO()
    #
    #     doc = BaseDocTemplate(buffer, pagesize=A4, pageTemplates=[template_header_and_invoice,template_tableonly])
    #     elements = [get_table()]
    #     doc.build(elements)
    #     buffer.seek(0)
    #     return buffer
    #
    # def get_buffer_v3():
    #     buffer = BytesIO()
    #     table = get_table()
    #     x, y = table.wrapOn(canvas.Canvas(BytesIO()), 190, 10000)
    #
    #     if y/mm <= 110:
    #         doc = BaseDocTemplate(buffer, pagesize=A4, pageTemplates=[template_header_and_invoice])
    #     elif y/mm <= 360:
    #         doc = BaseDocTemplate(buffer, pagesize=A4, pageTemplates=[template_headeronly,template_invoiceonly])
    #     else:
    #         templates = [template_headeronly]
    #         for i in range(int(((y/mm)-360)/277)+1):
    #             templates.append(template_tableonly)
    #         templates.append(template_invoiceonly)
    #         doc = BaseDocTemplate(buffer, pagesize=A4, pageTemplates=templates)
    #
    #     elements = [table, Spacer(1,108*mm)]
    #     doc.build(elements)
    #     buffer.seek(0)
    #     return buffer

    #####

    class QrInvoice(Flowable):
        def __init__(self):
            Flowable.__init__(self)
            self.width = 210
            self.height = 110
            self._fixedWidth = 210
            self._fixedHeight = 110

        def __repr__(self):
            return "QR-Invoice"

        def draw(self):
            self.canv.translate(-12*mm,-12*mm)
            draw_qr_invoice(self.canv)

    def get_buffer():
        buffer = BytesIO()

        doc = BaseDocTemplate(buffer, pagesize=A4, pageTemplates=[template_headeronly, template_tableonly])
        elements = [get_table(), Spacer(1,65*mm), TopPadder(QrInvoice())]
        doc.build(elements)
        buffer.seek(0)
        return buffer

    #####

    return get_buffer()
