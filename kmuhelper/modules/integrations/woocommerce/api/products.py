import kmuhelper.modules.main.models as models
from kmuhelper.modules.integrations.woocommerce.api import product_categories
from kmuhelper.modules.integrations.woocommerce.api._base import WC_BaseObjectAPI
from kmuhelper.modules.integrations.woocommerce.api._utils import preparestring


class WCProductsAPI(WC_BaseObjectAPI):
    LOG_PREFIX = "[deep_pink4][KMUHelper WooCommerce Products][/] -"

    MODEL = models.Product
    WC_OBJ_DOES_NOT_EXIST_CODE = "woocommerce_rest_product_invalid_id"
    WC_API_BASEURL = "products"

    def update_object_from_data(self, db_obj, wc_obj: dict):
        try:
            db_obj.selling_price = float(wc_obj["price"])
        except ValueError:
            pass

        db_obj.article_number = wc_obj["sku"]
        db_obj.name = preparestring(wc_obj["name"])
        db_obj.short_description = preparestring(wc_obj["short_description"])
        db_obj.description = preparestring(wc_obj["description"])
        db_obj.image_url = (
            (wc_obj["images"][0]["src"]) if len(wc_obj["images"]) > 0 else ""
        )
        if wc_obj["date_on_sale_from_gmt"]:
            db_obj.sale_from = wc_obj["date_on_sale_from_gmt"] + "+00:00"
        if wc_obj["date_on_sale_to_gmt"]:
            db_obj.sale_to = wc_obj["date_on_sale_to_gmt"] + "+00:00"
        if wc_obj["sale_price"]:
            db_obj.sale_price = wc_obj["sale_price"]

        # If product is a variation of a parent product
        if wc_obj["type"] == "variation":
            parent, created = models.Product.objects.get_or_create(
                woocommerceid=wc_obj["parent_id"]
            )
            if created:
                self.update_object_from_api(parent)
            db_obj.parent = parent

        # Categories
        db_obj.categories.clear()
        newcategories = []
        for category in wc_obj["categories"]:
            obj, created = models.ProductCategory.objects.get_or_create(
                woocommerceid=category["id"]
            )
            if created:
                product_categories.WCProductCategoriesAPI(
                    self.wcapi
                ).update_object_from_api(obj)
            newcategories.append(obj)
        db_obj.categories.add(*newcategories)

        db_obj.save()
        self.log("Product updated:", str(db_obj))

    def create_object_from_data(self, wc_obj: dict):
        try:
            selling_price = float(wc_obj["price"])
        except ValueError:
            selling_price = 0.0

        db_obj = models.Product.objects.create(
            woocommerceid=wc_obj["id"],
            article_number=wc_obj["sku"],
            name=preparestring(wc_obj["name"]),
            short_description=preparestring(wc_obj["short_description"]),
            description=preparestring(wc_obj["description"]),
            selling_price=selling_price,
            image_url=(wc_obj["images"][0]["src"]) if len(wc_obj["images"]) > 0 else "",
            sale_from=(
                wc_obj["date_on_sale_from_gmt"] + "+00:00"
                if wc_obj["date_on_sale_from"]
                else None
            ),
            sale_to=(
                wc_obj["date_on_sale_to_gmt"] + "+00:00"
                if wc_obj["date_on_sale_to"]
                else None
            ),
            sale_price=(wc_obj["sale_price"] if wc_obj["sale_price"] else None),
        )
        if wc_obj["manage_stock"]:
            db_obj.stock_current = wc_obj["stock_quantity"]

        # If product is a variation of a parent product
        if wc_obj["type"] == "variation":
            parent, created = models.Product.objects.get_or_create(
                woocommerceid=wc_obj["parent_id"]
            )
            if created:
                self.update_object_from_api(parent)
            db_obj.parent = parent

        # Categories
        for category in wc_obj["categories"]:
            obj, created = models.ProductCategory.objects.get_or_create(
                woocommerceid=category["id"]
            )
            if created:
                product_categories.WCProductCategoriesAPI(
                    self.wcapi
                ).update_object_from_api(obj)
            db_obj.categories.add(obj)
        db_obj.save()
        self.log("Product created:", str(db_obj))
        return db_obj
