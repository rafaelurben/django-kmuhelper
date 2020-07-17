# Generated by Django 3.0.4 on 2020-07-15 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kmuhelper', '0017_todoentry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='todoentry',
            name='beschrieb',
            field=models.TextField(blank=True, default='', verbose_name='Beschrieb'),
        ),
        migrations.AlterField(
            model_name='todoentry',
            name='priority',
            field=models.IntegerField(blank=True, default=0, verbose_name='Priorität'),
        ),
    ]