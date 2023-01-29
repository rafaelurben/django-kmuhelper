# Generated by Django 4.1.5 on 2023-01-29 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("kmuhelper", "0084_alter_produkt_mengenbezeichnung"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bestellungskosten",
            name="name",
            field=models.CharField(
                default="Zusätzliche Kosten",
                help_text="Unterstützt i18n: '[:de]Deutsch[:fr]Français[:it]Italiano[:en]English[:]'",
                max_length=500,
                verbose_name="Name",
            ),
        ),
        migrations.AlterField(
            model_name="kosten",
            name="name",
            field=models.CharField(
                default="Zusätzliche Kosten",
                help_text="Unterstützt i18n: '[:de]Deutsch[:fr]Français[:it]Italiano[:en]English[:]'",
                max_length=500,
                verbose_name="Name",
            ),
        ),
        migrations.AlterField(
            model_name="produkt",
            name="beschrieb",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Unterstützt i18n: '[:de]Deutsch[:fr]Français[:it]Italiano[:en]English[:]'",
                verbose_name="Beschrieb",
            ),
        ),
        migrations.AlterField(
            model_name="produkt",
            name="kurzbeschrieb",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Unterstützt i18n: '[:de]Deutsch[:fr]Français[:it]Italiano[:en]English[:]'",
                verbose_name="Kurzbeschrieb",
            ),
        ),
        migrations.AlterField(
            model_name="produkt",
            name="mengenbezeichnung",
            field=models.CharField(
                blank=True,
                default="Stück",
                help_text="Unterstützt i18n: '[:de]Deutsch[:fr]Français[:it]Italiano[:en]English[:]'",
                max_length=100,
                verbose_name="Mengenbezeichnung",
            ),
        ),
        migrations.AlterField(
            model_name="produkt",
            name="name",
            field=models.CharField(
                help_text="Unterstützt i18n: '[:de]Deutsch[:fr]Français[:it]Italiano[:en]English[:]'",
                max_length=500,
                verbose_name="Name",
            ),
        ),
    ]
