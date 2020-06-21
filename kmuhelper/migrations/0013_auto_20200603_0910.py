# Generated by Django 3.0.4 on 2020-06-03 07:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kmuhelper', '0012_auto_20200603_0859'),
    ]

    operations = [
        migrations.AlterField(
            model_name='einstellung',
            name='char',
            field=models.CharField(blank=True, default='', max_length=250, verbose_name='Inhalt (Text)              '),
        ),
        migrations.AlterField(
            model_name='einstellung',
            name='floa',
            field=models.FloatField(blank=True, default=0.0, verbose_name='Inhalt (Fliesskommazahl)   '),
        ),
        migrations.AlterField(
            model_name='einstellung',
            name='inte',
            field=models.IntegerField(blank=True, default=0, verbose_name='Inhalt (Zahl)              '),
        ),
        migrations.AlterField(
            model_name='einstellung',
            name='text',
            field=models.TextField(blank=True, default='', verbose_name='Inhalt (Mehrzeiliger Text) '),
        ),
        migrations.AlterField(
            model_name='einstellung',
            name='url',
            field=models.URLField(blank=True, default='', verbose_name='Inhalt (Url)               '),
        ),
    ]