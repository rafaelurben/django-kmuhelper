# Generated by Django 3.1.2 on 2020-10-10 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kmuhelper', '0041_auto_20201010_1630'),
    ]

    operations = [
        migrations.AlterField(
            model_name='einstellung',
            name='id',
            field=models.CharField(max_length=50, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='einstellung',
            name='name',
            field=models.CharField(max_length=200, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='geheime_einstellung',
            name='id',
            field=models.CharField(max_length=50, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]