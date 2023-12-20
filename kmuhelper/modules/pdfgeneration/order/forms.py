from django import forms

from kmuhelper import constants


class PDFOrderForm(forms.Form):
    # Fieldsets

    fieldsets = [
        {"fields": ["preset"]},
        {"fields": ["title", "text", "language"], "name": "Text & Sprache"},
        {"fields": ["do_print"], "name": "Optionen"},
        {"fields": ["do_download"], "name": "Ausgabe"},
    ]

    # Fields

    preset = forms.ChoiceField(
        label="Vorlage",
        choices=(
            ("invoice", "Rechnung"),
            ("delivery-note", "Lieferschein"),
            ("payment-reminder", "Zahlungserinnerung"),
        ),
        required=True,
        help_text="Die Vorlage definiert das Layout und die Inhalte der PDF-Datei",
    )
    title = forms.CharField(
        label="Titel",
        required=False,
        max_length=32,
        help_text="Z. B. 'Rechnung' oder 'Lieferschein' - Leer lassen für Standardwert der Vorlage",
    )
    text = forms.CharField(
        label="Text",
        required=False,
        widget=forms.Textarea,
        help_text="Dieser Text wird unterhalb des Titels angezeigt - Leer lassen für Standardwert der Vorlage",
    )
    language = forms.ChoiceField(
        label="Sprache",
        choices=constants.LANGUAGES,
        required=True,
        help_text="Die Sprache, in der die PDF-Datei generiert werden soll",
    )

    do_print = forms.BooleanField(
        label="Druckversion?",
        required=False,
        help_text="Wenn aktiviert, wird die PDF-Datei ohne Schnittmarker generiert",
    )
    do_download = forms.BooleanField(
        label="Herunterladen?",
        required=False,
        help_text="Datei automatisch herunterladen (dieses Verhalten kann je nach Browser variieren)",
    )

    def get_url_params(self):
        result = f"?custom&preset={self.cleaned_data['preset']}&language={self.cleaned_data['language']}"
        if self.cleaned_data["do_print"]:
            result += "&print"
        if self.cleaned_data["do_download"]:
            result += "&download"
        return result

    def update_order_settings(self, order):
        order.pdf_title = self.cleaned_data["title"]
        order.pdf_text = self.cleaned_data["text"]
        order.save()
