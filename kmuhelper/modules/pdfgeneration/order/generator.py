"""PDF creator for invoices and delivery notes"""

from datetime import datetime

from django.utils.translation import pgettext
from reportlab.lib.colors import black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, TopPadder, Flowable

from kmuhelper import settings
from kmuhelper.modules.pdfgeneration.base import PDFGenerator
from kmuhelper.modules.pdfgeneration.swiss_qr_invoice import QRInvoiceFlowable
from kmuhelper.translations import (
    autotranslate_quantity_description,
    autotranslate_fee_name,
    langselect,
)
from kmuhelper.utils import formatprice

style_default = ParagraphStyle("Normal", fontname="Helvetica")
style_bold = ParagraphStyle("Bold", fontname="Helvetica-Bold")

#####


class _PDFOrderPriceTable(Table):
    COLWIDTHS = [26 * mm, 80 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm]

    @classmethod
    def from_order(cls, order, lang="de", show_payment_conditions=None):
        data = [
            (
                pgettext("Text on generated order PDF", "Art-Nr."),
                pgettext("Text on generated order PDF", "Bezeichnung"),
                pgettext("Text on generated order PDF", "Anzahl"),
                pgettext("Text on generated order PDF", "Einheit"),
                pgettext("Text on generated order PDF", "Preis"),
                pgettext("Text on generated order PDF", "Total"),
            )
        ]

        # Products

        h_products = 0

        for item in order.products.through.objects.filter(order=order):
            subtotal_without_discount = item.calc_subtotal_without_discount()
            data.append(
                (
                    item.article_number,
                    Paragraph(langselect(item.name, lang)),
                    str(item.quantity),
                    langselect(
                        autotranslate_quantity_description(
                            item.quantity_description, item.quantity
                        ),
                        lang,
                    ),
                    formatprice(item.product_price),
                    formatprice(subtotal_without_discount),
                )
            )
            h_products += 1
            if item.discount:
                data.append(
                    (
                        "",
                        "- " + pgettext("Text on generated order PDF", "Rabatt"),
                        str(item.discount),
                        "%",
                        formatprice(subtotal_without_discount),
                        formatprice(item.calc_discount()),
                    )
                )
                h_products += 1
            if item.note:
                data.append(("", Paragraph(f"- <b>{item.note}</b>"), "", "", "", ""))
                h_products += 1

        # Costs

        h_costs = 0

        for item in order.fees.through.objects.filter(order=order):
            data.append(
                (
                    "",
                    Paragraph(langselect(autotranslate_fee_name(item.name), lang)),
                    "",
                    "",
                    "",
                    formatprice(item.price),
                )
            )
            h_costs += 1
            if item.discount:
                data.append(
                    (
                        "",
                        "- " + pgettext("Text on generated order PDF", "Rabatt"),
                        str(item.discount),
                        "%",
                        formatprice(item.calc_subtotal_without_discount()),
                        formatprice(item.calc_discount()),
                    )
                )
                h_costs += 1
            if item.note:
                data.append(("", Paragraph(f"- <b>{item.note}</b>"), "", "", "", ""))
                h_costs += 1

        # VAT

        h_vat = 0

        vat_dict = dict(order.get_vat_dict())
        for vat_rate in vat_dict:
            if float(vat_rate) == 0.0 and not settings.get_file_setting(
                "PRINT_ZERO_VAT", False
            ):
                # Skip zero VAT if not explicitly enabled
                continue

            data.append(
                (
                    "",
                    pgettext("Text on generated order PDF", "MwSt"),
                    vat_rate,
                    "%",
                    formatprice(float(vat_dict[vat_rate])),
                    formatprice(float(vat_dict[vat_rate]) * (float(vat_rate) / 100)),
                )
            )
            h_vat += 1

        # Total & Payment conditions

        if show_payment_conditions is None:
            show_payment_conditions = settings.get_db_setting(
                "print-payment-conditions", False
            )

        if show_payment_conditions and order.payment_conditions:
            totaltext = (
                pgettext(
                    "Text on generated order PDF",
                    "Rechnungsbetrag, zahlbar netto innert %s Tagen",
                )
                % order.get_payment_conditions_data()[-1]["days"]
            )
        else:
            totaltext = pgettext("Text on generated order PDF", "Rechnungsbetrag")

        data.append(
            (
                Paragraph(f"<b>{totaltext}</b>"),
                "",
                "",
                "CHF",
                "",
                formatprice(order.cached_sum),
            )
        )

        h_paycond = 0
        if show_payment_conditions and order.payment_conditions:
            for paycond in order.get_payment_conditions_data():
                if paycond["percent"] != 0.0:
                    data.append(
                        (
                            pgettext(
                                "Text on generated order PDF",
                                "%(days)s Tage %(percent)s%% Skonto",
                            )
                            % {"days": paycond["days"], "percent": paycond["percent"]},
                            "",
                            "",
                            "CHF",
                            "",
                            formatprice(paycond["price"]),
                        )
                    )
                    h_paycond += 1

        # Style

        style = [
            # Horizontal lines
            # Header
            ("LINEABOVE", (0, 0), (-1, 0), 1, black),
            # Header/Products divider
            ("LINEBELOW", (0, 0), (-1, 0), 1, black),
            # Products/Costs divider
            ("LINEBELOW", (0, h_products), (-1, h_products), 0.5, black),
            # Costs/VAT divider
            (
                "LINEBELOW",
                (0, h_products + h_costs),
                (-1, h_products + h_costs),
                0.5,
                black,
            ),
            # VAT/Footer divider
            (
                "LINEBELOW",
                (0, h_products + h_costs + h_vat),
                (-1, h_products + h_costs + h_vat),
                1,
                black,
            ),
            # Footer
            ("LINEBELOW", (0, -1), (-1, -1), 1, black),
            # Span for total line
            ("SPAN", (0, -1 - h_paycond), (2, -1 - h_paycond)),
            # Horizontal alignment (same for all rows)
            ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
            ("ALIGN", (-2, 0), (-2, -1), "RIGHT"),
            ("ALIGN", (-4, 0), (-4, -1), "RIGHT"),
            # Vertical alignment (same for whole table)
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            # Bold total line
            ("FONTNAME", (0, -1 - h_paycond), (-1, -1 - h_paycond), "Helvetica-Bold"),
        ]

        return cls(data, repeatRows=1, style=TableStyle(style), colWidths=cls.COLWIDTHS)


class _PDFOrderProductTable(Table):
    COLWIDTHS = [36 * mm, 110 * mm, 20 * mm, 20 * mm]

    @classmethod
    def from_order(cls, order, lang="de"):
        data = [
            (
                pgettext("Text on generated order PDF", "Art-Nr."),
                pgettext("Text on generated order PDF", "Bezeichnung"),
                pgettext("Text on generated order PDF", "Anzahl"),
                pgettext("Text on generated order PDF", "Einheit"),
            )
        ]

        productcount = 0

        # Products

        for item in order.products.through.objects.filter(order=order):
            data.append(
                (
                    item.article_number,
                    Paragraph(langselect(item.name, lang)),
                    str(item.quantity),
                    langselect(
                        autotranslate_quantity_description(
                            item.quantity_description, item.quantity
                        ),
                        lang,
                    ),
                )
            )
            if item.note:
                data.append(("", Paragraph(f"- <b>{item.note}</b>"), "", ""))

            productcount += item.quantity

        # Total

        data.append(
            (
                pgettext("Text on generated order PDF", "Anzahl Produkte"),
                "",
                str(productcount),
                "",
            )
        )

        style = TableStyle(
            [
                ("LINEABOVE", (0, 0), (-1, 0), 1, black),
                ("LINEBELOW", (0, 0), (-1, 0), 1, black),
                ("LINEABOVE", (0, -1), (-1, -1), 1, black),
                ("LINEBELOW", (0, -1), (-1, -1), 1, black),
                ("ALIGN", (1, -1), (1, -1), "CENTER"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )

        return cls(data, repeatRows=1, style=style, colWidths=cls.COLWIDTHS)


class _PDFOrderHeader(Flowable):
    def __init__(self, order, title, is_delivery_note=False):
        super().__init__()
        self.order = order
        self.title = str(title)
        self.is_delivery_note = is_delivery_note

    @classmethod
    def from_order(cls, order, title, is_delivery_note=False):
        elem = cls(order, title, is_delivery_note)
        elem.width = 210
        elem.height = 75
        elem._fixedWidth = 210
        elem._fixedHeight = 75
        return elem

    def get_address_lines(self) -> list:
        data = []

        if self.is_delivery_note:
            addr = self.order.addr_shipping
        else:
            addr = self.order.addr_billing

        if addr["company"]:
            data.append(addr["company"])
        if addr["first_name"] or addr["last_name"]:
            data.append(f'{addr["first_name"]} {addr["last_name"]}'.strip())
        data.append(addr["address_1"])
        if addr["address_2"]:
            data.append(addr["address_2"])
        data.append(f'{addr["postcode"]} {addr["city"]}'.strip())

        return data

    def get_header_block1(self) -> list:
        """Get titles and data for the first header block"""

        order = self.order
        recv = order.payment_receiver
        cp = order.contact_person

        data = [
            (pgettext("Text on generated order PDF", "Kontakt"), cp.name),
            (pgettext("Text on generated order PDF", "Tel."), cp.phone),
            (pgettext("Text on generated order PDF", "E-Mail"), cp.email),
        ]

        if recv.website:
            data.append((pgettext("Text on generated order PDF", "Web"), recv.website))
        if recv.swiss_uid:
            data.append(
                (pgettext("Text on generated order PDF", "MwSt."), recv.swiss_uid)
            )

        if len(data) > 4:
            # Only return last 4 elements if 4 lines are exceeded
            return data[-4:]
        return data

    def get_header_block2(self) -> list:
        """Get titles and data for the second header block"""

        order = self.order
        recv = order.payment_receiver

        match recv.invoice_display_mode:
            case "business_orders":
                data = [
                    (
                        pgettext("Text on generated order PDF", "Ihre Kundennummer"),
                        order.customer.pkfill(9) if order.customer else "-" * 9,
                    ),
                    (
                        pgettext("Text on generated order PDF", "Bestellnummer"),
                        order.pkfill(9),
                    ),
                    (
                        pgettext("Text on generated order PDF", "Bestelldatum"),
                        order.date.strftime("%d.%m.%Y"),
                    ),
                ]

                if self.is_delivery_note:
                    data.append(
                        (
                            pgettext("Text on generated order PDF", "Generiert am"),
                            datetime.now().date().strftime("%d.%m.%Y"),
                        )
                    )
                else:
                    data.append(
                        (
                            pgettext("Text on generated order PDF", "Rechnungsdatum"),
                            order.invoice_date.strftime("%d.%m.%Y"),
                        )
                    )

                return data
            case "business_services":
                data = [
                    (
                        pgettext("Text on generated order PDF", "Ihre Kundennummer"),
                        order.customer.pkfill(9) if order.customer else "-" * 9,
                    ),
                    (
                        pgettext("Text on generated order PDF", "Rechnungsnummer"),
                        order.pkfill(9),
                    ),
                    (
                        pgettext("Text on generated order PDF", "Rechnungsdatum"),
                        order.invoice_date.strftime("%d.%m.%Y"),
                    ),
                    (
                        pgettext("Text on generated order PDF", "Generiert am"),
                        datetime.now().date().strftime("%d.%m.%Y"),
                    ),
                ]

                return data
            case "club" | "private":
                data = [
                    (
                        pgettext("Text on generated order PDF", "Identifikation"),
                        order.customer.pkfill(9) if order.customer else "-" * 9,
                    ),
                    (
                        pgettext("Text on generated order PDF", "Rechnungsnummer"),
                        order.pkfill(9),
                    ),
                    (
                        pgettext("Text on generated order PDF", "Rechnungsdatum"),
                        order.invoice_date.strftime("%d.%m.%Y"),
                    ),
                    (
                        pgettext("Text on generated order PDF", "Generiert am"),
                        datetime.now().date().strftime("%d.%m.%Y"),
                    ),
                ]

                return data

    def draw_header(self):
        order = self.order
        recv = order.payment_receiver

        c = self.canv
        c.saveState()

        # Logo
        if recv.logourl:
            try:
                image = ImageReader(
                    recv.logourl
                )  # this will raise OSError if image is not available
                c.drawImage(
                    image,
                    120 * mm,
                    67 * mm,
                    width=20 * mm,
                    height=-20 * mm,
                    mask="auto",
                    anchor="nw",
                )
            except OSError:
                print(
                    "[KMUHelper PDF generation] Loading logo image for _PDFOrderHeader failed! URL: "
                    + recv.logourl
                )

        # Payment receiver name
        c.setFont("Helvetica-Bold", 14)
        c.drawString(12 * mm, 64 * mm, recv.display_name)

        # Payment receiver address
        t = c.beginText(12 * mm, 57 * mm)
        t.setFont("Helvetica", 10)
        t.textLine(recv.display_address_1)
        t.textLine(recv.display_address_2)
        c.drawText(t)

        # Header block 1: Company / contact person info
        block1 = self.get_header_block1()

        t1t = c.beginText(12 * mm, 46 * mm)  # Title
        t1t.setFont("Helvetica", 8)
        maxlen = max([len(title) for title, _ in block1])
        t1d = c.beginText((16 + maxlen * 1.35) * mm, 46 * mm)  # Data
        t1d.setFont("Helvetica", 8)

        for title, data in block1:
            t1t.textLine(title)
            t1d.textLine(data)

        c.drawText(t1t)
        c.drawText(t1d)

        # Header block 2: Customer/Order/Invoice info
        block2 = self.get_header_block2()

        t2t = c.beginText(12 * mm, 27 * mm)
        t2t.setFont("Helvetica", 12)
        t2d = c.beginText(64 * mm, 27 * mm)
        t2d.setFont("Helvetica", 12)

        for title, data in block2:
            t2t.textLine(title)
            t2d.textLine(data)

        c.drawText(t2t)
        c.drawText(t2d)

        # Customer address block
        t = c.beginText(120 * mm, 27 * mm)
        t.setFont("Helvetica", 12)

        for line in self.get_address_lines():
            t.textLine(line)

        c.drawText(t)

        # Title and date line
        c.setFont("Helvetica-Bold", 10)
        c.drawString(12 * mm, 0 * mm, self.title)

        c.setFont("Helvetica", 10)
        if len(self.title) <= 23:
            c.drawString(
                64 * mm,
                0 * mm,
                f"{order.date.year}-{order.pkfill()}"
                + (f" (Online #{order.woocommerceid})" if order.woocommerceid else ""),
            )
        else:
            c.drawString(
                120 * mm,
                0 * mm,
                f"{order.date.year}-{order.pkfill()}"
                + (f" (Online #{order.woocommerceid})" if order.woocommerceid else ""),
            )

        c.restoreState()

    def draw(self):
        self.canv.translate(-12 * mm, -40 * mm)
        self.draw_header()


class PDFOrder(PDFGenerator):
    def __init__(
        self,
        order,
        title,
        *,
        text=None,
        lang=None,
        is_delivery_note=False,
        add_cut_lines=True,
        show_payment_conditions=None,
    ):
        super().__init__()

        order.cached_sum = order.calc_total()

        lang = lang or order.language

        # Header
        self.elements = [
            _PDFOrderHeader.from_order(
                order, title=title, is_delivery_note=is_delivery_note
            ),
            Spacer(1, 48 * mm),
        ]

        # Custom text
        if text:
            self.elements += [
                Paragraph(text.replace("\n", "\n<br />")),
                Spacer(1, 10 * mm),
            ]

        # Main body
        if is_delivery_note:
            self.elements += [_PDFOrderProductTable.from_order(order, lang=lang)]
        else:
            self.elements += [
                _PDFOrderPriceTable.from_order(
                    order, lang=lang, show_payment_conditions=show_payment_conditions
                ),
                Spacer(1, 65 * mm),
                TopPadder(
                    QRInvoiceFlowable.from_order(order, add_cut_lines=add_cut_lines)
                ),
            ]
