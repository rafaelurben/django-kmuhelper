from django.utils.html import strip_tags

from rich import print
from rich.progress import Progress

from woocommerce import API as WCAPI

from kmuhelper import settings, constants
from kmuhelper.modules.main.models import Produkt, Kunde, Produktkategorie, Bestellung, Kosten
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
            tup = Produktkategorie.objects.get_or_create(woocommerceid=category["id"])
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
            tup = Produktkategorie.objects.get_or_create(woocommerceid=category["id"])
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
            first_name=customer["first_name"],
            last_name=customer["last_name"],
            company=customer["billing"]["company"],
            username=customer["username"],
            avatar_url=customer["avatar_url"],

            addr_billing_first_name=customer["billing"]["first_name"],
            addr_billing_last_name=customer["billing"]["last_name"],
            addr_billing_company=customer["billing"]["company"],
            addr_billing_address_1=customer["billing"]["address_1"],
            addr_billing_address_2=customer["billing"]["address_2"],
            addr_billing_city=customer["billing"]["city"],
            addr_billing_state=customer["billing"]["state"],
            addr_billing_postcode=customer["billing"]["postcode"],
            addr_billing_country=customer["billing"]["country"],
            addr_billing_email=customer["billing"]["email"],
            addr_billing_phone=customer["billing"]["phone"],

            addr_shipping_first_name=customer["shipping"]["first_name"],
            addr_shipping_last_name=customer["shipping"]["last_name"],
            addr_shipping_company=customer["shipping"]["company"],
            addr_shipping_address_1=customer["shipping"]["address_1"],
            addr_shipping_address_2=customer["shipping"]["address_2"],
            addr_shipping_city=customer["shipping"]["city"],
            addr_shipping_state=customer["shipping"]["state"],
            addr_shipping_postcode=customer["shipping"]["postcode"],
            addr_shipping_country=customer["shipping"]["country"],
            addr_shipping_email="",
            addr_shipping_phone="",
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
        customer.first_name = newcustomer["first_name"]
        customer.last_name = newcustomer["last_name"]
        customer.company = newcustomer["billing"]["company"] if newcustomer["billing"]["company"] else customer.company
        customer.username = newcustomer["username"]
        customer.avatar_url = newcustomer["avatar_url"]

        customer.addr_billing_first_name = newcustomer["billing"]["first_name"]
        customer.addr_billing_last_name = newcustomer["billing"]["last_name"]
        customer.addr_billing_company = newcustomer["billing"]["company"]
        customer.addr_billing_address_1 = newcustomer["billing"]["address_1"]
        customer.addr_billing_address_2 = newcustomer["billing"]["address_2"]
        customer.addr_billing_city = newcustomer["billing"]["city"]
        customer.addr_billing_state = newcustomer["billing"]["state"]
        customer.addr_billing_postcode = newcustomer["billing"]["postcode"]
        customer.addr_billing_country = newcustomer["billing"]["country"]
        customer.addr_billing_email = newcustomer["billing"]["email"]
        customer.addr_billing_phone = newcustomer["billing"]["phone"]

        customer.addr_shipping_first_name = newcustomer["shipping"]["first_name"]
        customer.addr_shipping_last_name = newcustomer["shipping"]["last_name"]
        customer.addr_shipping_company = newcustomer["shipping"]["company"]
        customer.addr_shipping_address_1 = newcustomer["shipping"]["address_1"]
        customer.addr_shipping_address_2 = newcustomer["shipping"]["address_2"]
        customer.addr_shipping_city = newcustomer["shipping"]["city"]
        customer.addr_shipping_state = newcustomer["shipping"]["state"]
        customer.addr_shipping_postcode = newcustomer["shipping"]["postcode"]
        customer.addr_shipping_country = newcustomer["shipping"]["country"]
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
            tup = Produktkategorie.objects.get_or_create(
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

            excludeids = str([obj.woocommerceid for obj in Produktkategorie.objects.all().exclude(
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
                    newcategory = Produktkategorie.objects.create(
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
                    tup[0].uebergeordnete_kategorie = Produktkategorie.objects.get(
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
            is_shipped=(True if order["status"] == "completed" else False),

            ausgelagert=(True if order["status"] == "completed" else False),

            payment_method=order["payment_method"],
            is_paid=(True if order["date_paid"] else False),

            customer_note=order["customer_note"],

            order_key=order["order_key"],

            addr_billing_first_name=order["billing"]["first_name"],
            addr_billing_last_name=order["billing"]["last_name"],
            addr_billing_company=order["billing"]["company"],
            addr_billing_address_1=order["billing"]["address_1"],
            addr_billing_address_2=order["billing"]["address_2"],
            addr_billing_city=order["billing"]["city"],
            addr_billing_state=order["billing"]["state"],
            addr_billing_postcode=order["billing"]["postcode"],
            addr_billing_country=order["billing"]["country"],
            addr_billing_email=order["billing"]["email"],
            addr_billing_phone=order["billing"]["phone"],

            addr_shipping_first_name=order["shipping"]["first_name"],
            addr_shipping_last_name=order["shipping"]["last_name"],
            addr_shipping_company=order["shipping"]["company"],
            addr_shipping_address_1=order["shipping"]["address_1"],
            addr_shipping_address_2=order["shipping"]["address_2"],
            addr_shipping_city=order["shipping"]["city"],
            addr_shipping_state=order["shipping"]["state"],
            addr_shipping_postcode=order["shipping"]["postcode"],
            addr_shipping_country=order["shipping"]["country"]
        )
        neworder.date = order["date_created_gmt"] + "+00:00"
        if order["customer_id"]:
            kunde = Kunde.objects.get_or_create(
                woocommerceid=int(order["customer_id"]))
            if kunde[1]:
                kunde = cls.customer_update(kunde[0], api=wcapi)
            else:
                kunde = kunde[0]

            neworder.kunde = kunde
            neworder.addr_shipping_email = kunde.addr_shipping_email
            neworder.addr_shipping_phone = kunde.addr_shipping_phone

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
            order.is_paid = True
        order.status = neworder["status"]
        order.customer_note = neworder["customer_note"]

        order.addr_billing_first_name = neworder["billing"]["first_name"]
        order.addr_billing_last_name = neworder["billing"]["last_name"]
        order.addr_billing_company = neworder["billing"]["company"]
        order.addr_billing_address_1 = neworder["billing"]["address_1"]
        order.addr_billing_address_2 = neworder["billing"]["address_2"]
        order.addr_billing_city = neworder["billing"]["city"]
        order.addr_billing_state = neworder["billing"]["state"]
        order.addr_billing_postcode = neworder["billing"]["postcode"]
        order.addr_billing_country = neworder["billing"]["country"]
        order.addr_billing_email = neworder["billing"]["email"]
        order.addr_billing_phone = neworder["billing"]["phone"]

        order.addr_shipping_first_name = neworder["shipping"]["first_name"]
        order.addr_shipping_last_name = neworder["shipping"]["last_name"]
        order.addr_shipping_company = neworder["shipping"]["company"]
        order.addr_shipping_address_1 = neworder["shipping"]["address_1"]
        order.addr_shipping_address_2 = neworder["shipping"]["address_2"]
        order.addr_shipping_city = neworder["shipping"]["city"]
        order.addr_shipping_state = neworder["shipping"]["state"]
        order.addr_shipping_postcode = neworder["shipping"]["postcode"]
        order.addr_shipping_country = neworder["shipping"]["country"]
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
