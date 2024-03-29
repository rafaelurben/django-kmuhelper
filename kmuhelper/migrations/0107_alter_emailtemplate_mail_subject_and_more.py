# Generated by Django 4.2.7 on 2023-11-22 22:20

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("kmuhelper", "0106_alter_app_arrival_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="emailtemplate",
            name="mail_subject",
            field=models.CharField(
                help_text="Unterstützt Platzhalter. Siehe unten für mehr Informationen.",
                max_length=50,
                verbose_name="Betreff",
            ),
        ),
        migrations.AlterField(
            model_name="emailtemplate",
            name="mail_text",
            field=models.TextField(
                help_text="Unterstützt Platzhalter. Siehe unten für mehr Informationen.",
                verbose_name="Text",
            ),
        ),
        migrations.AlterField(
            model_name="emailtemplate",
            name="mail_to",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Unterstützt Platzhalter. Siehe unten für mehr Informationen.",
                max_length=50,
                verbose_name="Empfänger",
            ),
        ),
    ]
