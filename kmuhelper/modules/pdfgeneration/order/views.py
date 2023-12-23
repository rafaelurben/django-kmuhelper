from datetime import datetime

from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.admin.options import get_content_type_for_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.utils import translation, timezone

from kmuhelper import constants
from kmuhelper.decorators import require_object, require_all_kmuhelper_perms
from kmuhelper.modules.main.models import Order
from kmuhelper.modules.pdfgeneration.order.forms import PDFOrderForm
from kmuhelper.modules.pdfgeneration.order.generator import PDFOrder
from kmuhelper.translations import Language
from kmuhelper.utils import render_error

_ = translation.gettext

# Views


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["view_order"])
@require_object(Order)
def order_view_pdf(request, obj):
    order = obj
    is_print_version = "print" in request.GET
    is_download = "download" in request.GET

    preset = request.GET.get("preset", "invoice")
    title = None
    text = None

    if "custom" in request.GET:
        title = order.pdf_title
        text = order.pdf_text

    # Get the language
    defaultlang = order.language
    lang = request.GET.get("language", defaultlang).lower()
    if lang not in dict(constants.LANGUAGES):
        lang = defaultlang

    # Set invoice date if not present
    if order.invoice_date is None:
        order.invoice_date = timezone.now()
        order.save()

    with Language(lang):
        match preset:
            case "invoice":
                title = title or _("Rechnung")
                pdf = PDFOrder(
                    order,
                    title,
                    text=text,
                    lang=lang,
                    add_cut_lines=not is_print_version,
                )
            case "delivery-note":
                title = title or _("Lieferschein")
                pdf = PDFOrder(
                    order, title, text=text, lang=lang, is_delivery_note=True
                )
            case "payment-reminder":
                days_to_pay = 14
                title = title or _("Zahlungserinnerung")
                text = text or _(
                    "Geschätzter Kunde\n\nVermutlich ist Ihnen entgangen, diese Rechnung vom %(original_date)s innert "
                    "der gewährten Frist zu begleichen.\nWir bitten Sie, dies innert %(days)d Tagen "
                    "nachzuholen.\n\nSollte sich Ihre Zahlung mit diesem Schreiben überkreuzen, so betrachten Sie "
                    "dieses bitte als gegenstandslos."
                ) % {
                    "original_date": order.invoice_date.strftime("%d.%m.%Y"),
                    "days": days_to_pay,
                }
                # Temporarily replace the order's date and payment conditions
                order.invoice_date = datetime.now().date()
                order.payment_conditions = f"0:{days_to_pay}"
                pdf = PDFOrder(
                    order,
                    title,
                    text=text,
                    lang=lang,
                    add_cut_lines=not is_print_version,
                    show_payment_conditions=False,
                )
            case other:
                return render_error(
                    request, status=400, message="Ungültige Vorlage: " + str(other)
                )

        # Log the action
        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=get_content_type_for_model(obj).pk,
            object_id=obj.pk,
            object_repr=str(obj),
            action_flag=CHANGE,
            change_message=f'PDF "{title}" aus Vorlage "{preset}" erstellt mit Text: "{text}"'
            if text
            else f'PDF "{title}" aus Vorlage "{preset}" erstellt.',
        )

        filename = f"{str(order)} - {title}.pdf"
        return pdf.get_response(as_attachment=is_download, filename=filename)


@login_required(login_url=reverse_lazy("admin:login"))
@require_all_kmuhelper_perms(["view_order"])
@require_object(Order)
def order_create_pdf_form(request, obj):
    initial = {
        "language": obj.language,
        "title": obj.pdf_title,
        "text": obj.pdf_text,
    }

    if request.method == "POST":
        form = PDFOrderForm(request.POST)
        if form.is_valid():
            form.update_order_settings(obj)
            url = reverse("admin:kmuhelper_order_pdf", args=[obj.id])
            return redirect(url + form.get_url_params())
    else:
        form = PDFOrderForm(initial=initial)

    return render(
        request,
        "admin/kmuhelper/order/pdf_form.html",
        {
            "form": form,
            "has_permission": True,
            "original": obj,
        },
    )
