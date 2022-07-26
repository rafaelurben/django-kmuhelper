from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect

from kmuhelper.decorators import require_object
from kmuhelper.modules.integrations.paymentimport.forms import CamtUploadForm
from kmuhelper.modules.integrations.paymentimport.models import PaymentImport


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
        obj.is_processed = True
        obj.save()
        messages.success(request, "Zahlungsimport wurde als verarbeitet markiert!")
        return redirect(reverse('admin:kmuhelper_paymentimport_changelist'))
    
    if obj.is_processed:
        messages.warning(request, "Achtung! Dieser Zahlungsimport wurde bereits als verarbeitet markiert!")

    ctx = obj.get_processing_context()
    return render(request, 'admin/kmuhelper/paymentimport/process.html', {
        'has_permission': True,
        'original': obj,
        'data': ctx,
    })
