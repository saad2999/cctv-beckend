# Generated by Django 5.1.1 on 2024-09-30 09:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='camera',
            name='ip_address',
        ),
    ]
