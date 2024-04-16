import kmuhelper.modules.main.models as models
from kmuhelper.modules.integrations.woocommerce.api._base import WC_BaseObjectAPI


class WCCustomersAPI(WC_BaseObjectAPI):
    LOG_PREFIX = "[deep_pink4][KMUHelper WooCommerce Customers][/] -"

    MODEL = models.Customer
    WC_OBJ_DOES_NOT_EXIST_CODE = "woocommerce_rest_invalid_id"
    WC_API_BASEURL = "customers"

    def update_object_from_data(self, db_obj, wc_obj: dict):
        db_obj.woocommerce_deleted = False

        db_obj.email = wc_obj["email"]
        db_obj.first_name = wc_obj["first_name"]
        db_obj.last_name = wc_obj["last_name"]
        db_obj.company = (
            wc_obj["billing"]["company"]
            if wc_obj["billing"]["company"]
            else db_obj.company
        )
        db_obj.username = wc_obj["username"]
        db_obj.avatar_url = wc_obj["avatar_url"]

        db_obj.addr_billing_first_name = wc_obj["billing"]["first_name"]
        db_obj.addr_billing_last_name = wc_obj["billing"]["last_name"]
        db_obj.addr_billing_company = wc_obj["billing"]["company"]
        db_obj.addr_billing_address_1 = wc_obj["billing"]["address_1"]
        db_obj.addr_billing_address_2 = wc_obj["billing"]["address_2"]
        db_obj.addr_billing_city = wc_obj["billing"]["city"]
        db_obj.addr_billing_state = wc_obj["billing"]["state"]
        db_obj.addr_billing_postcode = wc_obj["billing"]["postcode"]
        db_obj.addr_billing_country = wc_obj["billing"]["country"]
        db_obj.addr_billing_email = wc_obj["billing"]["email"]
        db_obj.addr_billing_phone = wc_obj["billing"]["phone"]

        db_obj.addr_shipping_first_name = wc_obj["shipping"]["first_name"]
        db_obj.addr_shipping_last_name = wc_obj["shipping"]["last_name"]
        db_obj.addr_shipping_company = wc_obj["shipping"]["company"]
        db_obj.addr_shipping_address_1 = wc_obj["shipping"]["address_1"]
        db_obj.addr_shipping_address_2 = wc_obj["shipping"]["address_2"]
        db_obj.addr_shipping_city = wc_obj["shipping"]["city"]
        db_obj.addr_shipping_state = wc_obj["shipping"]["state"]
        db_obj.addr_shipping_postcode = wc_obj["shipping"]["postcode"]
        db_obj.addr_shipping_country = wc_obj["shipping"]["country"]
        db_obj.save()

        self.log("Customer updated:", str(db_obj))

    def create_object_from_data(self, wc_obj: dict):
        db_obj = models.Customer.objects.create(
            woocommerceid=wc_obj["id"],
            email=wc_obj["email"],
            first_name=wc_obj["first_name"],
            last_name=wc_obj["last_name"],
            company=wc_obj["billing"]["company"],
            username=wc_obj["username"],
            avatar_url=wc_obj["avatar_url"],
            addr_billing_first_name=wc_obj["billing"]["first_name"],
            addr_billing_last_name=wc_obj["billing"]["last_name"],
            addr_billing_company=wc_obj["billing"]["company"],
            addr_billing_address_1=wc_obj["billing"]["address_1"],
            addr_billing_address_2=wc_obj["billing"]["address_2"],
            addr_billing_city=wc_obj["billing"]["city"],
            addr_billing_state=wc_obj["billing"]["state"],
            addr_billing_postcode=wc_obj["billing"]["postcode"],
            addr_billing_country=wc_obj["billing"]["country"],
            addr_billing_email=wc_obj["billing"]["email"],
            addr_billing_phone=wc_obj["billing"]["phone"],
            addr_shipping_first_name=wc_obj["shipping"]["first_name"],
            addr_shipping_last_name=wc_obj["shipping"]["last_name"],
            addr_shipping_company=wc_obj["shipping"]["company"],
            addr_shipping_address_1=wc_obj["shipping"]["address_1"],
            addr_shipping_address_2=wc_obj["shipping"]["address_2"],
            addr_shipping_city=wc_obj["shipping"]["city"],
            addr_shipping_state=wc_obj["shipping"]["state"],
            addr_shipping_postcode=wc_obj["shipping"]["postcode"],
            addr_shipping_country=wc_obj["shipping"]["country"],
            addr_shipping_email="",
            addr_shipping_phone="",
        )

        self.log("Customer created:", str(db_obj))
        return db_obj
