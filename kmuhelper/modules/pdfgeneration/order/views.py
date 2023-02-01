from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse_lazy

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

    match request.GET.get('mode', None):
        case 'invoice':
            filename = f'Rechnung zu Bestellung {str(order)}.pdf'
            pdf = PDFOrder(order, add_cut_lines=not is_print_version)
            return pdf.get_response(as_attachment=is_download, filename=filename)
        case 'delivery-note':
            filename = f'Lieferschein zu Bestellung {str(order)}.pdf'
            pdf = PDFOrder(order, is_delivery_note=True)
            return pdf.get_response(as_attachment=is_download, filename=filename)
        case 'payment-reminder':
            # TODO: Implement
            return render_error(request, status=501, message="Diese Funktion ist noch nicht implementiert.")
        case 'custom':
            # TODO: Implement
            return render_error(request, status=501, message="Diese Funktion ist noch nicht implementiert.")
        case other:
            return render_error(request, status=400, message="Ungültiger Modus: " + str(other))

@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.view_bestellung")
@require_object(Bestellung)
def bestellung_pdf_erstellen(request, obj):
    # TODO: PDF form
    
    return render_error(request, status=501, message="Diese Funktion ist noch nicht implementiert.")
