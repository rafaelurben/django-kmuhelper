# Generated by Django 3.0.4 on 2020-07-16 13:53

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("kmuhelper", "0022_auto_20200716_1534"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="ToDoEntry",
            new_name="ToDoNotiz",
        ),
        migrations.AlterModelOptions(
            name="todonotiz",
            options={"verbose_name": "ToDo Notiz", "verbose_name_plural": "ToDo Notiz"},
        ),
    ]
