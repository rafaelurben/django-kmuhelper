from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse_lazy

from kmuhelper.modules.main.models import Bestellung
from kmuhelper.decorators import require_object
from kmuhelper.utils import render_error


@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.view_bestellung")
@require_object(Bestellung)
def bestellung_pdf_ansehen(request, obj):
    lieferschein = bool("lieferschein" in dict(request.GET))
    digital = not bool("druck" in dict(request.GET))
    pdf = obj.get_pdf(lieferschein=lieferschein, digital=digital)
    return pdf


# Public views

@require_object(Bestellung, reverse_lazy("kmuhelper:info"), show_errorpage=True)
def public_view_order(request, obj, order_key):
    if not str(obj.order_key) == order_key:
        return render_error(request, status=404,
                            message="Der Bestellungsschlüssel dieser Bestellung stimmt nicht überein.")

    lieferschein = bool("lieferschein" in dict(request.GET))
    digital = not bool("druck" in dict(request.GET))
    return obj.get_pdf(lieferschein=lieferschein, digital=digital)
