# pylint: disable=no-member, unsubscriptable-object

from django.db import models
from django.core import mail
from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.http import FileResponse
from django.template.loader import get_template
from django.utils.html import mark_safe
from django.urls import reverse

from datetime import datetime
from random import randint
from pytz import utc
from django.utils import timezone

from kmuhelper.utils import send_mail, runden, clean, formatprice, modulo10rekursiv, send_pdf
from kmuhelper.pdf_generators.bestellung import pdf_bestellung

###################

from rich import print

prefix = "[deep_pink4][KMUHelper][/] -"


def log(string, *args):
    print(prefix, string, *args)

###################

def defaultlieferungsname():
    return "Lieferung vom "+str(datetime.now().strftime("%d.%m.%Y"))

def defaultbestellungsname():
    return "Bestellung vom "+str(datetime.now().strftime("%d.%m.%Y"))

def defaultzahlungsempfaenger():
    return Zahlungsempfaenger.objects.first().pk

def defaultansprechpartner():
    return Ansprechpartner.objects.first().pk

def defaultorderkey():
    return "kh-"+str(randint(10000000,99999999))


STATUS = [
    ("pending","Zahlung ausstehend"),
    ("processing","In Bearbeitung"),
    ("on-hold","In Wartestellung"),
    ("completed","Abgeschlossen"),
    ("cancelled","Storniert/Abgebrochen"),
    ("refunded","Rückerstattet"),
    ("failed","Fehlgeschlagen"),
    ("trash","Gelöscht")
]

MWSTSÄTZE = [
    (0.0, "0.0% (Mehrwertsteuerfrei)"),
    (7.7, "7.7% (Normalsatz)"),
    (3.7, "3.7% (Sondersatz für Beherbergungsdienstleistungen)"),
    (2.5, "2.5% (Reduzierter Satz)")
]

ZAHLUNGSMETHODEN = [
    ("bacs",    "Überweisung"),
    ("cheque",  "Scheck"),
    ("cod",     "Rechnung / Nachnahme"),
    ("paypal",  "PayPal")
]

LÄNDER = [
    ("CH","Schweiz"),
    ("LI","Liechtenstein")
]

SPRACHEN = [
    ("de","Deutsch [DE]"),
    ("fr","Französisch [FR]"),
    ("it","Italienisch [IT]"),
    ("en","Englisch [EN]")
]

GUTSCHEINTYPEN = [
    ("percent",         "Prozent"),
    ("fixed_cart",      "Fixer Betrag auf den Warenkorb"),
    ("fixed_product",   "Fixer Betrag auf ein Produkt")
]

#############

class Ansprechpartner(models.Model):
    name = models.CharField('Name', max_length=50, help_text="Auf Rechnung ersichtlich!")
    telefon = models.CharField('Telefon', max_length=50, help_text="Auf Rechnung ersichtlich!")
    email = models.EmailField('E-Mail', help_text="Auf Rechnung ersichtlich!")

    def __str__(self):
        return self.name

    __str__.short_description = 'Ansprechpartner'

    class Meta:
        verbose_name = "Ansprechpartner"
        verbose_name_plural = "Ansprechpartner"

    objects = models.Manager()



class Bestellungskosten(models.Model):
    bestellung = models.ForeignKey("Bestellung", on_delete=models.CASCADE)
    kosten = models.ForeignKey("Kosten", on_delete=models.PROTECT)
    bemerkung = models.CharField("Bemerkung", default="", max_length=250, blank=True, help_text="Wird auf die Rechnung gedruckt.")

    rabatt = models.IntegerField("Rabatt in %", default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])

    kostenpreis = models.FloatField("Preis (exkl. MwSt)", default=0.0)

    def zwischensumme(self):
        return runden(self.kostenpreis*((100-self.rabatt)/100))
    zwischensumme.short_description = "Zwischensumme (exkl. MwSt)"

    def zwischensumme_ohne_rabatt(self):
        return runden(self.kostenpreis)

    def nur_rabatt(self):
        return runden(self.kostenpreis*(self.rabatt/100))*-1

    def mwstsatz(self):
        return formatprice(self.kosten.mwstsatz)
    mwstsatz.short_description = "MwSt-Satz"

    def kosten_name(self):
        return self.kosten.clean_name()
    kosten_name.short_description = "Name"

    def __str__(self):
        return "1x "+str(self.kosten)
    __str__.short_description = "Bestellungskosten"

    def save(self, *args, **kwargs):
        if not self.kostenpreis:
            self.kostenpreis = runden(self.kosten.preis)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Bestellungskosten"
        verbose_name_plural = "Bestellungskosten"

    objects = models.Manager()

class Bestellungsposten(models.Model):
    bestellung = models.ForeignKey("Bestellung", on_delete=models.CASCADE)
    produkt = models.ForeignKey("Produkt", on_delete=models.PROTECT)
    bemerkung = models.CharField("Bemerkung", default="", max_length=250, blank=True, help_text="Wird auf die Rechnung gedruckt.")

    menge = models.IntegerField("Menge", default=1)
    rabatt = models.IntegerField("Rabatt in %", default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])

    produktpreis = models.FloatField("Produktpreis (exkl. MwSt)", default=0.0)

    def zwischensumme(self):
        return runden(self.produktpreis*self.menge*((100-self.rabatt)/100))
    zwischensumme.short_description = "Zwischensumme (exkl. MwSt)"

    def zwischensumme_ohne_rabatt(self):
        return runden(self.produktpreis*self.menge)

    def nur_rabatt(self):
        return runden(self.produktpreis*self.menge*(self.rabatt/100))*-1

    def mwstsatz(self):
        return formatprice(self.produkt.mwstsatz)
    mwstsatz.short_description = "MwSt-Satz"

    def __str__(self):
        return str(self.menge)+"x "+self.produkt.clean_name()
    __str__.short_description = "Bestellungsposten"

    def save(self, *args, **kwargs):
        if not self.produktpreis:
            self.produktpreis = runden(self.produkt.preis())
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Bestellungsposten"
        verbose_name_plural = "Bestellungsposten"

    objects = models.Manager()

class Bestellung(models.Model):
    woocommerceid = models.IntegerField('WooCommerce ID', default=0)

    datum = models.DateTimeField("Datum", default=timezone.now)

    status = models.CharField("Status", max_length=11, default="pending", choices=STATUS)
    versendet = models.BooleanField("Versendet", default=False, help_text="Sobald eine Bestellung als versendet markiert wurde, können Teile der Bestellung nicht mehr bearbeitet werden! Ausserdem werden die Produkte aus dem Lagerbestand entfernt.")
    trackingnummer = models.CharField("Trackingnummer", default="", blank=True, max_length=25, validators=[RegexValidator(r'^99\.[0-9]{2}\.[0-9]{6}\.[0-9]{8}$', 'Bite benutze folgendes Format: 99.xx.xxxxxx.xxxxxxxx')], help_text="Bitte gib hier eine Trackingnummer der Schweizer Post ein. (optional)")

    ausgelagert = models.BooleanField("Ausgelagert", default=False)

    zahlungsmethode = models.CharField("Zahlungsmethode", max_length=7, default="cod", choices=ZAHLUNGSMETHODEN)
    bezahlt = models.BooleanField("Bezahlt", default=False, help_text="Sobald eine Bestellung als bezahlt markiert wurde, können Teile der Bestellung nicht mehr bearbeitet werden!")

    kundennotiz = models.TextField("Kundennotiz", default="", blank=True, help_text="Vom Kunden erfasste Notiz.")
    #rechnungsnotiz = models.TextField("Rechnungsnotiz", default="", blank=True, help_text="Wird auf der Rechnung gedruckt.")

    order_key = models.CharField("Bestellungs-Schlüssel", max_length=50, default=defaultorderkey, blank=True)

    kunde = models.ForeignKey("Kunde", on_delete=models.SET_NULL, null=True, blank=True)
    zahlungsempfaenger = models.ForeignKey("Zahlungsempfaenger", on_delete=models.PROTECT, verbose_name="Zahlungsempfänger", default=defaultzahlungsempfaenger)
    ansprechpartner = models.ForeignKey("Ansprechpartner", on_delete=models.PROTECT, verbose_name="Ansprechpartner", default=defaultansprechpartner)

    rechnungsadresse_vorname = models.CharField("Vorname", max_length=50, default="", blank=True)
    rechnungsadresse_nachname = models.CharField("Nachname", max_length=50, default="", blank=True)
    rechnungsadresse_firma = models.CharField("Firma", max_length=50, default="", blank=True)
    rechnungsadresse_adresszeile1 = models.CharField("Adresszeile 1", max_length=50, default="", blank=True, help_text='Strasse und Hausnummer oder "Postfach" ohne Nummer - Wird bei QR-Rechnung als Strasse und Hausnummer bzw. Postfach verwendet!')
    rechnungsadresse_adresszeile2 = models.CharField("Adresszeile 2", max_length=50, default="", blank=True, help_text="Wird in QR-Rechnung NICHT verwendet!")
    rechnungsadresse_ort = models.CharField("Ort", max_length=50, default="", blank=True)
    rechnungsadresse_kanton = models.CharField("Kanton", max_length=50, default="", blank=True)
    rechnungsadresse_plz = models.CharField("Postleitzahl", max_length=50, default="", blank=True)
    rechnungsadresse_land = models.CharField("Land", max_length=2, default="CH", choices=LÄNDER)
    rechnungsadresse_email = models.EmailField("E-Mail Adresse", blank=True)
    rechnungsadresse_telefon = models.CharField("Telefon", max_length=50, default="", blank=True)

    lieferadresse_vorname = models.CharField("Vorname", max_length=50, default="", blank=True)
    lieferadresse_nachname = models.CharField("Nachname", max_length=50, default="", blank=True)
    lieferadresse_firma = models.CharField("Firma", max_length=50, default="", blank=True)
    lieferadresse_adresszeile1 = models.CharField("Adresszeile 1", max_length=50, default="", blank=True)
    lieferadresse_adresszeile2 = models.CharField("Adresszeile 2", max_length=50, default="", blank=True)
    lieferadresse_ort = models.CharField("Ort", max_length=50, default="", blank=True)
    lieferadresse_kanton = models.CharField("Kanton", max_length=50, default="", blank=True)
    lieferadresse_plz = models.CharField("Postleitzahl", max_length=50, default="", blank=True)
    lieferadresse_land = models.CharField("Land", max_length=2, default="CH", choices=LÄNDER)

    produkte = models.ManyToManyField("Produkt", through="Bestellungsposten", through_fields=("bestellung","produkt"))

    kosten = models.ManyToManyField("Kosten", through="Bestellungskosten", through_fields=("bestellung","kosten"))

    rechnung_gesendet = models.BooleanField("Rechnung gesendet", default=False)

    fix_summe = models.FloatField("Summe in CHF", default=0.0)

    def save(self, *args, **kwargs):
        double_save = True
        if self.pk:
            self.fix_summe = self.summe_gesamt()
            double_save = False
        elif (not self.woocommerceid) and self.kunde:
            self.rechnungsadresse_vorname = self.kunde.rechnungsadresse_vorname
            self.rechnungsadresse_nachname = self.kunde.rechnungsadresse_nachname
            self.rechnungsadresse_firma = self.kunde.rechnungsadresse_firma
            self.rechnungsadresse_adresszeile1 = self.kunde.rechnungsadresse_adresszeile1
            self.rechnungsadresse_adresszeile2 = self.kunde.rechnungsadresse_adresszeile2
            self.rechnungsadresse_ort = self.kunde.rechnungsadresse_ort
            self.rechnungsadresse_kanton = self.kunde.rechnungsadresse_kanton
            self.rechnungsadresse_plz = self.kunde.rechnungsadresse_plz
            self.rechnungsadresse_land = self.kunde.rechnungsadresse_land
            self.rechnungsadresse_email = self.kunde.rechnungsadresse_email
            self.rechnungsadresse_telefon = self.kunde.rechnungsadresse_telefon

            self.lieferadresse_vorname = self.kunde.lieferadresse_vorname
            self.lieferadresse_nachname = self.kunde.lieferadresse_nachname
            self.lieferadresse_firma = self.kunde.lieferadresse_firma
            self.lieferadresse_adresszeile1 = self.kunde.lieferadresse_adresszeile1
            self.lieferadresse_adresszeile2 = self.kunde.lieferadresse_adresszeile2
            self.lieferadresse_ort = self.kunde.lieferadresse_ort
            self.lieferadresse_kanton = self.kunde.lieferadresse_kanton
            self.lieferadresse_plz = self.kunde.lieferadresse_plz
            self.lieferadresse_land = self.kunde.lieferadresse_land
        if self.versendet and (not self.ausgelagert):
            for i in self.produkte.through.objects.filter(bestellung=self):
                i.produkt.lagerbestand -= i.menge
                i.produkt.save()
            self.ausgelagert = True
        super().save(*args, **kwargs)
        if double_save:
            self.save()

    def trackinglink(self):
        return "https://www.post.ch/swisspost-tracking?formattedParcelCodes="+self.trackingnummer if self.trackingnummer else None
    trackinglink.short_description = "Trackinglink"

    def referenznummer(self):
        a = str(self.pk).zfill(22)+"0000"
        b = a+str(modulo10rekursiv(a))
        c = b[0:2]+" "+b[2:7]+" "+b[7:12]+" "+b[12:17]+" "+b[17:22]+" "+b[22:27]
        return c

    def rechnungsinformationen(self):
        date = self.datum.strftime("%y%m%d")
        uid = self.zahlungsempfaenger.firmenuid.split("-")[1].replace(".","")
        mwstdict = self.mwstdict()
        mwststring = ";".join(satz+":"+str(mwstdict[satz]) for satz in mwstdict)
        return "//S1/10/"+str(self.pk)+"/11/"+date+"/30/"+uid+"/31/"+date+"/32/"+mwststring+"/40/"+"0:30"

    def mwstdict(self):
        mwst = {}
        for p in self.produkte.through.objects.filter(bestellung=self):
            if str(p.produkt.mwstsatz) in mwst:
                mwst[str(p.produkt.mwstsatz)] += p.zwischensumme()
            else:
                mwst[str(p.produkt.mwstsatz)] = p.zwischensumme()
        for k in self.kosten.through.objects.filter(bestellung=self):
            if str(k.kosten.mwstsatz) in mwst:
                mwst[str(k.kosten.mwstsatz)] += k.zwischensumme()
            else:
                mwst[str(k.kosten.mwstsatz)] = k.zwischensumme()
        return mwst

    def summe(self):
        summe = 0
        for i in self.produkte.through.objects.filter(bestellung=self):
            summe += i.zwischensumme()
        for i in self.kosten.through.objects.filter(bestellung=self):
            summe += i.zwischensumme()
        return runden(summe)
    summe.short_description = "Summe (exkl. MwSt) in CHF"

    def summe_mwst(self):
        summe_mwst = 0
        mwstdict = self.mwstdict()
        for mwstsatz in mwstdict:
            summe_mwst += runden(float(mwstdict[mwstsatz]*(float(mwstsatz)/100)))
        return runden(summe_mwst)
    summe_mwst.short_description = "Summe (nur MwSt) in CHF"

    def summe_gesamt(self):
        return runden(self.summe()+self.summe_mwst())
    summe_gesamt.short_description = "Summe in CHF"

    def name(self):
        return (self.datum.strftime("%Y")+"-" if self.datum and not isinstance(self.datum, str) else "")+str(self.pk).zfill(6)+(" (WC#"+str(self.woocommerceid)+")" if self.woocommerceid else "")+" - "+(str(self.kunde) if self.kunde is not None else "Gast")
    name.short_description = "Name"

    def info(self):
        return self.datum.strftime("%d.%m.%Y")+" - "+((self.kunde.firma if self.kunde.firma else (self.kunde.vorname+" "+self.kunde.nachname)) if self.kunde else "Gast")
    info.short_description = "Info"

    def __str__(self):
        return self.name()
    __str__.short_description = "Bestellung"

    def get_pdf(self, lieferschein:bool=False, digital:bool=True):
        return FileResponse(pdf_bestellung(self, lieferschein=lieferschein, digital=digital), as_attachment=False, filename=('Lieferschein' if lieferschein else 'Rechnung')+' zu Bestellung '+str(self)+'.pdf')

    def send_pdf_rechnung_to_customer(self):
        success = send_pdf(
            subject="Ihre Rechnung Nr. "+str(self.id)+(" (Online #"+str(self.woocommerceid)+")" if self.woocommerceid else ""),
            to=self.rechnungsadresse_email,
            template_name="kunde_rechnung.html",
            pdf_filename="Rechnung Nr. "+str(self.id)+(" (Online #"+str(self.woocommerceid)+")" if self.woocommerceid else "")+".pdf",
            pdf=pdf_bestellung(self, lieferschein=False, digital=True),
            context={
                "trackinglink": str(self.trackinglink()),
                "trackingdata": bool(self.trackinglink() and self.versendet),
                "id": str(self.id),
                "woocommerceid": str(self.woocommerceid),
                "woocommercedata": bool(self.woocommerceid)
            },
            headers={"Rechnungs-ID":str(self.id)},
            bcc=[self.zahlungsempfaenger.email]
        )
        if success:
            self.rechnung_gesendet = True
            self.save()
        return success

    def html_todo_notiz(self):
        if hasattr(self, "notiz"):
            link = reverse("admin:kmuhelper_todonotiz_change", kwargs={"object_id": self.notiz.pk})
            return mark_safe('<a target="_blank" href="'+link+'">Notiz ansehen</a>')
        else:
            link = reverse("admin:kmuhelper_todonotiz_add")+'?from_bestellung='+str(self.pk)
            return mark_safe('<a target="_blank" href="'+link+'">Notiz hinzufügen</a>')
    html_todo_notiz.short_description = "ToDo Notiz"

    def html_notiz(self):
        if hasattr(self, "notiz"):
            link = reverse("admin:kmuhelper_notiz_change", kwargs={"object_id": self.notiz.pk})
            return mark_safe('<a target="_blank" href="'+link+'">Notiz ansehen</a>')
        else:
            link = reverse("admin:kmuhelper_notiz_add")+'?from_bestellung='+str(self.pk)
            return mark_safe('<a target="_blank" href="'+link+'">Notiz hinzufügen</a>')
    html_notiz.short_description = "Notiz"

    def get_future_stock(self):
        data = {}
        for p in self.produkte.all():
            n_current = p.lagerbestand
            n_going = p.get_reserved_stock()
            n_coming = p.get_incoming_stock()
            n_min = p.soll_lagerbestand

            data[p.clean_name()] = {"current": n_current, "going": n_going, "coming": n_coming, "min": n_min}
        return data

    def email_stock_warning(self):
        warnings = []
        stock = self.get_future_stock()
        for n in stock:
            s = stock[n]
            if (s["current"]-s["going"]) < s["min"]:
                warnings.append({"product": n, "stock": s})

        if warnings != []:
            try:
                print("E-Mail Success:", send_mail(
                    subject="[KMUHelper] - Lagerbestand knapp!",
                    to=Einstellung.objects.get(id="email-stock-warning-receiver").inhalt,
                    template_name="bestellung_stock_warning.html",
                    context={
                        "warnings": warnings,
                    },
                ))
            except Exception as e:
                print("E-Mail Error!", e)

    class Meta:
        verbose_name = "Bestellung"
        verbose_name_plural = "Bestellungen"

    objects = models.Manager()


# class Gutschein(models.Model):
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



class Kategorie(models.Model):
    woocommerceid = models.IntegerField('WooCommerce ID', default=0)

    name = models.CharField('Name', max_length=250, default="")
    beschrieb = models.TextField('Beschrieb', default="", blank=True)
    bildlink = models.URLField('Bildlink', blank=True)

    uebergeordnete_kategorie = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Übergeordnete Kategorie")

    def bild(self):
        if self.bildlink:
            return mark_safe('<img src="'+self.bildlink+'" width="100px">')
        return ""
    bild.short_description = "Bild"

    def anzahl_produkte(self):
        return self.produkte.count()
    anzahl_produkte.short_description = "Anzahl Produkte"

    def clean_name(self):
        return clean(self.name)
    clean_name.short_description = "Name"

    def clean_beschrieb(self):
        return clean(self.beschrieb)
    clean_beschrieb.short_description = "Beschrieb"

    def __str__(self):
        return self.clean_name()
    __str__.short_description = "Kategorie"

    class Meta:
        verbose_name = "Kategorie"
        verbose_name_plural = "Kategorien"

    objects = models.Manager()



class Kosten(models.Model):
    name = models.CharField("Name", max_length=500, default="Zusätzliche Kosten")
    preis = models.FloatField("Preis (exkl. MwSt)", default=0.0)
    mwstsatz = models.FloatField('MwSt-Satz', choices=MWSTSÄTZE, default=7.7)

    @property
    def mengenbezeichnung(self):
        return clean("[:de]Stück[:fr]Pièce[:it]Pezzo[:en]Piece[:]")

    def clean_name(self):
        return clean(self.name)

    def __str__(self):
        return f"{ self.clean_name() } ({ self.preis } CHF " + ("+ "+str(self.mwstsatz)+"% MwSt" if self.mwstsatz else "") + ")"
    __str__.short_description = "Kosten"

    class Meta:
        verbose_name = "Kosten"
        verbose_name_plural = "Kosten"
    
    objects = models.Manager()



class Kunde(models.Model):
    woocommerceid = models.IntegerField('WooCommerce ID', default=0)

    email = models.EmailField("E-Mail Adresse", blank=True)
    vorname = models.CharField("Vorname", max_length=50, default="", blank=True)
    nachname = models.CharField("Nachname", max_length=50, default="", blank=True)
    firma = models.CharField("Firma", max_length=50, default="", blank=True)
    benutzername = models.CharField("Benutzername", max_length=50, default="", blank=True)
    avatar_url = models.URLField("Avatar URL", blank=True, editable=False)
    sprache = models.CharField("Sprache", default="de",choices=SPRACHEN, max_length=2)

    rechnungsadresse_vorname = models.CharField("Vorname", max_length=50, default="", blank=True)
    rechnungsadresse_nachname = models.CharField("Nachname", max_length=50, default="", blank=True)
    rechnungsadresse_firma = models.CharField("Firma", max_length=50, default="", blank=True)
    rechnungsadresse_adresszeile1 = models.CharField("Adresszeile 1", max_length=50, default="", blank=True, help_text='Strasse und Hausnummer oder "Postfach"')
    rechnungsadresse_adresszeile2 = models.CharField("Adresszeile 2", max_length=50, default="", blank=True, help_text="Wird in QR-Rechnung NICHT verwendet!")
    rechnungsadresse_ort = models.CharField("Ort", max_length=50, default="", blank=True)
    rechnungsadresse_kanton = models.CharField("Kanton", max_length=50, default="", blank=True)
    rechnungsadresse_plz = models.CharField("Postleitzahl", max_length=50, default="", blank=True)
    rechnungsadresse_land = models.CharField("Land", max_length=2, default="CH", choices=LÄNDER)
    rechnungsadresse_email = models.EmailField("E-Mail Adresse", blank=True)
    rechnungsadresse_telefon = models.CharField("Telefon", max_length=50, default="", blank=True)

    lieferadresse_vorname = models.CharField("Vorname", max_length=50, default="", blank=True)
    lieferadresse_nachname = models.CharField("Nachname", max_length=50, default="", blank=True)
    lieferadresse_firma = models.CharField("Firma", max_length=50, default="", blank=True)
    lieferadresse_adresszeile1 = models.CharField("Adresszeile 1", max_length=50, default="", blank=True)
    lieferadresse_adresszeile2 = models.CharField("Adresszeile 2", max_length=50, default="", blank=True)
    lieferadresse_ort = models.CharField("Ort", max_length=50, default="", blank=True)
    lieferadresse_kanton = models.CharField("Kanton", max_length=50, default="", blank=True)
    lieferadresse_plz = models.CharField("Postleitzahl", max_length=50, default="", blank=True)
    lieferadresse_land = models.CharField("Land", max_length=2, default="CH", choices=LÄNDER)

    zusammenfuegen = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Zusammenfügen mit", help_text="Dies kann nicht widerrufen werden! Werte im aktuellen Kunden werden bevorzugt.")
    webseite = models.URLField("Webseite", blank=True, default="")
    bemerkung = models.TextField("Bemerkung", default="", blank=True)

    registrierungsemail_gesendet = models.BooleanField("Registrierungsemail gesendet?", default=False)

    def avatar(self):
        if self.avatar_url:
            return mark_safe('<img src="'+self.avatar_url+'" width="50px">')
        return ""
    avatar.short_description = "Avatar"

    def __str__(self):
        return (
            str(self.pk).zfill(8)+" " +
            (("(WC#"+str(self.woocommerceid)+") ") if self.woocommerceid else "") +
            ((self.vorname + " ") if self.vorname else "") +
            ((self.nachname + " ") if self.nachname else "") +
            ((self.firma + " ") if self.firma else "") +
            (("(" + str(self.rechnungsadresse_plz) + " " + self.rechnungsadresse_ort + ")"))
        )
    __str__.short_description = "Kunde"

    class Meta:
        verbose_name = "Kunde"
        verbose_name_plural = "Kunden"

    def save(self, *args, **kwargs):
        if self.zusammenfuegen:
            self.woocommerceid = self.woocommerceid if self.woocommerceid else self.zusammenfuegen.woocommerceid

            self.email = self.email if self.email else self.zusammenfuegen.email
            self.vorname = self.vorname if self.vorname else self.zusammenfuegen.vorname
            self.nachname = self.nachname if self.nachname else self.zusammenfuegen.nachname
            self.firma = self.firma if self.firma else self.zusammenfuegen.firma
            self.benutzername = self.benutzername if self.benutzername else self.zusammenfuegen.benutzername
            self.avatar_url = self.avatar_url if self.avatar_url else self.zusammenfuegen.avatar_url
            self.sprache = self.sprache if self.sprache != "de" else self.zusammenfuegen.sprache

            self.rechnungsadresse_vorname = self.rechnungsadresse_vorname if self.rechnungsadresse_vorname else self.zusammenfuegen.rechnungsadresse_vorname
            self.rechnungsadresse_nachname = self.rechnungsadresse_nachname if self.rechnungsadresse_nachname else self.zusammenfuegen.rechnungsadresse_nachname
            self.rechnungsadresse_firma = self.rechnungsadresse_firma if self.rechnungsadresse_firma else self.zusammenfuegen.rechnungsadresse_firma
            self.rechnungsadresse_adresszeile1 = self.rechnungsadresse_adresszeile1 if self.rechnungsadresse_adresszeile1 else self.zusammenfuegen.rechnungsadresse_adresszeile1
            self.rechnungsadresse_adresszeile2 = self.rechnungsadresse_adresszeile2 if self.rechnungsadresse_adresszeile2 else self.zusammenfuegen.rechnungsadresse_adresszeile2
            self.rechnungsadresse_ort = self.rechnungsadresse_ort if self.rechnungsadresse_ort else self.zusammenfuegen.rechnungsadresse_ort
            self.rechnungsadresse_kanton = self.rechnungsadresse_kanton if self.rechnungsadresse_kanton else self.zusammenfuegen.rechnungsadresse_kanton
            self.rechnungsadresse_plz = self.rechnungsadresse_plz if self.rechnungsadresse_plz else self.zusammenfuegen.rechnungsadresse_plz
            self.rechnungsadresse_land = self.rechnungsadresse_land if self.rechnungsadresse_land else self.zusammenfuegen.rechnungsadresse_land
            self.rechnungsadresse_email = self.rechnungsadresse_email if self.rechnungsadresse_email else self.zusammenfuegen.rechnungsadresse_email
            self.rechnungsadresse_telefon = self.rechnungsadresse_telefon if self.rechnungsadresse_telefon else self.zusammenfuegen.rechnungsadresse_telefon

            self.lieferadresse_vorname = self.lieferadresse_vorname if self.lieferadresse_vorname else self.zusammenfuegen.lieferadresse_vorname
            self.lieferadresse_nachname = self.lieferadresse_nachname if self.lieferadresse_nachname else self.zusammenfuegen.lieferadresse_nachname
            self.lieferadresse_firma = self.lieferadresse_firma if self.lieferadresse_firma else self.zusammenfuegen.lieferadresse_firma
            self.lieferadresse_adresszeile1 = self.lieferadresse_adresszeile1 if self.lieferadresse_adresszeile1 else self.zusammenfuegen.lieferadresse_adresszeile1
            self.lieferadresse_adresszeile2 = self.lieferadresse_adresszeile2 if self.lieferadresse_adresszeile2 else self.zusammenfuegen.lieferadresse_adresszeile2
            self.lieferadresse_ort = self.lieferadresse_ort if self.lieferadresse_ort else self.zusammenfuegen.lieferadresse_ort
            self.lieferadresse_kanton = self.lieferadresse_kanton if self.lieferadresse_kanton else self.zusammenfuegen.lieferadresse_kanton
            self.lieferadresse_plz = self.lieferadresse_plz if self.lieferadresse_plz else self.zusammenfuegen.lieferadresse_plz
            self.lieferadresse_land = self.lieferadresse_land if self.lieferadresse_land else self.zusammenfuegen.lieferadresse_land

            self.webseite = self.webseite if self.webseite else self.zusammenfuegen.webseite
            self.notiz = self.notiz+" "+self.zusammenfuegen.notiz

            for bestellung in self.zusammenfuegen.bestellung_set.all():
                bestellung.kunde = self
                bestellung.save()
            self.zusammenfuegen.delete()
            self.zusammenfuegen = None
        super().save(*args, **kwargs)

    def send_register_mail(self):
        self.registrierungsemail_gesendet = bool(send_mail(
            subject="Registrierung erfolgreich!",
            to=self.email,
            template_name="kunde_registriert.html",
            context={
                "kunde": self
            },
            headers={"Kunden-ID": str(self.id)}
        ))
        self.save()
        return self.registrierungsemail_gesendet

    def html_todo_notiz(self):
        if hasattr(self, "notiz"):
            link = reverse("admin:kmuhelper_todonotiz_change", kwargs={"object_id": self.notiz.pk})
            return mark_safe('<a target="_blank" href="'+link+'">Notiz ansehen</a>')
        else:
            link = reverse("admin:kmuhelper_todonotiz_add")+'?from_kunde='+str(self.pk)
            return mark_safe('<a target="_blank" href="'+link+'">Notiz hinzufügen</a>')
    html_todo_notiz.short_description = "ToDo Notiz"

    def html_notiz(self):
        if hasattr(self, "notiz"):
            link = reverse("admin:kmuhelper_notiz_change", kwargs={"object_id": self.notiz.pk})
            return mark_safe('<a target="_blank" href="'+link+'">Notiz ansehen</a>')
        else:
            link = reverse("admin:kmuhelper_notiz_add")+'?from_kunde='+str(self.pk)
            return mark_safe('<a target="_blank" href="'+link+'">Notiz hinzufügen</a>')
    html_notiz.short_description = "Notiz"

    objects = models.Manager()



class Lieferant(models.Model):
    kuerzel = models.CharField("Kürzel", max_length=5)
    name = models.CharField('Name', max_length=50)

    webseite = models.URLField("Webseite", blank=True)
    telefon = models.CharField('Telefon', max_length=50, default="", blank=True)
    email = models.EmailField('E-Mail', null=True, blank=True)

    adresse = models.TextField('Adresse', default="", blank=True)
    notiz = models.TextField('Notiz', default="", blank=True)

    ansprechpartner = models.CharField('Ansprechpartner', max_length=250, default="", blank=True)
    ansprechpartnertel = models.CharField('Ansprechpartner Telefon', max_length=50, default="", blank=True)
    ansprechpartnermail = models.EmailField('Ansprechpartner E-Mail', null=True, default="", blank=True)

    def __str__(self):
        return self.name
    __str__.short_description = "Lieferant"

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



class Lieferungsposten(models.Model):
    lieferung = models.ForeignKey("Lieferung", on_delete=models.CASCADE)
    produkt = models.ForeignKey("Produkt", on_delete=models.PROTECT)
    menge = models.IntegerField("Menge", default=1)

    def __str__(self):
        return str(self.menge)+"x "+self.produkt.clean_name()
    __str__.short_description = "Lieferungsposten"

    class Meta:
        verbose_name = "Lieferungsposten"
        verbose_name_plural = "Lieferungsposten"

    objects = models.Manager()

class Lieferung(models.Model):
    name = models.CharField("Name", max_length=50, default=defaultlieferungsname)
    datum = models.DateField("Erfasst am", auto_now_add=True)

    lieferant = models.ForeignKey("Lieferant", on_delete=models.SET_NULL, null=True, blank=True)
    produkte = models.ManyToManyField("Produkt", through="Lieferungsposten", through_fields=("lieferung","produkt"))

    eingelagert = models.BooleanField("Eingelagert", default=False)

    def anzahlprodukte(self):
        anzahl = 0
        for i in self.produkte.through.objects.filter(lieferung=self):
            anzahl += i.menge
        return anzahl
    anzahlprodukte.short_description = "Produkte"

    def einlagern(self):
        if not self.eingelagert:
            for i in self.produkte.through.objects.filter(lieferung=self):
                i.produkt.lagerbestand += i.menge
                i.produkt.save()
            self.eingelagert = True
            self.save()
            return True
        else:
            return False

    def html_todo_notiz(self):
        if hasattr(self, "notiz"):
            link = reverse("admin:kmuhelper_todonotiz_change", kwargs={"object_id": self.notiz.pk})
            return mark_safe('<a target="_blank" href="'+link+'">Notiz ansehen</a>')
        else:
            link = reverse("admin:kmuhelper_todonotiz_add")+'?from_lieferung='+str(self.pk)
            return mark_safe('<a target="_blank" href="'+link+'">Notiz hinzufügen</a>')
    html_todo_notiz.short_description = "ToDo Notiz"

    def html_notiz(self):
        if hasattr(self, "notiz"):
            link = reverse("admin:kmuhelper_notiz_change", kwargs={"object_id": self.notiz.pk})
            return mark_safe('<a target="_blank" href="'+link+'">Notiz ansehen</a>')
        else:
            link = reverse("admin:kmuhelper_notiz_add")+'?from_lieferung='+str(self.pk)
            return mark_safe('<a target="_blank" href="'+link+'">Notiz hinzufügen</a>')
    html_notiz.short_description = "Notiz"

    def __str__(self):
        return self.name
    __str__.short_description = "Lieferung"

    class Meta:
        verbose_name = "Lieferung"
        verbose_name_plural = "Lieferungen"

    objects = models.Manager()


class Notiz(models.Model):
    name = models.CharField("Name", max_length=50)
    beschrieb = models.TextField("Beschrieb", default="", blank=True)

    erledigt = models.BooleanField("Erledigt", default=False)

    priority = models.IntegerField("Priorität", default=0, blank=True)
    erstellt_am = models.DateTimeField("Erstellt am", auto_now_add=True)

    bestellung = models.OneToOneField("Bestellung", blank=True, null=True, on_delete=models.CASCADE, related_name="notiz")
    produkt = models.OneToOneField("Produkt", blank=True, null=True, on_delete=models.CASCADE, related_name="notiz")
    kunde = models.OneToOneField("Kunde", blank=True, null=True, on_delete=models.CASCADE, related_name="notiz")
    lieferung = models.OneToOneField("Lieferung", blank=True, null=True, on_delete=models.CASCADE, related_name="notiz")

    def __str__(self):
        return self.name
    __str__.short_description = "Notiz"

    def links(self):
        text = ""
        if self.bestellung:
            text += "Bestellung <a href='"+reverse("admin:kmuhelper_bestellung_change", kwargs={"object_id":self.bestellung.pk})+"'>#"+str(self.bestellung.pk)+"</a><br>"
        if self.produkt:
            text += "Produkt <a href='"+reverse("admin:kmuhelper_produkt_change", kwargs={"object_id":self.produkt.pk})+"'>#"+str(self.produkt.pk)+"</a><br>"
        if self.kunde:
            text += "Kunde <a href='"+reverse("admin:kmuhelper_kunde_change", kwargs={"object_id":self.kunde.pk})+"'>#"+str(self.kunde.pk)+"</a><br>"
        if self.lieferung:
            text += "Lieferung <a href='"+reverse("admin:kmuhelper_lieferung_change", kwargs={"object_id":self.lieferung.pk})+"'>#"+str(self.lieferung.pk)+"</a><br>"
        return mark_safe(text or "Diese Notiz hat keine Verknüpfungen.")

    class Meta:
        verbose_name = "Notiz"
        verbose_name_plural = "Notizen"

    objects = models.Manager()


class Produktkategorie(models.Model):
    produkt = models.ForeignKey("Produkt", on_delete=models.CASCADE)
    kategorie = models.ForeignKey("Kategorie", on_delete=models.CASCADE)

    def __str__(self):
        return self.kategorie.name
    __str__.short_description = "Produktkategorie"

    class Meta:
        verbose_name = "Produktkategorie"
        verbose_name_plural = "Produktkategorien"

    objects = models.Manager()

class Produkt(models.Model):
    artikelnummer = models.CharField("Artikelnummer", max_length=25)

    woocommerceid = models.IntegerField('WooCommerce ID', default=0)

    name = models.CharField('Name', max_length=500)
    kurzbeschrieb = models.TextField('Kurzbeschrieb', default="", blank=True)
    beschrieb = models.TextField('Beschrieb', default="", blank=True)

    mengenbezeichnung = models.CharField('Mengenbezeichnung', max_length=100, default="[:de]Stück[:fr]Pièce[:it]Pezzo[:en]Piece[:]", blank=True)
    verkaufspreis = models.FloatField('Normalpreis in CHF (exkl. MwSt)', default=0)
    mwstsatz = models.FloatField('Mehrwertsteuersatz', choices= MWSTSÄTZE, default=7.7)

    lagerbestand = models.IntegerField("Lagerbestand", default=0)
    soll_lagerbestand = models.IntegerField("Soll-Lagerbestand", default=1)

    bemerkung = models.TextField('Bemerkung', default="", blank=True, help_text="Wird nicht gedruckt oder angezeigt; nur für eigene Zwecke.")
    #packlistenbemerkung = models.TextField('Packlistenbemerkung', default="", blank=True, help_text="Wird auf die Packliste gedruckt.")

    aktion_von = models.DateTimeField("In Aktion von", blank=True, null=True)
    aktion_bis = models.DateTimeField("In Aktion bis", blank=True, null=True)
    aktion_preis = models.FloatField("Aktionspreis in CHF (exkl. MwSt)", blank=True, null=True)

    datenblattlink = models.CharField('Datenblattlink', max_length=500, default="", blank=True)
    bildlink = models.URLField('Bildlink', default="", blank=True)

    lieferant = models.ForeignKey("Lieferant", on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Lieferant")
    lieferant_preis = models.CharField("Lieferantenpreis", default="", blank=True, max_length=20)
    lieferant_artikelnummer = models.CharField("Lieferantenartikelnummer", default="", blank=True, max_length=25)

    kategorien = models.ManyToManyField("Kategorie", through="Produktkategorie", through_fields=("produkt","kategorie"), verbose_name="Kategorie", related_name="produkte")

    def clean_name(self, lang="de"):
        return clean(self.name,lang)
    clean_name.short_description = "Name"

    def clean_kurzbeschrieb(self, lang="de"):
        return clean(self.kurzbeschrieb,lang)
    clean_kurzbeschrieb.short_description = "Kurzbeschrieb"

    def clean_beschrieb(self, lang="de"):
        return clean(self.beschrieb,lang)
    clean_beschrieb.short_description = "Beschrieb"

    def in_aktion(self, zeitpunkt:datetime=datetime.now(utc)):
        if self.aktion_von and self.aktion_bis and self.aktion_preis:
            return bool((self.aktion_von < zeitpunkt) and (zeitpunkt < self.aktion_bis))
        return False
    in_aktion.short_description = "In Aktion"
    in_aktion.boolean = True

    def preis(self, zeitpunkt:datetime=datetime.now(utc)):
        return self.aktion_preis if self.in_aktion(zeitpunkt) else self.verkaufspreis
    preis.short_description = "Aktueller Preis in CHF (exkl. MwSt)"

    def bild(self):
        if self.bildlink:
            return mark_safe('<img src="'+self.bildlink+'" width="100px">')
        return ""
    bild.short_description = "Bild"

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

    def save(self, *args, **kwargs):
        if self.mengenbezeichnung == "Stück":
            self.mengenbezeichnung = "[:de]Stück[:fr]Pièce[:it]Pezzo[:en]Piece[:]"
        elif self.mengenbezeichnung == "Flasche":
            self.mengenbezeichnung = "[:de]Flasche[:fr]Bouteille[:it]Bottiglia[:en]Bottle[:]"
        elif self.mengenbezeichnung == "Tube":
            self.mengenbezeichnung = "[:de]Tube[:fr]Tube[:it]Tubetto[:en]Tube[:]"
        super().save(*args, **kwargs)

    def html_todo_notiz(self):
        if hasattr(self, "notiz"):
            link = reverse("admin:kmuhelper_todonotiz_change", kwargs={"object_id": self.notiz.pk})
            return mark_safe('<a target="_blank" href="'+link+'">Notiz ansehen</a>')
        else:
            link = reverse("admin:kmuhelper_todonotiz_add")+'?from_produkt='+str(self.pk)
            return mark_safe('<a target="_blank" href="'+link+'">Notiz hinzufügen</a>')
    html_todo_notiz.short_description = "ToDo Notiz"

    def html_notiz(self):
        if hasattr(self, "notiz"):
            link = reverse("admin:kmuhelper_notiz_change", kwargs={"object_id": self.notiz.pk})
            return mark_safe('<a target="_blank" href="'+link+'">Notiz ansehen</a>')
        else:
            link = reverse("admin:kmuhelper_notiz_add")+'?from_produkt='+str(self.pk)
            return mark_safe('<a target="_blank" href="'+link+'">Notiz hinzufügen</a>')
    html_notiz.short_description = "Notiz"

    def __str__(self):
        return self.artikelnummer+" - "+self.clean_name()
    __str__.short_description = "Produkt"

    class Meta:
        verbose_name = "Produkt"
        verbose_name_plural = "Produkte"

    objects = models.Manager()



class Zahlungsempfaenger(models.Model):
    qriban = models.CharField("QR-IBAN", max_length=21+5 , validators=[RegexValidator(r'^(CH|LI)[0-9]{2}\s3[0-9]{3}\s[0-9]{4}\s[0-9]{4}\s[0-9]{4}\s[0-9]{1}$', 'Bite benutze folgendes Format: (CH|LI)pp 3xxx xxxx xxxx xxxx x')], help_text="QR-IBAN mit Leerzeichen")
    logourl = models.URLField("Logo (URL)", validators=[RegexValidator(r'''^[0-9a-zA-Z\-\.\|\?\(\)\*\+&"'_:;/]+\.(png|jpg)$''', '''Nur folgende Zeichen gestattet: 0-9a-zA-Z-_.:;/|?&()"'*+ - Muss auf .jpg/.png enden.''')], help_text="URL eines Bildes (.jpg/.png) - Wird auf die Rechnung gedruckt.")
    firmenname = models.CharField("Firmennname", max_length=70, help_text="Name der Firma")
    firmenuid = models.CharField("Firmen-UID", max_length=15 , validators=[RegexValidator(r'^CHE-[0-9]{3}\.[0-9]{3}\.[0-9]{3}$', 'Bite benutze folgendes Format: CHE-123.456.789')], help_text="UID der Firma - Format: CHE-123.456.789 (Mehrwertsteuernummer)")
    adresszeile1 = models.CharField("Strasse und Hausnummer oder 'Postfach'", max_length=70)
    adresszeile2 = models.CharField("PLZ und Ort", max_length=70)
    land = models.CharField("Land", max_length=2, choices=LÄNDER, default="CH")
    email = models.EmailField("E-Mail", default="", blank=True, help_text="Nicht auf der Rechnung ersichtlich")
    telefon = models.CharField("Telefon", max_length=70, default="", blank=True, help_text="Nicht auf der Rechnung ersichtlich")
    webseite = models.URLField("Webseite", help_text="Auf der Rechnung ersichtlich!")

    def has_valid_qr_iban(self):
        import string
        try:
            b = ''
            for i in (0,1):
                a = self.qriban[i].upper()
                if a not in string.ascii_uppercase:
                    return False
                else:
                    b += str(ord(a)-55)
            Nr = ''.join([z for z in self.qriban[2:] if z in string.digits])
            return (int(int(Nr[2:] + b + Nr [:2])%97) == 1)
        except IndexError:
            return False

    def has_valid_uid(self):
        try:
            u = self.firmenuid.split("-")[1].replace(".", "")
            p = 11 - (((int(u[0])*5)+(int(u[1])*4)+(int(u[2])*3)+(int(u[3])*2)+(int(u[4])*7)+(int(u[5])*6)+(int(u[6])*5)+(int(u[7])*4)) % 11)
            print(u,p)
            return int(u[8]) == p
        except Exception as e:
            print(e)
            return False

    def __str__(self):
        return self.firmenname
    __str__.short_description = "Zahlungsempfänger"

    class Meta:
        verbose_name = "Zahlungsempfänger"
        verbose_name_plural = "Zahlungsempfänger"

    objects = models.Manager()



######################

######################

EINSTELLUNGSTYPEN = [
    ("char", "Text"),
    ("text", "Mehrzeiliger Text"),
    ("bool", "Wahrheitswert"),
    ("int",  "Zahl"),
    ("float", "Fliesskommazahl"),
    ("url",  "Url"),
    ("email", "E-Mail"),
]

class Einstellung(models.Model):
    id   = models.CharField("ID", max_length=50, primary_key=True)
    name = models.CharField("Name", max_length=200)
    typ  = models.CharField("Typ", max_length=5, default="char", choices=EINSTELLUNGSTYPEN)

    char  = models.CharField(    "Inhalt (Text)", max_length=250, default="",    blank=True)
    text  = models.TextField(    "Inhalt (Mehrzeiliger Text)",    default="",    blank=True)
    boo   = models.BooleanField( "Inhalt (Wahrheitswert)",        default=False, blank=True)
    inte  = models.IntegerField( "Inhalt (Zahl)",                 default=0,     blank=True)
    floa  = models.FloatField(   "Inhalt (Fliesskommazahl)",      default=0.0,   blank=True)
    url   = models.URLField(     "Inhalt (Url)",                  default="",    blank=True)
    email = models.EmailField(   "Inhalt (E-Mail)",               default="",    blank=True)

    def __str__(self):
        return self.name
    __str__.short_description = "Einstellung"

    @property
    def inhalt(self):
        if self.typ == "char":
            return self.char
        elif self.typ == "text":
            return self.text
        elif self.typ == "bool":
            return self.boo
        elif self.typ == "int":
            return self.inte
        elif self.typ == "float":
            return self.floa
        elif self.typ == "url":
            return self.url
        elif self.typ == "email":
            return self.email

    @inhalt.setter
    def inhalt(self, var):
        if self.typ == "char":
            self.char = var
        elif self.typ == "text":
            self.text = var
        elif self.typ == "bool":
            self.boo = var
        elif self.typ == "int":
            self.inte = var
        elif self.typ == "float":
            self.floa = var
        elif self.typ == "url":
            self.url = var
        elif self.typ == "email":
            self.email = var

    def get_inhalt(self):
        return self.inhalt
    get_inhalt.short_description = "Inhalt"

    class Meta:
        verbose_name = "Einstellung"
        verbose_name_plural = "Einstellungen"

    objects = models.Manager()



class Geheime_Einstellung(models.Model):
    id = models.CharField("ID", max_length=50, primary_key=True)
    typ  = models.CharField("Typ", max_length=5, default="char", choices=EINSTELLUNGSTYPEN)

    char  = models.CharField(    "Inhalt (Text)", max_length=250, default="",    blank=True)
    text  = models.TextField(    "Inhalt (Mehrzeiliger Text)",    default="",    blank=True)
    boo   = models.BooleanField( "Inhalt (Wahrheitswert)",        default=False, blank=True)
    inte  = models.IntegerField( "Inhalt (Zahl)",                 default=0,     blank=True)
    floa  = models.FloatField(   "Inhalt (Fliesskommazahl)",      default=0.0,   blank=True)
    url   = models.URLField(     "Inhalt (Url)",                  default="",    blank=True)
    email = models.EmailField(   "Inhalt (E-Mail)",               default="",    blank=True)

    def __str__(self):
        return self.id
    __str__.short_description = "Geheime Einstellung"

    @property
    def inhalt(self):
        if self.typ == "char":
            return self.char
        elif self.typ == "text":
            return self.text
        elif self.typ == "bool":
            return self.boo
        elif self.typ == "int":
            return self.inte
        elif self.typ == "float":
            return self.floa
        elif self.typ == "url":
            return self.url
        elif self.typ == "email":
            return self.email

    @inhalt.setter
    def inhalt(self, var):
        if self.typ == "char":
            self.char = var
        elif self.typ == "text":
            self.text = var
        elif self.typ == "bool":
            self.boo = var
        elif self.typ == "int":
            self.inte = var
        elif self.typ == "float":
            self.floa = var
        elif self.typ == "url":
            self.url = var
        elif self.typ == "emal":
            return self.email

    def get_inhalt(self):
        return self.inhalt
    get_inhalt.short_description = "Inhalt"

    class Meta:
        verbose_name = "Geheime Einstellung"
        verbose_name_plural = "Geheime Einstellungen"

    objects = models.Manager()
