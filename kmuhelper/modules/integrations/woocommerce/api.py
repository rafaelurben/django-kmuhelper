from django.utils.html import strip_tags
from rich import print
from rich.progress import Progress
from woocommerce import API as WCAPI

from kmuhelper import settings, constants
from kmuhelper.modules.main.models import Product, Customer, ProductCategory, Order
from kmuhelper.utils import runden

PREFIX = "[deep_pink4][KMUHelper WooCommerce][/] -"


def log(string, *args):
    print(PREFIX, string, *args)


def preparestring(string):
    """Prepare a HTML string for import"""
    return (
        strip_tags(string.replace("</p>", " ").replace("</strong>", " "))
        .replace("&#8211;", "-")
        .replace("&#8211;", " ")
        .replace("&#215;", "x")
        .replace("&#8220;", '"')
        .replace("&#8221;", '"')
        .replace("&nbsp;", " ")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#8222;", '"')
        .replace("  ", " ")
    )


###############


class WooCommerce:
    """Manage connection with WooCommerce"""

    @classmethod
    def get_api(cls):
        """Create a API object from data stored in settings"""
        return WCAPI(
            url=settings.get_secret_db_setting("wc-url"),
            consumer_key=settings.get_secret_db_setting("wc-consumer_key"),
            consumer_secret=settings.get_secret_db_setting("wc-consumer_secret"),
        )

    # System status

    @classmethod
    def get_system_status(cls):
        """Get system status from WooCommerce"""
        wcapi = cls.get_api()
        try:
            request = wcapi.get("system_status")
            request.raise_for_status()
            return request.json()
        except Exception as e:
            log("Error while getting system status: ", e)
            return False

    # General methods

    @classmethod
    def product_create(cls, product, api=None):
        """Create a new product from WooCommerce data"""
        wcapi = api or cls.get_api()

        try:
            selling_price = float(product["price"])
        except ValueError:
            selling_price = 0.0

        newproduct = Product.objects.create(
            woocommerceid=product["id"],
            article_number=product["sku"],
            name=preparestring(product["name"]),
            short_description=preparestring(product["short_description"]),
            description=preparestring(product["description"]),
            selling_price=selling_price,
            image_url=(product["images"][0]["src"])
            if len(product["images"]) > 0
            else "",
            sale_from=(
                product["date_on_sale_from_gmt"] + "+00:00"
                if product["date_on_sale_from"]
                else None
            ),
            sale_to=(
                product["date_on_sale_to_gmt"] + "+00:00"
                if product["date_on_sale_to"]
                else None
            ),
            sale_price=(product["sale_price"] if product["sale_price"] else None),
        )
        if product["manage_stock"]:
            newproduct.stock_current = product["stock_quantity"]
        for category in product["categories"]:
            obj, created = ProductCategory.objects.get_or_create(
                woocommerceid=category["id"]
            )
            if created:
                cls.category_update(obj, api=wcapi)
            newproduct.categories.add(obj)
        newproduct.save()
        log("Product created:", str(newproduct))
        return newproduct

    @classmethod
    def product_update(cls, product, newproduct=None, api=None):
        """Update a specific product from WooCommerce"""
        wcapi = api or cls.get_api()

        if not newproduct:
            newproduct = wcapi.get(f"products/{product.woocommerceid}").json()

        try:
            product.selling_price = float(newproduct["price"])
        except ValueError:
            pass
        except KeyError:
            if (
                "code" in newproduct
                and newproduct["code"] == "woocommerce_rest_product_invalid_id"
            ):
                log(
                    "[red]Product does not exist in WooCommerce![/] Link removed!",
                    str(product),
                )
                product.woocommerceid = 0
                product.save()
                return product

        product.article_number = newproduct["sku"]
        product.name = preparestring(newproduct["name"])
        product.short_description = preparestring(newproduct["short_description"])
        product.description = preparestring(newproduct["description"])
        product.image_url = (
            (newproduct["images"][0]["src"]) if len(newproduct["images"]) > 0 else ""
        )
        if newproduct["date_on_sale_from_gmt"]:
            product.sale_from = newproduct["date_on_sale_from_gmt"] + "+00:00"
        if newproduct["date_on_sale_to_gmt"]:
            product.sale_to = newproduct["date_on_sale_to_gmt"] + "+00:00"
        if newproduct["sale_price"]:
            product.sale_price = newproduct["sale_price"]

        product.categories.clear()
        newcategories = []
        for category in newproduct["categories"]:
            obj, created = ProductCategory.objects.get_or_create(
                woocommerceid=category["id"]
            )
            if created:
                cls.category_update(obj, api=wcapi)
            newcategories.append(obj)
        product.categories.add(*newcategories)

        product.save()
        log("Product updated:", str(product))
        return product

    @classmethod
    def product_import(cls, api=None):
        """Import new products from WooCommerce"""
        wcapi = api or cls.get_api()

        with Progress() as progress:
            task_prepare = progress.add_task(
                PREFIX + " [orange_red1]Preparing product download...", total=1
            )

            excludeids = ",".join(
                [
                    str(obj.woocommerceid)
                    for obj in Product.objects.all().exclude(woocommerceid=0)
                ]
            )
            productlist = []

            progress.update(task_prepare, advance=1)
            progress.stop_task(task_prepare)

            task_download = progress.add_task(
                PREFIX + " [green]Downloading products..."
            )

            r = wcapi.get("products?exclude=" + excludeids)
            productlist += r.json()

            progress.update(
                task_download, advance=1, total=int(r.headers["X-WP-TotalPages"])
            )

            for page in range(2, int(r.headers["X-WP-TotalPages"]) + 1):
                productlist += wcapi.get(
                    "products?exclude=" + excludeids + "&page=" + str(page)
                ).json()
                progress.update(task_download, advance=1)

            progress.stop_task(task_download)

            if productlist:
                task_process = progress.add_task(
                    PREFIX + " [cyan]Processing products...", total=len(productlist)
                )
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
                PREFIX + " [orange_red1]Updating products...", total=products.count()
            )
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
        newcustomer = Customer.objects.create(
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
        log("Customer created:", str(newcustomer))
        return newcustomer

    @classmethod
    def customer_update(cls, customer, newcustomer=None, api=None):
        """Update a specific customer from WooCommerce"""
        wcapi = api or cls.get_api()

        if not newcustomer:
            newcustomer = wcapi.get(f"customers/{customer.woocommerceid}").json()

        if (
            "code" in newcustomer
            and newcustomer["code"] == "woocommerce_rest_customer_invalid_id"
        ):
            log(
                "[red]Customer does not exist in WooCommerce![/] Link removed.",
                str(customer),
            )
            customer.woocommerceid = 0
            customer.save()
            return customer

        customer.email = newcustomer["email"]
        customer.first_name = newcustomer["first_name"]
        customer.last_name = newcustomer["last_name"]
        customer.company = (
            newcustomer["billing"]["company"]
            if newcustomer["billing"]["company"]
            else customer.company
        )
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
        log("Customer updated:", str(customer))
        return customer

    @classmethod
    def customer_import(cls, api=None):
        """Import new customers from WooCommerce"""
        wcapi = api or cls.get_api()

        with Progress() as progress:
            task_prepare = progress.add_task(
                PREFIX + " [orange_red1]Preparing customer download...", total=1
            )

            excludeids = ",".join(
                [
                    str(obj.woocommerceid)
                    for obj in Customer.objects.all().exclude(woocommerceid=0)
                ]
            )
            customerlist = []

            progress.update(task_prepare, advance=1)
            progress.stop_task(task_prepare)

            task_download = progress.add_task(
                PREFIX + " [green]Downloading customers..."
            )

            r = wcapi.get("customers?exclude=" + excludeids)
            customerlist += r.json()

            progress.update(
                task_download, advance=1, total=int(r.headers["X-WP-TotalPages"])
            )

            for page in range(2, int(r.headers["X-WP-TotalPages"]) + 1):
                customerlist += wcapi.get(
                    "customers?exclude=" + excludeids + "&page=" + str(page)
                ).json()
                progress.update(task_download, advance=1)
            progress.stop_task(task_download)

            if customerlist:
                task_process = progress.add_task(
                    PREFIX + " [cyan]Processing customers...", total=len(customerlist)
                )
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
                PREFIX + " [orange_red1]Updating customers...", total=customers.count()
            )
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
            newcategory = wcapi.get(
                f"products/categories/{category.woocommerceid}"
            ).json()

        if (
            "code" in newcategory
            and newcategory["code"] == "woocommerce_rest_category_invalid_id"
        ):
            log(
                "[red]Category does not exist in WooCommerce![/] Link removed.",
                str(category),
            )
            category.woocommerceid = 0
            category.save()
            return category

        category.name = preparestring(newcategory["name"])
        category.description = preparestring(newcategory["description"])
        category.image_url = (
            (newcategory["image"]["src"]) if newcategory["image"] else ""
        )
        if newcategory["parent"]:
            obj, created = ProductCategory.objects.get_or_create(
                woocommerceid=newcategory["parent"]
            )
            if created:
                cls.category_update(obj, api=wcapi)
            category.parent_category = obj
        category.save()
        log("Category updated:", str(category))
        return category

    @classmethod
    def category_import(cls, api=None):
        """Import new categories from WooCommerce"""
        wcapi = api or cls.get_api()

        with Progress() as progress:
            task_prepare = progress.add_task(
                PREFIX + " [orange_red1]Preparing category download...", total=1
            )

            excludeids = ",".join(
                [
                    str(obj.woocommerceid)
                    for obj in ProductCategory.objects.all().exclude(woocommerceid=0)
                ]
            )
            categorylist = []

            progress.update(task_prepare, advance=1)
            progress.stop_task(task_prepare)

            task_download = progress.add_task(
                PREFIX + " [green]Downloading categories..."
            )

            r = wcapi.get("products/categories?exclude=" + excludeids)
            categorylist += r.json()

            progress.update(
                task_download, advance=1, total=int(r.headers["X-WP-TotalPages"])
            )

            for page in range(2, int(r.headers["X-WP-TotalPages"]) + 1):
                categorylist += wcapi.get(
                    "products/categories?exclude=" + excludeids + "&page=" + str(page)
                ).json()
                progress.update(task_download, advance=1)

            progress.stop_task(task_download)

            categorieswithparents = []

            if categorylist:
                task_process = progress.add_task(
                    PREFIX + " [cyan]Processing categories...", total=len(categorylist)
                )
                for category in categorylist:
                    newcategory = ProductCategory.objects.create(
                        name=preparestring(category["name"]),
                        description=preparestring(category["description"]),
                        image_url=(category["image"]["src"])
                        if category["image"]
                        else "",
                        woocommerceid=category["id"],
                    )
                    log("Category created:", category["name"])
                    if category["parent"]:
                        categorieswithparents.append((newcategory, category["parent"]))
                    progress.update(task_process, advance=1)
                progress.stop_task(task_process)

            if categorieswithparents:
                task_process2 = progress.add_task(
                    PREFIX + " [cyan]Processing category dependencies...",
                    total=len(categorieswithparents),
                )
                for cat, parentwcid in categorieswithparents:
                    cat.parent_category = ProductCategory.objects.get(
                        woocommerceid=parentwcid
                    )
                    cat.save()
                    progress.update(task_process2, advance=1)
                progress.stop_task(task_process2)
        return len(categorylist)

    @classmethod
    def category_bulk_update(cls, categories, api=None):
        """Update every category in a queryset"""
        wcapi = api or cls.get_api()

        with Progress() as progress:
            task = progress.add_task(
                PREFIX + " [orange_red1]Updating categories...",
                total=categories.count(),
            )
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

        neworder = Order.objects.create(
            woocommerceid=order["id"],
            status=order["status"],
            is_shipped=(True if order["status"] == "completed" else False),
            is_removed_from_stock=(True if order["status"] == "completed" else False),
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
            addr_shipping_country=order["shipping"]["country"],
        )
        neworder.date = order["date_created_gmt"] + "+00:00"
        if order["customer_id"]:
            customer, created = Customer.objects.get_or_create(
                woocommerceid=int(order["customer_id"])
            )
            if created:
                customer = cls.customer_update(customer, api=wcapi)

            neworder.customer = customer
            neworder.addr_shipping_email = customer.addr_shipping_email
            neworder.addr_shipping_phone = customer.addr_shipping_phone

        for item in order["line_items"]:
            product, created = Product.objects.get_or_create(
                woocommerceid=int(item["product_id"])
            )
            if created:
                product = cls.product_update(product, api=wcapi)

            neworder.products.add(
                product,
                through_defaults={
                    "quantity": int(item["quantity"]),
                    "product_price": runden(float(item["price"])),
                },
            )
        for item in order["shipping_lines"]:
            neworder.fees.through.objects.create(
                order=neworder,
                name=item["method_title"],
                price=float(item["total"]),
                vat_rate=(
                    constants.VAT_RATE_DEFAULT if float(item["total_tax"]) > 0 else 0
                ),
            )
        neworder.save()
        neworder.second_save()
        log("Order created:", str(neworder))

        if sendstockwarning:
            neworder.email_stock_warning()
        return neworder

    @classmethod
    def order_update(cls, order, neworder=None, api=None):
        """Update a specific order from WooCommerce"""
        wcapi = api or cls.get_api()

        if not neworder:
            neworder = wcapi.get(f"orders/{order.woocommerceid}").json()

        if (
            "code" in neworder
            and neworder["code"] == "woocommerce_rest_order_invalid_id"
        ):
            log(
                "[red]Order does not exist in WooCommerce![/] Link removed.", str(order)
            )
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
        log("Order updated: ", str(order))
        return order

    @classmethod
    def order_import(cls, api=None):
        """Import new orders from WooCommerce"""
        wcapi = api or cls.get_api()

        with Progress() as progress:
            task_prepare = progress.add_task(
                PREFIX + " [orange_red1]Preparing order download...", total=1
            )

            excludeids = ",".join(
                [
                    str(obj.woocommerceid)
                    for obj in Order.objects.all().exclude(woocommerceid=0)
                ]
            )
            orderlist = []

            progress.update(task_prepare, advance=1)
            progress.stop_task(task_prepare)

            task_download = progress.add_task(PREFIX + " [green]Downloading orders...")

            r = wcapi.get("orders?exclude=" + excludeids)
            orderlist += r.json()

            progress.update(
                task_download, advance=1, total=int(r.headers["X-WP-TotalPages"])
            )

            for page in range(2, int(r.headers["X-WP-TotalPages"]) + 1):
                orderlist += wcapi.get(
                    "orders?exclude=" + excludeids + "&page=" + str(page)
                ).json()
                progress.update(task_download, advance=1)
            progress.stop_task(task_download)

            if orderlist:
                task_process = progress.add_task(
                    PREFIX + " [cyan]Processing orders...", total=len(orderlist)
                )
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
                PREFIX + " [orange_red1]Updating orders...", total=orders.count()
            )
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
