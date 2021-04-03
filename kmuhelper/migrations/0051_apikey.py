# Generated by Django 3.1.7 on 2021-03-24 19:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('kmuhelper', '0050_produkt_lieferant_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApiKey',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.UUIDField(default=uuid.uuid4, unique=True, verbose_name='Key')),
                ('name', models.CharField(blank=True, default='', max_length=100, verbose_name='Name')),
                ('read', models.BooleanField(default=True, verbose_name='Read permission?')),
                ('write', models.BooleanField(default=False, verbose_name='Write permission?')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Api key',
                'verbose_name_plural': 'Api keys',
            },
        ),
    ]