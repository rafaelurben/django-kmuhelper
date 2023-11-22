# Generated by Django 3.1.7 on 2021-04-03 15:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("kmuhelper", "0052_bestellung_rechnungsdatum"),
    ]

    operations = [
        migrations.AddField(
            model_name="bestellung",
            name="rechnungstext",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Wird auf der Rechnung gedruckt! Unterstützt <abbr title='<b>Fett</b><u>Unterstrichen</u><i>Kursiv</i>'>bestimmten XML markup</abbr>.",
                verbose_name="Rechnungstext",
            ),
        ),
    ]
