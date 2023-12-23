from django.db import models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from kmuhelper.utils import package_version, python_version, formatprice
from kmuhelper.modules.main.models import Order
from kmuhelper.modules.api.constants import ENDPOINT_NOT_FOUND, SUCCESSFULLY_CHANGED
from kmuhelper.modules.api.decorators import (
    require_object,
    api_read,
    api_write,
    api_readwrite,
)

#####


def not_found(request):
    """Return a json error message"""

    return ENDPOINT_NOT_FOUND


#####


@api_read()
def versions(request):
    """Get the installed versions of some dependencies, their newest versions available and the current python version."""

    context = {
        "versions": {
            "Python": {"current": python_version(), "latest": "-", "uptodate": None},
        }
    }

    packages = [
        "Django",
        "django-kmuhelper",
        "requests",
        "WooCommerce",
        "reportlab",
        "rich",
        "defusedxml",
    ]

    for package in packages:
        context["versions"][package] = package_version(package)
    return JsonResponse(context)


@api_read(["view_order"])
def orders_unpaid(request):
    """Get sums of currently unpaid orders."""

    sum_unsent = (
        Order.objects.filter(is_paid=False, is_shipped=False).aggregate(
            models.Sum("cached_sum")
        )["cached_sum__sum"]
        or 0
    )
    sum_sent = (
        Order.objects.filter(is_paid=False, is_shipped=True).aggregate(
            models.Sum("cached_sum")
        )["cached_sum__sum"]
        or 0
    )

    context = {
        "orders_unpaid_sum": {
            "unsent": formatprice(round(sum_unsent, 2)),
            "sent": formatprice(round(sum_sent, 2)),
            "all": formatprice(round(sum_sent + sum_unsent, 2)),
        }
    }
    return JsonResponse(context)


@csrf_exempt
@api_write(["change_order"])
@require_object(Order)
def orders_set_paid(request, obj):
    """Set an order as paid"""

    if not obj.is_paid:
        obj.is_paid = True
        if obj.is_shipped and obj.status == "pending":
            obj.status = "completed"
        obj.save()
    return SUCCESSFULLY_CHANGED
