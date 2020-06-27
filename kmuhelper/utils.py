from django.http import HttpResponse, FileResponse
from django.conf import settings
from django.core import mail
from django.template.loader import get_template
from django.utils import translation

from datetime import datetime
from io import BytesIO
import os

################

def getfirstindex(data:list, search:list):
    for s in search:
        if s in data:
            return data.index(s)
    return None

def runden(preis):
    return float("{:.2f}".format(float(round(round(preis / 0.05) * 0.05, 2))))

def formatprice(preis):
    return "{:.2f}".format(float(preis))

def clean(string, lang="de"):
    if "[:"+lang+"]" in string:
        return string.split("[:"+lang+"]")[1].split("[:")[0]
    elif "[:de]" in string:
        return string.split("[:de]")[1].split("[:")[0]
    else:
        return string

###############

def send_mail(subject:str, to:str, template_name:str, context:dict={}, headers:dict={}, bcc:list=[]):
    html_message = get_template("kmuhelper/emails/"+template_name).render(context)

    msg = mail.EmailMessage(
        subject=subject,
        body=html_message,
        to=[to],
        headers=headers,
        bcc=bcc
    )

    msg.content_subtype = "html"

    return bool(msg.send())

def send_pdf(subject:str, to:str, template_name:str, pdf:BytesIO, pdf_filename:str="file.pdf", context:dict={}, headers:dict={}, bcc:list=[]):
    html_message = get_template("kmuhelper/emails/"+template_name).render(context)

    msg = mail.EmailMessage(
        subject=subject,
        body=html_message,
        to=[to],
        headers=headers,
        bcc=bcc
    )

    msg.content_subtype = "html"
    msg.attach(filename=pdf_filename, content=pdf.read(), mimetype="application/pdf")

    return bool(msg.send())

###############

def modulo10rekursiv(strNummer):
    intTabelle = [
        [0,9,4,6,8,2,7,1,3,5],
        [9,4,6,8,2,7,1,3,5,0],
        [4,6,8,2,7,1,3,5,0,9],
        [6,8,2,7,1,3,5,0,9,4],
        [8,2,7,1,3,5,0,9,4,6],
        [2,7,1,3,5,0,9,4,6,8],
        [7,1,3,5,0,9,4,6,8,2],
        [1,3,5,0,9,4,6,8,2,7],
        [3,5,0,9,4,6,8,2,7,1],
        [5,0,9,4,6,8,2,7,1,3],
    ]
    strNummer = strNummer.replace(" ","")
    uebertrag = 0
    for num in strNummer:
        uebertrag = intTabelle[uebertrag][int(num)]
    return [0,9,8,7,6,5,4,3,2,1][uebertrag]
