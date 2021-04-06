# pylint: disable=no-member

from django.db import models
from django.core import mail
from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.http import FileResponse
from django.template.loader import get_template
from django.utils.html import mark_safe
from django.utils.safestring import mark_safe
from django.urls import reverse

###################

from rich import print

prefix = "[deep_pink4][KMUHelper XMLImport][/] -"

def log(string, *args):
    print(prefix, string, *args)


class XMLFile(models.Model):
    pass


class XMLFileEntry(models.Model):
    pass