# Generated by Django 3.1.2 on 2020-10-18 12:19

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("kmuhelper", "0044_auto_20201010_1746"),
    ]

    operations = [
        migrations.CreateModel(
            name="EMail",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "typ",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("", "-"),
                            ("kunde_registriert", "Registrierungsmail Kunde"),
                        ],
                        default="",
                        max_length=50,
                        verbose_name="Typ",
                    ),
                ),
                ("subject", models.CharField(max_length=50, verbose_name="Betreff")),
                ("to", models.EmailField(max_length=254, verbose_name="Empfänger")),
                (
                    "html_template",
                    models.CharField(max_length=100, verbose_name="Name der Vorlage"),
                ),
                ("html_context", models.JSONField(verbose_name="Daten")),
                (
                    "token",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, verbose_name="Token"
                    ),
                ),
                (
                    "time_created",
                    models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am"),
                ),
                (
                    "time_sent",
                    models.DateTimeField(
                        blank=True, default=None, null=True, verbose_name="Gesendet um"
                    ),
                ),
            ],
            options={
                "verbose_name": "E-Mail",
                "verbose_name_plural": "E-Mails",
            },
        ),
        migrations.RemoveField(
            model_name="kunde",
            name="registrierungsemail_gesendet",
        ),
        migrations.AddField(
            model_name="kunde",
            name="registrierungsemail",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="kmuhelper.email",
            ),
        ),
    ]
