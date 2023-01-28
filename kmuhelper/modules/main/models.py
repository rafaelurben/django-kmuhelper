from datetime import datetime
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
from kmuhelper.overrides import CustomModel
from kmuhelper.pdf_generators import PDFOrder
from kmuhelper.utils import runden, clean, formatprice, modulo10rekursiv, send_pdf


def log(string, *args):
    print("[deep_pink4][KMUHelper Main][/] -", string, *args)

###################


def defaultlieferungsname():
    return "Lieferung vom "+str(datetime.now().strftime("%d.%m.%Y"))


def defaultzahlungsempfaenger():
    if Zahlungsempfaenger.objects.exists():
        return Zahlungsempfaenger.objects.first().pk
    return None


def defaultansprechpartner():
    if Ansprechpartner.objects.exists():
        return Ansprechpartner.objects.first().pk
    return None


def defaultorderkey():
    return "kh-"+str(randint(10000000, 99999999))


def defaultzahlungskonditionen():
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
    telefon = models.CharField(
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
    bemerkung = models.CharField(
        verbose_name="Bemerkung",
        default="",
        max_length=250,
        blank=True,
        help_text="Wird auf die Rechnung gedruckt.",
    )

    rabatt = models.FloatField(
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
    )
    preis = models.FloatField(
        verbose_name="Preis (exkl. MwSt)",
        default=0.0,
    )
    mwstsatz = models.FloatField(
        verbose_name="MwSt-Satz",
        choices=constants.MWSTSETS,
        default=constants.MWST_DEFAULT,
    )

    # Calculated data
    @admin.display(description="Zwischensumme (exkl. MwSt)")
    def zwischensumme(self):
        return runden(self.preis*((100-self.rabatt)/100))

    def zwischensumme_ohne_rabatt(self):
        return runden(self.preis)

    def nur_rabatt(self):
        return runden(self.preis*(self.rabatt/100))*-1

    # Display methods
    @admin.display(description="Name", ordering="name")
    def clean_name(self):
        return clean(self.name)

    @admin.display(description="Bestellungskosten")
    def __str__(self):
        return f'({self.pk}) -> {self.name}'

    def save(self, *args, **kwargs):
        if self.pk is None and self.kosten is not None:
            self.name = self.kosten.name
            self.preis = self.kosten.preis
            self.mwstsatz = self.kosten.mwstsatz
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
    bemerkung = models.CharField(
        verbose_name="Bemerkung",
        default="",
        max_length=250,
        blank=True,
        help_text="Wird auf die Rechnung gedruckt.",
    )

    menge = models.IntegerField(
        verbose_name="Menge",
        default=1,
    )
    rabatt = models.IntegerField(
        verbose_name="Rabatt in %",
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    produktpreis = models.FloatField(
        verbose_name="Produktpreis (exkl. MwSt)",
        default=0.0,
    )

    @admin.display(description="Zwischensumme (exkl. MwSt)")
    def zwischensumme(self):
        return runden(self.produktpreis*self.menge*((100-self.rabatt)/100))

    def zwischensumme_ohne_rabatt(self):
        return runden(self.produktpreis*self.menge)

    def nur_rabatt(self):
        return runden(self.produktpreis*self.menge*(self.rabatt/100))*-1

    @admin.display(description="MwSt-Satz")
    def mwstsatz(self):
        return formatprice(self.produkt.mwstsatz)

    @admin.display(description="Bestellungsposten")
    def __str__(self):
        return f'({self.bestellung.pk}) -> {self.menge}x {self.produkt}'

    def save(self, *args, **kwargs):
        if not self.produktpreis:
            self.produktpreis = runden(self.produkt.preis())
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

    datum = models.DateTimeField(
        verbose_name="Datum",
        default=timezone.now,
    )

    rechnungsdatum = models.DateField(
        verbose_name="Rechnungsdatum",
        default=None,
        blank=True,
        null=True,
        help_text="Datum der Rechnung. Wird auch als Startpunkt für die Zahlungskonditionen verwendet.",
    )
    rechnungstitel = models.CharField(
        verbose_name="Rechnungstitel",
        default="",
        blank=True,
        max_length=32,
        help_text="Titel der Rechnung. Leer lassen für 'RECHNUNG'",
    )
    rechnungstext = models.TextField(
        verbose_name="Rechnungstext",
        default="",
        blank=True,
        help_text=mark_safe(
            "Wird auf der Rechnung gedruckt! Unterstützt " +
            "<abbr title='<b>Fett</b><u>Unterstrichen</u><i>Kursiv</i>'>XML markup</abbr>."
        ),
    )
    zahlungskonditionen = models.CharField(
        verbose_name="Zahlungskonditionen",
        default=defaultzahlungskonditionen,
        validators=[
            RegexValidator(
                "^([0-9]+(\.[0-9]+)?:[0-9]+;)*0:[0-9]+$",
                "Bitte benutze folgendes Format: 'p:d;p:d' - p = Skonto in %; d = Tage",
            )
        ],
        max_length=16,
        help_text="Skonto und Zahlungsfrist nach Syntaxdefinition von Swico.\n\n" +
                  "Beispiel: '2:15;0:30' steht für 2% Skonto bei Zahlung innerhalb " +
                  "von 15 Tagen und eine Zahlungsfrist von 30 Tagen.\n\n" +
                  "Eine Zahlungsfrist MUSS vorhanden sein und am Schluss aufgeführt werden.",
    )

    status = models.CharField(
        verbose_name="Status",
        max_length=11,
        default='processing',
        choices=constants.ORDERSTATUS,
    )
    versendet = models.BooleanField(
        verbose_name="Versendet",
        default=False,
        help_text="Sobald eine Bestellung als versendet markiert wurde, können Teile " +
                  "der Bestellung nicht mehr bearbeitet werden! " +
                  "Ausserdem werden die Produkte aus dem Lagerbestand entfernt.",
    )
    trackingnummer = models.CharField(
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

    ausgelagert = models.BooleanField(
        verbose_name="Ausgelagert",
        default=False,
    )

    zahlungsmethode = models.CharField(
        verbose_name="Zahlungsmethode",
        max_length=7,
        default="cod",
        choices=constants.PAYMENTMETHODS,
    )
    bezahlt = models.BooleanField(
        verbose_name="Bezahlt",
        default=False,
        help_text="Sobald eine Bestellung als bezahlt markiert wurde, können Teile " +
                  "der Bestellung nicht mehr bearbeitet werden!",
    )

    kundennotiz = models.TextField(
        verbose_name="Kundennotiz",
        default="",
        blank=True,
        help_text="Vom Kunden erfasste Notiz.",
    )

    order_key = models.CharField(
        verbose_name="Bestellungs-Schlüssel",
        max_length=50,
        blank=True,
        default=defaultorderkey,
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
        default=defaultzahlungsempfaenger,
    )
    ansprechpartner = models.ForeignKey(
        to='Ansprechpartner',
        verbose_name="Ansprechpartner",
        on_delete=models.PROTECT,
        default=defaultansprechpartner,
    )

    rechnungsadresse_vorname = models.CharField(
        verbose_name="Vorname",
        max_length=250,
        default="",
        blank=True,
    )
    rechnungsadresse_nachname = models.CharField(
        verbose_name="Nachname",
        max_length=250,
        default="",
        blank=True,
    )
    rechnungsadresse_firma = models.CharField(
        verbose_name="Firma",
        max_length=250,
        default="",
        blank=True,
    )
    rechnungsadresse_adresszeile1 = models.CharField(
        verbose_name="Adresszeile 1",
        max_length=250,
        default="",
        blank=True,
        help_text="Strasse und Hausnummer oder 'Postfach'",
    )
    rechnungsadresse_adresszeile2 = models.CharField(
        verbose_name="Adresszeile 2",
        max_length=250,
        default="",
        blank=True,
        help_text="Wird in QR-Rechnung NICHT verwendet!",
    )
    rechnungsadresse_ort = models.CharField(
        verbose_name="Ort",
        max_length=250,
        default="",
        blank=True,
    )
    rechnungsadresse_kanton = models.CharField(
        verbose_name="Kanton",
        max_length=50,
        default="",
        blank=True,
    )
    rechnungsadresse_plz = models.CharField(
        verbose_name="Postleitzahl",
        max_length=50,
        default="",
        blank=True,
    )
    rechnungsadresse_land = models.CharField(
        verbose_name="Land",
        max_length=2,
        default="CH",
        choices=constants.COUNTRIES,
    )
    rechnungsadresse_email = models.EmailField(
        verbose_name="E-Mail Adresse",
        blank=True,
    )
    rechnungsadresse_telefon = models.CharField(
        verbose_name="Telefon",
        max_length=50,
        default="",
        blank=True,
    )

    lieferadresse_vorname = models.CharField(
        verbose_name="Vorname",
        max_length=250,
        default="",
        blank=True,
    )
    lieferadresse_nachname = models.CharField(
        verbose_name="Nachname",
        max_length=250,
        default="",
        blank=True,
    )
    lieferadresse_firma = models.CharField(
        verbose_name="Firma",
        max_length=250,
        default="",
        blank=True,
    )
    lieferadresse_adresszeile1 = models.CharField(
        verbose_name="Adresszeile 1",
        max_length=250,
        default="",
        blank=True,
    )
    lieferadresse_adresszeile2 = models.CharField(
        verbose_name="Adresszeile 2",
        max_length=250,
        default="",
        blank=True,
    )
    lieferadresse_ort = models.CharField(
        verbose_name="Ort",
        max_length=250,
        default="",
        blank=True,
    )
    lieferadresse_kanton = models.CharField(
        verbose_name="Kanton",
        max_length=50,
        default="",
        blank=True,
    )
    lieferadresse_plz = models.CharField(
        verbose_name="Postleitzahl",
        max_length=50,
        default="",
        blank=True,
    )
    lieferadresse_land = models.CharField(
        verbose_name="Land",
        max_length=2,
        default="CH",
        choices=constants.COUNTRIES,
    )
    lieferadresse_email = models.EmailField(
        verbose_name="E-Mail Adresse",
        blank=True,
    )
    lieferadresse_telefon = models.CharField(
        verbose_name="Telefon",
        max_length=50,
        default="",
        blank=True,
    )

    produkte = models.ManyToManyField(
        to='Produkt',
        through='Bestellungsposten',
        through_fields=('bestellung', 'produkt'),
    )

    kosten = models.ManyToManyField(
        to='Kosten',
        through='Bestellungskosten',
        through_fields=('bestellung', 'kosten'),
    )

    email_rechnung = models.ForeignKey(
        to='EMail',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='+',
    )
    email_lieferung = models.ForeignKey(
        to='EMail',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='+',
    )

    fix_summe = models.FloatField(
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

        for field in constants.LIEFERADRESSE_FIELDS+constants.RECHNUNGSADRESSE_FIELDS:
            setattr(self, field, getattr(self.kunde, field))

    def second_save(self, *args, **kwargs):
        "This HAS to be called after all related models have been saved."

        self.fix_summe = self.summe_gesamt()
        if self.versendet and (not self.ausgelagert):
            for i in self.produkte.through.objects.filter(bestellung=self):
                i.produkt.lagerbestand -= i.menge
                i.produkt.save()
            self.ausgelagert = True

        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.pk and not self.woocommerceid and self.kunde:
            self.import_customer_data()

        if self.rechnungsdatum is None:
            self.rechnungsdatum = timezone.now()

        super().save(*args, **kwargs)

    @admin.display(description="Trackinglink", ordering="trackingnummer")
    def trackinglink(self):
        return f'https://www.post.ch/swisspost-tracking?formattedParcelCodes={self.trackingnummer}' if self.trackingnummer else None

    def unstrukturierte_mitteilung(self):
        if self.zahlungsempfaenger.mode == "QRR":
            return str(self.datum.strftime("%d.%m.%Y"))
        return "Referenznummer: "+str(self.id)

    def referenznummer(self):
        a = self.pkfill(22)+"0000"
        b = a+str(modulo10rekursiv(a))
        c = b[0:2]+" "+b[2:7]+" "+b[7:12]+" " + \
            b[12:17]+" "+b[17:22]+" "+b[22:27]
        return c

    def rechnungsinformationen(self):
        date = (self.rechnungsdatum or self.datum).strftime("%y%m%d")

        output = f'//S1/10/{self.pk}/11/{date}'

        if self.zahlungsempfaenger.firmenuid:
            uid = self.zahlungsempfaenger.firmenuid.split("-")[1].replace(".", "")
            output += f'/30/{uid}'
        kond = self.zahlungskonditionen
        mwstdict = self.mwstdict()
        mwststring = ";".join(
            f'{satz}:{mwstdict[satz]}' for satz in mwstdict)

        output += f'/31/{date}/32/{mwststring}/40/{kond}'
        return output

    def paymentconditionsdict(self):
        "Get the payment conditions as a dictionary"
        data = {}
        for pc in self.zahlungskonditionen.split(";"):
            percent, days = pc.split(":")
            percent, days = float(percent), int(days)
            data[percent] = {
                "days": days,
                "percent": percent,
                "price": runden(self.fix_summe*(1-(percent/100))),
            }
        return data

    def mwstdict(self):
        "Get the VAT as a dictionary"
        mwst = {}
        for p in self.produkte.through.objects.filter(bestellung=self):
            if str(p.produkt.mwstsatz) in mwst:
                mwst[str(p.produkt.mwstsatz)] += p.zwischensumme()
            else:
                mwst[str(p.produkt.mwstsatz)] = p.zwischensumme()
        for k in self.kosten.through.objects.filter(bestellung=self):
            if str(k.mwstsatz) in mwst:
                mwst[str(k.mwstsatz)] += k.zwischensumme()
            else:
                mwst[str(k.mwstsatz)] = k.zwischensumme()
        for s in mwst:
            mwst[s] = runden(mwst[s])
        return mwst

    @admin.display(description="Summe (exkl. MwSt) in CHF")
    def summe(self):
        summe = 0
        for i in self.produkte.through.objects.filter(bestellung=self):
            summe += i.zwischensumme()
        for i in self.kosten.through.objects.filter(bestellung=self):
            summe += i.zwischensumme()
        return runden(summe)

    @admin.display(description="Summe (nur MwSt) in CHF")
    def summe_mwst(self):
        summe_mwst = 0
        mwstdict = self.mwstdict()
        for mwstsatz in mwstdict:
            summe_mwst += runden(float(mwstdict[mwstsatz]
                                       * (float(mwstsatz)/100)))
        return runden(summe_mwst)

    @admin.display(description="Summe in CHF")
    def summe_gesamt(self):
        return runden(self.summe()+self.summe_mwst())

    @admin.display(description="Name")
    def name(self):
        return (f'{self.datum.year}-' if self.datum and not isinstance(self.datum, str) else '') + \
               (f'{self.pkfill(6)}'+(f' (WC#{self.woocommerceid})' if self.woocommerceid else '')) + \
               (f' - {self.kunde}' if self.kunde is not None else " Gast")

    @admin.display(description="Info")
    def info(self):
        return f'{self.datum.strftime("%d.%m.%Y")} - '+((self.kunde.firma if self.kunde.firma else (f'{self.kunde.vorname} {self.kunde.nachname}')) if self.kunde else "Gast")

    @admin.display(description="Bestellung")
    def __str__(self):
        return self.name()

    def get_pdf(self, lieferschein: bool = False, digital: bool = True):
        return PDFOrder(self, lieferschein=lieferschein, digital=digital).get_response(as_attachment=False, filename=('Lieferschein' if lieferschein else 'Rechnung')+' zu Bestellung '+str(self)+'.pdf')

    def create_email_rechnung(self):
        context = {
            "trackinglink": str(self.trackinglink()),
            "trackingdata": bool(self.trackingnummer and self.versendet),
            "id": str(self.id),
            "woocommerceid": str(self.woocommerceid),
            "woocommercedata": bool(self.woocommerceid),
        }

        self.email_rechnung = EMail.objects.create(
            subject=f"Ihre Rechnung Nr. { self.id }"+(
                f' (Online #{self.woocommerceid})' if self.woocommerceid else ''),
            to=self.rechnungsadresse_email,
            html_template="bestellung_rechnung.html",
            html_context=context,
            notes=f"Diese E-Mail wurde automatisch aus Bestellung #{self.pk} generiert.",
        )

        filename = f"Rechnung Nr. { self.id }"+(
            f' (Online #{self.woocommerceid})' if self.woocommerceid else '')+".pdf"

        self.email_rechnung.add_attachments(
            Attachment.objects.create_from_binary(
                filename=filename,
                content=PDFOrder(self, lieferschein=False,
                                 digital=True).get_pdf()
            )
        )

        self.save()
        return self.email_rechnung

    def create_email_lieferung(self):
        context = {
            "trackinglink": str(self.trackinglink()),
            "trackingdata": bool(self.trackinglink() and self.versendet),
            "id": str(self.id),
            "woocommerceid": str(self.woocommerceid),
            "woocommercedata": bool(self.woocommerceid),
        }

        self.email_lieferung = EMail.objects.create(
            subject=f"Ihre Lieferung Nr. { self.id }",
            to=self.lieferadresse_email,
            html_template="bestellung_lieferung.html",
            html_context=context,
            notes=f"Diese E-Mail wurde automatisch aus Bestellung #{self.pk} generiert.",
        )

        filename = f"Lieferschein Nr. { self.id }.pdf"

        self.email_lieferung.add_attachments(
            Attachment.objects.create_from_binary(
                filename=filename,
                content=PDFOrder(self, lieferschein=True,
                                 digital=True).get_pdf()
            )
        )

        self.save()
        return self.email_lieferung

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

        return [p.get_stock_data() for p in self.produkte.all()]

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

    def get_public_pdf_url(self):
        return reverse('kmuhelper:public-view-order', args=(self.pk, self.order_key,))

    class Meta:
        verbose_name = "Bestellung"
        verbose_name_plural = "Bestellungen"

    def duplicate(self):
        new = Bestellung.objects.create(
            kunde=self.kunde,
            zahlungsempfaenger=self.zahlungsempfaenger,
            ansprechpartner=self.ansprechpartner,

            rechnungstitel=self.rechnungstitel,
            rechnungstext=self.rechnungstext,
            zahlungskonditionen=self.zahlungskonditionen,

            kundennotiz=f"Kopie aus Bestellung #{self.pk}\n--------------------------------\n{self.kundennotiz}",
        )

        for field in constants.LIEFERADRESSE_FIELDS+constants.RECHNUNGSADRESSE_FIELDS:
            setattr(new, field, getattr(self, field))

        for bp in self.produkte.through.objects.filter(bestellung=self):
            bp.copyto(new)
        for bk in self.kosten.through.objects.filter(bestellung=self):
            bk.copyto(new)
        new.save()
        return new

    def zu_lieferung(self):
        new = Lieferung.objects.create(
            name=f"Rücksendung von Bestellung #{self.pk}"
        )
        for lp in self.produkte.through.objects.filter(bestellung=self):
            new.produkte.add(lp.produkt, through_defaults={"menge": lp.menge})
        new.save()
        return new

    objects = models.Manager()

    admin_icon = "fas fa-clipboard-list"

    DICT_EXCLUDE_FIELDS = ['produkte', 'kosten', 'email_rechnung', 'email_lieferung', 'kunde',
                           'ansprechpartner', 'zahlungsempfaenger', 'ausgelagert',
                           'versendet', 'bezahlt', 'zahlungsmethode', 'order_key']


# class Gutschein(CustomModel):
#     woocommerceid = models.IntegerField('WooCommerce ID', default=0)
#
#     code = models.CharField("Gutscheincode", max_length=25)
#     menge = models.FloatField("Menge (Preis oder Anzahl Prozent)")
#     typ = models.CharField("Gutscheintyp", max_length=14, choices=GUTSCHEINTYPEN)
#     beschrieb = models.TextField("Beschrieb",default="",blank=True)
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
#     produktkategorien = models.ManyToManyField("Kategorie", verbose_name="Kategorie", verbose_name="Kategorien",help_text="Kategorien, auf welche der Gutschein angewendet werden kann.")
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
#         if ((self.mindestbetrag <= bestellung.summe_gesamt()) and (self.maximalbetrag == 0.0 or (self.maximalbetrag >= bestellung.summe_gesamt()))):
#             return True
#         else:
#             return False
#
#     def wert_fuer_bestellung(self, bestellung):
#         if self.gueltig_fuer_bestellung(bestellung):
#             if self.typ == "fixed_cart":
#                 return self.menge
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


class Kategorie(CustomModel):
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
    beschrieb = models.TextField(
        verbose_name="Beschrieb",
        default="",
        blank=True,
    )
    bildlink = models.URLField(
        verbose_name="Bildlink",
        blank=True,
    )

    uebergeordnete_kategorie = models.ForeignKey(
        to='self',
        verbose_name="Übergeordnete Kategorie",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    @admin.display(description="Bild", ordering="bildlink")
    def bild(self):
        if self.bildlink:
            return format_html('<img src="{}" width="100px">', self.bildlink)
        return ""

    @admin.display(description="Anzahl Produkte")
    def anzahl_produkte(self):
        return self.produkte.count()

    @admin.display(description="Name", ordering="name")
    def clean_name(self):
        return clean(self.name)

    @admin.display(description="Beschrieb", ordering="beschrieb")
    def clean_beschrieb(self):
        return clean(self.beschrieb)

    @admin.display(description="Kategorie")
    def __str__(self):
        return f'{self.clean_name()} ({self.pk})'

    class Meta:
        verbose_name = "Kategorie"
        verbose_name_plural = "Kategorien"

    objects = models.Manager()

    admin_icon = "fas fa-folder-tree"


class Kosten(CustomModel):
    """Model representing additional costs"""

    name = models.CharField(
        verbose_name="Name",
        max_length=500,
        default="Zusätzliche Kosten",
    )
    preis = models.FloatField(
        verbose_name="Preis (exkl. MwSt)",
        default=0.0,
    )
    mwstsatz = models.FloatField(
        verbose_name="MwSt-Satz",
        choices=constants.MWSTSETS,
        default=constants.MWST_DEFAULT,
    )

    @admin.display(description="Name", ordering="name")
    def clean_name(self):
        return clean(self.name)

    @admin.display(description="Kosten")
    def __str__(self):
        return f'{ self.clean_name() } ({ self.preis } CHF' + \
            (f' + {self.mwstsatz}% MwSt' if self.mwstsatz else '') + \
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
    vorname = models.CharField(
        verbose_name="Vorname",
        max_length=250,
        default="",
        blank=True,
    )
    nachname = models.CharField(
        verbose_name="Nachname",
        max_length=250,
        default="",
        blank=True,
    )
    firma = models.CharField(
        verbose_name="Firma",
        max_length=250,
        default="",
        blank=True,
    )
    benutzername = models.CharField(
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
    sprache = models.CharField(
        verbose_name="Sprache",
        default="de",
        choices=constants.LANGUAGES,
        max_length=2,
    )

    rechnungsadresse_vorname = models.CharField(
        verbose_name="Vorname",
        max_length=250,
        default="",
        blank=True,
    )
    rechnungsadresse_nachname = models.CharField(
        verbose_name="Nachname",
        max_length=250,
        default="",
        blank=True,
    )
    rechnungsadresse_firma = models.CharField(
        verbose_name="Firma",
        max_length=250,
        default="",
        blank=True,
    )
    rechnungsadresse_adresszeile1 = models.CharField(
        verbose_name="Adresszeile 1",
        max_length=250,
        default="",
        blank=True,
        help_text='Strasse und Hausnummer oder "Postfach"',
    )
    rechnungsadresse_adresszeile2 = models.CharField(
        verbose_name="Adresszeile 2",
        max_length=250,
        default="",
        blank=True,
        help_text="Wird in QR-Rechnung NICHT verwendet!",
    )
    rechnungsadresse_ort = models.CharField(
        verbose_name="Ort",
        max_length=250,
        default="",
        blank=True,
    )
    rechnungsadresse_kanton = models.CharField(
        verbose_name="Kanton",
        max_length=50,
        default="",
        blank=True,
    )
    rechnungsadresse_plz = models.CharField(
        verbose_name="Postleitzahl",
        max_length=50,
        default="",
        blank=True,
    )
    rechnungsadresse_land = models.CharField(
        verbose_name="Land",
        max_length=2,
        default="CH",
        choices=constants.COUNTRIES,
    )
    rechnungsadresse_email = models.EmailField(
        verbose_name="E-Mail Adresse",
        blank=True,
    )
    rechnungsadresse_telefon = models.CharField(
        verbose_name="Telefon",
        max_length=50,
        default="",
        blank=True,
    )

    lieferadresse_vorname = models.CharField(
        verbose_name="Vorname",
        max_length=250,
        default="",
        blank=True,
    )
    lieferadresse_nachname = models.CharField(
        verbose_name="Nachname",
        max_length=250,
        default="",
        blank=True,
    )
    lieferadresse_firma = models.CharField(
        verbose_name="Firma",
        max_length=250,
        default="",
        blank=True,
    )
    lieferadresse_adresszeile1 = models.CharField(
        verbose_name="Adresszeile 1",
        max_length=250,
        default="",
        blank=True,
    )
    lieferadresse_adresszeile2 = models.CharField(
        verbose_name="Adresszeile 2",
        max_length=250,
        default="",
        blank=True,
    )
    lieferadresse_ort = models.CharField(
        verbose_name="Ort",
        max_length=250,
        default="",
        blank=True,
    )
    lieferadresse_kanton = models.CharField(
        verbose_name="Kanton",
        max_length=50,
        default="",
        blank=True,
    )
    lieferadresse_plz = models.CharField(
        verbose_name="Postleitzahl",
        max_length=50,
        default="",
        blank=True,
    )
    lieferadresse_land = models.CharField(
        verbose_name="Land",
        max_length=2,
        default="CH",
        choices=constants.COUNTRIES,
    )
    lieferadresse_email = models.EmailField(
        verbose_name="E-Mail Adresse",
        blank=True,
    )
    lieferadresse_telefon = models.CharField(
        verbose_name="Telefon",
        max_length=50,
        default="",
        blank=True,
    )

    zusammenfuegen = models.ForeignKey(
        to='self',
        verbose_name="Zusammenfügen mit",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Dies kann nicht widerrufen werden! Werte im aktuellen Kunden werden bevorzugt.",
    )
    webseite = models.URLField(
        verbose_name="Webseite",
        default="",
        blank=True,
    )
    bemerkung = models.TextField(
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
        if self.vorname:
            s += f'{self.vorname} '
        if self.nachname:
            s += f'{self.nachname} '
        if self.firma:
            s += f'{self.firma} '
        if self.rechnungsadresse_plz and self.rechnungsadresse_ort:
            s += f'({self.rechnungsadresse_plz} {self.rechnungsadresse_ort})'
        return s

    class Meta:
        verbose_name = "Kunde"
        verbose_name_plural = "Kunden"

    def save(self, *args, **kwargs):
        if self.zusammenfuegen:
            self.woocommerceid = self.woocommerceid or self.zusammenfuegen.woocommerceid

            self.email = self.email or self.zusammenfuegen.email
            self.vorname = self.vorname or self.zusammenfuegen.vorname
            self.nachname = self.nachname or self.zusammenfuegen.nachname
            self.firma = self.firma or self.zusammenfuegen.firma
            self.benutzername = self.benutzername or self.zusammenfuegen.benutzername
            self.avatar_url = self.avatar_url or self.zusammenfuegen.avatar_url
            self.sprache = self.sprache if self.sprache != "de" else self.zusammenfuegen.sprache

            self.rechnungsadresse_vorname = self.rechnungsadresse_vorname or self.zusammenfuegen.rechnungsadresse_vorname
            self.rechnungsadresse_nachname = self.rechnungsadresse_nachname or self.zusammenfuegen.rechnungsadresse_nachname
            self.rechnungsadresse_firma = self.rechnungsadresse_firma or self.zusammenfuegen.rechnungsadresse_firma
            self.rechnungsadresse_adresszeile1 = self.rechnungsadresse_adresszeile1 or self.zusammenfuegen.rechnungsadresse_adresszeile1
            self.rechnungsadresse_adresszeile2 = self.rechnungsadresse_adresszeile2 or self.zusammenfuegen.rechnungsadresse_adresszeile2
            self.rechnungsadresse_ort = self.rechnungsadresse_ort or self.zusammenfuegen.rechnungsadresse_ort
            self.rechnungsadresse_kanton = self.rechnungsadresse_kanton or self.zusammenfuegen.rechnungsadresse_kanton
            self.rechnungsadresse_plz = self.rechnungsadresse_plz or self.zusammenfuegen.rechnungsadresse_plz
            self.rechnungsadresse_land = self.rechnungsadresse_land or self.zusammenfuegen.rechnungsadresse_land
            self.rechnungsadresse_email = self.rechnungsadresse_email or self.zusammenfuegen.rechnungsadresse_email
            self.rechnungsadresse_telefon = self.rechnungsadresse_telefon or self.zusammenfuegen.rechnungsadresse_telefon

            self.lieferadresse_vorname = self.lieferadresse_vorname or self.zusammenfuegen.lieferadresse_vorname
            self.lieferadresse_nachname = self.lieferadresse_nachname or self.zusammenfuegen.lieferadresse_nachname
            self.lieferadresse_firma = self.lieferadresse_firma or self.zusammenfuegen.lieferadresse_firma
            self.lieferadresse_adresszeile1 = self.lieferadresse_adresszeile1 or self.zusammenfuegen.lieferadresse_adresszeile1
            self.lieferadresse_adresszeile2 = self.lieferadresse_adresszeile2 or self.zusammenfuegen.lieferadresse_adresszeile2
            self.lieferadresse_ort = self.lieferadresse_ort or self.zusammenfuegen.lieferadresse_ort
            self.lieferadresse_kanton = self.lieferadresse_kanton or self.zusammenfuegen.lieferadresse_kanton
            self.lieferadresse_plz = self.lieferadresse_plz or self.zusammenfuegen.lieferadresse_plz
            self.lieferadresse_land = self.lieferadresse_land or self.zusammenfuegen.lieferadresse_land
            self.lieferadresse_email = self.lieferadresse_email or self.zusammenfuegen.lieferadresse_email
            self.lieferadresse_telefon = self.lieferadresse_telefon or self.zusammenfuegen.lieferadresse_telefon

            self.webseite = self.webseite or self.zusammenfuegen.webseite
            self.bemerkung = self.bemerkung+"\n"+self.zusammenfuegen.bemerkung

            for bestellung in self.zusammenfuegen.bestellungen.all():
                bestellung.kunde = self
                bestellung.save()

            if getattr(self.zusammenfuegen, 'notiz', False):
                notiz = self.zusammenfuegen.notiz
                notiz.kunde = None if getattr(self, 'notiz', False) else self
                notiz.save()

            self.zusammenfuegen.delete()
            self.zusammenfuegen = None
        super().save(*args, **kwargs)

    def create_email_registriert(self):
        context = {
            "kunde": {
                "id": self.pk,
                "vorname": self.vorname,
                "nachname": self.nachname,
                "firma": self.firma,
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

    DICT_EXCLUDE_FIELDS = ['email_registriert', 'zusammenfuegen']


class Lieferant(CustomModel):
    """Model representing a supplier (used only for categorizing)"""

    kuerzel = models.CharField(
        verbose_name="Kürzel",
        max_length=5,
    )
    name = models.CharField(
        verbose_name="Name",
        max_length=50,
    )

    webseite = models.URLField(
        verbose_name="Webseite",
        blank=True,
    )
    telefon = models.CharField(
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
        produkte = Produkt.objects.filter(lieferant=None)
        for produkt in produkte:
            produkt.lieferant = self
            produkt.save()
        return produkte.count()

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
    menge = models.IntegerField(
        verbose_name="Menge",
        default=1,
    )

    @admin.display(description="Lieferungsposten")
    def __str__(self):
        return f'({self.lieferung.pk}) -> {self.menge}x {self.produkt}'

    class Meta:
        verbose_name = "Lieferungsposten"
        verbose_name_plural = "Lieferungsposten"

    objects = models.Manager()


class Lieferung(CustomModel):
    """Model representing an *incoming* delivery"""

    name = models.CharField(
        verbose_name="Name",
        max_length=50,
        default=defaultlieferungsname,
    )
    datum = models.DateField(
        verbose_name="Erfasst am",
        auto_now_add=True,
    )

    lieferant = models.ForeignKey(
        to="Lieferant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    produkte = models.ManyToManyField(
        to="Produkt",
        through="Lieferungsposten",
        through_fields=("lieferung", "produkt"),
    )

    eingelagert = models.BooleanField(
        verbose_name="Eingelagert",
        default=False,
    )

    @admin.display(description="Anzahl Produklte")
    def anzahlprodukte(self):
        return self.produkte.through.objects.filter(lieferung=self).aggregate(models.Sum('menge'))["menge__sum"]

    def einlagern(self):
        if not self.eingelagert:
            for i in self.produkte.through.objects.filter(lieferung=self):
                i.produkt.lagerbestand += i.menge
                i.produkt.save()
            self.eingelagert = True
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
    beschrieb = models.TextField(
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


class Produktkategorie(CustomModel):
    """Model representing the connection between 'Produkt' and 'Kategorie'"""

    produkt = models.ForeignKey("Produkt", on_delete=models.CASCADE)
    kategorie = models.ForeignKey("Kategorie", on_delete=models.CASCADE)

    @admin.display(description="Produktkategorie")
    def __str__(self):
        return f'({self.kategorie.pk}) {self.kategorie.clean_name()} <-> {self.produkt}'

    class Meta:
        verbose_name = "Produktkategorie"
        verbose_name_plural = "Produktkategorien"

    objects = models.Manager()


class Produkt(CustomModel):
    """Model representing a product"""

    artikelnummer = models.CharField(
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
    )
    kurzbeschrieb = models.TextField(
        verbose_name='Kurzbeschrieb',
        default="",
        blank=True,
    )
    beschrieb = models.TextField(
        verbose_name='Beschrieb',
        default="",
        blank=True,
    )

    mengenbezeichnung = models.CharField(
        verbose_name='Mengenbezeichnung',
        max_length=100,
        default="[:de]Stück[:fr]Pièce[:it]Pezzo[:en]Piece[:]",
        blank=True,
    )
    verkaufspreis = models.FloatField(
        verbose_name='Normalpreis in CHF (exkl. MwSt)',
        default=0,
    )
    mwstsatz = models.FloatField(
        verbose_name='Mehrwertsteuersatz',
        choices=constants.MWSTSETS,
        default=constants.MWST_DEFAULT,
    )

    lagerbestand = models.IntegerField(
        verbose_name="Lagerbestand",
        default=0,
    )
    soll_lagerbestand = models.IntegerField(
        verbose_name="Soll-Lagerbestand",
        default=1,
    )

    bemerkung = models.TextField(
        verbose_name='Bemerkung',
        default="",
        blank=True,
        help_text="Wird nicht gedruckt oder angezeigt; nur für eigene Zwecke.",
    )

    aktion_von = models.DateTimeField(
        verbose_name="In Aktion von",
        blank=True,
        null=True,
    )
    aktion_bis = models.DateTimeField(
        verbose_name="In Aktion bis",
        blank=True,
        null=True,
    )
    aktion_preis = models.FloatField(
        verbose_name="Aktionspreis in CHF (exkl. MwSt)",
        blank=True,
        null=True,
    )

    datenblattlink = models.CharField(
        verbose_name='Datenblattlink',
        max_length=500,
        default="",
        blank=True,
    )
    bildlink = models.URLField(
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
    lieferant_artikelnummer = models.CharField(
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

    kategorien = models.ManyToManyField(
        to="Kategorie",
        through="Produktkategorie",
        through_fields=("produkt", "kategorie"),
        verbose_name="Kategorie",
        related_name="produkte",
    )

    @admin.display(description="Name", ordering="name")
    def clean_name(self, lang="de"):
        return clean(self.name, lang)

    @admin.display(description="Kurzbeschrieb", ordering="kurzbeschrieb")
    def clean_kurzbeschrieb(self, lang="de"):
        return clean(self.kurzbeschrieb, lang)

    @admin.display(description="Beschrieb", ordering="beschrieb")
    def clean_beschrieb(self, lang="de"):
        return clean(self.beschrieb, lang)

    @admin.display(description="In Aktion", boolean=True)
    def in_aktion(self, zeitpunkt: datetime = None):
        zp = zeitpunkt or timezone.now()
        if self.aktion_von and self.aktion_bis and self.aktion_preis:
            return bool((self.aktion_von < zp) and (zp < self.aktion_bis))
        return False

    @admin.display(description="Aktueller Preis in CHF (exkl. MwSt)")
    def preis(self, zeitpunkt: datetime = None):
        zp = zeitpunkt or timezone.now()
        return self.aktion_preis if self.in_aktion(zp) else self.verkaufspreis

    @admin.display(description="Bild", ordering="bildlink")
    def bild(self):
        if self.bildlink:
            return format_html('<img src="{}" width="100px">', self.bildlink)
        return ""

    def get_reserved_stock(self):
        n = 0
        for bp in Bestellungsposten.objects.filter(bestellung__versendet=False, produkt__id=self.id):
            n += bp.menge
        return n

    def get_incoming_stock(self):
        n = 0
        for lp in Lieferungsposten.objects.filter(lieferung__eingelagert=False, produkt__id=self.id):
            n += lp.menge
        return n

    def get_stock_data(self, includemessage=False):
        """Get the stock and product information as a dictionary"""

        p_id = self.id
        p_name = self.clean_name()
        p_artikelnummer = self.artikelnummer

        n_current = self.lagerbestand
        n_going = self.get_reserved_stock()
        n_coming = self.get_incoming_stock()
        n_min = self.soll_lagerbestand

        data = {
            "product": {
                "id": p_id,
                "artikelnummer": p_artikelnummer,
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

            formatdata = (adminlink, p_artikelnummer, stockstring)

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

    def save(self, *args, **kwargs):
        if self.mengenbezeichnung == "Stück":
            self.mengenbezeichnung = "[:de]Stück[:fr]Pièce[:it]Pezzo[:en]Piece[:]"
        elif self.mengenbezeichnung == "Flasche":
            self.mengenbezeichnung = "[:de]Flasche[:fr]Bouteille[:it]Bottiglia[:en]Bottle[:]"
        elif self.mengenbezeichnung == "Tube":
            self.mengenbezeichnung = "[:de]Tube[:fr]Tube[:it]Tubetto[:en]Tube[:]"
        super().save(*args, **kwargs)

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
        return f'{self.artikelnummer} - {self.clean_name()} ({self.pk})'

    class Meta:
        verbose_name = "Produkt"
        verbose_name_plural = "Produkte"

    objects = models.Manager()

    admin_icon = "fas fa-cubes"


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
    firmenname = models.CharField(
        verbose_name="Firmennname",
        max_length=70,
        help_text="Name der Firma oder des Empfängers",
    )
    firmenuid = models.CharField(
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
    adresszeile1 = models.CharField(
        verbose_name="Strasse und Hausnummer oder 'Postfach'",
        max_length=70,
    )
    adresszeile2 = models.CharField(
        verbose_name="PLZ und Ort",
        max_length=70,
    )
    land = models.CharField(
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
    telefon = models.CharField(
        verbose_name="Telefon",
        max_length=70,
        default="",
        blank=True,
        help_text="Nicht auf der Rechnung ersichtlich",
    )
    webseite = models.URLField(
        verbose_name="Webseite",
        help_text="Auf der Rechnung ersichtlich!",
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
            u = self.firmenuid.split("-")[1].replace(".", "")
            p = 11 - (((int(u[0])*5)+(int(u[1])*4)+(int(u[2])*3)+(int(u[3])*2) +
                       (int(u[4])*7)+(int(u[5])*6)+(int(u[6])*5)+(int(u[7])*4)) % 11)
            return int(u[8]) == p
        except Exception as e:
            log("Error while validating UID:", e)
            return False

    @admin.display(description="Zahlungsempfänger")
    def __str__(self):
        return f'{self.firmenname} ({self.pk})'

    class Meta:
        verbose_name = "Zahlungsempfänger"
        verbose_name_plural = "Zahlungsempfänger"

    objects = models.Manager()

    admin_icon = "fas fa-hand-holding-dollar"
