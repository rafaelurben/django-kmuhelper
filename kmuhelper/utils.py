from io import BytesIO
from django.http import HttpResponse, FileResponse
from django.conf import settings
from django.template.loader import get_template

from datetime import datetime
import os

#################

def runden(preis):
    return float("{:.2f}".format(float(round(round(preis / 0.05) * 0.05, 2))))

def p(preis):
    return "{:.2f}".format(float(preis))

def clean(string, lang="de"):
    if "[:"+lang+"]" in string:
        return string.split("[:"+lang+"]")[1].split("[:")[0]
    elif "[:de]" in string:
        return string.split("[:de]")[1].split("[:")[0]
    else:
        return string

################

def send_mail(subject:str, to:str, template_name:str, context:dict={}):
    from_email = settings.DEFAULT_FROM_EMAIL
    message = get_template("kmuhelper/emails/"+template_name+".txt").render(context)
    html_message = get_template("kmuhelper/emails/"+template_name+".html").render(context)
    auth_user = Einstellung.objects.get(id="email_user").inhalt if Einstellung.objects.get(id="email_user").inhalt else None
    auth_user = Einstellung.objects.get(id="email_password").inhalt if Einstellung.objects.get(id="email_password").inhalt else None

    return bool(mail.send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=[to],
        fail_silently=False,
        auth_user=auth_user,
        auth_password=auth_password,
        html_message=html_message
    ))


#####

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

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import pink, green, brown, white, black, gray
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer

#####


def pdf_rechnung(bestellung):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    sprache = bestellung.kunde.sprache if bestellung.kunde and bestellung.kunde.sprache else "de"
    bestelldatum = str(bestellung.datum.strftime("%d.%m.%Y"))
    ze = bestellung.zahlungsempfaenger

    def draw_qr_invoice(c):
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

        Rechnungstexte = {
            "de": ("Zahlteil",          "Konto / Zahlbar an",   "Referenz",    "Zusätzliche Informationen",   "Weitere Informationen",        "Währung",  "Betrag",  "Empfangsschein", "Annahmestelle",         "Vor der Einzahlung abzutrennen",   "Zahlbar durch", "Zahlbar durch (Name/Adresse)", "Zugunsten"),
            "fr": ("Section paiement",  "Compte / Payable à",   "Référence",   "Informations additionnelles", "Informations supplémentaires", "Monnaie",  "Montant", "Récépissé",      "Point de dépôt",        "A détacher avant le versement",    "Payable par",   "Payable par (nom/adresse)",    "En faveur de"),
            "it": ("Sezione pagamento", "Conto / Pagabile a",   "Riferimento", "Informazioni aggiuntive",     "Informazioni supplementari",   "Valuta",   "Importo", "Ricevuta",       "Punto di accettazione", "Da staccare prima del versamento", "Pagabile da",   "Pagabile da (nome/indirizzo)", "A favore di"),
            "en": ("Payment part",      "Account / Payable to", "Reference",   "Additional information",      "Further information",          "Currency", "Amount",  "Receipt",        "Acceptance point",      "Separate before paying in",        "Payable by",    "Payable by (name/address)",    "In favour of")
        }

        c.saveState()

        c.setFillColor("white")
        c.rect(0*mm,0*mm,210*mm,108*mm,fill=1,stroke=0)

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

        # Begrenzungen Empfangsschein und Zahlteil

        c.line(0*mm,105*mm,210*mm,105*mm)
        c.line(62*mm,0*mm,62*mm,105*mm)

        # Titel

        def titel(t, text, klein=False):
            t.setFont("Helvetica-Bold", 6 if klein else 8)
            t.textLine(text)
            t.moveCursor(0,2)
            t.setFont("Helvetica", 8 if klein else 10)

        # Empfangsschein Angaben
        t = c.beginText(5*mm,90*mm)
        titel(t,Rechnungstexte[sprache][1],True)
        t.textLine(ze.qriban)
        t.textLine(ze.firmenname)
        t.textLine(ze.adresszeile1)
        t.textLine(ze.adresszeile2)
        t.moveCursor(0,9)
        titel(t,Rechnungstexte[sprache][2],True)
        t.textLine(bestellung.referenznummer())
        t.moveCursor(0,9)
        titel(t,Rechnungstexte[sprache][10],True)
        t.textLine((bestellung.rechnungsadresse_vorname+" "+bestellung.rechnungsadresse_nachname) if not bestellung.rechnungsadresse_firma else bestellung.rechnungsadresse_firma)
        t.textLine(bestellung.rechnungsadresse_adresszeile1)
        t.textLine(bestellung.rechnungsadresse_plz+" "+bestellung.rechnungsadresse_ort)
        c.drawText(t)

        # Zahlteil Angaben
        t = c.beginText(118*mm,97*mm)
        titel(t,Rechnungstexte[sprache][1])
        t.textLine(ze.qriban)
        t.textLine(ze.firmenname)
        t.textLine(ze.adresszeile1)
        t.textLine(ze.adresszeile2)
        t.moveCursor(0,9)
        titel(t,Rechnungstexte[sprache][2])
        t.textLine(bestellung.referenznummer())
        t.moveCursor(0,9)
        titel(t,Rechnungstexte[sprache][3])
        t.textLine(bestelldatum)
        t.textLine(bestellung.rechnungsinformationen().split("/31/")[0]+"/31/")
        t.textLine(bestellung.rechnungsinformationen().split("/31/")[1])
        t.moveCursor(0,9)
        titel(t,Rechnungstexte[sprache][10])
        t.textLine((bestellung.rechnungsadresse_vorname+" "+bestellung.rechnungsadresse_nachname) if not bestellung.rechnungsadresse_firma else bestellung.rechnungsadresse_firma)
        t.textLine(bestellung.rechnungsadresse_adresszeile1)
        t.textLine(bestellung.rechnungsadresse_plz+" "+bestellung.rechnungsadresse_ort)
        c.drawText(t)

        # Texte
        c.setFont("Helvetica-Bold", 11)
        c.drawString(5*mm, 97*mm, Rechnungstexte[sprache][7])
        c.drawString(67*mm, 97*mm, Rechnungstexte[sprache][0])

        c.setFont("Helvetica-Bold", 6)
        c.drawString(5*mm, 33*mm, Rechnungstexte[sprache][5])
        c.drawString(20*mm, 33*mm, Rechnungstexte[sprache][6])
        c.drawString(38*mm, 20*mm, Rechnungstexte[sprache][8])

        c.setFont("Helvetica", 8)
        c.drawString(5*mm, 30*mm, "CHF")
        c.drawString(20*mm, 30*mm, format(bestellung.summe_gesamt(),"08,.2f").replace(","," ").lstrip(" 0"))

        c.setFont("Helvetica-Bold", 8)
        c.drawString(67*mm, 33*mm, Rechnungstexte[sprache][5])
        c.drawString(87*mm, 33*mm, Rechnungstexte[sprache][6])
        c.drawCentredString(105*mm, 107*mm, Rechnungstexte[sprache][9])

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

    def draw_header(c):
        Headertexte = {
            "de": ("Ihr/e Ansprechpartner/in", "Ihre Bestellung vom",    "Ihre Kundennummer",      "RECHNUNG"),
            "fr": ("Votre interlocuteur",      "Votre commande du",      "Votre numéro de client", "FACTURE"),
            "it": ("La Sua controparte",       "La Sua ordinazione del", "Il Suo codice cliente",  "FATTURA"),
            "en": ("Your contact",             "Date of your order",     "Your customer number",   "INVOICE")
        }

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
        t.textLine(Headertexte[sprache][0])
        t.textLine(Headertexte[sprache][1])
        t.textLine(Headertexte[sprache][2])
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
        c.drawString(12*mm, 220*mm, Headertexte[sprache][3])
        c.setFont("Helvetica", 10)
        c.drawString(64*mm, 220*mm, (bestellung.datum.strftime("%Y")+"-"+str(bestellung.pk).zfill(6)+(" (Online Nr. "+str(bestellung.woocommerceid)+")" if bestellung.woocommerceid else "")))

        c.restoreState()

    def draw_table(c):
        Tabellentexte = {
            "de": (("Art-Nr.",     "Bezeichnung",   "Anzahl",   "Einheit", "Preis",  "Total"),  "TOTAL",  "MwSt"),
            "fr": (("Art-Nr.",     "Appellation",   "Quantité", "Unité",   "Prix",   "Total"),  "TOTAL",  "TVA"),
            "it": (("Articolo n.", "Denominazione", "Quantità", "Unità",   "Prezzo", "Totale"), "TOTALE", "IVA"),
            "en": (("Item No.",    "Name",          "Quantity", "Unit",    "Price",  "Total"),  "TOTAL",  "VAT")
        }

        data = [Tabellentexte[sprache][0]]
        style = ParagraphStyle("Helvetica",fontname="Helvetica-Bold")


        for bp in bestellung.produkte.through.objects.filter(bestellung=bestellung):  # Produkte
            data.append((
                bp.produkt.artikelnummer,
                Paragraph(clean(bp.produkt.name,sprache),style),
                str(bp.menge),
                clean(bp.produkt.mengenbezeichnung,sprache),
                p(bp.produktpreis),
                p(bp.zwischensumme())
            ))
            if bp.bemerkung:
                data.append((
                    "",
                    bp.bemerkung,
                    "",
                    "",
                    "",
                    ""
                ))

        k = 0

        for bk in bestellung.kosten.through.objects.filter(bestellung=bestellung):  # Kosten
            data.append((
                clean(bk.kosten.name, sprache),
                "",
                "",
                "",
                "",
                p(bk.kosten.preis)
            ))
            k += 1
            if bk.bemerkung:
                data.append((
                    bk.bemerkung,
                    "",
                    "",
                    "",
                    "",
                    ""
                ))
                k += 1

        mwstdict = bestellung.mwstdict()
        for mwstsatz in mwstdict:  # Mehrwertsteuer
            data.append((
                Tabellentexte[sprache][2],
                "",
                mwstsatz,
                "%",
                p(float(mwstdict[mwstsatz])),
                p(float(mwstdict[mwstsatz]*(float(mwstsatz)/100)))
            ))
            k += 1

        data.append((  # Total
            Tabellentexte[sprache][1],
            "",
            "",
            "CHF",
            "",
            p(bestellung.summe_gesamt())
        ))

        style = TableStyle([
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
        ])

        table = Table(data, repeatRows=1, style=style, colWidths=[26*mm,80*mm,20*mm,20*mm,20*mm,20*mm])

        w, h = table.wrapOn(c, 186*mm, 100*mm)
        table.drawOn(c, 12*mm, 210*mm - h)

    # Header
    draw_header(c)
    # Table
    draw_table(c)
    # Swiss QR-Code
    draw_qr_invoice(c)


    ###

    c.showPage()
    c.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=False, filename='Rechnung zu Bestellung '+str(bestellung)+'.pdf')
