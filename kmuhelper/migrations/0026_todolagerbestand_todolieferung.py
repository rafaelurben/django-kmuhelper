# Generated by Django 3.0.4 on 2020-07-17 12:34

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("kmuhelper", "0025_auto_20200716_2126"),
    ]

    operations = [
        migrations.CreateModel(
            name="ToDoLagerbestand",
            fields=[],
            options={
                "verbose_name": "Produkt",
                "verbose_name_plural": "Produkte",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("kmuhelper.produkt",),
        ),
        migrations.CreateModel(
            name="ToDoLieferung",
            fields=[],
            options={
                "verbose_name": "Lieferung",
                "verbose_name_plural": "Lieferungen",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("kmuhelper.lieferung",),
        ),
    ]
