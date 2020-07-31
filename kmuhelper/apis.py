from woocommerce import API as WCAPI
from .models import Einstellung, Geheime_Einstellung, Produkt, Kunde, Kategorie, Bestellung, Bestellungsposten, Kosten
from .utils import runden
from django.utils.html import strip_tags
import pytz

###############


def preparestring(string):
    return strip_tags(string.replace("</p>", " ").replace("</strong>", " ")).replace("&#8211;", "-").replace("&#8211;", " ").replace("&#215;", "x").replace("&#8220;", '"').replace("&#8221;", '"').replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&quot;", '"').replace("&#8222;", '"').replace("  ", " ")

###############


class WooCommerce():
    @classmethod
    def get_api(self):
        return WCAPI(
            url=Geheime_Einstellung.objects.get(id="wc-url").get_inhalt(),
            consumer_key=Geheime_Einstellung.objects.get(
                id="wc-consumer_key").get_inhalt(),
            consumer_secret=Geheime_Einstellung.objects.get(
                id="wc-consumer_secret").get_inhalt()
        )

    @classmethod
    def product_create(self, product):
        try:
            verkaufspreis = float(product["price"])
        except ValueError:
            verkaufspreis = 0.0

        newproduct = Produkt.objects.create(
            woocommerceid=product["id"],
            artikelnummer=product["sku"],
            name=preparestring(product["name"]),
            kurzbeschrieb=preparestring(product["short_description"]),
            beschrieb=preparestring(product["description"]),
            verkaufspreis=verkaufspreis,
            bildlink=(product["images"][0]["src"]) if len(
                product["images"]) > 0 else "",
            aktion_von=(product["date_on_sale_from_gmt"] +
                        "+00:00" if product["date_on_sale_from"] else None),
            aktion_bis=(product["date_on_sale_to_gmt"] +
                        "+00:00" if product["date_on_sale_to"] else None),
            aktion_preis=(product["sale_price"]
                          if product["sale_price"] else None)
        )
        if product["manage_stock"]:
            newproduct.lagerbestand = product["stock_quantity"]
        for category in product["categories"]:
            tup = Kategorie.objects.get_or_create(woocommerceid=category["id"])
            if tup[1]:
                self.category_update(tup[0])
            newproduct.kategorien.add(tup[0])
        newproduct.save()
        print("[KMUHelper] - Produkt erstellt: " + str(newproduct))
        return newproduct

    @classmethod
    def product_update(self, product, newproduct=None):
        if not newproduct:
            newproduct = self.get_api().get("products/" + str(product.woocommerceid)).json()

        try:
            product.verkaufspreis = float(newproduct["price"])
        except ValueError:
            pass

        product.artikelnummer = newproduct["sku"]
        product.name = preparestring(newproduct["name"])
        product.kurzbeschrieb = preparestring(newproduct["short_description"])
        product.beschrieb = preparestring(newproduct["description"])
        product.bildlink = (newproduct["images"][0]["src"]) if len(
            newproduct["images"]) > 0 else ""
        if newproduct["date_on_sale_from_gmt"]:
            product.aktion_von = newproduct["date_on_sale_from_gmt"] + "+00:00"
        if newproduct["date_on_sale_to_gmt"]:
            product.aktion_bis = newproduct["date_on_sale_to_gmt"] + "+00:00"
        if newproduct["sale_price"]:
            product.aktion_preis = newproduct["sale_price"]

        product.kategorien.clear()
        newcategories = []
        for category in newproduct["categories"]:
            tup = Kategorie.objects.get_or_create(woocommerceid=category["id"])
            if tup[1]:
                self.category_update(tup[0])
            newcategories.append(tup[0])
        product.kategorien.add(*newcategories)

        product.save()
        print("[KMUHelper] - Produkt aktualisiert: " + str(product))
        return product

    @classmethod
    def product_import(self):
        excludeids = str([obj.woocommerceid for obj in Produkt.objects.all().exclude(
            woocommerceid=0)])[1:-1]
        wcapi = self.get_api()
        print("[KMUHelper] - Produkte von WooCommerce herunterladen...")
        productlist = []
        r = wcapi.get("products?exclude=" + excludeids)
        productlist += r.json()
        for page in range(2, int(r.headers['X-WP-TotalPages']) + 1):
            productlist += wcapi.get("products?exclude=" +
                                     excludeids + "&page=" + str(page)).json()
        print("[KMUHelper] - Produkte von WooCommerce heruntergeladen: " +
              str(len(productlist)))
        print("[KMUHelper] - Produkte von WooCommerce importieren...")
        for product in productlist:
            self.product_create(product)
        print("[KMUHelper] - Produkte von WooCommerce importiert: " +
              str(len(productlist)))
        return len(productlist)

    @classmethod
    def product_bulk_update(self, products):
        print("[KMUHelper] - Produkte von WooCommerce aktualisieren: " +
              str(len(products)))
        successcount = 0
        errorcount = 0
        for product in products:
            if product.woocommerceid:
                self.product_update(product)
                successcount += 1
            else:
                errorcount += 1
        print("[KMUHelper] - Produkte von WooCommerce aktualisiert: " +
              str(successcount))
        return (successcount, errorcount)

    @classmethod
    def customer_create(self, customer):
        newcustomer = Kunde.objects.create(
            woocommerceid=customer["id"],

            email=customer["email"],
            vorname=customer["first_name"],
            nachname=customer["last_name"],
            firma=customer["billing"]["company"],
            benutzername=customer["username"],
            avatar_url=customer["avatar_url"],

            rechnungsadresse_vorname=customer["billing"]["first_name"],
            rechnungsadresse_nachname=customer["billing"]["last_name"],
            rechnungsadresse_firma=customer["billing"]["company"],
            rechnungsadresse_adresszeile1=customer["billing"]["address_1"],
            rechnungsadresse_adresszeile2=customer["billing"]["address_2"],
            rechnungsadresse_ort=customer["billing"]["city"],
            rechnungsadresse_kanton=customer["billing"]["state"],
            rechnungsadresse_plz=customer["billing"]["postcode"],
            rechnungsadresse_land=customer["billing"]["country"],
            rechnungsadresse_email=customer["billing"]["email"],
            rechnungsadresse_telefon=customer["billing"]["phone"],

            lieferadresse_vorname=customer["shipping"]["first_name"],
            lieferadresse_nachname=customer["shipping"]["last_name"],
            lieferadresse_firma=customer["shipping"]["company"],
            lieferadresse_adresszeile1=customer["shipping"]["address_1"],
            lieferadresse_adresszeile2=customer["shipping"]["address_2"],
            lieferadresse_ort=customer["shipping"]["city"],
            lieferadresse_kanton=customer["shipping"]["state"],
            lieferadresse_plz=customer["shipping"]["postcode"],
            lieferadresse_land=customer["shipping"]["country"],

            registrierungsemail_gesendet=True
        )
        print("[KMUHelper] - Kunde erstellt: " + str(newcustomer))
        return newcustomer

    @classmethod
    def customer_update(self, customer, newcustomer=None):
        if not newcustomer:
            newcustomer = self.get_api().get("customers/" + str(customer.woocommerceid)).json()
        customer.email = newcustomer["email"]
        customer.vorname = newcustomer["first_name"]
        customer.nachname = newcustomer["last_name"]
        customer.firma = newcustomer["billing"]["company"] if newcustomer["billing"]["company"] else customer.firma
        customer.benutzername = newcustomer["username"]
        customer.avatar_url = newcustomer["avatar_url"]

        customer.rechnungsadresse_vorname = newcustomer["billing"]["first_name"]
        customer.rechnungsadresse_nachname = newcustomer["billing"]["last_name"]
        customer.rechnungsadresse_firma = newcustomer["billing"]["company"]
        customer.rechnungsadresse_adresszeile1 = newcustomer["billing"]["address_1"]
        customer.rechnungsadresse_adresszeile2 = newcustomer["billing"]["address_2"]
        customer.rechnungsadresse_ort = newcustomer["billing"]["city"]
        customer.rechnungsadresse_kanton = newcustomer["billing"]["state"]
        customer.rechnungsadresse_plz = newcustomer["billing"]["postcode"]
        customer.rechnungsadresse_land = newcustomer["billing"]["country"]
        customer.rechnungsadresse_email = newcustomer["billing"]["email"]
        customer.rechnungsadresse_telefon = newcustomer["billing"]["phone"]

        customer.lieferadresse_vorname = newcustomer["shipping"]["first_name"]
        customer.lieferadresse_nachname = newcustomer["shipping"]["last_name"]
        customer.lieferadresse_firma = newcustomer["shipping"]["company"]
        customer.lieferadresse_adresszeile1 = newcustomer["shipping"]["address_1"]
        customer.lieferadresse_adresszeile2 = newcustomer["shipping"]["address_2"]
        customer.lieferadresse_ort = newcustomer["shipping"]["city"]
        customer.lieferadresse_kanton = newcustomer["shipping"]["state"]
        customer.lieferadresse_plz = newcustomer["shipping"]["postcode"]
        customer.lieferadresse_land = newcustomer["shipping"]["country"]
        customer.save()
        print("[KMUHelper] - Kunde aktualisiert: " + str(customer))
        return customer

    @classmethod
    def customer_import(self):
        excludeids = str(
            [obj.woocommerceid for obj in Kunde.objects.all().exclude(woocommerceid=0)])[1:-1]
        wcapi = self.get_api()
        print("[KMUHelper] - Kunden von WooCommerce herunterladen...")
        customerlist = []
        r = wcapi.get("customers?exclude=" + excludeids)
        customerlist += r.json()
        for page in range(2, int(r.headers['X-WP-TotalPages']) + 1):
            customerlist += wcapi.get("customers?exclude=" +
                                      excludeids + "&page=" + str(page)).json()
        print("[KMUHelper] - Kunden von WooCommerce heruntergeladen: " +
              str(len(customerlist)))
        print("[KMUHelper] - Kunden von WooCommerce importieren...")
        for customer in customerlist:
            self.customer_create(customer)
        print("[KMUHelper] - Kunden von WooCommerce importiert: " +
              str(len(customerlist)))
        return len(customerlist)

    @classmethod
    def customer_bulk_update(self, customers):
        print("[KMUHelper] - Kunden von WooCommerce aktualisieren: " +
              str(len(customers)))
        successcount = 0
        errorcount = 0
        for customer in customers:
            if customer.woocommerceid:
                self.customer_update(customer)
                successcount += 1
            else:
                errorcount += 1
        print("[KMUHelper] - Kunden von WooCommerce aktualisiert: " +
              str(successcount))
        return (successcount, errorcount)

    @classmethod
    def category_update(self, category, newcategory=None):
        if not newcategory:
            newcategory = self.get_api().get("products/categories/" +
                                             str(category.woocommerceid)).json()
        category.name = preparestring(newcategory["name"])
        category.beschrieb = preparestring(newcategory["description"])
        category.bildlink = (
            newcategory["image"]["src"]) if newcategory["image"] else ""
        if newcategory["parent"]:
            tup = Kategorie.objects.get_or_create(
                woocommerceid=newcategory["parent"])
            if tup[1]:
                self.category_update(tup[0])
            category.uebergeordnete_kategorie = tup[0]
        category.save()
        print("[KMUHelper] - Kategorie aktualisiert: " + str(category))
        return category

    @classmethod
    def category_import(self):
        excludeids = str([obj.woocommerceid for obj in Kategorie.objects.all().exclude(
            woocommerceid=0)])[1:-1]
        wcapi = self.get_api()
        print("[KMUHelper] - Kategorien von WooCommerce herunterladen...")
        categorylist = []
        r = wcapi.get("products/categories?exclude=" + excludeids)
        categorylist += r.json()
        for page in range(2, int(r.headers['X-WP-TotalPages']) + 1):
            categorylist += wcapi.get("products/categories?exclude=" +
                                      excludeids + "&page=" + str(page)).json()
        print("[KMUHelper] - Kategorien von WooCommerce heruntergeladen: " +
              str(len(categorylist)))
        print("[KMUHelper] - Kategorien von WooCommerce importieren...")
        categorieswithparents = []
        for category in categorylist:
            newcategory = Kategorie.objects.create(
                name=preparestring(category["name"]),
                beschrieb=preparestring(category["description"]),
                bildlink=(category["image"]["src"]
                          ) if category["image"] else "",
                woocommerceid=category["id"]
            )
            print("[KMUHelper] - Kategorie erstellt: " + category["name"])
            if category["parent"]:
                categorieswithparents.append((newcategory, category["parent"]))
        for tup in categorieswithparents:
            tup[0].uebergeordnete_kategorie = Kategorie.objects.get(
                woocommerceid=tup[1])
            tup[0].save()
        print("[KMUHelper] - Kategorien von WooCommerce importiert: " +
              str(len(categorylist)))
        return len(categorylist)

    @classmethod
    def category_bulk_update(self, categories):
        print("[KMUHelper] - Kategorien von WooCommerce aktualisieren: " +
              str(len(categories)))
        successcount = 0
        errorcount = 0
        for category in categories:
            if category.woocommerceid:
                self.category_update(category)
                successcount += 1
            else:
                errorcount += 1
        print(
            "[KMUHelper] - Kategorien von WooCommerce aktualisiert: " + str(successcount))
        return (successcount, errorcount)

    @classmethod
    def order_create(self, order):
        neworder = Bestellung.objects.create(
            woocommerceid=order["id"],

            status=order["status"],
            versendet=(True if order["status"] == "completed" else False),

            ausgelagert=(True if order["status"] == "completed" else False),

            zahlungsmethode=order["payment_method"],
            bezahlt=(True if order["date_paid"] else False),

            kundennotiz=order["customer_note"],

            order_key=order["order_key"],

            rechnungsadresse_vorname=order["billing"]["first_name"],
            rechnungsadresse_nachname=order["billing"]["last_name"],
            rechnungsadresse_firma=order["billing"]["company"],
            rechnungsadresse_adresszeile1=order["billing"]["address_1"],
            rechnungsadresse_adresszeile2=order["billing"]["address_2"],
            rechnungsadresse_ort=order["billing"]["city"],
            rechnungsadresse_kanton=order["billing"]["state"],
            rechnungsadresse_plz=order["billing"]["postcode"],
            rechnungsadresse_land=order["billing"]["country"],
            rechnungsadresse_email=order["billing"]["email"],
            rechnungsadresse_telefon=order["billing"]["phone"],

            lieferadresse_vorname=order["shipping"]["first_name"],
            lieferadresse_nachname=order["shipping"]["last_name"],
            lieferadresse_firma=order["shipping"]["company"],
            lieferadresse_adresszeile1=order["shipping"]["address_1"],
            lieferadresse_adresszeile2=order["shipping"]["address_2"],
            lieferadresse_ort=order["shipping"]["city"],
            lieferadresse_kanton=order["shipping"]["state"],
            lieferadresse_plz=order["shipping"]["postcode"],
            lieferadresse_land=order["shipping"]["country"]
        )
        neworder.datum = order["date_created_gmt"] + "+00:00"
        if order["customer_id"]:
            kunde = Kunde.objects.get_or_create(
                woocommerceid=int(order["customer_id"]))
            if kunde[1]:
                kunde = self.customer_update(kunde[0])
            else:
                kunde = kunde[0]
        else:
            kunde = None
        neworder.kunde = kunde
        for item in order["line_items"]:
            product = Produkt.objects.get_or_create(
                woocommerceid=int(item["product_id"]))
            if product[1]:
                product = self.product_update(product[0])
            else:
                product = product[0]
            neworder.produkte.add(product, through_defaults={"menge": int(
                item["quantity"]), "produktpreis": runden(float(item["price"]))})
        for item in order["shipping_lines"]:
            neworder.kosten.add(Kosten.objects.get_or_create(name=item["method_title"], preis=float(
                item["total"]), mwstsatz=(7.7 if float(item["total_tax"]) > 0 else 0))[0])
        neworder.save()
        print("[KMUHelper] - Bestellung erstellt: " + str(neworder.pk))
        return neworder

    @classmethod
    def order_update(self, order, neworder=None):
        if not neworder:
            neworder = self.get_api().get("orders/" + str(order.woocommerceid)).json()
        if neworder["date_paid"]:
            order.bezahlt = True
        order.status = neworder["status"]
        order.kundennotiz = neworder["customer_note"]

        order.rechnungsadresse_vorname = neworder["billing"]["first_name"]
        order.rechnungsadresse_nachname = neworder["billing"]["last_name"]
        order.rechnungsadresse_firma = neworder["billing"]["company"]
        order.rechnungsadresse_adresszeile1 = neworder["billing"]["address_1"]
        order.rechnungsadresse_adresszeile2 = neworder["billing"]["address_2"]
        order.rechnungsadresse_ort = neworder["billing"]["city"]
        order.rechnungsadresse_kanton = neworder["billing"]["state"]
        order.rechnungsadresse_plz = neworder["billing"]["postcode"]
        order.rechnungsadresse_land = neworder["billing"]["country"]
        order.rechnungsadresse_email = neworder["billing"]["email"]
        order.rechnungsadresse_telefon = neworder["billing"]["phone"]

        order.lieferadresse_vorname = neworder["shipping"]["first_name"]
        order.lieferadresse_nachname = neworder["shipping"]["last_name"]
        order.lieferadresse_firma = neworder["shipping"]["company"]
        order.lieferadresse_adresszeile1 = neworder["shipping"]["address_1"]
        order.lieferadresse_adresszeile2 = neworder["shipping"]["address_2"]
        order.lieferadresse_ort = neworder["shipping"]["city"]
        order.lieferadresse_kanton = neworder["shipping"]["state"]
        order.lieferadresse_plz = neworder["shipping"]["postcode"]
        order.lieferadresse_land = neworder["shipping"]["country"]
        order.save()
        print("[KMUHelper] - Bestellung aktualisiert: " + str(order))
        return order

    @classmethod
    def order_import(self):
        excludeids = str([obj.woocommerceid for obj in Bestellung.objects.all(
        ).exclude(woocommerceid=0)])[1:-1]
        wcapi = self.get_api()
        print("[KMUHelper] - Bestellungen von WooCommerce herunterladen...")
        orderlist = []
        r = wcapi.get("orders?exclude=" + excludeids)
        orderlist += r.json()
        for page in range(2, int(r.headers['X-WP-TotalPages']) + 1):
            orderlist += wcapi.get("orders?exclude=" +
                                   excludeids + "&page=" + str(page)).json()
        print("[KMUHelper] - Bestellungen von WooCommerce heruntergeladen: " +
              str(len(orderlist)))
        print("[KMUHelper] - Bestellungen von WooCommerce importieren...")
        for order in orderlist:
            self.order_create(order)
        print("[KMUHelper] - Bestellungen von WooCommerce importiert: " +
              str(len(orderlist)))
        return len(orderlist)

    @classmethod
    def order_bulk_update(self, orders):
        print("[KMUHelper] - Kunden von WooCommerce aktualisieren: " +
              str(len(orders)))
        successcount = 0
        errorcount = 0
        for order in orders:
            if order.woocommerceid:
                self.order_update(order)
                successcount += 1
            else:
                errorcount += 1
        print("[KMUHelper] - Kunden von WooCommerce aktualisiert: " +
              str(successcount))
        return (successcount, errorcount)
