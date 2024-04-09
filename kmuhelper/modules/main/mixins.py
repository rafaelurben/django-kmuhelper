from django.db import models
from django.utils.translation import (
    gettext_lazy,
    pgettext_lazy,
)

from kmuhelper import constants

_ = gettext_lazy


class AddressModelMixin(models.Model):
    """This model mixin provides billing and shipping address fields and utility methods"""

    # Billing address

    @property
    def addr_billing(self):
        return {
            field.replace("addr_billing_", ""): getattr(self, field)
            for field in constants.ADDR_BILLING_FIELDS
        }

    addr_billing_first_name = models.CharField(
        verbose_name=pgettext_lazy("address", "Vorname"),
        max_length=250,
        default="",
        blank=True,
    )
    addr_billing_last_name = models.CharField(
        verbose_name=pgettext_lazy("address", "Nachname"),
        max_length=250,
        default="",
        blank=True,
    )
    addr_billing_company = models.CharField(
        verbose_name=pgettext_lazy("address", "Firma"),
        max_length=250,
        default="",
        blank=True,
    )
    addr_billing_address_1 = models.CharField(
        verbose_name=pgettext_lazy("address", "Adresszeile 1"),
        max_length=250,
        default="",
        blank=True,
        help_text=_('Strasse und Hausnummer oder "Postfach"'),
    )
    addr_billing_address_2 = models.CharField(
        verbose_name=pgettext_lazy("address", "Adresszeile 2"),
        max_length=250,
        default="",
        blank=True,
        help_text=_("Wird in QR-Rechnung NICHT verwendet!"),
    )
    addr_billing_city = models.CharField(
        verbose_name=pgettext_lazy("address", "Ort"),
        max_length=250,
        default="",
        blank=True,
    )
    addr_billing_state = models.CharField(
        verbose_name=pgettext_lazy("address", "Kanton"),
        max_length=50,
        default="",
        blank=True,
    )
    addr_billing_postcode = models.CharField(
        verbose_name=pgettext_lazy("address", "Postleitzahl"),
        max_length=50,
        default="",
        blank=True,
    )
    addr_billing_country = models.CharField(
        verbose_name=pgettext_lazy("address", "Land"),
        max_length=2,
        default="CH",
        choices=constants.COUNTRIES,
    )
    addr_billing_email = models.EmailField(
        verbose_name=pgettext_lazy("address", "E-Mail-Adresse"),
        blank=True,
    )
    addr_billing_phone = models.CharField(
        verbose_name=pgettext_lazy("address", "Telefon"),
        max_length=50,
        default="",
        blank=True,
    )

    # Shipping address

    @property
    def addr_shipping(self):
        return {
            field.replace("addr_shipping_", ""): getattr(self, field)
            for field in constants.ADDR_SHIPPING_FIELDS
        }

    addr_shipping_first_name = models.CharField(
        verbose_name=pgettext_lazy("address", "Vorname"),
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_last_name = models.CharField(
        verbose_name=pgettext_lazy("address", "Nachname"),
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_company = models.CharField(
        verbose_name=pgettext_lazy("address", "Firma"),
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_address_1 = models.CharField(
        verbose_name=pgettext_lazy("address", "Adresszeile 1"),
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_address_2 = models.CharField(
        verbose_name=pgettext_lazy("address", "Adresszeile 2"),
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_city = models.CharField(
        verbose_name=pgettext_lazy("address", "Ort"),
        max_length=250,
        default="",
        blank=True,
    )
    addr_shipping_state = models.CharField(
        verbose_name=pgettext_lazy("address", "Kanton"),
        max_length=50,
        default="",
        blank=True,
    )
    addr_shipping_postcode = models.CharField(
        verbose_name=pgettext_lazy("address", "Postleitzahl"),
        max_length=50,
        default="",
        blank=True,
    )
    addr_shipping_country = models.CharField(
        verbose_name=pgettext_lazy("address", "Land"),
        max_length=2,
        default="CH",
        choices=constants.COUNTRIES,
    )
    addr_shipping_email = models.EmailField(
        verbose_name=pgettext_lazy("address", "E-Mail-Adresse"),
        blank=True,
    )
    addr_shipping_phone = models.CharField(
        verbose_name=pgettext_lazy("address", "Telefon"),
        max_length=50,
        default="",
        blank=True,
    )

    # Check function

    def addresses_are_equal(self):
        for field in constants.ADDR_FIELDS:
            if getattr(self, f"addr_billing_{field}") != getattr(
                self, f"addr_shipping_{field}"
            ):
                return False
        return True

    # Meta

    class Meta:
        abstract = True
