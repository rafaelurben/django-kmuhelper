import csv

from django.core.management.base import BaseCommand, CommandError

from kmuhelper.modules.main.models import Kunde
from kmuhelper.utils import getfirstindex


class Command(BaseCommand):
    help = 'Imports customers from a .csv file.'

    def add_arguments(self, parser):
        parser.add_argument(
            'filepath', help="Absolute filepath to the .csv file", type=str)

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Import gestartet!"))
        try:
            with open(options["filepath"], newline='', encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

            indexrow = rows.pop(0)

            ###
            index_id = getfirstindex(indexrow, ["Nummer", "ID"])

            index_email = getfirstindex(
                indexrow, ["Email", "E-Mail", "EMail", "EMAIL"])
            index_first_name = getfirstindex(
                indexrow, ["Vorname"])
            index_last_name = getfirstindex(
                indexrow, ["Name", "Nachname"])
            index_sprache = getfirstindex(
                indexrow, ["Sprache", "SPRACHE"])

            index_company = getfirstindex(
                indexrow, ["Firma"])
            index_strasse = getfirstindex(
                indexrow, ["Strasse"])
            index_city = getfirstindex(
                indexrow, ["Ort"])
            index_postcode = getfirstindex(
                indexrow, ["PLZ", "Plz", "Postleitzahl"])
            index_country = getfirstindex(
                indexrow, ["Land"])
            index_phone = getfirstindex(
                indexrow, ["Telefon", "Telefon1"])

            index_address_2 = getfirstindex(
                indexrow, ["Adresszeile2", "Zusatz"])

            index_notiz = getfirstindex(
                indexrow, ["Notiz"])
            index_web = getfirstindex(
                indexrow, ["Webseite", "Homepage"])

            ###

            for row in rows:
                objid = row[index_id] if index_id is not None else None

                email = row[index_email] if index_email is not None else ""
                first_name = row[index_first_name] if index_first_name is not None else ""
                last_name = row[index_last_name] if index_last_name is not None else ""
                sprache = ("de" if row[index_sprache].upper() in ["D", "DE", "DEUTSCH"] else
                           ("fr" if row[index_sprache].upper() in ["F", "FR", "FRANZÖSISCH"] else
                            ("it" if row[index_sprache].upper() in ["I", "IT", "ITALIENISCH"] else
                             ("en" if row[index_sprache].upper() in ["E", "EN", "ENGLISCH"] else
                              "de")))) if index_sprache is not None else "de"

                company = row[index_company] if index_company is not None else ""
                address_1 = row[index_strasse] if index_strasse is not None else ""
                address_2 = row[index_address_2] if index_address_2 is not None else ""
                city = row[index_city] if index_city is not None else ""
                postcode = row[index_postcode] if index_postcode is not None else ""
                country = row[index_country] if index_country is not None else ""
                phone = row[index_phone] if index_phone is not None else ""

                notiz = row[index_notiz] if index_notiz is not None else ""
                webseite = row[index_web] if index_web is not None else ""

                oldwithid = Kunde.objects.filter(pk=objid).exists()
                oldwithemail = Kunde.objects.filter(
                    email=email).exists() if email else False
                oldwithidandemail = Kunde.objects.filter(
                    pk=objid, email=email).exists()

                self.stdout.write(self.style.SUCCESS(""))

                if not oldwithid and not oldwithemail:
                    self.stdout.write(self.style.SUCCESS("Kunden erstellen:" +
                                                         "\n  ID:         " + str(objid) +
                                                         "\n  E-Mail:     " + email +
                                                         "\n  Vorname:    " + first_name +
                                                         "\n  Nachname:   " + last_name +
                                                         "\n  Firma:      " + company
                                                         ))
                    Kunde.objects.create(
                        pk=objid,

                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        company=company,
                        sprache=sprache,

                        addr_billing_first_name=first_name,
                        addr_billing_last_name=last_name,
                        addr_billing_company=company,
                        addr_billing_address_1=address_1,
                        addr_billing_address_2=address_2,
                        addr_billing_city=city,
                        #addr_billing_state = "",
                        addr_billing_postcode=postcode,
                        addr_billing_country=country,
                        addr_billing_email=email,
                        addr_billing_phone=phone,

                        addr_shipping_first_name=first_name,
                        addr_shipping_last_name=last_name,
                        addr_shipping_company=company,
                        addr_shipping_address_1=address_1,
                        addr_shipping_address_2=address_2,
                        addr_shipping_city=city,
                        #addr_shipping_state = "",
                        addr_shipping_postcode=postcode,
                        addr_shipping_country=country,

                        webseite=webseite,
                        notiz=notiz
                    )
                elif oldwithidandemail:
                    self.stdout.write(self.style.SUCCESS("Kunde existiert bereits!" +
                                                         "\n  ID:         " + str(objid) +
                                                         "\n  E-Mail:     " + email +
                                                         "\n  Vorname:    " + first_name +
                                                         "\n  Nachname:   " + last_name +
                                                         "\n  Firma:      " + company
                                                         ))
                elif oldwithemail and not oldwithid:
                    old = Kunde.objects.get(email=email)
                    self.stdout.write(self.style.SUCCESS("Kunde mit der E-Mail '"+email+"' existiert bereits, jedoch ist die ID unterschiedlich!" +
                                                         "\n  KMUHelper-Daten:" +
                                                         "\n    ID:       " + str(old.pk) +
                                                         "\n    Vorname:  " + old.first_name +
                                                         "\n    Nachname: " + old.last_name +
                                                         "\n    Firma:    " + old.addr_billing_company +
                                                         "\n  CSV Daten:" +
                                                         "\n    ID:       " + str(objid) +
                                                         "\n    Vorname:  " + first_name +
                                                         "\n    Nachname: " + last_name +
                                                         "\n    Firma:    " + company
                                                         ))
                    if input("ID aus der CSV-Datei verwenden? [y/n] ").lower() in ["y", "yes", "j", "ja", "aktualisieren"]:
                        oldid = old.pk
                        old.pk = int(objid)
                        old.save()
                        new = old
                        old = Kunde.objects.get(objid=oldid)
                        new.zusammenfuegen = old
                        new.save()
                        self.stdout.write(
                            self.style.SUCCESS("ID aktualisiert!"))
                elif not oldwithemail and oldwithid:
                    old = Kunde.objects.get(pk=objid)
                    self.stdout.write(self.style.SUCCESS("Kunde mit der ID '"+str(objid)+"' existiert bereits, jedoch ist die E-Mail unterschiedlich!" +
                                                         "\n  KMUHelper-Daten:" +
                                                         "\n    E-Mail:   " + old.email +
                                                         "\n    Vorname:  " + old.first_name +
                                                         "\n    Nachname: " + old.last_name +
                                                         "\n    Firma:    " + old.addr_billing_company +
                                                         "\n  CSV Daten:" +
                                                         "\n    E-Mail:   " + email +
                                                         "\n    Vorname:  " + first_name +
                                                         "\n    Nachname: " + last_name +
                                                         "\n    Firma:    " + company
                                                         ))
                    if input("E-Mail aus der CSV-Datei verwenden? [y/n] ").lower() in ["y", "yes", "j", "ja", "aktualisieren"]:
                        old.email = email
                        old.save()
                        self.stdout.write(
                            self.style.SUCCESS("E-Mail aktualisiert!"))
                elif oldwithemail and oldwithid:
                    self.stdout.write(self.style.SUCCESS(
                        "Irgendetwas stimmt nicht! Es besteht ein Kunde mit der E-Mail '"+email+"' aber ein Anderer mit der ID '"+str(objid)+"'."))

        except FileNotFoundError:
            raise CommandError('Datei nicht gefunden!')
