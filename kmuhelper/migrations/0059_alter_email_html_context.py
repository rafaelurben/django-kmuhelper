# Generated by Django 3.2 on 2021-04-13 15:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("kmuhelper", "0058_auto_20210413_0101"),
    ]

    operations = [
        migrations.AlterField(
            model_name="email",
            name="html_context",
            field=models.JSONField(
                blank=True, default=dict, null=True, verbose_name="Daten"
            ),
        ),
    ]
