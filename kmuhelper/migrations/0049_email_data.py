# Generated by Django 3.1.3 on 2021-02-02 21:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("kmuhelper", "0048_auto_20210202_2101"),
    ]

    operations = [
        migrations.AddField(
            model_name="email",
            name="data",
            field=models.JSONField(default=dict, verbose_name="Extradaten"),
        ),
    ]
