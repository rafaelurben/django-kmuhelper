from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from kmuhelper import settings

WC_ID_PRESENT_DESCRIPTION = format_html(
    '<abbr title="{}">{}</abbr>', _("Mit WooCommerce-Objekt verknüpft?"), "🔗"
)


class WooCommerceModelMixin(models.Model):
    WOOCOMMERCE_URL_FORMAT = "{}/wp-admin/post.php?action=edit&post={}"

    woocommerceid = models.IntegerField(
        verbose_name=_("WooCommerce ID"),
        default=0,
    )

    def get_woocommerce_url(self):
        return self.WOOCOMMERCE_URL_FORMAT.format(
            settings.get_secret_db_setting("wc-url"), self.woocommerceid
        )

    # Display

    @admin.display(description="WooCommerce", ordering="woocommerceid")
    def display_woocommerce_id(self):
        if not self.woocommerceid:
            return None

        link = self.get_woocommerce_url()

        return format_html(
            '<a target="_blank" href="{}">#{}</a>',
            link,
            str(self.woocommerceid),
        )

    @admin.display(
        description=WC_ID_PRESENT_DESCRIPTION, ordering="woocommerceid", boolean=True
    )
    def display_woocommerce_id_present(self):
        return bool(self.woocommerceid)

    class Meta:
        abstract = True
