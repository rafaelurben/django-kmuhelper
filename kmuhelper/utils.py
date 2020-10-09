from django.http import HttpResponse, FileResponse
from django.conf import settings
from django.core import mail
from django.template.loader import get_template
from django.utils import translation

from datetime import datetime
from io import BytesIO

import sys
import requests

################


def python_version():
    return str(sys.version.split(" ")[0])

def _package_versions_pypi(project, testpypi=False):
    from packaging.version import Version, InvalidVersion
    url = "https://"+("test." if testpypi else "")+"pypi.org/pypi/"+project+"/json"
    versions = requests.get(url).json()["releases"].keys()
    versions_safe = []
    for v in versions:
        try:
            Version(v)
            versions_safe.append(v)
        except (InvalidVersion):
            continue
    return sorted(versions_safe, key=Version)

def package_version(package, testpypi=False):
    from packaging.version import parse as parse_version
    import subprocess

    all_versions = _package_versions_pypi(package, testpypi)

    latest_version = all_versions[-1]

    # cmd = [sys.executable, '-m', 'pip', 'install', '{}==random'.format(package)]

    # if testpypi:
    #     cmd.insert(4, "https://test.pypi.org/simple/")
    #     cmd.insert(4, "-i")
    
    # latest_version = str(subprocess.run(cmd, capture_output=True, text=True))
    # latest_version = latest_version[latest_version.find('(from versions:')+15:]
    # latest_version = latest_version[:latest_version.find(')')]
    # latest_version = latest_version.replace(' ','').split(',')[-1]

    current_version = str(subprocess.run([sys.executable, '-m', 'pip', 'show', '{}'.format(package)], capture_output=True, text=True))
    current_version = current_version[current_version.find('Version:')+8:]
    current_version = current_version[:current_version.find('\\n')].replace(' ', '')
    return {
        #"all":      all_versions,
        "latest":    latest_version, 
        "current":   current_version, 
        "uptodate":  parse_version(latest_version) <= parse_version(current_version),
    }

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
