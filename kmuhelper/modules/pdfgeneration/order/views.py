from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse_lazy

from kmuhelper.modules.main.models import Bestellung
from kmuhelper.decorators import require_object
from kmuhelper.utils import render_error

from kmuhelper.modules.pdfgeneration.order.generator import PDFOrder

# Private views

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

# Public views

@require_object(Bestellung, reverse_lazy("kmuhelper:info"), show_errorpage=True)
def public_view_order(request, obj, order_key):
    if not str(obj.order_key) == order_key:
        return render_error(request, status=404,
                            message="Der Bestellungsschlüssel dieser Bestellung stimmt nicht überein.")

    order = obj
    is_download = 'download' in request.GET
    is_delivery_note = bool("lieferschein" in dict(request.GET))
    is_print_version = bool("druck" in dict(request.GET))
    
    if is_delivery_note:
        filename = f'Lieferschein zu Bestellung {str(order)}.pdf'
        pdf = PDFOrder(order, is_delivery_note=True)
        return pdf.get_response(as_attachment=is_download, filename=filename)
    else:
        filename = f'Rechnung zu Bestellung {str(order)}.pdf'
        pdf = PDFOrder(order, add_cut_lines=not is_print_version)
        return pdf.get_response(as_attachment=is_download, filename=filename)
