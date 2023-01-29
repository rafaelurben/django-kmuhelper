# Generated by Django 4.1.5 on 2023-01-29 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("kmuhelper", "0086_rename_produktkategorie"),
    ]

    operations = [
        migrations.AddField(
            model_name="bestellung",
            name="bezahlt_am",
            field=models.DateField(
                blank=True, default=None, null=True, verbose_name="Bezahlt am"
            ),
        ),
        migrations.AddField(
            model_name="bestellung",
            name="versendet_am",
            field=models.DateField(
                blank=True, default=None, null=True, verbose_name="Versendet am"
            ),
        ),
    ]
