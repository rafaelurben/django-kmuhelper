from django.utils.html import strip_tags

from rich import print
from rich.progress import Progress

from woocommerce import API as WCAPI

from kmuhelper import settings, constants
from kmuhelper.modules.main.models import Produkt, Kunde, Kategorie, Bestellung, Kosten
from kmuhelper.utils import runden


PREFIX = "[deep_pink4][KMUHelper][/] -"


def log(string, *args):
    print(PREFIX, string, *args)


def preparestring(string):
    """Prepare a HTML string for import"""
    return strip_tags(string.replace("</p>", " ").replace("</strong>", " ")).replace("&#8211;", "-").replace("&#8211;", " ").replace("&#215;", "x").replace("&#8220;", '"').replace("&#8221;", '"').replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&quot;", '"').replace("&#8222;", '"').replace("  ", " ")

###############


class WooCommerce():
    """Manage connection with WooCommerce"""

    @classmethod
    def get_api(cls):
        """Create a API object from data stored in settings"""
        return WCAPI(
            url=settings.get_secret_db_setting(
                "wc-url"),
            consumer_key=settings.get_secret_db_setting(
                "wc-consumer_key"),
            consumer_secret=settings.get_secret_db_setting(
                "wc-consumer_secret")
        )

    # General methods

    @classmethod
    def product_create(cls, product, api=None):
        """Create a new product from WooCommerce data"""
        wcapi = api or cls.get_api()

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
                cls.category_update(tup[0], api=wcapi)
            newproduct.kategorien.add(tup[0])
        newproduct.save()
        log("Produkt erstellt:", str(newproduct))
        return newproduct

    @classmethod
    def product_update(cls, product, newproduct=None, api=None):
        """Update a specific product from WooCommerce"""
        wcapi = api or cls.get_api()

        if not newproduct:
            newproduct = wcapi.get(f'products/{product.woocommerceid}').json()

        try:
            product.verkaufspreis = float(newproduct["price"])
        except ValueError:
            pass
        except KeyError:
            if "code" in newproduct and newproduct["code"] == "woocommerce_rest_product_invalid_id":
                log(PREFIX +
                    " [red]Produkt existiert in WooCommerce nicht![/]")
                product.woocommerceid = 0
                product.save()
                return product

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
                cls.category_update(tup[0], api=wcapi)
            newcategories.append(tup[0])
        product.kategorien.add(*newcategories)

        product.save()
        log("Produkt aktualisiert:", str(product))
        return product

    @classmethod
    def product_import(cls, api=None):
        """Import new products from WooCommerce"""
        wcapi = api or cls.get_api()

        with Progress() as progress:
            task_prepare = progress.add_task(
                PREFIX + " [orange_red1]Produktdownload vorbereiten...", total=1)

            excludeids = str([obj.woocommerceid for obj in Produkt.objects.all().exclude(
                woocommerceid=0)])[1:-1]
            productlist = []

            progress.update(task_prepare, advance=1)
            progress.stop_task(task_prepare)

            task_download = progress.add_task(
                PREFIX + " [green]Produkte herunterladen...")

            r = wcapi.get("products?exclude=" + excludeids)
            productlist += r.json()

            progress.update(task_download, advance=1,
                            total=int(r.headers['X-WP-TotalPages']))

            for page in range(2, int(r.headers['X-WP-TotalPages']) + 1):
                productlist += wcapi.get("products?exclude=" +
                                         excludeids + "&page=" + str(page)).json()
                progress.update(task_download, advance=1)

            progress.stop_task(task_download)

            if productlist:
                task_process = progress.add_task(
                    PREFIX + " [cyan]Produkte verarbeiten...", total=len(productlist))
                for product in productlist:
                    cls.product_create(product, api=wcapi)
                    progress.update(task_process, advance=1)
                progress.stop_task(task_process)
        return len(productlist)

    @classmethod
    def product_bulk_update(cls, products, api=None):
        """Update every product in a queryset"""
        wcapi = api or cls.get_api()

        with Progress() as progress:
            task = progress.add_task(
                PREFIX + " [orange_red1]Produkte aktualisieren...", total=products.count())
            successcount = 0
            errorcount = 0
            for product in products:
                if product.woocommerceid:
                    cls.product_update(product, api=wcapi)
                    successcount += 1
                else:
                    errorcount += 1
                progress.update(task, advance=1)
            progress.stop_task(task)
        return (successcount, errorcount)

    @classmethod
    def customer_create(cls, customer):
        """Create a new customer from WooCommerce data"""
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
            lieferadresse_email="",
            lieferadresse_telefon="",
        )
        log("Kunde erstellt:", str(newcustomer))
        return newcustomer

    @classmethod
    def customer_update(cls, customer, newcustomer=None, api=None):
        """Update a specific customer from WooCommerce"""
        wcapi = api or cls.get_api()

        if not newcustomer:
            newcustomer = wcapi.get(f'customers/{customer.woocommerceid}').json()

        if "code" in newcustomer and newcustomer["code"] == "woocommerce_rest_customer_invalid_id":
            log("[red]Kunde existiert in WooCommerce nicht![/]")
            customer.woocommerceid = 0
            customer.save()
            return customer

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
        log("Kunde aktualisiert:", str(customer))
        return customer

    @classmethod
    def customer_import(cls, api=None):
        """Import new customers from WooCommerce"""
        wcapi = api or cls.get_api()

        with Progress() as progress:
            task_prepare = progress.add_task(
                PREFIX + " [orange_red1]Kundendownload vorbereiten...", total=1)

            excludeids = str([obj.woocommerceid for obj in Kunde.objects.all().exclude(
                woocommerceid=0)])[1:-1]
            customerlist = []

            progress.update(task_prepare, advance=1)
            progress.stop_task(task_prepare)

            task_download = progress.add_task(
                PREFIX + " [green]Kunden herunterladen...")

            r = wcapi.get("customers?exclude=" + excludeids)
            customerlist += r.json()

            progress.update(task_download, advance=1,
                            total=int(r.headers['X-WP-TotalPages']))

            for page in range(2, int(r.headers['X-WP-TotalPages']) + 1):
                customerlist += wcapi.get("customers?exclude=" +
                                          excludeids + "&page=" + str(page)).json()
                progress.update(task_download, advance=1)
            progress.stop_task(task_download)

            if customerlist:
                task_process = progress.add_task(
                    PREFIX + " [cyan]Kunden verarbeiten...", total=len(customerlist))
                for customer in customerlist:
                    cls.customer_create(customer)
                    progress.update(task_process, advance=1)
                progress.stop_task(task_process)
        return len(customerlist)

    @classmethod
    def customer_bulk_update(cls, customers, api=None):
        """Update every customer in a queryset"""
        wcapi = api or cls.get_api()

        with Progress() as progress:
            task = progress.add_task(
                PREFIX + " [orange_red1]Kunden aktualisieren...", total=customers.count())
            successcount = 0
            errorcount = 0
            for customer in customers:
                if customer.woocommerceid:
                    cls.customer_update(customer, api=wcapi)
                    successcount += 1
                else:
                    errorcount += 1
                progress.update(task, advance=1)
            progress.stop_task(task)
        return (successcount, errorcount)

    @classmethod
    def category_update(cls, category, newcategory=None, api=None):
        """Update a specific category from WooCommerce"""
        wcapi = api or cls.get_api()

        if not newcategory:
            newcategory = wcapi.get(f'products/categories/{category.woocommerceid}').json()

        if "code" in newcategory and newcategory["code"] == "woocommerce_rest_category_invalid_id":
            log("[red]Kategorie existiert in WooCommerce nicht![/]")
            category.woocommerceid = 0
            category.save()
            return category

        category.name = preparestring(newcategory["name"])
        category.beschrieb = preparestring(newcategory["description"])
        category.bildlink = (
            newcategory["image"]["src"]) if newcategory["image"] else ""
        if newcategory["parent"]:
            tup = Kategorie.objects.get_or_create(
                woocommerceid=newcategory["parent"])
            if tup[1]:
                cls.category_update(tup[0], api=wcapi)
            category.uebergeordnete_kategorie = tup[0]
        category.save()
        log("Kategorie aktualisiert:", str(category))
        return category

    @classmethod
    def category_import(cls, api=None):
        """Import new categories from WooCommerce"""
        wcapi = api or cls.get_api()

        with Progress() as progress:
            task_prepare = progress.add_task(
                PREFIX + " [orange_red1]Kategoriendownload vorbereiten...", total=1)

            excludeids = str([obj.woocommerceid for obj in Kategorie.objects.all().exclude(
                woocommerceid=0)])[1:-1]
            categorylist = []

            progress.update(task_prepare, advance=1)
            progress.stop_task(task_prepare)

            task_download = progress.add_task(
                PREFIX + " [green]Kategorien herunterladen...")

            r = wcapi.get("products/categories?exclude=" + excludeids)
            categorylist += r.json()

            progress.update(task_download, advance=1,
                            total=int(r.headers['X-WP-TotalPages']))

            for page in range(2, int(r.headers['X-WP-TotalPages']) + 1):
                categorylist += wcapi.get("products/categories?exclude=" +
                                          excludeids + "&page=" + str(page)).json()
                progress.update(task_download, advance=1)

            progress.stop_task(task_download)

            categorieswithparents = []

            if categorylist:
                task_process = progress.add_task(
                    PREFIX + " [cyan]Kategorien verarbeiten...", total=len(categorylist))
                for category in categorylist:
                    newcategory = Kategorie.objects.create(
                        name=preparestring(category["name"]),
                        beschrieb=preparestring(category["description"]),
                        bildlink=(category["image"]["src"]
                                  ) if category["image"] else "",
                        woocommerceid=category["id"]
                    )
                    log("Kategorie erstellt:", category["name"])
                    if category["parent"]:
                        categorieswithparents.append(
                            (newcategory, category["parent"]))
                    progress.update(task_process, advance=1)
                progress.stop_task(task_process)

            if categorieswithparents:
                task_process2 = progress.add_task(
                    PREFIX + " [cyan]Kategorieabhängigkeiten verarbeiten...", total=len(categorieswithparents))
                for tup in categorieswithparents:
                    tup[0].uebergeordnete_kategorie = Kategorie.objects.get(
                        woocommerceid=tup[1])
                    tup[0].save()
                    progress.update(task_process2, advance=1)
                progress.stop_task(task_process2)
        return len(categorylist)

    @classmethod
    def category_bulk_update(cls, categories, api=None):
        """Update every category in a queryset"""
        wcapi = api or cls.get_api()

        with Progress() as progress:
            task = progress.add_task(
                PREFIX + " [orange_red1]Kategorien aktualisieren...", total=categories.count())
            successcount = 0
            errorcount = 0
            for category in categories:
                if category.woocommerceid:
                    cls.category_update(category, api=wcapi)
                    successcount += 1
                else:
                    errorcount += 1
                progress.update(task, advance=1)
            progress.stop_task(task)
        return (successcount, errorcount)

    @classmethod
    def order_create(cls, order, api=None, sendstockwarning=True):
        """Create a new order from WooCommerce data"""
        wcapi = api or cls.get_api()

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
                kunde = cls.customer_update(kunde[0], api=wcapi)
            else:
                kunde = kunde[0]

            neworder.kunde = kunde
            neworder.lieferadresse_email = kunde.lieferadresse_email
            neworder.lieferadresse_telefon = kunde.lieferadresse_telefon

        for item in order["line_items"]:
            product = Produkt.objects.get_or_create(
                woocommerceid=int(item["product_id"]))
            if product[1]:
                product = cls.product_update(product[0], api=wcapi)
            else:
                product = product[0]

            neworder.produkte.add(
                product, 
                through_defaults={
                    "menge": int(item["quantity"]),
                    "produktpreis": runden(float(item["price"]))
                }
            )
        for item in order["shipping_lines"]:
            neworder.kosten.through.objects.create(
                bestellung=neworder,
                name=item['method_title'],
                preis=float(item["total"]),
                mwstsatz=(constants.MWST_DEFAULT if float(item["total_tax"]) > 0 else 0)
            )
        neworder.save()
        neworder.second_save()
        log("Bestellung erstellt:", str(neworder))

        if sendstockwarning:
            neworder.email_stock_warning()
        return neworder

    @classmethod
    def order_update(cls, order, neworder=None, api=None):
        """Update a specific order from WooCommerce"""
        wcapi = api or cls.get_api()

        if not neworder:
            neworder = wcapi.get(f'orders/{order.woocommerceid}').json()

        if "code" in neworder and neworder["code"] == "woocommerce_rest_order_invalid_id":
            log("[red]Bestellung existiert in WooCommerce nicht![/]")
            order.woocommerceid = 0
            order.save()
            return order

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
        log("Bestellung aktualisiert: ", str(order))
        return order

    @classmethod
    def order_import(cls, api=None):
        """Import new orders from WooCommerce"""
        wcapi = api or cls.get_api()

        with Progress() as progress:
            task_prepare = progress.add_task(
                PREFIX + " [orange_red1]Bestellungsdownload vorbereiten...", total=1)

            excludeids = str([obj.woocommerceid for obj in Bestellung.objects.all().exclude(
                woocommerceid=0)])[1:-1]
            orderlist = []

            progress.update(task_prepare, advance=1)
            progress.stop_task(task_prepare)

            task_download = progress.add_task(
                PREFIX + " [green]Bestellungen herunterladen...")

            r = wcapi.get("orders?exclude=" + excludeids)
            orderlist += r.json()

            progress.update(task_download, advance=1,
                            total=int(r.headers['X-WP-TotalPages']))

            for page in range(2, int(r.headers['X-WP-TotalPages']) + 1):
                orderlist += wcapi.get("orders?exclude=" +
                                       excludeids + "&page=" + str(page)).json()
                progress.update(task_download, advance=1)
            progress.stop_task(task_download)

            if orderlist:
                task_process = progress.add_task(
                    PREFIX + " [cyan]Bestellungen verarbeiten...", total=len(orderlist))
                for order in orderlist:
                    cls.order_create(order, api=wcapi, sendstockwarning=False)
                    progress.update(task_process, advance=1)
                progress.stop_task(task_process)
        return len(orderlist)

    @classmethod
    def order_bulk_update(cls, orders, api=None):
        """Update every order in a queryset"""
        wcapi = api or cls.get_api()

        with Progress() as progress:
            task = progress.add_task(
                PREFIX + " [orange_red1]Bestellungen aktualisieren...", total=orders.count())
            successcount = 0
            errorcount = 0
            for order in orders:
                if order.woocommerceid:
                    cls.order_update(order, api=wcapi)
                    successcount += 1
                else:
                    errorcount += 1
                progress.update(task, advance=1)
            progress.stop_task(task)
        return (successcount, errorcount)
