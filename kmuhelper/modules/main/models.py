from datetime import datetime, timedelta
from random import randint
from rich import print
import string


from django.db import models
from django.contrib import admin, messages
from django.core import mail
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.html import mark_safe, format_html
from django.urls import reverse

from kmuhelper import settings, constants
from kmuhelper.modules.emails.models import EMail, Attachment
from kmuhelper.modules.pdfgeneration import PDFOrder
from kmuhelper.overrides import CustomModel
from kmuhelper.utils import runden, formatprice, modulo10rekursiv, send_pdf, faq
from kmuhelper.translations import langselect, I18N_HELP_TEXT

from django.utils import translation
_ = translation.gettext

def log(string, *args):
    print("[deep_pink4][KMUHelper Main][/] -", string, *args)

###################


def default_delivery_title():
    return "Lieferung vom "+str(datetime.now().strftime("%d.%m.%Y"))


def default_payment_recipient():
    if Zahlungsempfaenger.objects.exists():
        return Zahlungsempfaenger.objects.first().pk
    return None


def default_contact_person():
    if Ansprechpartner.objects.exists():
        return Ansprechpartner.objects.first().pk
    return None


def default_order_key():
    return "kh-"+str(randint(10000000, 99999999))


def default_payment_conditions():
    return settings.get_db_setting("default-payment-conditions", "0:30")

# GUTSCHEINTYPEN = [
#     ("percent", "Prozent"),
#     ("fixed_cart", "Fixer Betrag auf den Warenkorb"),
#     ("fixed_product", "Fixer Betrag auf ein Produkt")
# ]

# ORDER_FREQUENCY_TYPES = [
#     ("weekly", "Wöchentlich"),
#     ("monthly", "Monatlich"),
#     ("yearly", "Jährlich"),
# ]

#############


class Ansprechpartner(CustomModel):
    """Model representing a contact person"""

    name = models.CharField(
        verbose_name="Name",
        max_length=50,
        help_text="Auf Rechnung ersichtlich!",
    )
    phone = models.CharField(
        verbose_name="Telefon",
        max_length=50,
        help_text="Auf Rechnung ersichtlich!",
    )
    email = models.EmailField(
        verbose_name="E-Mail",
        help_text="Auf Rechnung ersichtlich!",
    )

    @admin.display(description="Ansprechpartner")
    def __str__(self):
        return f"{self.name} ({self.pk})"

    class Meta:
        verbose_name = "Ansprechpartner"
        verbose_name_plural = "Ansprechpartner"

    objects = models.Manager()

    admin_icon = "fas fa-user-tie"


class Bestellungskosten(CustomModel):
    """Model representing costs for an order (e.g. shipping costs)"""

    # Links to other models
    bestellung = models.ForeignKey(
        to='Bestellung',
        on_delete=models.CASCADE,
    )
    kosten = models.ForeignKey(
        to='Kosten',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
    )

    # Custom data printed on the invoice
    note = models.CharField(
        verbose_name="Bemerkung",
        default="",
        max_length=250,
        blank=True,
        help_text="Wird auf die Rechnung gedruckt.",
    )

    discount = models.FloatField(
        verbose_name="Rabatt in %",
        default=0.0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    # Data from Kosten
    name = models.CharField(
        verbose_name="Name",
        max_length=500,
        default="Zusätzliche Kosten",
        help_text=I18N_HELP_TEXT,
    )
    price = models.FloatField(
        verbose_name="Preis (exkl. MwSt)",
        default=0.0,
    )
    vat_rate = models.FloatField(
        verbose_name="MwSt-Satz",
        choices=constants.VAT_RATES,
        default=constants.VAT_RATE_DEFAULT,
    )

    # Calculated data
    def calc_subtotal(self):
        return runden(self.price*((100-self.discount)/100))

    def calc_subtotal_without_discount(self):
        return runden(self.price)

    def calc_discount(self):
        return runden(self.price*(self.discount/100))*-1

    # Display methods
    @admin.display(description="Name", ordering="name")
    def clean_name(self):
        return langselect(self.name)

    @admin.display(description="Zwischensumme (exkl. MwSt)")
    def display_subtotal(self):
        return formatprice(self.calc_subtotal()) + " CHF"

    @admin.display(description="Bestellungskosten")
    def __str__(self):
        if self.kosten:
            return f"({self.pk}) {self.clean_name()} ({self.kosten.pk})"
        return f"({self.pk}) {self.clean_name()}"

    def save(self, *args, **kwargs):
        if self.pk is None and self.kosten is not None:
            self.name = self.kosten.name
            self.price = self.kosten.price
            self.vat_rate = self.kosten.vat_rate
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Bestellungskosten"
        verbose_name_plural = "Bestellungskosten"

    objects = models.Manager()

    def copyto(self, bestellung):
        self.pk = None
        self._state.adding = True
        self.bestellung = bestellung
        self.save()


class Bestellungsposten(CustomModel):
    """Model representing the connection between 'Bestellung' and 'Produkt'"""

    bestellung = models.ForeignKey(
        to='Bestellung',
        on_delete=models.CASCADE,
    )
    produkt = models.ForeignKey(
        to='Produkt',
        on_delete=models.PROTECT,
    )
    note = models.CharField(
        verbose_name="Bemerkung",
        default="",
        max_length=250,
        blank=True,
        help_text="Wird auf die Rechnung gedruckt.",
    )

    quantity = models.IntegerField(
        verbose_name="Menge",
        default=1,
    )
    discount = models.IntegerField(
        verbose_name="Rabatt in %",
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    product_price = models.FloatField(
        verbose_name="Produktpreis (exkl. MwSt)",
        default=0.0,
    )

    # Calculated data
    def calc_subtotal(self):
        return runden(self.product_price*self.quantity*((100-self.discount)/100))

    def calc_subtotal_without_discount(self):
        return runden(self.product_price*self.quantity)

    def calc_discount(self):
        return runden(self.product_price*self.quantity*(self.discount/100))*-1

    # Display methods
    @admin.display(description="MwSt-Satz")
    def display_vat_rate(self):
        return formatprice(self.produkt.vat_rate)

    @admin.display(description="Zwischensumme (exkl. MwSt)")
    def display_subtotal(self):
        return formatprice(self.calc_subtotal()) + " CHF"

    @admin.display(description="Bestellungsposten")
    def __str__(self):
        return f'({self.pk}) {self.quantity}x {self.produkt.clean_name()} ({self.produkt.pk})'

    def save(self, *args, **kwargs):
        if not self.product_price:
            self.product_price = runden(self.produkt.get_current_price())
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Bestellungsposten"
        verbose_name_plural = "Bestellungsposten"

    objects = models.Manager()

    def copyto(self, bestellung):
        self.pk = None
        self._state.adding = True
        self.bestellung = bestellung
        self.save()


class Bestellung(CustomModel):
    """Model representing an order"""

    woocommerceid = models.IntegerField(
        verbose_name="WooCommerce ID",
        default=0,
    )

    date = models.DateTimeField(
        verbose_name="Datum",
        default=timezone.now,
    )

    invoice_date = models.DateField(
        verbose_name="Rechnungsdatum",
        default=None,
        blank=True,
        null=True,
        help_text="Datum der Rechnung. Wird auch als Startpunkt für die Zahlungskonditionen verwendet.",
    )
    pdf_title = models.CharField(
        verbose_name="Rechnungstitel",
        default="",
        blank=True,
        max_length=32,
        help_text="Titel der Rechnung. Leer lassen für 'RECHNUNG'",
    )
    pdf_text = models.TextField(
        verbose_name="Rechnungstext",
        default="",
        blank=True,
        help_text=mark_safe(
            "Wird auf der Rechnung gedruckt! Unterstützt " +
            "<abbr title='<b>Fett</b><u>Unterstrichen</u><i>Kursiv</i>'>XML markup</abbr>."
        ),
    )
    payment_conditions = models.CharField(
        verbose_name="Zahlungskonditionen",
        default=default_payment_conditions,
        validators=[
            RegexValidator(
                "^([0-9]+(\.[0-9]+)?:[0-9]+;)*0:[0-9]+$",
                "Bitte benutze folgendes Format: 'p:d;p:d' - p = Skonto in %; d = Tage",
            )
        ],
        max_length=16,
        help_text="Skonto und Zahlungsfrist -> "+faq('wie-funktionieren-zahlungskonditionen', 'Mehr erfahren'),
    )

    status = models.CharField(
        verbose_name="Status",
        max_length=11,
        default='processing',
        choices=constants.ORDERSTATUS,
    )
    is_shipped = models.BooleanField(
        verbose_name="Versendet",
        default=False,
        help_text='Mehr Infos -> '+faq('was-passiert-wenn-ich-eine-bestellung-als-bezahltversendet-markiere', 'FAQ'),
    )
    shipped_on = models.DateField(
        verbose_name="Versendet am",
        default=None,
        blank=True,
        null=True,
    )
    tracking_number = models.CharField(
        verbose_name="Trackingnummer",
        default="",
        blank=True,
        max_length=25,
        validators=[
            RegexValidator(
                r'^99\.[0-9]{2}\.[0-9]{6}\.[0-9]{8}$',
                'Bite benutze folgendes Format: 99.xx.xxxxxx.xxxxxxxx',
            )
        ],
        help_text="Bitte gib hier eine Trackingnummer der Schweizer Post ein. (optional)",
    )

    is_removed_from_stock = models.BooleanField(
        verbose_name="Ausgelagert",
        default=False,
    )

    payment_method = models.CharField(
        verbose_name="Zahlungsmethode",
        max_length=7,
        default="cod",
        choices=constants.PAYMENTMETHODS,
    )
    is_paid = models.BooleanField(
        verbose_name="Bezahlt",
        default=False,
        help_text='Mehr Infos -> '+faq('was-passiert-wenn-ich-eine-bestellung-als-bezahltversendet-markiere', 'FAQ'),
    )
    paid_on = models.DateField(
        verbose_name="Bezahlt am",
        default=None,
        blank=True,
        null=True,
    )

    customer_note = models.TextField(
        verbose_name="Kundennotiz",
        default="",
        blank=True,
        help_text="Vom Kunden erfasste Notiz.",
    )

    order_key = models.CharField(
        verbose_name="Bestellungs-Schlüssel",
        max_length=50,
        blank=True,
        default=default_order_key,
    )

    kunde = models.ForeignKey(
        to='Kunde',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='bestellungen',
    )
    zahlungsempfaenger = models.ForeignKey(
        to='Zahlungsempfaenger',
        on_delete=models.PROTECT,
        verbose_name="Zahlungsempfänger",
        default=default_payment_recipient,
    )
    ansprechpartner = models.ForeignKey(
        to='Ansprechpartner',
        verbose_name="Ansprechpartner",
        on_delete=models.PROTECT,
        default=default_contact_person,
    )

    # Billing address

    @property
    def addr_billing(self):
        return {
            'first_name': self.addr_billing_first_name,
            'last_name': self.addr_billing_last_name,
            'company': self.addr_billing_company,
            'address_1': self.addr_billing_address_1,
            'address_2': self.addr_billing_address_2,
            'postcode': self.addr_billing_postcode,
            'city': self.addr_billing_city,
            'state': self.addr_billing_state,
            'country': self.addr_billing_country,
            'email': self.addr_billing_email,
            'phone': self.addr_billing_phone,
        }

    addr_billing_first_name = models.CharField(
        verbose_name="Vorname",
        max_length=250,
        default="",
        blank=True,
    )
    addr_billing_last_name = models.CharField(
        verbose_name="Nachname",
        max_length=250,
        default="",
        blank=True,
    )
    addr_billing_company = models.CharField(
        verbose_name="Firma",
        max_length=250,
        default="",
        blank=True,
    )
    addr_billing_address_1 = models.CharField(
        verbose_name="Adresszeile 1",
        max_length=250,
        default="",
        blank=True,
        help_text="Strasse und Hausnummer oder 'Postfach'",
    )
    addr_billing_address_2 = models.CharField(
        verbose_name="Adresszeile 2",
        max_length=250,
        default="",
        blank=True,
        help_text="Wird in QR-Rechnung NICHT verwendet!",
    )
    addr_billing_city = models.CharField(
        verbose_name="Ort",
        max_length=250,
        default="",
        blank=True,
    )
    addr_billing_state = models.CharField(
        verbose_name="Kanton",
        max_length=50,
        default="",
        blank=True,
    )
    addr_billing_postcode = models.CharField(
        verbose_name="Postleitzahl",
        max_length=50,
        default="",
        blank=True,
    )
    addr_billing_country = models.CharField(
        verbose_name="Land",
        max_length=2,
        default="CH",
        choices=constants.COUNTRIES,
    )
    addr_billing_email = models.EmailField(
        verbose_name="E-Mail Adresse",
        blank=True,
    )
    addr_billing_phone = models.CharField(
        verbose_name="Telefon",
        max_length=50,
        default="",
        blank=True,
    )

    # Shipping address

    @property
    def addr_shipping(self):
        return {
            'first_name': self.addr_shipping_first_name,
            'last_name': self.addr_shipping_last_name,
            'company': self.addr_shipping_company,
            'address_1': self.addr_shipping_address_1,
            'address_2': self.addr_shipping_address_2,
            'postcode': self.addr_shipping_postcode,
            'city': self.addr_shipping_city,
            'state': self.addr_shipping_state,
            'country': self.addr_shipping_country,
            'email': self.addr_shipping_email,
            'phone': self.addr_shipping_phone,
        }

    addr_shipping_first_name = models.CharField(
        verbose_name="Vorname",
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_last_name = models.CharField(
        verbose_name="Nachname",
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_company = models.CharField(
        verbose_name="Firma",
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_address_1 = models.CharField(
        verbose_name="Adresszeile 1",
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_address_2 = models.CharField(
        verbose_name="Adresszeile 2",
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_city = models.CharField(
        verbose_name="Ort",
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_state = models.CharField(
        verbose_name="Kanton",
        max_length=50,
        default="",
        blank=True,
    )
    addr_shipping_postcode = models.CharField(
        verbose_name="Postleitzahl",
        max_length=50,
        default="",
        blank=True,
    )
    addr_shipping_country = models.CharField(
        verbose_name="Land",
        max_length=2,
        default="CH",
        choices=constants.COUNTRIES,
    )
    addr_shipping_email = models.EmailField(
        verbose_name="E-Mail Adresse",
        blank=True,
    )
    addr_shipping_phone = models.CharField(
        verbose_name="Telefon",
        max_length=50,
        default="",
        blank=True,
    )

    # Connections

    products = models.ManyToManyField(
        to='Produkt',
        through='Bestellungsposten',
        through_fields=('bestellung', 'produkt'),
    )

    kosten = models.ManyToManyField(
        to='Kosten',
        through='Bestellungskosten',
        through_fields=('bestellung', 'kosten'),
    )

    email_link_invoice = models.ForeignKey(
        to='EMail',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='+',
    )
    email_link_shipped = models.ForeignKey(
        to='EMail',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='+',
    )

    cached_sum = models.FloatField(
        verbose_name="Summe in CHF",
        default=0.0,
    )

    # # Wiederkehrende Rechnungen

    # recurring = models.BooleanField("Wiederkehrend", default=False)
    # recurring_next = models.DateField("Wiederkehrend am", default=None, blank=True, null=True)
    # recurring_until = models.DateField("Wiederkehrend bis", default=None, blank=True, null=True)
    # recurring_frequency = models.CharField("Häufigkeit", choices=ORDER_FREQUENCY_TYPES, default=None, blank=True, null=True)

    def import_customer_data(self):
        "Copy the customer data from the customer into the order"

        for field in constants.ADDR_SHIPPING_FIELDS+constants.ADDR_BILLING_FIELDS:
            setattr(self, field, getattr(self.kunde, field))

    def second_save(self, *args, **kwargs):
        "This HAS to be called after all related models have been saved."

        self.cached_sum = self.calc_total()
        if self.is_shipped and (not self.is_removed_from_stock):
            for i in self.products.through.objects.filter(bestellung=self):
                i.produkt.lagerbestand -= i.quantity
                i.produkt.save()
            self.is_removed_from_stock = True

        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.pk and not self.woocommerceid and self.kunde:
            self.import_customer_data()

        if self.invoice_date is None:
            self.invoice_date = timezone.now()

        super().save(*args, **kwargs)

    @admin.display(description="Trackinglink", ordering="tracking_number")
    def tracking_link(self):
        return f'https://www.post.ch/swisspost-tracking?formattedParcelCodes={self.tracking_number}' if self.tracking_number else None

    def unstrukturierte_mitteilung(self):
        if self.zahlungsempfaenger.mode == "QRR":
            return str(self.date.strftime("%d.%m.%Y"))
        return _("Referenznummer:")+" "+str(self.id)

    def referenznummer(self):
        a = self.pkfill(22)+"0000"
        b = a+str(modulo10rekursiv(a))
        c = b[0:2]+" "+b[2:7]+" "+b[7:12]+" " + \
            b[12:17]+" "+b[17:22]+" "+b[22:27]
        return c

    def rechnungsinformationen(self):
        date = (self.invoice_date or self.date).strftime("%y%m%d")

        output = f'//S1/10/{self.pk}/11/{date}'

        if self.zahlungsempfaenger.swiss_uid:
            uid = self.zahlungsempfaenger.swiss_uid.split("-")[1].replace(".", "")
            output += f'/30/{uid}'
        cond = self.payment_conditions
        vat_dict = self.get_vat_dict()
        var_str = ";".join(
            f'{rate}:{vat_dict[rate]}' for rate in vat_dict)

        output += f'/31/{date}/32/{var_str}/40/{cond}'
        return output

    def get_payment_conditions_data(self):
        "Get the payment conditions as a list of dictionaries"

        data = []
        for pc in self.payment_conditions.split(";"):
            percent, days = pc.split(":")
            percent, days = float(percent), int(days)
            data.append({
                "days": days,
                "date": (self.invoice_date or self.order_date)+timedelta(days=days),
                "percent": percent,
                "price": runden(self.cached_sum*(1-(percent/100))),
            })
        data.sort(key=lambda x: x["date"])
        return data

    def get_vat_dict(self):
        "Get the VAT as a dictionary"
        vat_dict = {}
        for p in self.products.through.objects.filter(bestellung=self).select_related('produkt'):
            if str(p.produkt.vat_rate) in vat_dict:
                vat_dict[str(p.produkt.vat_rate)] += p.calc_subtotal()
            else:
                vat_dict[str(p.produkt.vat_rate)] = p.calc_subtotal()
        for k in self.kosten.through.objects.filter(bestellung=self).select_related('kosten'):
            if str(k.vat_rate) in vat_dict:
                vat_dict[str(k.vat_rate)] += k.calc_subtotal()
            else:
                vat_dict[str(k.vat_rate)] = k.calc_subtotal()
        for s in vat_dict:
            vat_dict[s] = runden(vat_dict[s])
        return vat_dict

    def calc_total_without_vat(self):
        total = 0
        for i in self.products.through.objects.filter(bestellung=self).select_related("produkt"):
            total += i.calc_subtotal()
        for i in self.kosten.through.objects.filter(bestellung=self).select_related("kosten"):
            total += i.calc_subtotal()
        return runden(total)

    def calc_total_vat(self):
        total_vat = 0
        vat_dict = self.get_vat_dict()
        for vat_rate in vat_dict:
            total_vat += runden(float(vat_dict[vat_rate]
                                       * (float(vat_rate)/100)))
        return runden(total_vat)

    def calc_total(self):
        return runden(self.calc_total_without_vat()+self.calc_total_vat())

    @admin.display(description="Rechnungstotal")
    def display_total_breakdown(self):
        return f'{formatprice(self.calc_total_without_vat())} CHF + {formatprice(self.calc_total_vat())} CHF MwSt = {formatprice(self.calc_total())} CHF'

    @admin.display(description="Total", ordering="cached_sum")
    def display_cached_sum(self):
        return f'{formatprice(self.cached_sum)} CHF'

    @admin.display(description="Name")
    def name(self):
        return (f'{self.date.year}-' if self.date and not isinstance(self.date, str) else '') + \
               (f'{self.pkfill(6)}'+(f' (WC#{self.woocommerceid})' if self.woocommerceid else '')) + \
               (f' - {self.kunde}' if self.kunde is not None else " Gast")

    @admin.display(description="Info")
    def info(self):
        return f'{self.date.strftime("%d.%m.%Y")} - '+((self.kunde.company if self.kunde.company else (f'{self.kunde.first_name} {self.kunde.last_name}')) if self.kunde else "Gast")

    @admin.display(description="Bezahlt nach")
    def display_paid_after(self):
        if self.paid_on is None:
            return "-"
        
        daydiff = (self.paid_on - self.invoice_date).days
        return f'{daydiff} Tag{"en" if daydiff != 1 else ""}'

    @admin.display(description="Konditionen")
    def display_payment_conditions(self):
        "Get the payment conditions as a multiline string of values"

        conditions = self.get_payment_conditions_data()
        output = ""

        for condition in conditions:
            datestr = condition["date"].strftime("%d.%m.%Y")
            price = formatprice(condition["price"])
            percent = condition["percent"]
            output += f'{price} CHF bis {datestr} ({percent}%)<br>'

        return mark_safe(output)

    def is_correct_payment(self, amount: float, date: datetime):
        "Check if a payment made on a certain date has the correct amount for this order"

        if amount == self.cached_sum:
            return True
        
        for condition in self.get_payment_conditions_data():
            if amount == condition["price"] and date <= condition["date"]:
                return True

        return False

    @admin.display(description="Bestellung")
    def __str__(self):
        return self.name()

    def create_email_invoice(self):
        context = {
            "tracking_link": str(self.tracking_link()),
            "trackingdata": bool(self.tracking_number and self.is_shipped),
            "id": str(self.id),
            "woocommerceid": str(self.woocommerceid),
            "woocommercedata": bool(self.woocommerceid),
        }

        self.email_link_invoice = EMail.objects.create(
            subject=f"Ihre Rechnung Nr. { self.id }"+(
                f' (Online #{self.woocommerceid})' if self.woocommerceid else ''),
            to=self.addr_billing_email,
            html_template="bestellung_rechnung.html",
            html_context=context,
            notes=f"Diese E-Mail wurde automatisch aus Bestellung #{self.pk} generiert.",
        )

        filename = f"Rechnung Nr. { self.id }"+(
            f' (Online #{self.woocommerceid})' if self.woocommerceid else '')+".pdf"

        self.email_link_invoice.add_attachments(
            Attachment.objects.create_from_binary(
                filename=filename,
                content=PDFOrder(self, "Rechnung").get_pdf()
            )
        )

        self.save()
        return self.email_link_invoice

    def create_email_shipped(self):
        context = {
            "tracking_link": str(self.tracking_link()),
            "trackingdata": bool(self.tracking_link() and self.is_shipped),
            "id": str(self.id),
            "woocommerceid": str(self.woocommerceid),
            "woocommercedata": bool(self.woocommerceid),
        }

        self.email_link_shipped = EMail.objects.create(
            subject=f"Ihre Lieferung Nr. { self.id }",
            to=self.addr_shipping_email,
            html_template="bestellung_lieferung.html",
            html_context=context,
            notes=f"Diese E-Mail wurde automatisch aus Bestellung #{self.pk} generiert.",
        )

        filename = f"Lieferschein Nr. { self.id }.pdf"

        self.email_link_shipped.add_attachments(
            Attachment.objects.create_from_binary(
                filename=filename,
                content=PDFOrder(self, "Lieferschein", is_delivery_note=True).get_pdf()
            )
        )

        self.save()
        return self.email_link_shipped

    @admin.display(description="🔗 Notiz")
    def html_app_notiz(self):
        if hasattr(self, "notiz"):
            link = reverse("admin:kmuhelper_app_todo_change",
                           kwargs={"object_id": self.notiz.pk})
            text = "Notiz ansehen"
        else:
            link = reverse("admin:kmuhelper_app_todo_add") + \
                '?from_bestellung='+str(self.pk)
            text = "Notiz hinzufügen"
        return format_html('<a target="_blank" href="{}">{}</a>', link, text)

    @admin.display(description="🔗 Notiz")
    def html_notiz(self):
        if hasattr(self, "notiz"):
            link = reverse("admin:kmuhelper_notiz_change",
                           kwargs={"object_id": self.notiz.pk})
            text = "Notiz ansehen"
        else:
            link = reverse("admin:kmuhelper_notiz_add") + \
                '?from_bestellung='+str(self.pk)
            text = "Notiz hinzufügen"
        return format_html('<a target="_blank" href="{}">{}</a>', link, text)

    def get_stock_data(self):
        """Get the stock data of all products in this order"""

        return [p.get_stock_data() for p in self.products.all()]

    def email_stock_warning(self):
        email_receiver = settings.get_db_setting(
            "email-stock-warning-receiver")

        if email_receiver:
            warnings = []
            stock = self.get_stock_data()
            for data in stock:
                if data["stock_in_danger"]:
                    warnings.append(data)

            if warnings != []:
                email = EMail.objects.create(
                    subject="[KMUHelper] - Lagerbestand knapp!",
                    to=email_receiver,
                    html_template="bestellung_stock_warning.html",
                    html_context={
                        "warnings": warnings,
                    },
                    notes=f"Diese E-Mail wurde automatisch aus Bestellung #{self.pk} generiert.",
                )

                success = email.send(
                    headers={
                        "Bestellungs-ID": str(self.pk)
                    },
                )
                return bool(success)
        else:
            log("Keine E-Mail für Warnungen zum Lagerbestand festgelegt!")
        return None

    class Meta:
        verbose_name = "Bestellung"
        verbose_name_plural = "Bestellungen"

    def duplicate(self):
        new = Bestellung.objects.create(
            kunde=self.kunde,
            zahlungsempfaenger=self.zahlungsempfaenger,
            ansprechpartner=self.ansprechpartner,

            pdf_title=self.pdf_title,
            pdf_text=self.pdf_text,
            payment_conditions=self.payment_conditions,

            customer_note=f"Kopie aus Bestellung #{self.pk}\n--------------------------------\n{self.customer_note}",
        )

        for field in constants.ADDR_SHIPPING_FIELDS+constants.ADDR_BILLING_FIELDS:
            setattr(new, field, getattr(self, field))

        for bp in self.products.through.objects.filter(bestellung=self):
            bp.copyto(new)
        for bk in self.kosten.through.objects.filter(bestellung=self):
            bk.copyto(new)
        new.save()
        return new

    def copy_to_delivery(self):
        new = Lieferung.objects.create(
            name=f"Rücksendung von Bestellung #{self.pk}"
        )
        for lp in self.products.through.objects.filter(bestellung=self):
            new.products.add(lp.produkt, through_defaults={"quantity": lp.quantity})
        new.save()
        return new

    objects = models.Manager()

    admin_icon = "fas fa-clipboard-list"

    DICT_EXCLUDE_FIELDS = ['products', 'kosten', 'email_link_invoice', 'email_link_shipped', 'kunde',
                           'ansprechpartner', 'zahlungsempfaenger', 'is_removed_from_stock',
                           'is_shipped', 'is_paid', 'payment_method', 'order_key']


# class Gutschein(CustomModel):
#     woocommerceid = models.IntegerField('WooCommerce ID', default=0)
#
#     code = models.CharField("Gutscheincode", max_length=25)
#     amount = models.FloatField("Menge (Preis oder Anzahl Prozent)")
#     typ = models.CharField("Gutscheintyp", max_length=14, choices=GUTSCHEINTYPEN)
#     description = models.TextField("Beschrieb",default="",blank=True)
#     #datum_bis = models.DateField("Gültig bis", blank=True, null=True)
#     #nicht_kumulierbar = models.BooleanField("Nicht kumulierbar", default=True, help_text="Aktivieren, damit der Gutschein nicht kumuliert werden kann.")
#
#     produkte = models.ManyToManyField("Produkt", verbose_name="Produkte", help_text="Produkte, auf welche der Gutschein angewendet werden kann.")
#     ausgeschlossene_produkte = models.ManyToManyField("Produkt", verbose_name="Ausgeschlossenes Produkt", verbose_name_plural="Ausgeschlossene Produkte",help_text="Produkte, auf welche der Gutschein nicht angewendet werden kann.")
#
#     #limit_gesamt = models.IntegerField("Gesamtlimit", default=0, help_text="Anzahl Benutzungen")
#     #limit_pro_kunde = models.IntegerField("Limit pro Kunde", default=0, help_text="Anzahl Benutzungen pro Kunde")
#     limit_artikel = models.IntegerField("Limit an Artikeln", default=0, help_text="Anzahl Artikel, auf welche der Gutschein maximal angewendet werden kann.")
#
#     #kostenlose_lieferung = models.BooleanField("Kostenlose Lieferung", default=False, help_text="Wenn aktiviert, erlaube kostenlose Lieferung")
#
#     produktkategorien = models.ManyToManyField("Produktkategorie", verbose_name="Kategorie", verbose_name="Kategorien",help_text="Kategorien, auf welche der Gutschein angewendet werden kann.")
#     ausgeschlossene_produktkategorien = models.ManyToManyField("Kategorie", verbose_name="Ausgeschlossene Kategorie", verbose_name_plural="Ausgeschlossene Kategorie",help_text="Kategorien, auf welche der Gutschein nicht angewendet werden kann.")
#
#     nicht_kumulierbar_mit_aktion = models.BooleanField("Nicht kumulierbar mit Aktion", default=True, help_text="Aktivieren, damit der Gutschein nicht auf Produkte angewendet werden kann, welche in Aktion sind.")
#     mindestbetrag = models.FloatField("Mindestbetrag", default=0.0)
#     maximalbetrag = models.FloatField("Maximalbetrag", default=0.0)
#
#     #erlaubte_emails
#     #benutzt_von = models.ManyToManyField("Kunde")
#
#     def gueltig_fuer_bestellung(self, bestellung):
#         if ((self.mindestbetrag <= bestellung.calc_total()) and (self.maximalbetrag == 0.0 or (self.maximalbetrag >= bestellung.calc_total()))):
#             return True
#         else:
#             return False
#
#     def wert_fuer_bestellung(self, bestellung):
#         if self.gueltig_fuer_bestellung(bestellung):
#             if self.typ == "fixed_cart":
#                 return self.amount
#             elif self.typ == "fixed_product":
#                 pass
#             elif self.typ == "percent":
#                 pass
#         else:
#             return 0.0
#
#     class Meta:
#         verbose_name = "Gutschein"
#         verbose_name_plural = "Gutscheine"
#
#     objects = models.Manager()



class Kosten(CustomModel):
    """Model representing additional costs"""

    name = models.CharField(
        verbose_name="Name",
        max_length=500,
        default="Zusätzliche Kosten",
        help_text=I18N_HELP_TEXT,
    )
    price = models.FloatField(
        verbose_name="Preis (exkl. MwSt)",
        default=0.0,
    )
    vat_rate = models.FloatField(
        verbose_name="MwSt-Satz",
        choices=constants.VAT_RATES,
        default=constants.VAT_RATE_DEFAULT,
    )

    @admin.display(description="Name", ordering="name")
    def clean_name(self):
        return langselect(self.name)

    @admin.display(description="Kosten")
    def __str__(self):
        return f'{ self.clean_name() } ({ self.price } CHF' + \
            (f' + {self.vat_rate}% MwSt' if self.vat_rate else '') + \
            f') ({self.pk})'

    class Meta:
        verbose_name = "Kosten"
        verbose_name_plural = "Kosten"

    objects = models.Manager()

    admin_icon = "fas fa-coins"


class Kunde(CustomModel):
    """Model representing a customer"""

    woocommerceid = models.IntegerField(
        verbose_name="WooCommerce ID",
        default=0,
    )

    email = models.EmailField(
        verbose_name="E-Mail Adresse",
        blank=True,
    )
    first_name = models.CharField(
        verbose_name="Vorname",
        max_length=250,
        default="",
        blank=True,
    )
    last_name = models.CharField(
        verbose_name="Nachname",
        max_length=250,
        default="",
        blank=True,
    )
    company = models.CharField(
        verbose_name="Firma",
        max_length=250,
        default="",
        blank=True,
    )
    username = models.CharField(
        verbose_name="Benutzername",
        max_length=50,
        default="",
        blank=True,
    )
    avatar_url = models.URLField(
        verbose_name="Avatar URL",
        blank=True,
        editable=False,
    )
    language = models.CharField(
        verbose_name="Sprache",
        default="de",
        choices=constants.LANGUAGES,
        max_length=2,
    )

    addr_billing_first_name = models.CharField(
        verbose_name="Vorname",
        max_length=250,
        default="",
        blank=True,
    )
    addr_billing_last_name = models.CharField(
        verbose_name="Nachname",
        max_length=250,
        default="",
        blank=True,
    )
    addr_billing_company = models.CharField(
        verbose_name="Firma",
        max_length=250,
        default="",
        blank=True,
    )
    addr_billing_address_1 = models.CharField(
        verbose_name="Adresszeile 1",
        max_length=250,
        default="",
        blank=True,
        help_text='Strasse und Hausnummer oder "Postfach"',
    )
    addr_billing_address_2 = models.CharField(
        verbose_name="Adresszeile 2",
        max_length=250,
        default="",
        blank=True,
        help_text="Wird in QR-Rechnung NICHT verwendet!",
    )
    addr_billing_city = models.CharField(
        verbose_name="Ort",
        max_length=250,
        default="",
        blank=True,
    )
    addr_billing_state = models.CharField(
        verbose_name="Kanton",
        max_length=50,
        default="",
        blank=True,
    )
    addr_billing_postcode = models.CharField(
        verbose_name="Postleitzahl",
        max_length=50,
        default="",
        blank=True,
    )
    addr_billing_country = models.CharField(
        verbose_name="Land",
        max_length=2,
        default="CH",
        choices=constants.COUNTRIES,
    )
    addr_billing_email = models.EmailField(
        verbose_name="E-Mail Adresse",
        blank=True,
    )
    addr_billing_phone = models.CharField(
        verbose_name="Telefon",
        max_length=50,
        default="",
        blank=True,
    )

    addr_shipping_first_name = models.CharField(
        verbose_name="Vorname",
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_last_name = models.CharField(
        verbose_name="Nachname",
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_company = models.CharField(
        verbose_name="Firma",
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_address_1 = models.CharField(
        verbose_name="Adresszeile 1",
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_address_2 = models.CharField(
        verbose_name="Adresszeile 2",
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_city = models.CharField(
        verbose_name="Ort",
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_state = models.CharField(
        verbose_name="Kanton",
        max_length=50,
        default="",
        blank=True,
    )
    addr_shipping_postcode = models.CharField(
        verbose_name="Postleitzahl",
        max_length=50,
        default="",
        blank=True,
    )
    addr_shipping_country = models.CharField(
        verbose_name="Land",
        max_length=2,
        default="CH",
        choices=constants.COUNTRIES,
    )
    addr_shipping_email = models.EmailField(
        verbose_name="E-Mail Adresse",
        blank=True,
    )
    addr_shipping_phone = models.CharField(
        verbose_name="Telefon",
        max_length=50,
        default="",
        blank=True,
    )

    combine_with = models.ForeignKey(
        to='self',
        verbose_name="Zusammenfügen mit",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Dies kann nicht widerrufen werden! Werte im aktuellen Kunden werden bevorzugt.",
    )
    website = models.URLField(
        verbose_name="Webseite",
        default="",
        blank=True,
    )
    note = models.TextField(
        verbose_name="Bemerkung",
        default="",
        blank=True,
    )

    email_registriert = models.ForeignKey(
        to='EMail',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    @admin.display(description="Avatar", ordering="avatar_url")
    def avatar(self):
        if self.avatar_url:
            return mark_safe('<img src="'+self.avatar_url+'" width="50px">')
        return ""

    @admin.display(description="Kunde")
    def __str__(self):
        s = f'{self.pkfill(8)} '
        if self.woocommerceid:
            s += f'(WC#{self.woocommerceid}) '
        if self.first_name:
            s += f'{self.first_name} '
        if self.last_name:
            s += f'{self.last_name} '
        if self.company:
            s += f'{self.company} '
        if self.addr_billing_postcode and self.addr_billing_city:
            s += f'({self.addr_billing_postcode} {self.addr_billing_city})'
        return s

    class Meta:
        verbose_name = "Kunde"
        verbose_name_plural = "Kunden"

    def save(self, *args, **kwargs):
        if self.combine_with:
            self.woocommerceid = self.woocommerceid or self.combine_with.woocommerceid

            self.email = self.email or self.combine_with.email
            self.first_name = self.first_name or self.combine_with.first_name
            self.last_name = self.last_name or self.combine_with.last_name
            self.company = self.company or self.combine_with.company
            self.username = self.username or self.combine_with.username
            self.avatar_url = self.avatar_url or self.combine_with.avatar_url
            self.language = self.language if self.language != "de" else self.combine_with.language

            self.addr_billing_first_name = self.addr_billing_first_name or self.combine_with.addr_billing_first_name
            self.addr_billing_last_name = self.addr_billing_last_name or self.combine_with.addr_billing_last_name
            self.addr_billing_company = self.addr_billing_company or self.combine_with.addr_billing_company
            self.addr_billing_address_1 = self.addr_billing_address_1 or self.combine_with.addr_billing_address_1
            self.addr_billing_address_2 = self.addr_billing_address_2 or self.combine_with.addr_billing_address_2
            self.addr_billing_city = self.addr_billing_city or self.combine_with.addr_billing_city
            self.addr_billing_state = self.addr_billing_state or self.combine_with.addr_billing_state
            self.addr_billing_postcode = self.addr_billing_postcode or self.combine_with.addr_billing_postcode
            self.addr_billing_country = self.addr_billing_country or self.combine_with.addr_billing_country
            self.addr_billing_email = self.addr_billing_email or self.combine_with.addr_billing_email
            self.addr_billing_phone = self.addr_billing_phone or self.combine_with.addr_billing_phone

            self.addr_shipping_first_name = self.addr_shipping_first_name or self.combine_with.addr_shipping_first_name
            self.addr_shipping_last_name = self.addr_shipping_last_name or self.combine_with.addr_shipping_last_name
            self.addr_shipping_company = self.addr_shipping_company or self.combine_with.addr_shipping_company
            self.addr_shipping_address_1 = self.addr_shipping_address_1 or self.combine_with.addr_shipping_address_1
            self.addr_shipping_address_2 = self.addr_shipping_address_2 or self.combine_with.addr_shipping_address_2
            self.addr_shipping_city = self.addr_shipping_city or self.combine_with.addr_shipping_city
            self.addr_shipping_state = self.addr_shipping_state or self.combine_with.addr_shipping_state
            self.addr_shipping_postcode = self.addr_shipping_postcode or self.combine_with.addr_shipping_postcode
            self.addr_shipping_country = self.addr_shipping_country or self.combine_with.addr_shipping_country
            self.addr_shipping_email = self.addr_shipping_email or self.combine_with.addr_shipping_email
            self.addr_shipping_phone = self.addr_shipping_phone or self.combine_with.addr_shipping_phone

            self.website = self.website or self.combine_with.website
            self.note = self.note+"\n"+self.combine_with.note

            for bestellung in self.combine_with.bestellungen.all():
                bestellung.kunde = self
                bestellung.save()

            if getattr(self.combine_with, 'notiz', False):
                notiz = self.combine_with.notiz
                notiz.kunde = None if getattr(self, 'notiz', False) else self
                notiz.save()

            self.combine_with.delete()
            self.combine_with = None
        super().save(*args, **kwargs)

    def create_email_registriert(self):
        context = {
            "kunde": {
                "id": self.pk,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "company": self.company,
                "email": self.email,
            }
        }

        self.email_registriert = EMail.objects.create(
            subject="Registrierung erfolgreich!",
            to=self.email,
            html_template="kunde_registriert.html",
            html_context=context,
            notes=f"Diese E-Mail wurde automatisch aus Kunde #{self.pk} generiert.",
        )

        self.save()
        return self.email_registriert

    @admin.display(description="🔗 Notiz")
    def html_app_notiz(self):
        if hasattr(self, "notiz"):
            link = reverse("admin:kmuhelper_app_todo_change",
                           kwargs={"object_id": self.notiz.pk})
            text = "Notiz ansehen"
        else:
            link = reverse("admin:kmuhelper_app_todo_add") + \
                '?from_kunde='+str(self.pk)
            text = "Notiz hinzufügen"
        return format_html('<a target="_blank" href="{}">{}</a>', link, text)

    @admin.display(description="🔗 Notiz")
    def html_notiz(self):
        if hasattr(self, "notiz"):
            link = reverse("admin:kmuhelper_notiz_change",
                           kwargs={"object_id": self.notiz.pk})
            text = "Notiz ansehen"
        else:
            link = reverse("admin:kmuhelper_notiz_add") + \
                '?from_kunde='+str(self.pk)
            text = "Notiz hinzufügen"
        return format_html('<a target="_blank" href="{}">{}</a>', link, text)

    objects = models.Manager()

    admin_icon = "fas fa-users"

    DICT_EXCLUDE_FIELDS = ['email_registriert', 'combine_with']


class Lieferant(CustomModel):
    """Model representing a supplier (used only for categorizing)"""

    abbreviation = models.CharField(
        verbose_name="Kürzel",
        max_length=5,
    )
    name = models.CharField(
        verbose_name="Name",
        max_length=50,
    )

    website = models.URLField(
        verbose_name="Webseite",
        blank=True,
    )
    phone = models.CharField(
        verbose_name="Telefon",
        max_length=50,
        default="",
        blank=True,
    )
    email = models.EmailField(
        verbose_name="E-Mail",
        null=True,
        blank=True,
    )

    adresse = models.TextField(
        verbose_name="Adresse",
        default="",
        blank=True,
    )
    notiz = models.TextField(
        verbose_name="Notiz",
        default="",
        blank=True,
    )

    ansprechpartner = models.CharField(
        verbose_name="Ansprechpartner",
        max_length=250,
        default="",
        blank=True,
    )
    ansprechpartnertel = models.CharField(
        verbose_name="Ansprechpartner Telefon",
        max_length=50,
        default="",
        blank=True,
    )
    ansprechpartnermail = models.EmailField(
        verbose_name="Ansprechpartner E-Mail",
        null=True,
        default="",
        blank=True,
    )

    @admin.display(description="Lieferant")
    def __str__(self):
        return f'{self.name} ({self.pk})'

    def zuordnen(self):
        products = Produkt.objects.filter(lieferant=None)
        for produkt in products:
            produkt.lieferant = self
            produkt.save()
        return products.count()

    class Meta:
        verbose_name = "Lieferant"
        verbose_name_plural = "Lieferanten"

    objects = models.Manager()

    admin_icon = "fas fa-truck"


class Lieferungsposten(CustomModel):
    """Model representing the connection between 'Lieferung' and 'Produkt'"""

    lieferung = models.ForeignKey(
        to="Lieferung",
        on_delete=models.CASCADE,
    )
    produkt = models.ForeignKey(
        to="Produkt",
        on_delete=models.PROTECT,
    )
    quantity = models.IntegerField(
        verbose_name="Menge",
        default=1,
    )

    @admin.display(description="Lieferungsposten")
    def __str__(self):
        return f'({self.lieferung.pk}) -> {self.quantity}x {self.produkt}'

    class Meta:
        verbose_name = "Lieferungsposten"
        verbose_name_plural = "Lieferungsposten"

    objects = models.Manager()


class Lieferung(CustomModel):
    """Model representing an *incoming* delivery"""

    name = models.CharField(
        verbose_name="Name",
        max_length=50,
        default=default_delivery_title,
    )
    date = models.DateField(
        verbose_name="Erfasst am",
        auto_now_add=True,
    )

    lieferant = models.ForeignKey(
        to="Lieferant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    products = models.ManyToManyField(
        to="Produkt",
        through="Lieferungsposten",
        through_fields=("lieferung", "produkt"),
    )

    is_added_to_stock = models.BooleanField(
        verbose_name="Eingelagert",
        default=False,
    )

    @admin.display(description="Anzahl Produklte")
    def total_quantity(self):
        return self.products.through.objects.filter(lieferung=self).aggregate(models.Sum('quantity'))["quantity__sum"]

    def einlagern(self):
        if not self.is_added_to_stock:
            for i in self.products.through.objects.filter(lieferung=self):
                i.produkt.lagerbestand += i.quantity
                i.produkt.save()
            self.is_added_to_stock = True
            self.save()
            return True
        return False

    @admin.display(description="🔗 Notiz")
    def html_app_notiz(self):
        if hasattr(self, "notiz"):
            link = reverse("admin:kmuhelper_app_todo_change",
                           kwargs={"object_id": self.notiz.pk})
            text = "Notiz ansehen"
        else:
            link = reverse("admin:kmuhelper_app_todo_add") + \
                '?from_lieferung='+str(self.pk)
            text = "Notiz hinzufügen"
        return format_html('<a target="_blank" href="{}">{}</a>', link, text)

    @admin.display(description="🔗 Notiz")
    def html_notiz(self):
        if hasattr(self, "notiz"):
            link = reverse("admin:kmuhelper_notiz_change",
                           kwargs={"object_id": self.notiz.pk})
            text = "Notiz ansehen"
        else:
            link = reverse("admin:kmuhelper_notiz_add") + \
                '?from_lieferung='+str(self.pk)
            text = "Notiz hinzufügen"
        return format_html('<a target="_blank" href="{}">{}</a>', link, text)

    @admin.display(description="Lieferung")
    def __str__(self):
        return f'{self.name} ({self.pk})'

    class Meta:
        verbose_name = "Lieferung"
        verbose_name_plural = "Lieferungen"

    objects = models.Manager()

    admin_icon = "fas fa-truck-ramp-box"


class Notiz(CustomModel):
    """Model representing a note"""

    name = models.CharField(
        verbose_name="Name",
        max_length=50,
    )
    description = models.TextField(
        verbose_name="Beschrieb",
        default="",
        blank=True,
    )

    erledigt = models.BooleanField(
        verbose_name="Erledigt",
        default=False,
    )

    priority = models.IntegerField(
        verbose_name="Priorität",
        default=0,
        blank=True,
    )
    erstellt_am = models.DateTimeField(
        verbose_name="Erstellt am",
        auto_now_add=True,
    )

    bestellung = models.OneToOneField(
        to="Bestellung",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="notiz",
    )
    produkt = models.OneToOneField(
        to="Produkt",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="notiz",
    )
    kunde = models.OneToOneField(
        to="Kunde",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="notiz",
    )
    lieferung = models.OneToOneField(
        to="Lieferung",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="notiz",
    )

    @admin.display(description="🔗 Notiz")
    def __str__(self):
        return f'{self.name} ({self.pk})'

    def links(self):
        text = ""
        if self.bestellung:
            url = reverse("admin:kmuhelper_bestellung_change",
                          kwargs={"object_id": self.bestellung.pk})
            text += f"Bestellung <a href='{url}'>#{self.bestellung.pk}</a><br>"
        if self.produkt:
            url = reverse("admin:kmuhelper_produkt_change",
                          kwargs={"object_id": self.produkt.pk})
            text += f"Produkt <a href='{url}'>#{self.produkt.pk}</a><br>"
        if self.kunde:
            url = reverse("admin:kmuhelper_kunde_change",
                          kwargs={"object_id": self.kunde.pk})
            text += f"Kunde <a href='{url}'>#{self.kunde.pk}</a><br>"
        if self.lieferung:
            url = reverse("admin:kmuhelper_lieferung_change",
                          kwargs={"object_id": self.lieferung.pk})
            text += f"Lieferung <a href='{url}'>#{self.lieferung.pk}</a><br>"
        return mark_safe(text) or "Diese Notiz hat keine Verknüpfungen."

    class Meta:
        verbose_name = "Notiz"
        verbose_name_plural = "Notizen"

    objects = models.Manager()

    admin_icon = "fas fa-note-sticky"


class Produkt(CustomModel):
    """Model representing a product"""

    article_number = models.CharField(
        verbose_name="Artikelnummer",
        max_length=25,
    )

    woocommerceid = models.IntegerField(
        verbose_name='WooCommerce ID',
        default=0,
    )

    name = models.CharField(
        verbose_name='Name',
        max_length=500,
        help_text=I18N_HELP_TEXT,
    )
    short_description = models.TextField(
        verbose_name='Kurzbeschrieb',
        default="",
        blank=True,
        help_text=I18N_HELP_TEXT,
    )
    description = models.TextField(
        verbose_name='Beschrieb',
        default="",
        blank=True,
        help_text=I18N_HELP_TEXT,
    )

    quantity_description = models.CharField(
        verbose_name='Mengenbezeichnung',
        max_length=100,
        default="Stück",
        blank=True,
        help_text=I18N_HELP_TEXT,
    )
    selling_price = models.FloatField(
        verbose_name='Normalpreis in CHF (exkl. MwSt)',
        default=0,
    )
    vat_rate = models.FloatField(
        verbose_name='Mehrwertsteuersatz',
        choices=constants.VAT_RATES,
        default=constants.VAT_RATE_DEFAULT,
    )

    lagerbestand = models.IntegerField(
        verbose_name="Lagerbestand",
        default=0,
    )
    soll_lagerbestand = models.IntegerField(
        verbose_name="Soll-Lagerbestand",
        default=1,
    )

    note = models.TextField(
        verbose_name='Bemerkung',
        default="",
        blank=True,
        help_text="Wird nicht gedruckt oder angezeigt; nur für eigene Zwecke.",
    )

    sale_from = models.DateTimeField(
        verbose_name="In Aktion von",
        blank=True,
        null=True,
    )
    sale_to = models.DateTimeField(
        verbose_name="In Aktion bis",
        blank=True,
        null=True,
    )
    sale_price = models.FloatField(
        verbose_name="Aktionspreis in CHF (exkl. MwSt)",
        blank=True,
        null=True,
    )

    datasheet_url = models.CharField(
        verbose_name='Datenblattlink',
        max_length=500,
        default="",
        blank=True,
    )
    image_url = models.URLField(
        verbose_name='Bildlink',
        default="",
        blank=True,
    )

    lieferant = models.ForeignKey(
        to="Lieferant",
        verbose_name="Lieferant",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    lieferant_preis = models.CharField(
        verbose_name="Lieferantenpreis",
        default="",
        blank=True,
        max_length=20,
    )
    lieferant_article_number = models.CharField(
        verbose_name="Lieferantenartikelnummer",
        default="",
        blank=True,
        max_length=25,
    )
    lieferant_url = models.URLField(
        verbose_name="Lieferantenurl (Für Nachbestellungen)",
        default="",
        blank=True,
    )

    categories = models.ManyToManyField(
        to="Produktkategorie",
        through="ProduktProduktkategorieVerbindung",
        through_fields=("produkt", "kategorie"),
        verbose_name="Kategorie",
        related_name="products",
    )

    @admin.display(description="Name", ordering="name")
    def clean_name(self, lang="de"):
        return langselect(self.name, lang)

    @admin.display(description="Kurzbeschrieb", ordering="short_description")
    def clean_short_description(self, lang="de"):
        return langselect(self.short_description, lang)

    @admin.display(description="Beschrieb", ordering="description")
    def clean_description(self, lang="de"):
        return langselect(self.description, lang)

    @admin.display(description="In Aktion", boolean=True)
    def is_on_sale(self, zeitpunkt: datetime = None):
        zp = zeitpunkt or timezone.now()
        if self.sale_from and self.sale_to and self.sale_price:
            return bool((self.sale_from < zp) and (zp < self.sale_to))
        return False

    @admin.display(description="Aktueller Preis in CHF (exkl. MwSt)")
    def get_current_price(self, zeitpunkt: datetime = None):
        zp = zeitpunkt or timezone.now()
        return self.sale_price if self.is_on_sale(zp) else self.selling_price

    @admin.display(description="Bild", ordering="image_url")
    def html_image(self):
        if self.image_url:
            return format_html('<img src="{}" width="100px">', self.image_url)
        return ""

    def get_reserved_stock(self):
        n = 0
        for bp in Bestellungsposten.objects.filter(bestellung__is_shipped=False, produkt__id=self.id):
            n += bp.quantity
        return n

    def get_incoming_stock(self):
        n = 0
        for lp in Lieferungsposten.objects.filter(lieferung__is_added_to_stock=False, produkt__id=self.id):
            n += lp.quantity
        return n

    def get_stock_data(self, includemessage=False):
        """Get the stock and product information as a dictionary"""

        p_id = self.id
        p_name = self.clean_name()
        p_article_number = self.article_number

        n_current = self.lagerbestand
        n_going = self.get_reserved_stock()
        n_coming = self.get_incoming_stock()
        n_min = self.soll_lagerbestand

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
            "stock_overbooked": n_current-n_going < 0,
            "stock_in_danger": n_current-n_going < n_min,
        }

        if includemessage:
            stockstring = f"Aktuell: { n_current } | Ausgehend: { n_going }" + (
                f" | Eingehend: { n_coming }" if n_coming else "")
            adminurl = reverse(
                f'admin:kmuhelper_produkt_change', args=[self.pk])
            adminlink = format_html('<a href="{}">{}</a>', adminurl, p_name)

            formatdata = (adminlink, p_article_number, stockstring)

            if data["stock_overbooked"]:
                data["message"] = format_html(
                    'Zu wenig Lagerbestand bei "{}" [{}]: {}', *formatdata)
            elif data["stock_in_danger"]:
                data["message"] = format_html(
                    'Knapper Lagerbestand bei "{}" [{}]: {}', *formatdata)

        return data

    def show_stock_warning(self, request):
        data = self.get_stock_data(includemessage=True)

        if data["stock_overbooked"]:
            messages.error(request, data["message"])
        elif data["stock_in_danger"]:
            messages.warning(request, data["message"])

    @admin.display(description="🔗 Notiz")
    def html_app_notiz(self):
        if hasattr(self, "notiz"):
            link = reverse("admin:kmuhelper_app_todo_change",
                           kwargs={"object_id": self.notiz.pk})
            text = "Notiz ansehen"
        else:
            link = reverse("admin:kmuhelper_app_todo_add") + \
                '?from_produkt='+str(self.pk)
            text = "Notiz hinzufügen"
        return format_html('<a target="_blank" href="{}">{}</a>', link, text)

    @admin.display(description="🔗 Notiz")
    def html_notiz(self):
        if hasattr(self, "notiz"):
            link = reverse("admin:kmuhelper_notiz_change",
                           kwargs={"object_id": self.notiz.pk})
            text = "Notiz ansehen"
        else:
            link = reverse("admin:kmuhelper_notiz_add") + \
                '?from_produkt='+str(self.pk)
            text = "Notiz hinzufügen"
        return format_html('<a target="_blank" href="{}">{}</a>', link, text)

    @admin.display(description="Produkt")
    def __str__(self):
        return f'{self.article_number} - {self.clean_name()} ({self.pk})'

    class Meta:
        verbose_name = "Produkt"
        verbose_name_plural = "Produkte"

    objects = models.Manager()

    admin_icon = "fas fa-cubes"


class Produktkategorie(CustomModel):
    """Model representing a category for products"""

    woocommerceid = models.IntegerField(
        verbose_name="WooCommerce ID",
        default=0,
    )

    name = models.CharField(
        verbose_name="Name",
        max_length=250,
        default="",
    )
    description = models.TextField(
        verbose_name="Beschrieb",
        default="",
        blank=True,
    )
    image_url = models.URLField(
        verbose_name="Bildlink",
        blank=True,
    )

    parent_category = models.ForeignKey(
        to='self',
        verbose_name="Übergeordnete Kategorie",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    @admin.display(description="Bild", ordering="image_url")
    def html_image(self):
        if self.image_url:
            return format_html('<img src="{}" width="100px">', self.image_url)
        return ""

    @admin.display(description="Anzahl Produkte")
    def total_quantity(self):
        return self.products.count()

    @admin.display(description="Name", ordering="name")
    def clean_name(self):
        return langselect(self.name)

    @admin.display(description="Beschrieb", ordering="description")
    def clean_description(self):
        return langselect(self.description)

    @admin.display(description="Kategorie")
    def __str__(self):
        return f'{self.clean_name()} ({self.pk})'

    class Meta:
        verbose_name = "Produktkategorie"
        verbose_name_plural = "Produktkategorien"

    objects = models.Manager()

    admin_icon = "fas fa-folder-tree"

class ProduktProduktkategorieVerbindung(CustomModel):
    """Model representing the connection between 'Produkt' and 'Produktkategorie'"""

    produkt = models.ForeignKey("Produkt", on_delete=models.CASCADE)
    kategorie = models.ForeignKey("Produktkategorie", on_delete=models.CASCADE)

    @admin.display(description="Produktkategorie")
    def __str__(self):
        return f'({self.kategorie.pk}) {self.kategorie.clean_name()} <-> {self.produkt}'

    class Meta:
        verbose_name = "Produkt-Kategorie-Verknüpfung"
        verbose_name_plural = "Produkt-Kategorie-Verknüpfungen"

    objects = models.Manager()


class Zahlungsempfaenger(CustomModel):
    """Model representing a payment receiver for the qr bill"""

    mode = models.CharField(
        verbose_name="Modus",
        max_length=15,
        choices=[
            ('QRR', "QR-Referenz"),
            ('NON', "Ohne Referenz"),
        ],
        default='QRR'
    )

    qriban = models.CharField(
        verbose_name="QR-IBAN",
        max_length=21+5,
        validators=[
            RegexValidator(
                r'^(CH|LI)[0-9]{2}\s3[0-9]{3}\s[0-9]{4}\s[0-9]{4}\s[0-9]{4}\s[0-9]{1}$',
                'Bite benutze folgendes Format: (CH|LI)pp 3xxx xxxx xxxx xxxx x',
            ),
        ],
        help_text="QR-IBAN mit Leerzeichen (Nur verwendet im Modus 'QR-Referenz')",
        blank=True,
        default="",
    )
    iban = models.CharField(
        verbose_name="IBAN",
        max_length=21+5,
        validators=[
            RegexValidator(
                r'^(CH|LI)[0-9]{2}\s[0-9]{4}\s[0-9]{4}\s[0-9]{4}\s[0-9]{4}\s[0-9]{1}$',
                'Bite benutze folgendes Format: (CH|LI)pp 3xxx xxxx xxxx xxxx x',
            ),
        ],
        help_text="IBAN mit Leerzeichen (Nur verwendet im Modus 'Ohne Referenz')",
        blank=True,
        default="",
    )

    logourl = models.URLField(
        verbose_name="Logo (URL)",
        validators=[
            RegexValidator(
                r'''^[0-9a-zA-Z\-\.\|\?\(\)\*\+&"'_:;/]+\.(png|jpg)$''',
                '''Nur folgende Zeichen gestattet: 0-9a-zA-Z-_.:;/|?&()"'*+ - ''' +
                '''Muss auf .jpg/.png enden.''',
            ),
        ],
        help_text="URL eines Bildes (.jpg/.png) - Wird auf die Rechnung gedruckt.",
        blank=True,
        default="",
    )
    name = models.CharField(
        verbose_name="Firmennname",
        max_length=70,
        help_text="Name der Firma oder des Empfängers",
    )
    swiss_uid = models.CharField(
        verbose_name="Firmen-UID",
        max_length=15,
        validators=[
            RegexValidator(
                r'^CHE-[0-9]{3}\.[0-9]{3}\.[0-9]{3}$',
                'Bite benutze folgendes Format: CHE-123.456.789'
            )
        ],
        help_text="UID der Firma - Format: CHE-123.456.789 (Mehrwertsteuernummer)",
        blank=True,
        default="",
    )
    address_1 = models.CharField(
        verbose_name="Strasse und Hausnummer oder 'Postfach'",
        max_length=70,
    )
    address_2 = models.CharField(
        verbose_name="PLZ und Ort",
        max_length=70,
    )
    country = models.CharField(
        verbose_name="Land",
        max_length=2,
        choices=constants.COUNTRIES,
        default="CH",
    )
    email = models.EmailField(
        verbose_name="E-Mail",
        default="",
        blank=True,
        help_text="Nicht auf der Rechnung ersichtlich",
    )
    phone = models.CharField(
        verbose_name="Telefon",
        max_length=70,
        default="",
        blank=True,
        help_text="Nicht auf der Rechnung ersichtlich",
    )
    website = models.URLField(
        verbose_name="Webseite",
        default="",
        blank=True,
        help_text="Auf der Rechnung ersichtlich, sofern vorhanden!",
    )

    @classmethod
    def _check_iban(cls, iban: str):
        try:
            b = ''
            for i in (0, 1):
                a = str(iban)[i].upper()
                if a not in string.ascii_uppercase:
                    return False
                b += str(ord(a)-55)
            Nr = ''.join([z for z in str(iban)
                          [2:] if z in string.digits])
            return int(int(Nr[2:] + b + Nr[:2]) % 97) == 1
        except IndexError:
            return False

    def has_valid_qr_iban(self):
        return self._check_iban(self.qriban)

    def has_valid_iban(self):
        return self._check_iban(self.iban)

    def has_valid_uid(self):
        try:
            u = self.swiss_uid.split("-")[1].replace(".", "")
            p = 11 - (((int(u[0])*5)+(int(u[1])*4)+(int(u[2])*3)+(int(u[3])*2) +
                       (int(u[4])*7)+(int(u[5])*6)+(int(u[6])*5)+(int(u[7])*4)) % 11)
            return int(u[8]) == p
        except Exception as e:
            log("Error while validating UID:", e)
            return False

    @admin.display(description="Zahlungsempfänger")
    def __str__(self):
        return f'{self.name} ({self.pk})'

    class Meta:
        verbose_name = "Zahlungsempfänger"
        verbose_name_plural = "Zahlungsempfänger"

    objects = models.Manager()

    admin_icon = "fas fa-hand-holding-dollar"
