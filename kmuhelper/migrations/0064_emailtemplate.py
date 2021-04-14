# Generated by Django 3.2 on 2021-04-13 22:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kmuhelper', '0063_help_texts'),
    ]

    operations = [
        migrations.CreateModel(
            name='EMailTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50, verbose_name='Titel')),
                ('description', models.TextField(blank=True, default='', verbose_name='Beschreibung')),
                ('mail_subject', models.CharField(max_length=50, verbose_name='Betreff')),
                ('mail_text', models.TextField(verbose_name='Text')),
                ('mail_template', models.CharField(default='default.html', max_length=50, verbose_name='Designvorlage')),
                ('mail_context', models.JSONField(blank=True, default=dict, null=True, verbose_name='Daten')),
            ],
            options={
                'verbose_name': 'E-Mail Vorlage',
                'verbose_name_plural': 'E-Mail Vorlagen',
            },
        ),
    ]
