from datetime import datetime

from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.admin.options import get_content_type_for_model
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse

from django.utils import translation
_ = translation.gettext

from kmuhelper import constants
from kmuhelper.modules.main.models import Bestellung
from kmuhelper.decorators import require_object
from kmuhelper.utils import render_error
from kmuhelper.translations import Language

from kmuhelper.modules.pdfgeneration.order.forms import PDFOrderForm
from kmuhelper.modules.pdfgeneration.order.generator import PDFOrder

# Views

@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.view_bestellung")
@require_object(Bestellung)
def bestellung_pdf_ansehen(request, obj):
    order = obj
    is_print_version = 'print' in request.GET
    is_download = 'download' in request.GET

    preset = request.GET.get('preset', 'invoice')
    title = None
    text = None

    if 'custom' in request.GET:
        title = order.rechnungstitel
        text = order.rechnungstext

    # Get the language
    defaultlang = order.kunde.sprache if order.kunde and order.kunde.sprache else "de"
    lang = request.GET.get('language', defaultlang).lower()
    if lang not in dict(constants.LANGUAGES):
        lang = defaultlang

    with Language(lang):
        match preset:
            case 'invoice':
                title = title or _("Rechnung")
                pdf = PDFOrder(order, title, text=text, add_cut_lines=not is_print_version)
            case 'delivery-note':
                title = title or _("Lieferschein")
                pdf = PDFOrder(order, title, text=text, is_delivery_note=True)
            case 'payment-reminder':
                days_to_pay = 14
                title = title or _("Zahlungserinnerung")
                text = text or _("Geschätzter Kunde\n\nVermutlich ist Ihnen entgangen, diese Rechnung vom %(original_date)s innert der gewährten Frist zu begleichen.\nWir bitten Sie, dies innert %(days)d Tagen nachzuholen.\n\nSollte sich Ihre Zahlung mit diesem Schreiben überkreuzen, so betrachten Sie dieses bitte als gegenstandslos.") % {
                    'original_date': order.rechnungsdatum.strftime("%d.%m.%Y"),
                    'days': days_to_pay,
                }
                # Temporarily replace the order's date and payment conditions
                order.rechnungsdatum = datetime.now().date()
                order.zahlungskonditionen = f"0:{days_to_pay}"
                pdf = PDFOrder(order, title, text=text, add_cut_lines=not is_print_version, show_payment_conditions=False)
            case other:
                return render_error(request, status=400, message="Ungültige Vorlage: " + str(other))

        # Log the action
        LogEntry.objects.log_action(
            user_id=request.user.id, 
            content_type_id=get_content_type_for_model(obj).pk,
            object_id=obj.pk,
            object_repr=str(obj),
            action_flag=CHANGE,
            change_message=f'PDF "{title}" aus Vorlage "{preset}" erstellt mit Text: "{text}"' if text else f'PDF "{title}" aus Vorlage "{preset}" erstellt.',
        )

        filename = f'{str(order)} - {title}.pdf'
        return pdf.get_response(as_attachment=is_download, filename=filename)

@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("kmuhelper.view_bestellung")
@require_object(Bestellung)
def bestellung_pdf_erstellen(request, obj):
    initial={
        'language': obj.kunde.sprache if obj.kunde and obj.kunde.sprache else 'de',
        'title': obj.rechnungstitel,
        'text': obj.rechnungstext,
    }
    
    if request.method == 'POST':
        form = PDFOrderForm(request.POST)
        if form.is_valid():
            form.update_order_settings(obj)
            url = reverse('admin:kmuhelper_bestellung_pdf', args=[obj.id])
            return redirect(url+form.get_url_params())
    else:
        form = PDFOrderForm(initial=initial)

    return render(request, 'admin/kmuhelper/bestellung/pdf_form.html', {
        'form': form,
        'has_permission': True,
        'original': obj,
    })
