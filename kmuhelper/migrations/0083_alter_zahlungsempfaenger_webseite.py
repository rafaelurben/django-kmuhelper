# Generated by Django 4.1.5 on 2023-01-29 16:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kmuhelper', '0082_rename_kostenpreis_bestellungskosten_preis_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zahlungsempfaenger',
            name='webseite',
            field=models.URLField(blank=True, default='', help_text='Auf der Rechnung ersichtlich, sofern vorhanden!', verbose_name='Webseite'),
        ),
    ]