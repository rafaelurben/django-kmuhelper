# Generated by Django 3.2 on 2021-10-05 21:29

import django.core.validators
from django.db import migrations, models
import kmuhelper.modules.main.models


class Migration(migrations.Migration):

    dependencies = [
        ('kmuhelper', '0075_einstellung_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bestellung',
            name='zahlungskonditionen',
            field=models.CharField(default=kmuhelper.modules.main.models.defaultzahlungskonditionen, help_text="Skonto und Zahlfrist nach Syntaxdefinition von Swico. z.B. '2:15;0:30' steht für 2% Skonto bei Zahlung in 15 Tagen und eine Zahlungsfrist von 30 Tagen.", max_length=16, validators=[django.core.validators.RegexValidator('^[0-9]+:[0-9]+(;[0-9]+:[0-9]+)*$', "Bitte benutze folgendes Format: 'p:d;p:d' - p = Skonto in %; d = Tage")], verbose_name='Zahlungskonditionen'),
        ),
    ]
