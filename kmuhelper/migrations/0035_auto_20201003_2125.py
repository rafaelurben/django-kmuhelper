# Generated by Django 3.1 on 2020-10-03 19:25
# pylint: disable=no-member

import django.core.validators
from django.db import migrations, models
from kmuhelper.models import Bestellungskosten


def resave_bestellungskosten(apps, schema_editor):
    for k in Bestellungskosten.objects.all():
        k.save()


class Migration(migrations.Migration):

    dependencies = [
        ('kmuhelper', '0034_bestellungsposten_rabatt'),
    ]

    operations = [
        migrations.AddField(
            model_name='bestellungskosten',
            name='kostenpreis',
            field=models.FloatField(default=0.0, verbose_name='Kostenpreis (exkl. MwSt)'),
        ),
        migrations.AddField(
            model_name='bestellungskosten',
            name='rabatt',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Rabatt in %'),
        ),
        migrations.AlterField(
            model_name='bestellungsposten',
            name='produktpreis',
            field=models.FloatField(default=0.0, verbose_name='Produktpreis (exkl. MwSt)'),
        ),
        migrations.RunPython(resave_bestellungskosten),
    ]
