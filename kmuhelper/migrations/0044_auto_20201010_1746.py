# Generated by Django 3.1.2 on 2020-10-10 15:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kmuhelper', '0043_auto_20201010_1739'),
    ]

    operations = [
        migrations.AlterField(
            model_name='einstellung',
            name='boo',
            field=models.BooleanField(blank=True, default=False, verbose_name='Inhalt (Wahrheitswert)'),
        ),
        migrations.AlterField(
            model_name='geheime_einstellung',
            name='boo',
            field=models.BooleanField(blank=True, default=False, verbose_name='Inhalt (Wahrheitswert)'),
        ),
    ]
