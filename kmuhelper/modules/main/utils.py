import logging
from dataclasses import dataclass, asdict

from django.contrib import messages
from django.db.models import Sum, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _

log = logging.getLogger(__name__)


class StockUtils:
    @dataclass(frozen=True)
    class StockData:
        product: "StockUtils.StockData.StockDataProduct"
        stock: "StockUtils.StockData.StockDataStock"

        @dataclass(frozen=True)
        class StockDataProduct:
            id: int
            article_number: str
            name: str

        @dataclass(frozen=True)
        class StockDataStock:
            current: int
            going: int
            coming: int
            min: int

            @property
            def overbooked(self) -> bool:
                return self.current - self.going < 0

            @property
            def in_danger(self) -> bool:
                return self.current - self.going < self.min

        def as_dict(self):
            return asdict(self)

    @staticmethod
    def get_stock_data(product_ids: list[int]) -> list[StockData]:
        from kmuhelper.modules.main.models import Product, OrderItem, SupplyItem

        qs = Product.objects.filter(id__in=product_ids).annotate(
            total_going=Coalesce(
                Subquery(
                    OrderItem.objects.filter(
                        order__is_removed_from_stock=False, linked_product_id=OuterRef("pk")
                    )
                    .values("linked_product_id")
                    .annotate(total=Sum("quantity"))
                    .values("total")
                ),
                Value(0),
            ),
            total_coming=Coalesce(
                Subquery(
                    SupplyItem.objects.filter(
                        supply__is_added_to_stock=False, product_id=OuterRef("pk")
                    )
                    .values("product_id")
                    .annotate(total=Sum("quantity"))
                    .values("total")
                ),
                Value(0),
            ),
        )

        return list(
            map(
                lambda product: StockUtils.StockData(
                    product=StockUtils.StockData.StockDataProduct(
                        id=product.id,
                        article_number=product.article_number,
                        name=product.clean_name(),
                    ),
                    stock=StockUtils.StockData.StockDataStock(
                        current=product.stock_current,
                        going=product.total_going,
                        coming=product.total_coming,
                        min=product.stock_target,
                    ),
                ),
                qs,
            )
        )

    @staticmethod
    def generate_admin_message(request: HttpRequest, dat: StockData):
        if not dat.stock.overbooked and not dat.stock.in_danger:
            return

        stockstring = f"{_('Aktuell')}: {dat.stock.current} | {_('Ausgehend')}: {dat.stock.going}"
        if dat.stock.coming:
            stockstring += f" | {_('Eingehend')}: {dat.stock.coming}"

        admin_url = reverse(f"admin:kmuhelper_product_change", args=[dat.product.id])
        admin_link = format_html('<a href="{}">{}</a>', admin_url, dat.product.name)

        formatdata = (admin_link, dat.product.article_number, stockstring)

        if dat.stock.overbooked:
            msg = _("Zu wenig Lagerbestand bei")
            msg_html = format_html('{} "{}" [{}]: {}', msg, *formatdata)
            messages.error(request, msg_html)
        elif dat.stock.in_danger:
            msg = _("Knapper Lagerbestand bei")
            msg_html = format_html('{} "{}" [{}]: {}', msg, *formatdata)
            messages.warning(request, msg_html)

    @staticmethod
    def generate_admin_messages(request: HttpRequest, stock_data: list[StockData]):
        for dat in stock_data:
            StockUtils.generate_admin_message(request, dat)

    @staticmethod
    def send_stock_warning(
        stock_data: list[StockData],
        trigger: str = "",
        notes: str = "",
        email_receiver: str | None = None,
    ) -> bool | None:
        from kmuhelper import settings
        from kmuhelper.modules.emails.models import EMail

        email_receiver = email_receiver or settings.get_db_setting("email-stock-warning-receiver")

        if not email_receiver:
            log.warning("No email receiver for stock warning set in settings.")
            return None

        warnings: list[StockUtils.StockData] = list(
            filter(lambda s: s.stock.in_danger, stock_data)
        )

        if len(warnings) > 0:
            email = EMail.objects.create(
                subject=_("[KMUHelper] - Lagerbestand knapp!"),
                to=email_receiver,
                html_template="order_stock_warning.html",
                html_context={
                    "warnings": list(map(lambda w: w.as_dict(), warnings)),
                    "trigger": trigger,
                },
                notes=notes,
            )

            success = email.send()
            return bool(success)
        return None
