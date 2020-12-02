# Generated by Django 3.1.2 on 2020-10-18 15:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kmuhelper', '0045_auto_20201018_1419'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bestellung',
            name='rechnung_gesendet',
        ),
        migrations.AddField(
            model_name='bestellung',
            name='rechnungsemail',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='kmuhelper.email'),
        ),
        migrations.AlterField(
            model_name='email',
            name='html_context',
            field=models.JSONField(default=dict, verbose_name='Daten'),
        ),
        migrations.AlterField(
            model_name='email',
            name='typ',
            field=models.CharField(blank=True, choices=[('', '-'), ('kunde_registriert', 'Registrierungsmail Kunde'), ('rechnung', 'Rechnung')], default='', max_length=50, verbose_name='Typ'),
        ),
    ]