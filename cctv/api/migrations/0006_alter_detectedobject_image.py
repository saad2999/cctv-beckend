# Generated by Django 5.1.1 on 2024-11-13 12:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_alter_detectedobject_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='detectedobject',
            name='image',
            field=models.ImageField(upload_to='media/detected/'),
        ),
    ]
