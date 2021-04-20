from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect

from kmuhelper.decorators import require_object
from kmuhelper.integrations.paymentimport.forms import CamtUploadForm
from kmuhelper.integrations.paymentimport.models import PaymentImport


@login_required(login_url=reverse_lazy('admin:login'))
@permission_required('kmuhelper.add_paymentimport')
def upload(request):
    if request.method == 'POST':
        form = CamtUploadForm(request.POST, request.FILES)
        if form.is_valid():
            return form.create_payment_import_and_redirect(request)
    else:
        form = CamtUploadForm()

    return render(request, 'admin/kmuhelper/paymentimport/upload.html', {
        'form': form,
        'has_permission': True
    })


@login_required(login_url=reverse_lazy('admin:login'))
@permission_required('kmuhelper.change_paymentimport')
@require_object(PaymentImport)
def process(request, obj):
    if request.method == 'POST':
        obj.process()
        messages.success(request, "Grüne Bestellungen wurden als bezahlt markiert.")
        return redirect(reverse('admin:kmuhelper_paymentimport_changelist'))
    else:
        obj.add_processing_info_messages(request)
        return render(request, 'admin/kmuhelper/paymentimport/process.html', {
            'has_permission': True
        })
