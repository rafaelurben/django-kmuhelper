# Generated by Django 3.0.4 on 2020-07-15 17:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("kmuhelper", "0018_auto_20200715_1639"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bestellung",
            name="kunde",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="kmuhelper.Kunde",
            ),
        ),
    ]
