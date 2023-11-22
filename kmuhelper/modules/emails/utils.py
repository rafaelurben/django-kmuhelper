from io import BytesIO

from django.core import mail
from django.template.loader import get_template

# These utils are not currently used, but they are still here for reference


def send_mail(subject: str, to: str, template_name: str, context: dict = {}, **kwargs):
    html_message = get_template("kmuhelper/emails/" + template_name).render(context)

    msg = mail.EmailMessage(subject=subject, body=html_message, to=[to], **kwargs)

    msg.content_subtype = "html"

    return bool(msg.send())


def send_pdf(
    subject: str,
    to: str,
    template_name: str,
    pdf: BytesIO,
    pdf_filename: str = "file.pdf",
    context: dict = {},
    **kwargs
):
    html_message = get_template("kmuhelper/emails/" + template_name).render(context)

    msg = mail.EmailMessage(subject=subject, body=html_message, to=[to], **kwargs)

    msg.content_subtype = "html"
    msg.attach(filename=pdf_filename, content=pdf.read(), mimetype="application/pdf")

    return bool(msg.send())
