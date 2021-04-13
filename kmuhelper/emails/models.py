# pylint: disable=unsupported-assignment-operation, no-member

import uuid

from io import BytesIO
from rich import print

from multi_email_field.fields import MultiEmailField

from django.db import models
from django.conf import settings
from django.contrib import admin
from django.core import mail
from django.core.files import storage
from django.http import FileResponse
from django.urls import reverse
from django.utils import timezone
from django.template.loader import get_template


def log(string, *args):
    print("[deep_pink4][KMUHelper E-Mails][/] -", string, *args)

#####


EMAILTYPEN = [
    ("", "-"),
    ("kunde_registriert", "Registrierungsmail Kunde"),
    ("bestellung_rechnung", "Rechnung"),
    ("bestellung_stock_warning", "Warnung zum Lagerbestand"),
]

#####


def getfilepath(instance, filename):
    return 'attachments/' + \
        timezone.now().strftime('%Y-%m-%d_%H-%M-%S_') + filename


class AttachmentManager(models.Manager):
    def create_from_binary(self, filename, content):
        """Create an Attachment object from binary data"""

        file = storage.default_storage.save(filename, content)
        return self.create(
            filename=filename,
            file=file,
            autocreated=True,
        )


class Attachment(models.Model):
    filename = models.CharField("Dateiname", max_length=50)
    file = models.FileField("Datei", upload_to=getfilepath,
                            storage=storage.default_storage)

    description = models.TextField("Beschreibung", default="", blank=True)
    autocreated = models.BooleanField("Automatisch generiert", default=False)

    token = models.UUIDField("Token", default=uuid.uuid4, editable=False)

    time_created = models.DateTimeField("Erstellt um", auto_now_add=True)

    @admin.display(description="Anhang")
    def __str__(self):
        return str(self.filename)

    def get_file_response(self, download=False):
        return FileResponse(storage.default_storage.open(self.file.path, 'rb'),
                            as_attachment=download, filename=self.filename)

    def get_url(self):
        """Get the public view online URL"""

        path = reverse("kmuhelper:attachment-view",
                       kwargs={"object_id": self.pk})
        return path+f"?token={self.token}"

    class Meta:
        verbose_name = "Anhang"
        verbose_name_plural = "Anhänge"
        default_permissions = ('add', 'change', 'view', 'delete', 'download')

    objects = AttachmentManager()

    # Custom delete

    def delete(self, *args, **kwargs):
        """Delete the associated file before deleting the model object"""
        self.file.delete()
        super().delete(*args, **kwargs)


class EMailAttachment(models.Model):
    attachment = models.ForeignKey(
        "Attachment", on_delete=models.PROTECT, related_name="emails")
    email = models.ForeignKey(
        "EMail", on_delete=models.CASCADE)

    @admin.display(description="E-Mail Anhang")
    def __str__(self):
        return "EMail-Anhang Verknüpfung"

    class Meta:
        verbose_name = "E-Mail Anhang"
        verbose_name_plural = "E-Mail Anhänge"

    objects = models.Manager()


class EMail(models.Model):
    typ = models.CharField("Typ", choices=EMAILTYPEN,
                           max_length=50, default="", blank=True)

    subject = models.CharField("Betreff", max_length=50)

    to = MultiEmailField("Empfänger")
    cc = MultiEmailField("CC", default="", blank=True)
    bcc = MultiEmailField("BCC", default="", blank=True)

    html_template = models.CharField("Dateiname der Vorlage", max_length=100)
    html_context = models.JSONField("Daten", default=dict, blank=True)

    token = models.UUIDField("Token", default=uuid.uuid4, editable=False)

    time_created = models.DateTimeField("Erstellt am", auto_now_add=True)
    time_sent = models.DateTimeField(
        "Gesendet um", blank=True, null=True, default=None)

    sent = models.BooleanField("Gesendet?", default=False)

    notes = models.TextField("Notizen", blank=True, default="")

    attachments = models.ManyToManyField(
        "Attachment", through="EMailAttachment")

    @admin.display(description="E-Mail")
    def __str__(self):
        return f"{self.subject} ({self.pk})"

    def render(self, online=False):
        """Render the email and return the rendered string"""

        context = dict(self.html_context)
        context["isonline"] = online
        if online:
            context["attachments"] = list(self.attachments.all())
        else:
            context["view_online_url"] = self.get_url_with_domain()
        return get_template("kmuhelper/emails/"+str(self.html_template)).render(context)

    def add_attachments(self, *attachments):
        """Add one or more Attachment objects to this EMail"""

        self.attachments.add(*attachments)
        self.save()

    def send(self, **options):
        """Send the mail with given attachments.
        Options are passed to django.core.mail.EmailMessage"""

        msg = mail.EmailMessage(
            subject=self.subject,
            body=self.render(),
            to=self.to.splitlines() if isinstance(self.to, str) else self.to,
            cc=self.cc.splitlines() if isinstance(self.cc, str) else self.cc,
            bcc=self.bcc.splitlines() if isinstance(self.bcc, str) else self.bcc,
            **options
        )

        if hasattr(settings, "KMUHELPER_LOG_EMAIL"):
            msg.bcc.append(settings.KMUHELPER_LOG_EMAIL)

        msg.content_subtype = "html"

        for attachment in self.attachments.all():
            msg.attach(filename=attachment.filename,
                       content=attachment.file.read())

        success = msg.send()

        log("ID:", self.pk, "- Subject:", self.subject, "- Success:", success)

        if success:
            self.time_sent = timezone.now()
            self.sent = True
            self.save()
        return success

    def get_url(self):
        """Get the public view online URL"""

        path = reverse("kmuhelper:email-view",
                       kwargs={"object_id": self.pk})
        return path+f"?token={self.token}"

    def get_url_with_domain(self):
        """Get the public view online URL with domain prefix"""

        domain = getattr(settings, "KMUHELPER_DOMAIN", None)

        if domain:
            url = self.get_url()
            return domain+url

        log("[orange_red1]Einstellung KMUHELPER_DOMAIN ist nicht gesetzt! " +
            "E-Mails werden ohne 'online ansehen' Links versendet!")
        return None

    class Meta:
        verbose_name = "E-Mail"
        verbose_name_plural = "E-Mails"
        default_permissions = ('add', 'change', 'view', 'delete', 'send')

    objects = models.Manager()
