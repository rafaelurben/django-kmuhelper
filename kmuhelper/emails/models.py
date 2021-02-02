# pylint: disable=unsupported-assignment-operation

from django.db import models
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from django.utils.html import mark_safe
from django.template.loader import get_template
from django.conf import settings

import uuid
from io import BytesIO

#####

from rich import print

prefix = "[deep_pink4][KMUHelper E-Mails][/] -"

def log(string, *args):
    print(prefix, string, *args)

#####

EMAILTYPEN = [
    ("", "-"),
    ("kunde_registriert", "Registrierungsmail Kunde"),
    ("bestellung_rechnung", "Rechnung"),
    ("bestellung_stock_warning", "Warnung zum Lagerbestand"),
]

#####

class EMailAttachment():
    def __init__(self, filename, content, url=None, mimetype="application/pdf"):
        self.filename = filename
        self.content = content
        self.url = url
        self.mimetype = mimetype

        if isinstance(content, BytesIO):
            self.content = content.read()

class EMail(models.Model):
    typ = models.CharField("Typ", choices=EMAILTYPEN, max_length=50, default="", blank=True)
    
    subject = models.CharField("Betreff", max_length=50)
    to = models.EmailField("Empfänger")

    html_template = models.CharField("Dateiname der Vorlage", max_length=100)
    html_context = models.JSONField("Daten", default=dict)

    token = models.UUIDField("Token", default=uuid.uuid4, editable=False)

    time_created = models.DateTimeField("Erstellt am", auto_now_add=True)
    time_sent = models.DateTimeField("Gesendet um", blank=True, null=True, default=None)

    data = models.JSONField("Extradaten", default=dict)

    notes = models.TextField("Notizen", blank=True, default="")

    def __str__(self):
        return f"{self.subject} ({self.pk})"
    __str__.short_description = "E-Mail"

    def is_sent(self):
        return self.time_sent is not None
    is_sent.short_description = "Gesendet?"
    is_sent.boolean = True

    def render(self, online=False):
        context = dict(self.html_context)
        context["isonline"] = online
        context["view_online_url"] = None if online else self.get_url()
        context["data"] = self.data if online else None
        return get_template("kmuhelper/emails/"+str(self.html_template)).render(context)

    def send(self, attachments=[], **options):
        msg = mail.EmailMessage(
            subject=self.subject,
            body=self.render(),
            to=[self.to],
            **options
        )

        msg.content_subtype = "html"

        for attachment in attachments:
            msg.attach(filename=attachment.filename, content=attachment.content, mimetype=attachment.mimetype)

        success = msg.send()

        log("ID:", self.pk, "- Subject:", self.subject, "- Success:", success)

        if success:
            self.time_sent = timezone.now()
            self.data["attachments"] = [{"filename": a.filename, "url": a.url} for a in attachments]
            self.save()
        return success

    def get_url(self):
        domain = getattr(settings, "KMUHELPER_DOMAIN", None)
        if domain:
            return domain+reverse("kmuhelper:email-view", kwargs={"object_id": self.pk})+f"?token={self.token}"
        else:
            log("Einstellung KMUHELPER_DOMAIN ist nicht gesetzt! E-Mails werden ohne 'online ansehen' Links versendet!")
            return None

    class Meta:
        verbose_name = "E-Mail"
        verbose_name_plural = "E-Mails"

    objects = models.Manager()
