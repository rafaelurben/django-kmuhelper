from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse_lazy
from django.shortcuts import render, redirect

from kmuhelper.modules.settings.forms import SettingsForm

@login_required(login_url=reverse_lazy('admin:login'))
@permission_required('kmuhelper.change_einstellung')
def settings_form(request):
    if request.method == 'POST':
        form = SettingsForm(request.POST)
        if form.is_valid():
            form.save_settings()
            messages.success(request, "Einstellungen gespeichert!")
            # Redirect to prevent resending the form on reload
            return redirect('kmuhelper:settings')
    else:
        form = SettingsForm()

    return render(request, 'kmuhelper/settings/form.html', {
        'form': form,
        'has_permission': True
    })

@login_required(login_url=reverse_lazy('admin:login'))
def build_info(request):
    return render(request, 'kmuhelper/settings/build_info.html')