"""
Tests for the product model
"""

import unittest
from datetime import timedelta

from django.utils import timezone

from kmuhelper.modules.main.models import Product


class ProductTest(unittest.TestCase):
    def test_sale_price_ended_before(self):
        sale_from = timezone.now() - timedelta(days=7)
        sale_to = timezone.now() - timedelta(seconds=1)
        prod = Product(
            selling_price=10, sale_price=5, sale_from=sale_from, sale_to=sale_to
        )
        self.assertAlmostEqual(prod.get_current_price(), 10)
        self.assertEqual(prod.display_current_price(), "10.00 CHF")

    def test_sale_price_starts_after(self):
        sale_from = timezone.now() + timedelta(seconds=10)
        sale_to = timezone.now() + timedelta(days=7)
        prod = Product(
            selling_price=10, sale_price=5, sale_from=sale_from, sale_to=sale_to
        )
        self.assertAlmostEqual(prod.get_current_price(), 10)
        self.assertEqual(prod.display_current_price(), "10.00 CHF")

    def test_sale_price_current(self):
        sale_from = timezone.now() - timedelta(seconds=10)
        sale_to = timezone.now() + timedelta(seconds=10)
        prod = Product(
            selling_price=10, sale_price=5, sale_from=sale_from, sale_to=sale_to
        )
        self.assertAlmostEqual(prod.get_current_price(), 5)
        self.assertEqual(prod.display_current_price(), "5.00 CHF")
