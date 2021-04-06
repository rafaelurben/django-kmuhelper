# Generated by Django 3.1.7 on 2021-04-03 18:08

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kmuhelper', '0054_auto_20210403_1941'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bestellung',
            name='zahlungskonditionen',
            field=models.CharField(default='0:30', help_text="Skonto und Zahlfrist nach Syntaxdefinition von Swico. z.B. '2:15;0:30'", max_length=16, validators=[django.core.validators.RegexValidator('^[0-9]+:[0-9]+(;[0-9]+:[0-9]+)*$')], verbose_name='Zahlungskonditionen'),
        ),
    ]