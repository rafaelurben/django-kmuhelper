from django.utils.translation import gettext

import kmuhelper.modules.main.models as models
from kmuhelper import constants
from kmuhelper.modules.integrations.woocommerce.api import products, customers
from kmuhelper.modules.integrations.woocommerce.api._base import WC_BaseObjectAPI
from kmuhelper.utils import runden

_ = gettext


class WCOrdersAPI(WC_BaseObjectAPI):
    LOG_PREFIX = "[deep_pink4][KMUHelper WooCommerce Orders][/] -"

    MODEL = models.Order
    WC_OBJ_DOES_NOT_EXIST_CODE = "woocommerce_rest_shop_order_invalid_id"
    WC_API_BASEURL = "orders"

    def update_object_from_data(self, db_obj, wc_obj: dict):
        db_obj.woocommerce_deleted = False

        if wc_obj["date_paid"]:
            db_obj.is_paid = True
        db_obj.status = wc_obj["status"]
        db_obj.customer_note = wc_obj["customer_note"]

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
        self.log("Order updated: ", str(db_obj))

    def create_object_from_data(self, wc_obj: dict, sendstockwarning=True):
        db_obj = models.Order.objects.create(
            woocommerceid=wc_obj["id"],
            status=wc_obj["status"],
            is_shipped=(True if wc_obj["status"] == "completed" else False),
            is_removed_from_stock=(True if wc_obj["status"] == "completed" else False),
            payment_method=wc_obj["payment_method"],
            is_paid=(True if wc_obj["date_paid"] else False),
            customer_note=wc_obj["customer_note"],
            order_key=wc_obj["order_key"],
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
        )
        db_obj.date = wc_obj["date_created_gmt"] + "+00:00"
        if wc_obj["customer_id"]:
            customer, created = models.Customer.objects.get_or_create(
                woocommerceid=int(wc_obj["customer_id"])
            )
            if created:
                customers.WCCustomersAPI(self.wcapi).update_object_from_api(customer)

            db_obj.customer = customer
            db_obj.addr_shipping_email = customer.addr_shipping_email
            db_obj.addr_shipping_phone = customer.addr_shipping_phone

        for item in wc_obj["line_items"]:
            # Use variation id if available and != 0
            if "variation_id" in item and item["variation_id"]:
                product_id = item["variation_id"]
            else:
                product_id = item["product_id"]

            quantity = int(item["quantity"])
            product_price = runden(float(item["subtotal"]) / quantity)
            # subtotal/quantity is used instead of price to exclude discounts => handled under "coupon_lines"

            if product_id != 0:
                product, created = models.Product.objects.get_or_create(
                    woocommerceid=int(product_id)
                )
                if created:
                    products.WCProductsAPI(self.wcapi).update_object_from_api(product)

                db_obj.products.through.objects.create(
                    order=db_obj,
                    linked_product=product,
                    quantity=quantity,
                    product_price=product_price,
                )
            else:
                self.log("Product ID in a line item was 0!")
                db_obj.products.through.objects.create(
                    order=db_obj,
                    linked_product=None,
                    quantity=quantity,
                    product_price=product_price,
                    name=item["name"],
                    article_number=str(item["sku"]),
                )

        for item in wc_obj["shipping_lines"]:
            db_obj.fees.through.objects.create(
                order=db_obj,
                name=item["method_title"],
                price=float(item["total"]),
                vat_rate=(
                    constants.VAT_RATE_DEFAULT if float(item["total_tax"]) > 0 else 0
                ),
            )

        for item in wc_obj["fee_lines"]:
            db_obj.fees.through.objects.create(
                order=db_obj,
                name=item["name"],
                price=float(item["total"]),
                vat_rate=(
                    constants.VAT_RATE_DEFAULT if float(item["total_tax"]) > 0 else 0
                ),
            )

        for item in wc_obj["coupon_lines"]:
            db_obj.fees.through.objects.create(
                order=db_obj,
                name=_("Coupon: %(code)s") % {"code": item["code"]},
                price=-float(item["discount"]),
                vat_rate=(
                    constants.VAT_RATE_DEFAULT if float(item["discount_tax"]) > 0 else 0
                ),
            )

        db_obj.save()
        db_obj.second_save()
        self.log("Order created:", str(db_obj))

        if sendstockwarning:
            db_obj.email_stock_warning()
        return db_obj
