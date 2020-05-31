from django.core.management.base import BaseCommand, CommandError
from kmuhelper.models import Kunde
from kmuhelper.utils import getfirstindex

import csv

class Command(BaseCommand):
    help = 'Imports customers from a .csv file.'

    def add_arguments(self, parser):
        parser.add_argument('filepath', help="Absolute filepath to the .csv file", type=str)

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Import gestartet!"))
        try:
            with open(options["filepath"], newline='', encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

            indexrow = rows.pop(0)

            ###
            index_id = getfirstindex(indexrow, ["Nummer", "ID"])

            index_email = getfirstindex(indexrow, ["Email", "E-Mail","EMail","EMAIL"])
            index_vorname = getfirstindex(indexrow, ["Vorname"])
            index_nachname = getfirstindex(indexrow, ["Name", "Nachname"])
            index_sprache = getfirstindex(indexrow, ["Sprache", "SPRACHE"])

            index_firma = getfirstindex(indexrow, ["Firma"])
            index_strasse = getfirstindex(indexrow, ["Strasse"])
            index_ort = getfirstindex(indexrow, ["Ort"])
            index_plz = getfirstindex(indexrow, ["PLZ","Plz","Postleitzahl"])
            index_land = getfirstindex(indexrow, ["Land"])
            index_telefon = getfirstindex(indexrow, ["Telefon", "Telefon1"])

            index_adresszeile2 = getfirstindex(indexrow, ["Adresszeile2", "Zusatz"])

            index_notiz = getfirstindex(indexrow, ["Notiz"])
            index_web = getfirstindex(indexrow, ["Webseite", "Homepage"])
            ###
            for row in rows:
                id = row[index_id] if index_id is not None else None

                email = row[index_email] if index_email is not None else ""
                vorname = row[index_vorname] if index_vorname is not None else ""
                nachname = row[index_nachname] if index_nachname is not None else ""
                sprache =   ("de" if row[index_sprache].upper() in ["D","DE","DEUTSCH"] else
                            ("fr" if row[index_sprache].upper() in ["F","FR","FRANZÖSISCH"] else
                            ("it" if row[index_sprache].upper() in ["I","IT","ITALIENISCH"] else
                            ("en" if row[index_sprache].upper() in ["E","EN","ENGLISCH"] else
                            "de")))) if index_sprache is not None else "de"

                firma = row[index_firma] if index_firma is not None else ""
                adresszeile1 = row[index_strasse] if index_strasse is not None else ""
                adresszeile2 = row[index_adresszeile2] if index_adresszeile2 is not None else ""
                ort = row[index_ort] if index_ort is not None else ""
                plz = row[index_plz] if index_plz is not None else ""
                land = row[index_land] if index_land is not None else ""
                telefon = row[index_telefon] if index_telefon is not None else ""

                notiz = row[index_notiz] if index_notiz is not None else ""
                webseite = row[index_web] if index_web is not None else ""

                oldwithid = Kunde.objects.filter(id=id).exists()
                oldwithemail = Kunde.objects.filter(email=email).exists() if email else False
                oldwithidandemail = Kunde.objects.filter(id=id, email=email).exists()

                self.stdout.write(self.style.SUCCESS(""))

                if not oldwithid and not oldwithemail:
                    self.stdout.write(self.style.SUCCESS("Kunden erstellen:"+
                        "\n  ID:         "+ str(id)+
                        "\n  E-Mail:     "+ email+
                        "\n  Vorname:    "+ vorname+
                        "\n  Nachname:   "+ nachname+
                        "\n  Firma:      "+ firma
                    ))
                    Kunde.objects.create(
                        id=id,

                        email=email,
                        vorname=vorname,
                        nachname=nachname,
                        firma=firma,
                        sprache=sprache,

                        rechnungsadresse_vorname = vorname,
                        rechnungsadresse_nachname = nachname,
                        rechnungsadresse_firma = firma,
                        rechnungsadresse_adresszeile1 = adresszeile1,
                        rechnungsadresse_adresszeile2 = adresszeile2,
                        rechnungsadresse_ort = ort,
                        #rechnungsadresse_kanton = "",
                        rechnungsadresse_plz = plz,
                        rechnungsadresse_land = land,
                        rechnungsadresse_email = email,
                        rechnungsadresse_telefon = telefon,

                        lieferadresse_vorname = vorname,
                        lieferadresse_nachname = nachname,
                        lieferadresse_firma = firma,
                        lieferadresse_adresszeile1 = adresszeile1,
                        lieferadresse_adresszeile2 = adresszeile2,
                        lieferadresse_ort = ort,
                        #lieferadresse_kanton = "",
                        lieferadresse_plz = plz,
                        lieferadresse_land = land,

                        webseite = webseite,
                        notiz = notiz
                    )
                elif oldwithidandemail:
                    self.stdout.write(self.style.SUCCESS("Kunde existiert bereits!"+
                        "\n  ID:         "+ str(id)+
                        "\n  E-Mail:     "+ email+
                        "\n  Vorname:    "+ vorname+
                        "\n  Nachname:   "+ nachname+
                        "\n  Firma:      "+ firma
                    ))
                elif oldwithemail and not oldwithid:
                    old = Kunde.objects.get(email=email)
                    self.stdout.write(self.style.SUCCESS("Kunde mit der E-Mail '"+email+"' existiert bereits, jedoch ist die ID unterschiedlich!"+
                        "\n  KMUHelper-Daten:"+
                        "\n    ID:       "+ str(old.id)+
                        "\n    Vorname:  "+ old.vorname+
                        "\n    Nachname: "+ old.nachname+
                        "\n    Firma:    "+ old.rechnungsadresse_firma+
                        "\n  CSV Daten:"+
                        "\n    ID:       "+ str(id)+
                        "\n    Vorname:  "+ vorname+
                        "\n    Nachname: "+ nachname+
                        "\n    Firma:    "+ firma
                    ))
                    if input("ID aus der CSV-Datei verwenden? [y/n] ").lower() in ["y","yes","j","ja","aktualisieren"]:
                        oldid = old.id
                        old.id = int(id)
                        old.save()
                        new = old
                        old = Kunde.objects.get(id=oldid)
                        new.zusammenfuegen = old
                        new.save()
                        self.stdout.write(self.style.SUCCESS("ID aktualisiert!"))
                elif not oldwithemail and oldwithid:
                    old = Kunde.objects.get(id=id)
                    self.stdout.write(self.style.SUCCESS("Kunde mit der ID '"+str(id)+"' existiert bereits, jedoch ist die E-Mail unterschiedlich!"+
                        "\n  KMUHelper-Daten:"+
                        "\n    E-Mail:   "+ old.email+
                        "\n    Vorname:  "+ old.vorname+
                        "\n    Nachname: "+ old.nachname+
                        "\n    Firma:    "+ old.rechnungsadresse_firma+
                        "\n  CSV Daten:"+
                        "\n    E-Mail:   "+ email+
                        "\n    Vorname:  "+ vorname+
                        "\n    Nachname: "+ nachname+
                        "\n    Firma:    "+ firma
                    ))
                    if input("E-Mail aus der CSV-Datei verwenden? [y/n] ").lower() in ["y","yes","j","ja","aktualisieren"]:
                        old.email = email
                        old.save()
                        self.stdout.write(self.style.SUCCESS("E-Mail aktualisiert!"))
                elif oldwithemail and oldwithid:
                    self.stdout.write(self.style.SUCCESS("Irgendetwas stimmt nicht! Es besteht ein Kunde mit der E-Mail '"+email+"' aber ein Anderer mit der ID '"+str(id)+"'."))

        except FileNotFoundError:
            raise CommandError('Datei nicht gefunden!')
