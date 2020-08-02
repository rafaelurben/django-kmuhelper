# Generated by Django 3.0.4 on 2020-08-02 19:05

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kmuhelper', '0032_auto_20200802_0018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ansprechpartner',
            name='email',
            field=models.EmailField(help_text='Auf Rechnung ersichtlich!', max_length=254, verbose_name='E-Mail'),
        ),
        migrations.AlterField(
            model_name='ansprechpartner',
            name='name',
            field=models.CharField(help_text='Auf Rechnung ersichtlich!', max_length=50, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='ansprechpartner',
            name='telefon',
            field=models.CharField(help_text='Auf Rechnung ersichtlich!', max_length=50, verbose_name='Telefon'),
        ),
        migrations.AlterField(
            model_name='zahlungsempfaenger',
            name='adresszeile1',
            field=models.CharField(max_length=70, verbose_name="Strasse und Hausnummer oder 'Postfach'"),
        ),
        migrations.AlterField(
            model_name='zahlungsempfaenger',
            name='firmenname',
            field=models.CharField(help_text='Name der Firma', max_length=70, verbose_name='Firmennname'),
        ),
        migrations.AlterField(
            model_name='zahlungsempfaenger',
            name='firmenuid',
            field=models.CharField(help_text='UID der Firma - Format: CHE-123.456.789 (Mehrwertsteuernummer)', max_length=15, validators=[django.core.validators.RegexValidator('^CHE-[0-9]{3}\\.[0-9]{3}\\.[0-9]{3}$', 'Bite benutze folgendes Format: CHE-123.456.789')], verbose_name='Firmen-UID'),
        ),
        migrations.AlterField(
            model_name='zahlungsempfaenger',
            name='logourl',
            field=models.URLField(help_text='URL eines Bildes (.jpg/.png) - Wird auf die Rechnung gedruckt.', validators=[django.core.validators.RegexValidator('^[0-9a-zA-Z\\-\\.\\|\\?\\(\\)\\*\\+&"\'_:;/]+\\.(png|jpg)$', 'Nur folgende Zeichen gestattet: 0-9a-zA-Z-_.:;/|?&()"\'*+ - Muss auf .jpg/.png enden.')], verbose_name='Logo (URL)'),
        ),
        migrations.AlterField(
            model_name='zahlungsempfaenger',
            name='qriban',
            field=models.CharField(help_text='QR-IBAN mit Leerzeichen', max_length=26, validators=[django.core.validators.RegexValidator('^CH[0-9]{2}\\s3[0-9]{3}\\s[0-9]{4}\\s[0-9]{4}\\s[0-9]{4}\\s[0-9]{1}$', 'Bite benutze folgendes Format: CHxx 3xxx xxxx xxxx xxxx x')], verbose_name='QR-IBAN'),
        ),
        migrations.AlterField(
            model_name='zahlungsempfaenger',
            name='webseite',
            field=models.URLField(help_text='Auf der Rechnung ersichtlich!', verbose_name='Webseite'),
        ),
    ]