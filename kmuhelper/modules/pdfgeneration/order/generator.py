"""PDF creator for invoices and delivery notes"""

from datetime import datetime

from kmuhelper import settings
from kmuhelper.translations import autotranslate_quantity_description, autotranslate_fee_name, langselect
from kmuhelper.utils import formatprice
from kmuhelper.modules.pdfgeneration.base import PDFGenerator
from kmuhelper.modules.pdfgeneration.swiss_qr_invoice import QRInvoiceFlowable

from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, TopPadder, Flowable
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import black

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

        for bp in order.products.through.objects.filter(order=order):
            subtotal_without_discount = bp.calc_subtotal_without_discount()
            data.append((
                bp.product.article_number,
                Paragraph(langselect(bp.product.name, lang)),
                str(bp.quantity),
                langselect(autotranslate_quantity_description(
                    bp.product.quantity_description, bp.quantity), lang),
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

        for bk in order.fees.through.objects.filter(order=order):
            data.append((
                "",
                Paragraph(langselect(autotranslate_fee_name(bk.name), lang)),
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

        for bp in order.products.through.objects.filter(order=order):
            data.append((
                bp.product.article_number,
                Paragraph(langselect(bp.product.name, lang)),
                str(bp.quantity),
                langselect(autotranslate_quantity_description(
                    bp.product.quantity_description, bp.quantity), lang),
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
        recv = order.payment_receiver

        c = self.canv
        c.saveState()

        # Logo
        if recv.logourl:
            c.drawImage(ImageReader(recv.logourl), 120*mm, 67*mm,
                        width=20*mm, height=-20*mm, mask="auto", anchor="nw")

        # Payment receiver name
        c.setFont("Helvetica-Bold", 14)
        c.drawString(12*mm, 64*mm, recv.display_name)

        # Payment receiver address
        t = c.beginText(12*mm, 57*mm)
        t.setFont("Helvetica", 10)
        t.textLine(recv.display_address_1)
        t.textLine(recv.display_address_2)
        c.drawText(t)

        # Company / contact person info: Title
        t = c.beginText(12*mm, 46*mm)
        t.setFont("Helvetica", 8)
        t.textLine(pgettext('Text on generated order PDF', "Tel."))
        t.textLine(pgettext('Text on generated order PDF', "E-Mail"))
        if recv.website:
            t.textLine(pgettext('Text on generated order PDF', "Web"))
        if recv.swiss_uid:
            t.textLine(pgettext('Text on generated order PDF', "MwSt"))
        c.drawText(t)

        # Company / contact person info: Content
        t = c.beginText(24*mm, 46*mm)
        t.setFont("Helvetica", 8)
        t.textLine(order.contact_person.phone)
        t.textLine(order.contact_person.email)
        if recv.website:
            t.textLine(recv.website)
        if recv.swiss_uid:
            t.textLine(recv.swiss_uid)
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
        t.textLine(order.customer.pkfill(9) if order.customer else "-"*9)
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

        lang = lang or order.language

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
                    QRInvoiceFlowable.from_order(
                        order, add_cut_lines=add_cut_lines
                    )
                ),
            ]

        # Set the elements
        self.elements = elements
