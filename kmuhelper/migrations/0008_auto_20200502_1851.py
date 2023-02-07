# Generated by Django 3.0.4 on 2020-05-02 16:51

import django.core.validators
from django.db import migrations, models
import kmuhelper.modules.main.models


class Migration(migrations.Migration):

    dependencies = [
        ('kmuhelper', '0007_auto_20200502_1530'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bestellung',
            name='order_key',
            field=models.CharField(blank=True, default=kmuhelper.modules.main.models.default_order_key, max_length=50, verbose_name='Bestellungs-Schlüssel'),
        ),
        migrations.AlterField(
            model_name='bestellung',
            name='trackingnummer',
            field=models.CharField(blank=True, default='', help_text='Bitte gib hier eine Trackingnummer der Schweizer Post ein. (optional)', max_length=25, validators=[django.core.validators.RegexValidator('^99\\.[0-9]{2}\\.[0-9]{6}\\.[0-9]{8}$', 'Bite benutze folgendes Format: 99.xx.xxxxxx.xxxxxxxx')], verbose_name='Trackingnummer'),
        ),
    ]
