import kmuhelper.modules.main.models as models
from kmuhelper.modules.integrations.woocommerce.api._base import WC_BaseObjectAPI
from kmuhelper.modules.integrations.woocommerce.api._utils import preparestring


class WCProductCategoriesAPI(WC_BaseObjectAPI):
    LOG_PREFIX = "[deep_pink4][KMUHelper WooCommerce Product categories][/] -"

    MODEL = models.ProductCategory
    WC_OBJ_DOES_NOT_EXIST_CODE = "woocommerce_rest_term_invalid"
    WC_API_BASEURL = "products/categories"

    def update_object_from_data(self, db_obj, wc_obj: dict):
        db_obj.woocommerce_deleted = False

        db_obj.name = preparestring(wc_obj["name"])
        db_obj.description = preparestring(wc_obj["description"])
        db_obj.image_url = (wc_obj["image"]["src"]) if wc_obj["image"] else ""
        if wc_obj["parent"]:
            obj, created = models.ProductCategory.objects.get_or_create(
                woocommerceid=wc_obj["parent"]
            )
            if created:
                self.update_object_from_api(obj)
            db_obj.parent_category = obj
        db_obj.save()

        self.log("Category updated:", str(db_obj))

    def create_object_from_data(self, wc_obj: dict):
        db_obj = models.ProductCategory.objects.create(
            name=preparestring(wc_obj["name"]),
            description=preparestring(wc_obj["description"]),
            image_url=(wc_obj["image"]["src"]) if wc_obj["image"] else "",
            woocommerceid=wc_obj["id"],
        )

        self.log("Category created:", wc_obj["name"])
        return db_obj

    def _post_process_imported_objects(
        self, db_obj__wc_obj_list: list[tuple[object, dict]]
    ):
        for db_obj, wc_obj in db_obj__wc_obj_list:
            if wc_obj["parent"]:
                db_obj.parent_category = models.ProductCategory.objects.get(
                    woocommerceid=wc_obj["parent"]
                )
                db_obj.save()
