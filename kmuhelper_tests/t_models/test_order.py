"""
Tests for the order model and corresponding orderitem and orderfee models
"""

from django.test import TestCase

from kmuhelper.constants import VAT_RATE_DEFAULT
from kmuhelper.modules.main.models import (
    Order,
    OrderItem,
    OrderFee,
    ContactPerson,
    PaymentReceiver,
)
from kmuhelper.utils import runden


class OrderTest(TestCase):
    def setUp(self):
        self.contact_person = ContactPerson.objects.create(
            name="X X", phone="x", email="x@x"
        )
        self.payment_receiver = PaymentReceiver.objects.create()

    # Order total

    def test_order_total__no_vat(self):
        obj = Order.objects.create(
            contact_person=self.contact_person,
            payment_receiver=self.payment_receiver,
        )

        obj.products.through.objects.bulk_create(
            [
                OrderItem(product_price=10.5, quantity=1, vat_rate=0.0, order=obj),
                OrderItem(product_price=5.05, quantity=2, vat_rate=0.0, order=obj),
            ]
        )

        obj.fees.through.objects.bulk_create(
            [
                OrderFee(price=9.95, vat_rate=0.0, order=obj),
            ]
        )

        total_expected = 10.5 + (5.05 * 2) + 9.95
        total_calculated = obj.calc_total()

        self.assertAlmostEqual(
            total_expected, total_calculated, 2, "Order total does not match!"
        )

    def test_order_total__with_vat(self):
        obj = Order.objects.create(
            contact_person=self.contact_person,
            payment_receiver=self.payment_receiver,
        )

        obj.products.through.objects.bulk_create(
            [
                OrderItem(
                    product_price=10.5, quantity=1, vat_rate=VAT_RATE_DEFAULT, order=obj
                ),
                OrderItem(
                    product_price=5.05, quantity=2, vat_rate=VAT_RATE_DEFAULT, order=obj
                ),
            ]
        )

        obj.fees.through.objects.bulk_create(
            [
                OrderFee(price=9.95, vat_rate=VAT_RATE_DEFAULT, order=obj),
            ]
        )

        VAT_FACTOR = 1 + 0.01 * VAT_RATE_DEFAULT
        total_expected = runden(
            runden(10.5 * VAT_FACTOR)
            + runden(5.05 * 2 * VAT_FACTOR)
            + runden(9.95 * VAT_FACTOR)
        )
        total_calculated = obj.calc_total()

        self.assertEqual(total_expected, total_calculated)

    # Order item discount

    def test_order_item__discount(self):
        item = OrderItem(product_price=5.55, quantity=17, discount=10, vat_rate=0.0)

        price_expected = runden(5.55 * 17 * (1 - 0.1))
        price_calculated = item.calc_subtotal()

        self.assertEqual(price_expected, price_calculated)
