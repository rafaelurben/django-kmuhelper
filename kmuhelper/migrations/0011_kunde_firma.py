# Generated by Django 3.0.4 on 2020-05-31 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kmuhelper', '0010_kunde_webseite'),
    ]

    operations = [
        migrations.AddField(
            model_name='kunde',
            name='firma',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='Firma'),
        ),
    ]
