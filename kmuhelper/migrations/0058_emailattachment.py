# Generated by Django 3.2 on 2021-04-12 19:57

from django.db import migrations, models
import kmuhelper.emails.models


class Migration(migrations.Migration):

    dependencies = [
        ('kmuhelper', '0057_auto_20210412_1633'),
    ]

    operations = [
        migrations.CreateModel(
            name='EMailAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=50, verbose_name='Dateiname')),
                ('file', models.FileField(upload_to=kmuhelper.emails.models.getfilepath, verbose_name='Datei')),
                ('description', models.TextField(blank=True, default='', verbose_name='Beschreibung')),
                ('autocreated', models.BooleanField(default=False, verbose_name='Automatisch generiert')),
                ('time_created', models.DateTimeField(auto_now_add=True, verbose_name='Erstellt um')),
            ],
            options={
                'verbose_name': 'E-Mail Anhang',
                'verbose_name_plural': 'E-Mail Anhänge',
                'default_permissions': ('add', 'change', 'view', 'delete', 'download'),
            },
        ),
    ]
