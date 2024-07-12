import string
from datetime import datetime, timedelta
from random import randint

import requests
from django.contrib import admin, messages
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.db import models
from django.forms import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.utils.html import mark_safe, format_html
from django.utils.text import format_lazy
from django.utils.translation import (
    gettext_lazy,
    gettext,
    npgettext,
    pgettext_lazy,
)
from kmuhelper import settings, constants
from kmuhelper.modules.emails.models import EMail, Attachment
from kmuhelper.modules.integrations.woocommerce.mixins import WooCommerceModelMixin
from kmuhelper.modules.main.mixins import AddressModelMixin
from kmuhelper.modules.pdfgeneration import PDFOrder
from kmuhelper.overrides import CustomModel
from kmuhelper.translations import langselect, I18N_HELP_TEXT, Language
from kmuhelper.utils import runden, formatprice, modulo10rekursiv, faq
from rich import print

_ = gettext_lazy


def log(content, *args):
    print("[deep_pink4][KMUHelper Main][/] -", content, *args)


###################


def default_delivery_title():
    datestr = datetime.now().strftime("%d.%m.%Y")
    return gettext("Lieferung vom %(date)s") % {"date": datestr}


# noinspection DuplicatedCode
def default_payment_recipient():
    if (
        PaymentReceiver.objects.exists()
        and PaymentReceiver.objects.filter(is_default=True).exists()
    ):
        return PaymentReceiver.objects.filter(is_default=True).first().pk
    # Fallback if there isn't a default payment receiver: Use the most recently used one
    if Order.objects.exists():
        newest_order = Order.objects.order_by("-date").first()
        return newest_order.payment_receiver_id
    if PaymentReceiver.objects.exists():
        return PaymentReceiver.objects.first().pk
    return None


# noinspection DuplicatedCode
def default_contact_person():
    if (
        ContactPerson.objects.exists()
        and ContactPerson.objects.filter(is_default=True).exists()
    ):
        return ContactPerson.objects.filter(is_default=True).first().pk
    # Fallback if there isn't a default contact person: Use the most recently used one
    if Order.objects.exists():
        newest_order = Order.objects.order_by("-date").first()
        return newest_order.contact_person_id
    if ContactPerson.objects.exists():
        return ContactPerson.objects.first().pk
    return None


def default_order_key():
    return "kh-" + str(randint(10000000, 99999999))


def default_payment_conditions():
    return settings.get_db_setting("default-payment-conditions")


#############


class ContactPerson(CustomModel):
    """Model representing a contact person"""

    PKFILL_WIDTH = 3

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=50,
        help_text=_("Auf Rechnung ersichtlich!"),
    )
    phone = models.CharField(
        verbose_name=_("Telefon"),
        max_length=50,
        help_text=_("Auf Rechnung ersichtlich!"),
    )
    email = models.EmailField(
        verbose_name=_("E-Mail"),
        help_text=_("Auf Rechnung ersichtlich!"),
    )

    # Default

    is_default = models.BooleanField(
        verbose_name=_("Standard?"),
        default=False,
        help_text=_(
            "Aktivieren, um diese Kontaktperson als Standard zu setzen. Die Standard-Kontaktperson wird bei "
            "der Erstellung einer neuen Bestellung sowie beim Import einer Bestellung von WooCommerce verwendet."
        ),
    )

    @admin.display(description=_("Ansprechpartner"), ordering="name")
    def __str__(self):
        return f"[{self.pk}] {self.name}"

    class Meta:
        verbose_name = _("Ansprechpartner")
        verbose_name_plural = _("Ansprechpartner")

    objects = models.Manager()

    ADMIN_ICON = "fa-solid fa-user-tie"


class OrderFee(CustomModel):
    """Model representing fees for an order (e.g. shipping costs)"""

    # Links to other models
    order = models.ForeignKey(
        to="Order",
        on_delete=models.CASCADE,
    )
    linked_fee = models.ForeignKey(
        to="Fee",
        verbose_name=_("Verknüpfte Kosten"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
    )

    # Custom data printed on the invoice
    note = models.CharField(
        verbose_name=_("Bemerkung"),
        default="",
        max_length=250,
        blank=True,
        help_text=_("Wird auf die Rechnung gedruckt."),
    )

    discount = models.FloatField(
        verbose_name=_("Rabatt in %"),
        default=0.0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    # Data copied from linked Fee
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=500,
        default=_("Zusätzliche Kosten"),
        help_text=I18N_HELP_TEXT,
    )
    price = models.FloatField(
        verbose_name=_("Preis (exkl. MwSt)"),
        default=0.0,
    )
    vat_rate = models.FloatField(
        verbose_name=_("MwSt-Satz"),
        choices=constants.VAT_RATES,
        default=constants.VAT_RATE_DEFAULT,
    )

    # Calculated data
    def calc_subtotal(self):
        return runden(self.price * ((100 - self.discount) / 100))

    def calc_subtotal_without_discount(self):
        return runden(self.price)

    def calc_discount(self):
        return runden(self.price * (self.discount / 100)) * -1

    # Display methods
    @admin.display(description=_("Name"), ordering="name")
    def clean_name(self, lang="de"):
        return langselect(self.name, lang)

    def __str__(self):
        if self.linked_fee:
            return f"[{self.pk}] {self.clean_name()} (#{self.linked_fee.pk})"
        return f"[{self.pk}] {self.clean_name()}"

    def save(self, *args, **kwargs):
        if self.pk is None and self.linked_fee is not None:
            # Copy data from linked fee
            self.name = self.linked_fee.name
            self.vat_rate = self.linked_fee.vat_rate
            # Don't override price if already here (required for WooCommerce import)
            self.price = self.price or self.linked_fee.price
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Bestellungskosten")
        verbose_name_plural = _("Bestellungskosten")

    objects = models.Manager()

    def copyto(self, order):
        self.pk = None
        self._state.adding = True
        self.order = order
        self.save()


class OrderItem(CustomModel):
    """Model representing the connection between 'Order' and 'Product'"""

    # Links to other models
    order = models.ForeignKey(
        to="Order",
        on_delete=models.CASCADE,
    )
    linked_product = models.ForeignKey(
        to="Product",
        verbose_name=_("Verknüpftes Produkt"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
    )

    # Custom data printed on the invoice
    note = models.CharField(
        verbose_name=_("Bemerkung"),
        default="",
        max_length=250,
        blank=True,
        help_text=_("Wird auf die Rechnung gedruckt."),
    )

    quantity = models.IntegerField(
        verbose_name=_("Menge"),
        default=1,
    )
    discount = models.FloatField(
        verbose_name=_("Rabatt in %"),
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    # Data copied from linked product
    article_number = models.CharField(
        verbose_name=_("Artikelnummer"),
        max_length=25,
    )
    quantity_description = models.CharField(
        verbose_name=_("Mengenbezeichnung"),
        max_length=100,
        default="Stück",
        blank=True,
        help_text=I18N_HELP_TEXT,
    )
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=500,
        default="",
        help_text=I18N_HELP_TEXT,
    )
    product_price = models.FloatField(
        verbose_name=_("Produktpreis (exkl. MwSt)"),
        default=0.0,
    )
    vat_rate = models.FloatField(
        verbose_name=_("MwSt-Satz"),
        choices=constants.VAT_RATES,
        default=constants.VAT_RATE_DEFAULT,
    )

    # Calculated data
    def calc_subtotal(self):
        return runden(
            self.product_price * self.quantity * ((100 - self.discount) / 100)
        )

    def calc_subtotal_without_discount(self):
        return runden(self.product_price * self.quantity)

    def calc_discount(self):
        return runden(self.product_price * self.quantity * (self.discount / 100)) * -1

    # Display methods
    @admin.display(description=_("Bezeichnung"), ordering="name")
    def clean_name(self, lang="de"):
        return langselect(self.name, lang)

    @admin.display(description=_("MwSt-Satz"))
    def display_vat_rate(self):
        return formatprice(self.vat_rate)

    def __str__(self):
        if self.linked_product_id:
            return (
                f"[{self.pk}] {self.quantity}x {self.clean_name()} (Art. {self.article_number}, "
                f"#{self.linked_product_id})"
            )
        return f"[{self.pk}] {self.quantity}x {self.clean_name()} (Art. {self.article_number})"

    def save(self, *args, **kwargs):
        if self.pk is None and self.linked_product is not None:
            # Copy data from linked product
            self.article_number = self.linked_product.article_number
            self.quantity_description = self.linked_product.quantity_description
            self.name = self.linked_product.name
            self.vat_rate = self.linked_product.vat_rate
            # Don't override price if already here (required for WooCommerce import)
            self.product_price = runden(
                self.product_price or self.linked_product.get_current_price()
            )
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Bestellungsposten")
        verbose_name_plural = _("Bestellungsposten")

    objects = models.Manager()

    def copyto(self, order):
        self.pk = None
        self._state.adding = True
        self.order = order
        self.save()


class Order(CustomModel, AddressModelMixin, WooCommerceModelMixin):
    """Model representing an order"""

    NOTE_RELATION = "order"

    date = models.DateTimeField(
        verbose_name=_("Datum"),
        default=timezone.now,
    )

    invoice_date = models.DateField(
        verbose_name=_("Rechnungsdatum"),
        default=None,
        blank=True,
        null=True,
        help_text=_(
            "Wird auch als Startpunkt für die Zahlungskonditionen verwendet. Wird beim Erstellen "
            "eines PDF automatisch mit dem aktuellen Datum befüllt."
        ),
    )

    payment_conditions = models.CharField(
        verbose_name=_("Zahlungskonditionen"),
        default=default_payment_conditions,
        validators=[
            RegexValidator(
                r"^([0-9]+(\.[0-9]+)?:[0-9]+;)*0:[0-9]+$",
                _(
                    "Bitte benutze folgendes Format: 'p:d;p:d' - p = Skonto in %; d = Tage"
                ),
            )
        ],
        max_length=25,
        blank=True,
        null=True,
        help_text=format_lazy(
            "{} -> {}",
            _("Skonto und Zahlungsfrist"),
            faq("wie-funktionieren-zahlungskonditionen"),
        ),
    )

    status = models.CharField(
        verbose_name=_("Status"),
        max_length=11,
        default="processing",
        choices=constants.ORDERSTATUS,
    )
    is_shipped = models.BooleanField(
        verbose_name=_("Versendet?"),
        default=False,
        help_text=format_lazy(
            "{} -> {}",
            _("Mehr Infos"),
            faq("was-passiert-wenn-ich-eine-bestellung-als-bezahltversendet-markiere"),
        ),
    )
    shipped_on = models.DateField(
        verbose_name=_("Versendet am"),
        default=None,
        blank=True,
        null=True,
    )
    tracking_number = models.CharField(
        verbose_name=_("Trackingnummer"),
        default="",
        blank=True,
        max_length=35,
        validators=[
            RegexValidator(
                r"^[A-Z0-9\.]{8,}$",
                _(
                    "Erlaubte Zeichen: Grossbuchstaben, Zahlen und Punkte. Länge: 8-35 Zeichen"
                ),
            )
        ],
        help_text=_("Trackingnummer ohne Leerzeichen. (optional)"),
    )

    is_removed_from_stock = models.BooleanField(
        verbose_name=_("Ausgelagert?"),
        default=False,
    )

    payment_method = models.CharField(
        verbose_name=_("Zahlungsmethode"),
        max_length=7,
        default="cod",
        choices=constants.PAYMENTMETHODS,
    )
    is_paid = models.BooleanField(
        verbose_name=_("Bezahlt?"),
        default=False,
        help_text=format_lazy(
            "{} -> {}",
            _("Mehr Infos"),
            faq("was-passiert-wenn-ich-eine-bestellung-als-bezahltversendet-markiere"),
        ),
    )
    paid_on = models.DateField(
        verbose_name=_("Bezahlt am"),
        default=None,
        blank=True,
        null=True,
    )

    payment_purpose = models.CharField(
        verbose_name=_("Zahlungszweck"),
        max_length=50,
        default="",
        blank=True,
        help_text=_("Wird in QR-Rechnung verwendet."),
    )

    customer_note = models.TextField(
        verbose_name=_("Kundennotiz"),
        default="",
        blank=True,
        help_text=_("Vom Kunden erfasste Notiz."),
    )

    order_key = models.CharField(
        verbose_name=_("Bestellungs-Schlüssel"),
        max_length=50,
        blank=True,
        default=default_order_key,
    )

    customer = models.ForeignKey(
        to="Customer",
        on_delete=models.SET_NULL,
        verbose_name=_("Kunde"),
        blank=True,
        null=True,
        related_name="orders",
    )
    payment_receiver = models.ForeignKey(
        to="PaymentReceiver",
        on_delete=models.PROTECT,
        verbose_name=_("Zahlungsempfänger"),
        default=default_payment_recipient,
    )
    contact_person = models.ForeignKey(
        to="ContactPerson",
        verbose_name=_("Ansprechpartner"),
        on_delete=models.PROTECT,
        default=default_contact_person,
    )

    # Connections

    products = models.ManyToManyField(
        to="Product",
        through="OrderItem",
        through_fields=("order", "linked_product"),
    )

    fees = models.ManyToManyField(
        to="Fee",
        through="OrderFee",
        through_fields=("order", "linked_fee"),
    )

    email_link_invoice = models.ForeignKey(
        to="EMail",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )
    email_link_shipped = models.ForeignKey(
        to="EMail",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )

    cached_sum = models.FloatField(
        verbose_name=_("Total in CHF"),
        default=0.0,
    )

    # Data for PDF generation (only editable via PDF generation form)

    pdf_title = models.CharField(
        editable=False,
        default="",
        blank=True,
        max_length=32,
    )
    pdf_text = models.TextField(
        editable=False,
        default="",
        blank=True,
    )

    # Properties

    @property
    def language(self):
        if self.customer is not None:
            return self.customer.language
        return "de"

    # Functions

    def import_customer_data(self):
        "Copy the customer data from the customer into the order"

        for field in constants.ADDR_SHIPPING_FIELDS + constants.ADDR_BILLING_FIELDS:
            setattr(self, field, getattr(self.customer, field))

    def second_save(self, *args, **kwargs):
        "This HAS to be called after all related models have been saved."

        self.cached_sum = self.calc_total()
        if self.is_shipped and (not self.is_removed_from_stock):
            for i in self.products.through.objects.filter(order=self):
                if i.linked_product is not None:
                    i.linked_product.stock_current -= i.quantity
                    i.linked_product.save()
            self.is_removed_from_stock = True

        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.pk and not self.woocommerceid and self.customer:
            self.import_customer_data()

        super().save(*args, **kwargs)

    @admin.display(description=_("Trackinglink"), ordering="tracking_number")
    def tracking_link(self):
        return (
            f"https://www.post.ch/swisspost-tracking?formattedParcelCodes={self.tracking_number}"
            if self.tracking_number
            else None
        )

    def get_unstructured_message(self):
        "Returns the unstructured message for the QR-Invoice"

        if self.payment_purpose:
            return self.payment_purpose
        if self.payment_receiver.mode == "QRR":
            return str(self.date.strftime("%d.%m.%Y"))
        return _("Referenznummer") + ": " + str(self.id)

    def get_qr_reference_number(self):
        """Returns the formatted reference number for the QR-Invoice"""

        a = self.pkfill(22) + "0000"
        b = a + str(modulo10rekursiv(a))
        c = (
            b[0:2]
            + " "
            + b[2:7]
            + " "
            + b[7:12]
            + " "
            + b[12:17]
            + " "
            + b[17:22]
            + " "
            + b[22:27]
        )
        return c

    def get_qr_billing_information(self):
        """Returns the billing information for the QR-Invoice

        Definition 1:
        https://www.swico.ch/media/filer_public/1c/cd/1ccd7062-fc69-40f8-be3f-2a3ba9048c5f/v2_qr-bill-s1-syntax-fr.pdf
        Definition 2 (page 61...):
        https://www.six-group.com/dam/download/banking-services/interbank-clearing/de/standardization/ig-qr-bill-de.pdf
        """

        date = (self.invoice_date or self.date).strftime("%y%m%d")

        output = f"//S1/10/{self.pk}/11/{date}"

        if self.payment_receiver.swiss_uid:
            uid = self.payment_receiver.swiss_uid.split("-")[1].replace(".", "")
            output += f"/30/{uid}"

        vat_dict = self.get_vat_dict()
        var_str = ";".join(f"{rate}:{vat_dict[rate]}" for rate in vat_dict)
        output += f"/31/{date}/32/{var_str}"

        if self.payment_conditions:
            output += f"/40/{self.payment_conditions}"
        return output

    def get_payment_conditions_data(self):
        """Get the payment conditions as a list of dictionaries"""

        if not self.payment_conditions:
            return []

        data = []
        for pc in self.payment_conditions.split(";"):
            percent, days = pc.split(":")
            percent, days = float(percent), int(days)
            data.append(
                {
                    "days": days,
                    "date": (self.invoice_date or self.date) + timedelta(days=days),
                    "percent": percent,
                    "price": runden(self.cached_sum * (1 - (percent / 100))),
                }
            )
        data.sort(key=lambda x: x["date"])
        return data

    def get_vat_dict(self):
        """Get the VAT as a dictionary

        Format: { rate: total, rate2: total2 }"""
        vat_dict = {}
        for p in self.products.through.objects.filter(order=self):
            if str(p.vat_rate) in vat_dict:
                vat_dict[str(p.vat_rate)] += p.calc_subtotal()
            else:
                vat_dict[str(p.vat_rate)] = p.calc_subtotal()
        for k in self.fees.through.objects.filter(order=self):
            if str(k.vat_rate) in vat_dict:
                vat_dict[str(k.vat_rate)] += k.calc_subtotal()
            else:
                vat_dict[str(k.vat_rate)] = k.calc_subtotal()
        for s in vat_dict:
            vat_dict[s] = runden(vat_dict[s])
        return vat_dict

    def calc_total_without_vat(self):
        total = 0
        for i in self.products.through.objects.filter(order=self):
            total += i.calc_subtotal()
        for i in self.fees.through.objects.filter(order=self):
            total += i.calc_subtotal()
        return runden(total)

    def calc_total_vat(self):
        total_vat = 0
        vat_dict = self.get_vat_dict()
        for vat_rate in vat_dict:
            total_vat += runden(float(vat_dict[vat_rate] * (float(vat_rate) / 100)))
        return runden(total_vat)

    def calc_total(self):
        return runden(self.calc_total_without_vat() + self.calc_total_vat())

    @admin.display(description=_("Rechnungstotal"))
    def display_total_breakdown(self):
        return f"{formatprice(self.calc_total_without_vat())} CHF + {formatprice(self.calc_total_vat())} CHF MwSt = {formatprice(self.calc_total())} CHF"

    @admin.display(description=_("Total"), ordering="cached_sum")
    def display_cached_sum(self):
        return f"{formatprice(self.cached_sum)} CHF"

    @admin.display(description=_("Name"))
    def name(self):
        return (
            (
                f"{self.date.year}-"
                if self.date and not isinstance(self.date, str)
                else ""
            )
            + (
                f"{self.pkfill()}"
                + (f" (WC#{self.woocommerceid})" if self.woocommerceid else "")
            )
            + " - "
            + self.display_customer()
        )

    @admin.display(description=_("Info"))
    def info(self):
        return f'{self.date.strftime("%d.%m.%Y")} - ' + self.display_customer()

    @admin.display(description=_("Bezahlt nach"))
    def display_paid_after(self):
        if self.paid_on is None or self.invoice_date is None:
            return "-"

        daydiff = (self.paid_on - self.invoice_date).days

        return npgettext(
            "Paid after ...",
            _("%(count)d Tag") % {"count": daydiff},
            _("%(count)d Tagen") % {"count": daydiff},
            daydiff,
        )

    @admin.display(description=_("Konditionen"))
    def display_payment_conditions(self):
        """Get the payment conditions as a multiline string of values"""

        conditions = self.get_payment_conditions_data()
        output = ""

        for condition in conditions:
            datestr = condition["date"].strftime("%d.%m.%Y")
            price = formatprice(condition["price"])
            percent = condition["percent"]
            output += f"{price} CHF " + gettext("bis") + f" {datestr} ({percent}%)<br>"

        return mark_safe(output)

    @admin.display(description=_("Kunde"), ordering="customer")
    def display_customer(self):
        if self.customer:
            return str(self.customer)

        id0 = "0".zfill(Customer.PKFILL_WIDTH)
        text = f"[{id0}] ({_('Gast')}) "
        if self.addr_billing_first_name:
            text += self.addr_billing_first_name + " "
        if self.addr_billing_last_name:
            text += self.addr_billing_last_name + " "
        if self.addr_billing_company:
            text += self.addr_billing_company + " "
        if self.addr_billing_postcode and self.addr_billing_city:
            text += f"({self.addr_billing_postcode} {self.addr_billing_city})"

        return text

    @admin.display(
        description=format_html(
            '<abbr title="{}"><i class="fa-solid fa-truck-fast"></i></abbr>',
            _("Als versendet markiert?"),
        ),
        ordering="is_shipped",
        boolean=True,
    )
    def display_is_shipped(self):
        return self.is_shipped

    @admin.display(
        description=format_html(
            '<abbr title="{}"><i class="fa-solid fa-hand-holding-dollar"></i></abbr>',
            _("Als bezahlt markiert?"),
        ),
        ordering="is_paid",
        boolean=True,
    )
    def display_is_paid(self):
        return self.is_paid

    def is_correct_payment(self, amount: float, date: datetime):
        """Check if a payment made on a certain date has the correct amount for this order"""

        if amount == self.cached_sum:
            return True

        for condition in self.get_payment_conditions_data():
            if amount == condition["price"] and date <= condition["date"]:
                return True

        return False

    @admin.display(description=_("Bestellung"))
    def __str__(self):
        return self.name()

    def create_email_invoice(self, lang=None):
        lang = lang or self.language
        with Language(lang):
            context = {
                "tracking_link": str(self.tracking_link()),
                "trackingdata": bool(self.tracking_number and self.is_shipped),
                "id": str(self.pk),
                "woocommerceid": str(self.woocommerceid),
                "woocommercedata": bool(self.woocommerceid),
            }

            if self.woocommerceid:
                ctx = {
                    "id": str(self.pk),
                    "onlineid": str(self.woocommerceid),
                }
                subject = (
                    gettext("Ihre Bestellung Nr. %(id)s (Online #%(onlineid)s)") % ctx
                )
                filename = (
                    gettext("Rechnung Nr. %(id)s (Online #%(onlineid)s).pdf") % ctx
                )
            else:
                ctx = {
                    "id": str(self.pk),
                }
                subject = gettext("Ihre Bestellung Nr. %(id)s") % ctx
                filename = gettext("Rechnung Nr. %(id)s.pdf") % ctx

            self.email_link_invoice = EMail.objects.create(
                subject=subject,
                to=self.addr_billing_email,
                language=lang,
                html_template="order_invoice.html",
                html_context=context,
                notes=gettext(
                    "Diese E-Mail wurde automatisch aus Bestellung #%d generiert."
                )
                % self.pk,
            )

            self.email_link_invoice.add_attachments(
                Attachment.objects.create_from_binary(
                    filename=filename,
                    content=PDFOrder(self, gettext("Rechnung")).get_pdf(),
                )
            )

            self.save()
            return self.email_link_invoice

    def create_email_shipped(self, lang=None):
        lang = lang or self.language
        with Language(lang):
            context = {
                "tracking_link": str(self.tracking_link()),
                "trackingdata": bool(self.tracking_link() and self.is_shipped),
                "id": str(self.pk),
                "woocommerceid": str(self.woocommerceid),
                "woocommercedata": bool(self.woocommerceid),
            }

            if self.woocommerceid:
                ctx = {
                    "id": str(self.pk),
                    "onlineid": str(self.woocommerceid),
                }
                subject = (
                    gettext("Ihre Lieferung Nr. %(id)s (Online #%(onlineid)s)") % ctx
                )
                filename = (
                    gettext("Lieferschein Nr. %(id)s (Online #%(onlineid)s).pdf") % ctx
                )
            else:
                ctx = {
                    "id": str(self.pk),
                }
                subject = gettext("Ihre Lieferung Nr. %(id)s") % ctx
                filename = gettext("Lieferschein Nr. %(id)s.pdf") % ctx

            self.email_link_shipped = EMail.objects.create(
                subject=subject,
                to=self.addr_shipping_email,
                language=lang,
                html_template="order_supply.html",
                html_context=context,
                notes=gettext(
                    "Diese E-Mail wurde automatisch aus Bestellung #%d generiert."
                )
                % self.pk,
            )

            self.email_link_shipped.add_attachments(
                Attachment.objects.create_from_binary(
                    filename=filename,
                    content=PDFOrder(
                        self, _("Lieferschein"), is_delivery_note=True
                    ).get_pdf(),
                )
            )

            self.save()
            return self.email_link_shipped

    def get_stock_data(self):
        """Get the stock data of all products in this order"""

        return [p.get_stock_data() for p in self.products.all()]

    def email_stock_warning(self):
        email_receiver = settings.get_db_setting("email-stock-warning-receiver")

        if email_receiver:
            warnings = []
            stock = self.get_stock_data()
            for data in stock:
                if data["stock_in_danger"]:
                    warnings.append(data)

            if warnings != []:
                email = EMail.objects.create(
                    subject=gettext("[KMUHelper] - Lagerbestand knapp!"),
                    to=email_receiver,
                    html_template="order_stock_warning.html",
                    html_context={
                        "warnings": warnings,
                    },
                    notes=gettext(
                        "Diese E-Mail wurde automatisch aus Bestellung #%d generiert."
                    )
                    % self.pk,
                )

                success = email.send(
                    headers={"Bestellungs-ID": str(self.pk)},
                )
                return bool(success)
        else:
            log("No email receiver for stock warning set.")
        return None

    class Meta:
        verbose_name = _("Bestellung")
        verbose_name_plural = _("Bestellungen")

    def duplicate(self):
        new = Order.objects.create(
            customer=self.customer,
            payment_receiver=self.payment_receiver,
            contact_person=self.contact_person,
            pdf_title=self.pdf_title,
            pdf_text=self.pdf_text,
            payment_conditions=self.payment_conditions,
            customer_note=gettext("Kopie aus Bestellung #%d") % self.pk
            + "\n"
            + "-" * 32
            + "\n"
            + self.customer_note,
        )

        for field in constants.ADDR_SHIPPING_FIELDS + constants.ADDR_BILLING_FIELDS:
            setattr(new, field, getattr(self, field))

        for bp in self.products.through.objects.filter(order=self):
            bp.copyto(new)
        for bk in self.fees.through.objects.filter(order=self):
            bk.copyto(new)
        new.save()
        return new

    def copy_to_supply(self):
        new = Supply.objects.create(
            name=gettext("Rücksendung von Bestellung #%d") % self.pk,
        )
        for lp in self.products.through.objects.filter(order=self):
            if lp.linked_product is not None:
                new.products.add(
                    lp.linked_product, through_defaults={"quantity": lp.quantity}
                )
        new.save()
        return new

    objects = models.Manager()

    ADMIN_ICON = "fa-solid fa-clipboard-list"

    DICT_EXCLUDE_FIELDS = [
        "products",
        "fees",
        "email_link_invoice",
        "email_link_shipped",
        "customer",
        "contact_person",
        "payment_receiver",
        "is_removed_from_stock",
        "is_shipped",
        "is_paid",
        "payment_method",
        "order_key",
    ]


class Fee(CustomModel):
    """Model representing additional costs"""

    PKFILL_WIDTH = 3

    name = models.CharField(
        verbose_name=_("Bezeichnung"),
        max_length=500,
        default=_("Zusätzliche Kosten"),
        help_text=I18N_HELP_TEXT,
    )
    price = models.FloatField(
        verbose_name=_("Preis (exkl. MwSt)"),
        default=0.0,
    )
    vat_rate = models.FloatField(
        verbose_name=_("MwSt-Satz"),
        choices=constants.VAT_RATES,
        default=constants.VAT_RATE_DEFAULT,
    )

    @admin.display(description=_("Bezeichnung"), ordering="name")
    def clean_name(self):
        return langselect(self.name)

    @admin.display(description=_("Kosten"))
    def __str__(self):
        vat_addition = f" + {self.vat_rate}% MwSt" if self.vat_rate else ""
        return f"[{self.pk}] { self.clean_name() } ({ self.price } CHF{vat_addition})"

    class Meta:
        verbose_name = _("Kosten")
        verbose_name_plural = _("Kosten")

    objects = models.Manager()

    ADMIN_ICON = "fa-solid fa-coins"


class Customer(CustomModel, AddressModelMixin, WooCommerceModelMixin):
    """Model representing a customer"""

    PKFILL_WIDTH = 8
    WOOCOMMERCE_URL_FORMAT = "{}/wp-admin/user-edit.php?user_id={}"
    NOTE_RELATION = "customer"

    email = models.EmailField(
        verbose_name=_("E-Mail Adresse"),
        blank=True,
    )
    first_name = models.CharField(
        verbose_name=_("Vorname"),
        max_length=250,
        default="",
        blank=True,
    )
    last_name = models.CharField(
        verbose_name=_("Nachname"),
        max_length=250,
        default="",
        blank=True,
    )
    company = models.CharField(
        verbose_name=_("Firma"),
        max_length=250,
        default="",
        blank=True,
    )
    username = models.CharField(
        verbose_name=_("Benutzername"),
        max_length=50,
        default="",
        blank=True,
    )
    avatar_url = models.URLField(
        verbose_name=_("Avatar URL"),
        blank=True,
        editable=False,
    )
    language = models.CharField(
        verbose_name=_("Sprache"),
        default="de",
        choices=constants.LANGUAGES,
        max_length=2,
    )

    combine_with = models.ForeignKey(
        to="self",
        verbose_name=_("Zusammenfügen mit"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_(
            "Dies kann nicht widerrufen werden! Werte im aktuellen Kunden werden bevorzugt."
        ),
    )
    website = models.URLField(
        verbose_name=_("Webseite"),
        default="",
        blank=True,
    )
    note = models.TextField(
        verbose_name=_("Bemerkung"),
        default="",
        blank=True,
    )

    email_link_registered = models.ForeignKey(
        to="EMail",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    @admin.display(description=_("Avatar"), ordering="avatar_url")
    def avatar(self):
        if self.avatar_url:
            return mark_safe('<img src="' + self.avatar_url + '" width="50px">')
        return ""

    @admin.display(description=_("Kunde"))
    def __str__(self):
        s = f"[{self.pkfill()}] "
        if self.woocommerceid:
            s += f"(WC#{self.woocommerceid}) "
        if self.first_name or self.addr_billing_first_name:
            s += f"{self.first_name or self.addr_billing_first_name} "
        if self.last_name or self.addr_billing_last_name:
            s += f"{self.last_name or self.addr_billing_last_name} "
        if self.company or self.addr_billing_company:
            s += f"{self.company or self.addr_billing_company} "
        if self.addr_billing_postcode and self.addr_billing_city:
            s += f"({self.addr_billing_postcode} {self.addr_billing_city})"
        return s

    class Meta:
        verbose_name = _("Kunde")
        verbose_name_plural = _("Kunden")

    def save(self, *args, **kwargs):
        if self.combine_with:
            self.combine_with_customer(self.combine_with)
            self.combine_with = None
        super().save(*args, **kwargs)

    def combine_with_customer(self, other: "Customer"):
        """Combine this customer with another customer.

        Values in the current customer are preferred. The other customer gets deleted.
        """

        for FIELD_NAME in (
            constants.ADDR_BILLING_FIELDS
            + constants.ADDR_SHIPPING_FIELDS
            + [
                "woocommerceid",
                "email",
                "first_name",
                "last_name",
                "company",
                "username",
                "avatar_url",
                "language",
                "website",
            ]
        ):
            setattr(
                self,
                FIELD_NAME,
                getattr(self, FIELD_NAME) or getattr(other, FIELD_NAME),
            )

        self.note = self.note + "\n" + other.note

        for order in other.orders.all():
            order.customer = self
            order.save()

        if getattr(other, "linked_note", False):
            other_linked_note = other.linked_note
            other_linked_note.linked_customer = (
                None if getattr(self, "linked_note", False) else self
            )
            other_linked_note.save()

        other.delete()

    def create_email_registered(self, lang=None):
        lang = lang or self.language
        with Language(lang):
            context = {
                "customer": {
                    "id": self.pk,
                    "first_name": self.first_name,
                    "last_name": self.last_name,
                    "company": self.company,
                    "email": self.email,
                }
            }

            self.email_link_registered = EMail.objects.create(
                subject=gettext("Registrierung erfolgreich!"),
                to=self.email,
                language=lang,
                html_template="customer_registered.html",
                html_context=context,
                notes=gettext("Diese E-Mail wurde automatisch aus Kunde #%d generiert.")
                % self.pk,
            )

            self.save()
            return self.email_link_registered

    objects = models.Manager()

    ADMIN_ICON = "fa-solid fa-users"

    DICT_EXCLUDE_FIELDS = ["email_link_registered", "combine_with"]


class Supplier(CustomModel):
    """Model representing a supplier (used only for categorizing)"""

    PKFILL_WIDTH = 4

    abbreviation = models.CharField(
        verbose_name=_("Kürzel"),
        max_length=5,
    )
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=50,
    )

    website = models.URLField(
        verbose_name=_("Webseite"),
        blank=True,
    )
    phone = models.CharField(
        verbose_name=_("Telefon"),
        max_length=50,
        default="",
        blank=True,
    )
    email = models.EmailField(
        verbose_name=_("E-Mail"),
        null=True,
        blank=True,
    )

    address = models.TextField(
        verbose_name=_("Adresse"),
        default="",
        blank=True,
    )
    note = models.TextField(
        verbose_name=_("Notiz"),
        default="",
        blank=True,
    )

    contact_person_name = models.CharField(
        verbose_name=_("Name"),
        max_length=250,
        default="",
        blank=True,
    )
    contact_person_phone = models.CharField(
        verbose_name=_("Telefon"),
        max_length=50,
        default="",
        blank=True,
    )
    contact_person_email = models.EmailField(
        verbose_name=_("E-Mail"),
        null=True,
        default="",
        blank=True,
    )

    @admin.display(description=_("Lieferant"))
    def __str__(self):
        return f"[{self.pk}] {self.name}"

    def assign(self):
        products = Product.objects.filter(supplier=None)
        for product in products:
            product.supplier = self
            product.save()
        return products.count()

    class Meta:
        verbose_name = _("Lieferant")
        verbose_name_plural = _("Lieferanten")

    objects = models.Manager()

    ADMIN_ICON = "fa-solid fa-truck"


class SupplyItem(CustomModel):
    """Model representing the connection between 'Supply' and 'Product'"""

    supply = models.ForeignKey(
        to="Supply",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        to="Product",
        verbose_name=_("Produkt"),
        on_delete=models.PROTECT,
    )
    quantity = models.IntegerField(
        verbose_name=_("Menge"),
        default=1,
    )

    @admin.display(description=_("Lieferungsposten"))
    def __str__(self):
        return f"[{self.pk}] {self.quantity}x {self.product}"

    class Meta:
        verbose_name = _("Lieferungsposten")
        verbose_name_plural = _("Lieferungsposten")

    objects = models.Manager()


class Supply(CustomModel):
    """Model representing an *incoming* delivery"""

    NOTE_RELATION = "delivery"

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=50,
        default=default_delivery_title,
    )
    date = models.DateField(
        verbose_name=_("Erfasst am"),
        auto_now_add=True,
    )

    supplier = models.ForeignKey(
        to="Supplier",
        verbose_name=_("Lieferant"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    products = models.ManyToManyField(
        to="Product",
        through="SupplyItem",
        through_fields=("supply", "product"),
    )

    is_added_to_stock = models.BooleanField(
        verbose_name=_("Eingelagert?"),
        default=False,
    )

    @admin.display(description=_("Anzahl Produkte"))
    def total_quantity(self):
        return self.products.through.objects.filter(supply=self).aggregate(
            models.Sum("quantity")
        )["quantity__sum"]

    def add_to_stock(self):
        if not self.is_added_to_stock:
            for i in self.products.through.objects.filter(supply=self):
                i.product.stock_current += i.quantity
                i.product.save()
            self.is_added_to_stock = True
            self.save()
            return True
        return False

    @admin.display(description=_("Lieferung"))
    def __str__(self):
        return f"[{self.pk}] {self.name}"

    class Meta:
        verbose_name = _("Lieferung")
        verbose_name_plural = _("Lieferungen")

    objects = models.Manager()

    ADMIN_ICON = "fa-solid fa-truck-ramp-box"


class Note(CustomModel):
    """Model representing a note"""

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=50,
    )
    description = models.TextField(
        verbose_name=_("Beschrieb"),
        default="",
        blank=True,
    )

    done = models.BooleanField(
        verbose_name=_("Erledigt?"),
        default=False,
    )

    priority = models.IntegerField(
        verbose_name=_("Priorität"),
        default=0,
        blank=True,
    )
    created_at = models.DateTimeField(
        verbose_name=_("Erstellt am"),
        auto_now_add=True,
    )

    linked_order = models.OneToOneField(
        to="Order",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="linked_note",
    )
    linked_product = models.OneToOneField(
        to="Product",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="linked_note",
    )
    linked_customer = models.OneToOneField(
        to="Customer",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="linked_note",
    )
    linked_supply = models.OneToOneField(
        to="Supply",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="linked_note",
    )

    @admin.display(description=_("🔗 Notiz"))
    def __str__(self):
        return f"[{self.pk}] {self.name}"

    def links(self):
        text = ""
        if self.linked_order:
            url = reverse(
                "admin:kmuhelper_order_change",
                kwargs={"object_id": self.linked_order.pk},
            )
            text += _("Bestellung")
            text += f" <a href='{url}'>#{self.linked_order.pk}</a><br>"
        if self.linked_product:
            url = reverse(
                "admin:kmuhelper_product_change",
                kwargs={"object_id": self.linked_product.pk},
            )
            text += _("Produkt")
            text += f" <a href='{url}'>#{self.linked_product.pk}</a><br>"
        if self.linked_customer:
            url = reverse(
                "admin:kmuhelper_customer_change",
                kwargs={"object_id": self.linked_customer.pk},
            )
            text += _("Kunde")
            text += f" <a href='{url}'>#{self.linked_customer.pk}</a><br>"
        if self.linked_supply:
            url = reverse(
                "admin:kmuhelper_supply_change",
                kwargs={"object_id": self.linked_supply.pk},
            )
            text += _("Lieferung")
            text += f" <a href='{url}'>#{self.linked_supply.pk}</a><br>"
        return mark_safe(text) or gettext("Diese Notiz hat keine Verknüpfungen.")

    class Meta:
        verbose_name = _("Notiz")
        verbose_name_plural = _("Notizen")

    objects = models.Manager()

    ADMIN_ICON = "fa-solid fa-note-sticky"


class Product(CustomModel, WooCommerceModelMixin):
    """Model representing a product"""

    NOTE_RELATION = "product"

    article_number = models.CharField(
        verbose_name=_("Artikelnummer"),
        max_length=25,
    )

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=500,
        help_text=I18N_HELP_TEXT,
    )
    short_description = models.TextField(
        verbose_name=_("Kurzbeschrieb"),
        default="",
        blank=True,
        help_text=I18N_HELP_TEXT,
    )
    description = models.TextField(
        verbose_name=_("Beschrieb"),
        default="",
        blank=True,
        help_text=I18N_HELP_TEXT,
    )

    quantity_description = models.CharField(
        verbose_name=_("Mengenbezeichnung"),
        max_length=100,
        default="Stück",
        blank=True,
        help_text=I18N_HELP_TEXT,
    )
    selling_price = models.FloatField(
        verbose_name=_("Normalpreis in CHF (exkl. MwSt)"),
        default=0,
    )
    vat_rate = models.FloatField(
        verbose_name=_("MwSt-Satz"),
        choices=constants.VAT_RATES,
        default=constants.VAT_RATE_DEFAULT,
    )

    stock_current = models.IntegerField(
        verbose_name=_("Lagerbestand"),
        default=0,
    )
    stock_target = models.IntegerField(
        verbose_name=_("Soll-Lagerbestand"),
        default=1,
    )

    note = models.TextField(
        verbose_name=_("Bemerkung"),
        default="",
        blank=True,
        help_text=_("Wird nicht gedruckt oder angezeigt; nur für eigene Zwecke."),
    )

    sale_from = models.DateTimeField(
        verbose_name=_("In Aktion von"),
        blank=True,
        null=True,
    )
    sale_to = models.DateTimeField(
        verbose_name=_("In Aktion bis"),
        blank=True,
        null=True,
    )
    sale_price = models.FloatField(
        verbose_name=_("Aktionspreis in CHF (exkl. MwSt)"),
        blank=True,
        null=True,
    )

    datasheet_url = models.CharField(
        verbose_name=_("Datenblattlink"),
        max_length=500,
        default="",
        blank=True,
    )
    image_url = models.URLField(
        verbose_name=_("Bildlink"),
        default="",
        blank=True,
    )

    supplier = models.ForeignKey(
        to="Supplier",
        verbose_name=_("Lieferant"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    supplier_price = models.CharField(
        verbose_name=_("Einkaufspreis"),
        default="",
        blank=True,
        max_length=20,
    )
    supplier_article_number = models.CharField(
        verbose_name=_("Lieferantenartikelnummer"),
        default="",
        blank=True,
        max_length=25,
    )
    supplier_url = models.URLField(
        verbose_name=_("Lieferantenurl (Für Nachbestellungen)"),
        default="",
        blank=True,
    )

    parent = models.ForeignKey(
        to="self",
        related_name="children",
        verbose_name=_("Übergeordnetes Produkt"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    categories = models.ManyToManyField(
        to="ProductCategory",
        through="ProductProductCategoryConnection",
        through_fields=("product", "category"),
        verbose_name=_("Kategorien"),
        related_name="products",
    )

    @admin.display(description=_("Bezeichnung"), ordering="name")
    def clean_name(self, lang="de"):
        return langselect(self.name, lang)

    @admin.display(description=_("Kurzbeschrieb"), ordering="short_description")
    def clean_short_description(self, lang="de"):
        return langselect(self.short_description, lang)

    @admin.display(description=_("Beschrieb"), ordering="description")
    def clean_description(self, lang="de"):
        return langselect(self.description, lang)

    @admin.display(description=_("Aktion?"), boolean=True)
    def is_on_sale(self):
        dt = timezone.now()
        if (not self.sale_price) or (self.selling_price == self.sale_price):
            # No sale price or sale price = regular price
            return None
        if self.sale_from and dt < self.sale_from:
            # Not yet started
            return False
        if self.sale_to and self.sale_to < dt:
            # Already ended
            return False
        return True

    def get_current_price(self):
        return self.sale_price if self.is_on_sale() else self.selling_price

    @admin.display(description=_("Aktueller Preis"))
    def display_current_price(self):
        return formatprice(self.get_current_price()) + " CHF"

    @admin.display(description=_("Nr."), ordering="article_number")
    def display_article_number(self):
        return self.article_number

    @admin.display(description=_("Produktbild"), ordering="image_url")
    def html_image(self):
        if self.image_url:
            return format_html('<img src="{}" width="100px">', self.image_url)
        return ""

    # Stock

    def get_reserved_stock(self):
        return (
            OrderItem.objects.filter(
                order__is_shipped=False, linked_product_id=self.pk
            ).aggregate(models.Sum("quantity"))["quantity__sum"]
            or 0
        )

    def get_incoming_stock(self):
        return (
            SupplyItem.objects.filter(
                supply__is_added_to_stock=False, product__id=self.pk
            ).aggregate(models.Sum("quantity"))["quantity__sum"]
            or 0
        )

    def get_stock_data(self, includemessage=False):
        """Get the stock and product information as a dictionary"""

        p_id = self.pk
        p_name = self.clean_name()
        p_article_number = self.article_number

        n_current = self.stock_current
        n_going = self.get_reserved_stock()
        n_coming = self.get_incoming_stock()
        n_min = self.stock_target

        data = {
            "product": {
                "id": p_id,
                "article_number": p_article_number,
                "name": p_name,
            },
            "stock": {
                "current": n_current,
                "going": n_going,
                "coming": n_coming,
                "min": n_min,
            },
            "stock_overbooked": n_current - n_going < 0,
            "stock_in_danger": n_current - n_going < n_min,
        }

        if includemessage:
            t_current = gettext("Aktuell")
            t_going = gettext("Ausgehend")
            t_coming = gettext("Eingehend")

            stockstring = f"{t_current}: { n_current } | {t_going}: { n_going }"
            if t_coming:
                stockstring += f" | {t_coming}: { n_coming }"

            adminurl = reverse(f"admin:kmuhelper_product_change", args=[self.pk])
            adminlink = format_html('<a href="{}">{}</a>', adminurl, p_name)

            formatdata = (adminlink, p_article_number, stockstring)

            if data["stock_overbooked"]:
                msg = gettext("Zu wenig Lagerbestand bei")
                data["message"] = format_html('{} "{}" [{}]: {}', msg, *formatdata)
            elif data["stock_in_danger"]:
                msg = gettext("Knapper Lagerbestand bei")
                data["message"] = format_html('{} "{}" [{}]: {}', msg, *formatdata)

        return data

    def show_stock_warning(self, request):
        data = self.get_stock_data(includemessage=True)

        if data["stock_overbooked"]:
            messages.error(request, data["message"])
        elif data["stock_in_danger"]:
            messages.warning(request, data["message"])

    @admin.display(description=_("Produkt"))
    def __str__(self):
        return f"[{self.pk}] {self.article_number} - {self.clean_name()}"

    class Meta:
        verbose_name = _("Produkt")
        verbose_name_plural = _("Produkte")

    objects = models.Manager()

    ADMIN_ICON = "fa-solid fa-cubes"


class ProductCategory(CustomModel, WooCommerceModelMixin):
    """Model representing a category for products"""

    WOOCOMMERCE_URL_FORMAT = (
        "{}/wp-admin/term.php?taxonomy=product_cat&tag_ID={}&post_type=product"
    )
    PKFILL_WIDTH = 4

    name = models.CharField(
        verbose_name=_("Bezeichnung"),
        max_length=250,
        default="",
    )
    description = models.TextField(
        verbose_name=_("Beschrieb"),
        default="",
        blank=True,
    )
    image_url = models.URLField(
        verbose_name=_("Bildlink"),
        blank=True,
    )

    parent_category = models.ForeignKey(
        to="self",
        verbose_name=_("Übergeordnete Kategorie"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    @admin.display(description=_("Bild"), ordering="image_url")
    def html_image(self):
        if self.image_url:
            return format_html('<img src="{}" width="100px">', self.image_url)
        return ""

    @admin.display(description=_("Anzahl Produkte"))
    def total_quantity(self):
        return self.products.count()

    @admin.display(description=_("Bezeichnung"), ordering="name")
    def clean_name(self):
        return langselect(self.name)

    @admin.display(description=_("Beschrieb"), ordering="description")
    def clean_description(self):
        return langselect(self.description)

    @admin.display(description=_("Kategorie"))
    def __str__(self):
        return f"[{self.pk}] {self.clean_name()}"

    class Meta:
        verbose_name = _("Produktkategorie")
        verbose_name_plural = _("Produktkategorien")

    objects = models.Manager()

    ADMIN_ICON = "fa-solid fa-folder-tree"


class ProductProductCategoryConnection(CustomModel):
    """Model representing the connection between 'Product' and 'ProductCategory'"""

    product = models.ForeignKey(
        to="Product",
        verbose_name=_("Produkt"),
        on_delete=models.CASCADE,
    )
    category = models.ForeignKey(
        to="ProductCategory",
        verbose_name=_("Produktkategorie"),
        on_delete=models.CASCADE,
    )

    @admin.display(description=_("Produkt-Kategorie-Verknüpfung"))
    def __str__(self):
        return f"{self.category.clean_name()} <- [{self.pk}] -> {self.product}"

    class Meta:
        verbose_name = _("Produkt-Kategorie-Verknüpfung")
        verbose_name_plural = _("Produkt-Kategorie-Verknüpfungen")

    objects = models.Manager()


class PaymentReceiver(CustomModel):
    """Model representing a payment receiver for the qr bill"""

    PKFILL_WIDTH = 3

    # Internal

    internal_name = models.CharField(
        verbose_name=_("Interne Bezeichnung"),
        max_length=250,
        default="",
    )

    # Payment

    mode = models.CharField(
        verbose_name=_("Modus"),
        max_length=15,
        choices=[
            ("QRR", _("QR-Referenz")),
            ("NON", _("Ohne Referenz")),
        ],
        default="QRR",
    )

    qriban = models.CharField(
        verbose_name=_("QR-IBAN"),
        max_length=21 + 5,
        validators=[
            RegexValidator(
                r"^(CH|LI)[0-9]{2}\s3[0-9]{3}\s[0-9]{4}\s[0-9]{4}\s[0-9]{4}\s[0-9]{1}$",
                _("Bite benutze folgendes Format: (CH|LI)pp 3xxx xxxx xxxx xxxx x"),
            ),
        ],
        help_text=_("QR-IBAN mit Leerzeichen (Nur verwendet im Modus 'QR-Referenz')"),
        blank=True,
        default="",
    )
    iban = models.CharField(
        verbose_name=_("IBAN"),
        max_length=21 + 5,
        validators=[
            RegexValidator(
                r"^(CH|LI)[0-9]{2}\s[0-9]{4}\s[0-9]{4}\s[0-9]{4}\s[0-9]{4}\s[0-9]{1}$",
                _("Bite benutze folgendes Format: (CH|LI)pp 3xxx xxxx xxxx xxxx x"),
            ),
        ],
        help_text=_("IBAN mit Leerzeichen (Nur verwendet im Modus 'Ohne Referenz')"),
        blank=True,
        default="",
    )

    # Display information

    display_name = models.CharField(
        verbose_name=_("Anzeigename"),
        max_length=70,
        default="",
        help_text=_("Wird oben auf der Rechnung angezeigt."),
    )
    display_address_1 = models.CharField(
        verbose_name=_("Adresszeile 1"),
        max_length=70,
        default="",
        help_text=_("Wird oben auf der Rechnung angezeigt."),
    )
    display_address_2 = models.CharField(
        verbose_name=_("Adresszeile 2"),
        max_length=70,
        default="",
        help_text=_("Wird oben auf der Rechnung angezeigt."),
    )

    website = models.URLField(
        verbose_name=_("Webseite"),
        default="",
        blank=True,
        help_text=_("Auf der Rechnung ersichtlich, sofern vorhanden!"),
    )

    logourl = models.URLField(
        verbose_name=_("Logo (URL)"),
        validators=[
            RegexValidator(
                r"""^[0-9a-zA-Z\-\.\|\?\(\)\*\+&"'_:;/]+\.(png|jpg)$""",
                _("""Nur folgende Zeichen gestattet: 0-9a-zA-Z-_.:;/|?&()"'*+ - """)
                + _("""Muss auf .jpg/.png enden."""),
            ),
        ],
        help_text=_("URL eines Bildes (.jpg/.png) - Wird auf die Rechnung gedruckt."),
        blank=True,
        default="",
    )

    swiss_uid = models.CharField(
        verbose_name=_("Firmen-UID"),
        max_length=15,
        validators=[
            RegexValidator(
                r"^CHE-[0-9]{3}\.[0-9]{3}\.[0-9]{3}$",
                _("Bite benutze folgendes Format: CHE-123.456.789"),
            )
        ],
        help_text=_("UID der Firma - Format: CHE-123.456.789 (Mehrwertsteuernummer)"),
        blank=True,
        default="",
    )

    invoice_display_mode = models.CharField(
        verbose_name=_("Anzeigemodus für Rechnungen"),
        max_length=25,
        choices=constants.INVOICE_DISPLAY_MODES,
        default="business_orders",
        help_text=_("Je nach Modus werden andere Daten auf der Rechnung angezeigt."),
    )

    # Payment information

    invoice_name = models.CharField(
        verbose_name=_("Kontoinhaber"),
        max_length=70,
        help_text=_("Name / Firma"),
    )
    invoice_street = models.CharField(
        verbose_name=pgettext_lazy("address", "Strasse"),
        max_length=70,
        help_text=_("Strasse oder Postfach"),
    )
    invoice_street_nr = models.CharField(
        verbose_name=pgettext_lazy("address", "Hausnummer"),
        max_length=16,
        blank=True,
    )
    invoice_postcode = models.CharField(
        verbose_name=pgettext_lazy("address", "Postleitzahl"),
        max_length=16,
    )
    invoice_city = models.CharField(
        verbose_name=pgettext_lazy("address", "Ort"),
        max_length=35,
    )
    invoice_country = models.CharField(
        verbose_name=_("Land"),
        max_length=2,
        choices=constants.COUNTRIES,
        default="CH",
    )

    # Default

    is_default = models.BooleanField(
        verbose_name=_("Standard?"),
        default=False,
        help_text=_(
            "Aktivieren, um diesen Zahlungsempfänger als Standard zu setzen. Der Standard-Zahlungsempfänger wird bei "
            "der Erstellung einer neuen Bestellung sowie beim Import einer Bestellung von WooCommerce verwendet."
        ),
    )

    # Validation

    @classmethod
    def _check_iban(cls, iban: str, qr_required=False):
        try:
            b = ""
            # Translate letters to numbers
            for i in (0, 1):
                a = str(iban)[i].upper()
                if a not in string.ascii_uppercase:
                    return False
                b += str(ord(a) - 55)
            # Select only digits
            num = "".join([z for z in str(iban)[2:] if z in string.digits])
            # Check if QR-IBAN is required
            if qr_required and not num[2] == "3":
                return False
            # Validate IBAN
            result = int(int(num[2:] + b + num[:2]) % 97) == 1
            return result
        except IndexError:
            return False

    @classmethod
    def _check_uid(cls, uid: str):
        try:
            u = uid.split("-")[1].replace(".", "")
            p = 11 - (
                (
                    (int(u[0]) * 5)
                    + (int(u[1]) * 4)
                    + (int(u[2]) * 3)
                    + (int(u[3]) * 2)
                    + (int(u[4]) * 7)
                    + (int(u[5]) * 6)
                    + (int(u[6]) * 5)
                    + (int(u[7]) * 4)
                )
                % 11
            )
            return int(u[8]) == p
        except Exception as e:
            log("Error while validating UID:", e)
            return False

    def has_valid_qr_iban(self):
        return self._check_iban(self.qriban, qr_required=True)

    def has_valid_iban(self):
        return self._check_iban(self.iban)

    def has_valid_uid(self):
        return self._check_uid(self.swiss_uid)

    # Properties

    @property
    @admin.display(description=_("Interne Bezeichnung"))
    def admin_name(self):
        return self.internal_name or self.display_name or self.invoice_name

    @property
    @admin.display(description=_("IBAN"))
    def active_iban(self):
        return self.qriban if self.mode == "QRR" else self.iban

    # More

    @admin.display(description=_("Zahlungsempfänger"))
    def __str__(self):
        return f"[{self.pk}] {self.admin_name}"

    def clean(self):
        super().clean()

        errors = {}

        if self.mode == "QRR" and not self.has_valid_qr_iban():
            errors["qriban"] = ValidationError(
                _("Im Modus 'QR-Referenz' muss eine gültige QR-IBAN angegeben werden!")
            )
        if self.mode == "NON" and not self.has_valid_iban():
            errors["iban"] = ValidationError(
                _("Im Modus 'Ohne Referenz' muss eine gültige IBAN angegeben werden!")
            )
        if self.swiss_uid and not self.has_valid_uid():
            errors["swiss_uid"] = ValidationError(
                _("Die UID ist ungültig!"), code="invalid"
            )
        if self.logourl:
            try:
                response = requests.get(self.logourl)
                response.raise_for_status()
            except requests.RequestException as e:
                errors["logourl"] = ValidationError(
                    _("An dieser Adresse konnte kein Bild abgerufen werden! Fehler: %s")
                    % str(e)
                )

        if errors:
            raise ValidationError(errors)

    class Meta:
        verbose_name = _("Zahlungsempfänger")
        verbose_name_plural = _("Zahlungsempfänger")

    objects = models.Manager()

    ADMIN_ICON = "fa-solid fa-hand-holding-dollar"
