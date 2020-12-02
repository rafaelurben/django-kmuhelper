# Generated by Django 3.1.2 on 2020-10-09 21:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kmuhelper', '0039_auto_20201006_1803'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lieferung',
            name='notiz',
        ),
        migrations.AddField(
            model_name='notiz',
            name='lieferung',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notiz', to='kmuhelper.lieferung'),
        ),
    ]