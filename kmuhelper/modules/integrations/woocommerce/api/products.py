import kmuhelper.modules.main.models as models
from kmuhelper.modules.integrations.woocommerce.api import product_categories
from kmuhelper.modules.integrations.woocommerce.api._base import WC_BaseObjectAPI
from kmuhelper.modules.integrations.woocommerce.api._utils import preparestring


class WCProductsAPI(WC_BaseObjectAPI):
    LOG_PREFIX = "[deep_pink4][KMUHelper WooCommerce Products][/] -"

    MODEL = models.Product
    WC_OBJ_DOES_NOT_EXIST_CODE = "woocommerce_rest_product_invalid_id"
    WC_API_BASEURL = "products"

    def update_object_from_data(
        self, db_obj: models.Product, wc_obj: dict, is_create_event: bool = False
    ):
        db_obj.woocommerce_deleted = False

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

        # Update dependencies
        self._update_dependencies(
            db_obj, wc_obj, force_update_variations=is_create_event
        )

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

        # Update dependencies
        self._update_dependencies(db_obj, wc_obj)

        db_obj.save()
        self.log("Product created:", str(db_obj))
        return db_obj

    def _update_dependencies(
        self,
        db_obj: models.Product,
        wc_obj: dict,
        force_update_variations: bool = False,
    ):
        # Save before updating dependencies
        db_obj.save()

        # If product is a variation of a parent product
        if wc_obj["type"] == "variation":
            db_parent, created = models.Product.objects.get_or_create(
                woocommerceid=wc_obj["parent_id"]
            )
            if created:
                self.log("Updating parent...")
                self.update_object_from_api(db_parent)
            db_obj.parent = db_parent

        # If product is variable (has variations), also update variations
        if wc_obj["type"] == "variable" and "variations" in wc_obj:
            # Update variations
            for variation_id in wc_obj["variations"]:
                db_variation, created = models.Product.objects.get_or_create(
                    woocommerceid=variation_id
                )
                if (
                    created
                    or db_variation.woocommerce_deleted
                    or force_update_variations
                ):
                    self.log("Updating variation...")
                    self.update_object_from_api(db_variation)
            # Delete orphan variations
            for db_orphan in db_obj.children.exclude(
                woocommerceid__in=wc_obj["variations"]
            ).exclude(woocommerce_deleted=True):
                self.log("Marked orphan variation as deleted:", str(db_orphan))
                db_orphan.woocommerce_deleted = True
                db_orphan.save()

        # Categories
        db_obj.categories.clear()
        for wc_category in wc_obj["categories"]:
            db_category, created = models.ProductCategory.objects.get_or_create(
                woocommerceid=wc_category["id"]
            )
            if created:
                self.log("Created linked category! Updating...")
                product_categories.WCProductCategoriesAPI(
                    self.wcapi
                ).update_object_from_api(db_category)
            db_obj.categories.add(db_category, through_defaults=None)

    def delete_object_from_data(self, db_obj, wc_obj: dict):
        """Mark an existing object as deleted

        Returns: nothing"""

        db_obj.woocommerce_deleted = True
        db_obj.save()

        # If product has variations that have not been marked as deleted yet
        for db_child in db_obj.children.exclude(woocommerce_deleted=True):
            self.log("Marked undeleted variation as deleted:", str(db_child))
            db_child.woocommerce_deleted = True
            db_child.save()
