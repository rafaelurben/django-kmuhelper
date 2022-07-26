import uuid

from rich import print

from django.db import models
from django.contrib import admin, messages
from django.core import mail
from django.core.files import storage
from django.http import FileResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.loader import get_template

from kmuhelper.external.multi_email_field.fields import MultiEmailField

from kmuhelper import settings
from kmuhelper.overrides import CustomModel


def log(string, *args):
    print("[deep_pink4][KMUHelper E-Mails][/] -", string, *args)


#####


def getfilepath(instance, filename):
    return 'attachments/' + \
        timezone.now().strftime('%Y-%m-%d_%H-%M-%S_') + filename


class AttachmentManager(models.Manager):
    """Manager for the 'Attachment' model"""

    def create_from_binary(self, filename, content):
        """Create an Attachment object from binary data"""

        filepath = getfilepath(None, filename)

        file = storage.default_storage.save(filepath, content)
        return self.create(
            filename=filename,
            file=file,
            autocreated=True,
        )


class Attachment(CustomModel):
    """Model representing an attachment"""

    filename = models.CharField(
        verbose_name="Dateiname",
        max_length=50,
    )
    file = models.FileField(
        verbose_name="Datei",
        upload_to=getfilepath,
        storage=storage.default_storage,
    )

    description = models.TextField(
        verbose_name="Beschreibung",
        default="",
        blank=True,
    )
    autocreated = models.BooleanField(
        verbose_name="Automatisch generiert",
        default=False,
    )

    token = models.UUIDField(
        verbose_name="Token",
        default=uuid.uuid4,
        editable=False,
    )

    time_created = models.DateTimeField(
        verbose_name="Erstellt um",
        auto_now_add=True,
    )

    @admin.display(description="Anhang")
    def __str__(self):
        return f"{self.filename} ({self.pk})"

    def get_file_response(self, download=False):
        """Get this attachment as a file response"""

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

    admin_icon = "fas fa-paperclip"

    # Custom delete

    def delete(self, *args, **kwargs):
        """Delete the associated file before deleting the model object"""

        self.file.delete()
        super().delete(*args, **kwargs)


class EMailAttachment(CustomModel):
    """Model representing the connection between 'EMail' and 'Attachment'"""

    attachment = models.ForeignKey(
        to='Attachment',
        on_delete=models.PROTECT,
        related_name="emails",
    )
    email = models.ForeignKey(
        to='EMail',
        on_delete=models.CASCADE,
    )

    @admin.display(description="E-Mail-Anhang")
    def __str__(self):
        return f'({self.email.pk}) -> {self.attachment}'

    class Meta:
        verbose_name = "E-Mail-Anhang"
        verbose_name_plural = "E-Mail-Anhänge"

    objects = models.Manager()


class EMail(CustomModel):
    """Model representing an email"""

    subject = models.CharField(
        verbose_name="Betreff",
        max_length=50,
        help_text="Wird Standardmässig auch als Untertitel verwendet.",
    )

    to = MultiEmailField(
        verbose_name="Empfänger",
        help_text="Direkte Empfänger",
    )
    cc = MultiEmailField(
        verbose_name="CC",
        default="",
        blank=True,
        help_text="Kopie",
    )
    bcc = MultiEmailField(
        verbose_name="BCC",
        default="",
        blank=True,
        help_text="Blindkopie",
    )

    html_template = models.CharField(
        verbose_name="Designvorlage",
        default="default.html",
        max_length=50,
        help_text="Dateiname der Designvorlage unter 'kmuhelper/emails/'.",
    )
    text = models.TextField(
        verbose_name="Text",
        default="",
        blank=True,
        help_text="Hauptinhalt - wird nicht von allen Designvorlagen verwendet. " +
                  "Links und E-Mail Adressen werden automatisch verlinkt.",
    )
    html_context = models.JSONField(
        verbose_name="Daten",
        default=dict,
        blank=True,
        null=True,
        help_text="Daten im JSON-Format, mit welchen die Designvorlage befüllt wird.",
    )

    token = models.UUIDField(
        verbose_name="Token",
        default=uuid.uuid4,
        editable=False,
    )

    time_created = models.DateTimeField(
        verbose_name="Erstellt am",
        auto_now_add=True,
        help_text="Datum und Zeit der Erstellung dieser E-Mail.",
    )
    time_sent = models.DateTimeField(
        verbose_name="Gesendet um",
        blank=True,
        null=True,
        default=None,
        help_text="Datum und Zeit des letzten erfolgreichen Sendeversuches.",
    )

    sent = models.BooleanField(
        verbose_name="Gesendet?",
        default=False,
    )

    notes = models.TextField(
        verbose_name="Notizen",
        blank=True,
        default="",
        help_text="Diese Notizen haben keine Einwirkung auf die E-Mail selbst.",
    )

    attachments = models.ManyToManyField(
        to='Attachment',
        through='EMailAttachment',
    )

    @admin.display(description="E-Mail")
    def __str__(self):
        return f"{self.subject} ({self.pk})"

    def is_valid(self, request=None):
        """Check if the email is valid.
        If not, add messages to request.

        Returns:
            0: Has errors
            1: Has warnings
            2: No warnings or errors
        """

        template = f"kmuhelper/emails/{self.html_template}"
        errors = []
        warnings = []

        # Check 1: Template

        try:
            get_template(template)
        except TemplateDoesNotExist:
            errors.append(
                f"Vorlage '{template}' wurde nicht gefunden."
            )
        except TemplateSyntaxError as error:
            errors.append(
                f"Vorlage '{template}' enthält ungültige Syntax: {error}"
            )

        # Check 2: Receiver

        if not self.to:
            warnings.append(
                "Nachricht hat keine(n) Empfänger!"
            )

        # Add messages and return

        if request:
            for msg in errors:
                messages.error(request, msg)
            for msg in warnings:
                messages.warning(request, msg)

        haserrors = len(errors) > 0
        haswarnings = len(warnings) > 0
        return 0 if haserrors else 1 if haswarnings else 2

    def get_context(self):
        """Get the context for rendering"""

        ctx = dict(self.html_context) if self.html_context is not None else {}

        defaultcontext = settings.get_file_setting(
            "KMUHELPER_EMAILS_DEFAULT_CONTEXT", {})
        signature = settings.get_db_setting("email-signature", "") or \
            defaultcontext.get("postcontent", "")

        data = {
            **defaultcontext,
            "subtitle": self.subject,
            "postconent": signature,
            **ctx,
            "text": self.text,
        }

        return data

    def render(self, online=False):
        """Render the email and return the rendered string"""

        context = self.get_context()

        if online:
            context["isonline"] = True
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

        if settings.has_file_setting("KMUHELPER_LOG_EMAIL"):
            msg.bcc.append(settings.get_file_setting("KMUHELPER_LOG_EMAIL"))

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

        domain = settings.get_file_setting("KMUHELPER_DOMAIN", None)

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

    admin_icon = "fas fa-envelope"


class EMailTemplate(CustomModel):
    """Model representing an email template (not to confuse with design template)"""

    title = models.CharField(
        verbose_name="Titel",
        max_length=50,
    )
    description = models.TextField(
        verbose_name="Beschreibung",
        default="",
        blank=True,
    )

    mail_to = models.CharField(
        verbose_name="Empfänger",
        max_length=50,
        default="",
        blank=True,
    )
    mail_subject = models.CharField(
        verbose_name="Betreff",
        max_length=50,
    )
    mail_text = models.TextField(
        verbose_name="Text",
    )
    mail_template = models.CharField(
        verbose_name="Designvorlage",
        default="default.html",
        max_length=50,
    )
    mail_context = models.JSONField(
        verbose_name="Daten",
        default=dict,
        blank=True,
        null=True,
    )

    @admin.display(description="E-Mail-Vorlage")
    def __str__(self):
        return f"{self.title} ({self.pk})"

    @admin.display(description="Vorlage benutzen")
    def get_use_link(self):
        link = reverse("admin:kmuhelper_emailtemplate_use", args=[self.pk])
        text = "Vorlage benutzen"
        return format_html('<a href="{}">{}</a>', link, text)

    def create_mail(self, variables=dict()):
        """Use this template and replace variables"""

        def parse_vars(text):
            for var in variables:
                vartext = f'@{ var.upper() }@'
                varcontent = variables[var]
                text = text.replace(vartext, varcontent)
            return text

        email = EMail.objects.create(
            to=parse_vars(self.mail_to),
            subject=parse_vars(self.mail_subject),
            text=parse_vars(self.mail_text),
            html_template=self.mail_template,
            html_context=self.mail_context,
        )

        return email

    class Meta:
        verbose_name = "E-Mail-Vorlage"
        verbose_name_plural = "E-Mail-Vorlagen"

    objects = models.Manager()

    admin_icon = "fas fa-envelope-open-text"
