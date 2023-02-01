from datetime import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse_lazy

from django.utils import translation
_ = translation.gettext

from kmuhelper.modules.main.models import Bestellung
from kmuhelper.decorators import require_object
from kmuhelper.utils import render_error

from kmuhelper.modules.pdfgeneration.order.generator import PDFOrder

# Views

@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.view_bestellung")
@require_object(Bestellung)
def bestellung_pdf_ansehen(request, obj):
    order = obj
    is_print_version = 'print' in request.GET
    is_download = 'download' in request.GET

    title = None
    text = None

    if 'custom' in request.GET:
        title = order.rechnungstitel
        text = order.rechnungstext

    match request.GET.get('preset', 'invoice'):
        case 'invoice':
            title = title or translation.gettext_lazy("Rechnung")
            pdf = PDFOrder(order, title, add_cut_lines=not is_print_version)
        case 'delivery-note':
            title = title or translation.gettext_lazy("Lieferschein")
            pdf = PDFOrder(order, title, is_delivery_note=True)
        case 'payment-reminder':
            days_to_pay = 14
            title = title or translation.gettext_lazy("Zahlungserinnerung")
            text = text or translation.gettext_lazy("Geschätzter Kunde\n\nVermutlich ist Ihnen entgangen, diese Rechnung innert der gewährten Frist zu begleichen.\nWir bitten Sie, dies innert %s Tagen nachzuholen.\n\nSollte sich Ihre Zahlung mit diesem Schreiben überkreuzen, so betrachten Sie dieses bitte als gegenstandslos.") % days_to_pay
            # Temporarily replace the order's date and payment conditions
            order.rechnungsdatum = datetime.now().date()
            order.zahlungskonditionen = f"0:{days_to_pay}"
            pdf = PDFOrder(order, title, text=text, add_cut_lines=not is_print_version, show_payment_conditions=False)
        case other:
            return render_error(request, status=400, message="Ungültige Vorlage: " + str(other))

    filename = f'{str(order)} - {title}.pdf'
    return pdf.get_response(as_attachment=is_download, filename=filename)

@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.view_bestellung")
@require_object(Bestellung)
def bestellung_pdf_erstellen(request, obj):
    # TODO: PDF form
    
    return render_error(request, status=501, message="Diese Funktion ist noch nicht implementiert.")
