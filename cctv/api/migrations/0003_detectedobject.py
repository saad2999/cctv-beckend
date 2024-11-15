# Generated by Django 5.1.1 on 2024-11-12 05:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_remove_camera_ip_address'),
    ]

    operations = [
        migrations.CreateModel(
            name='DetectedObject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=50)),
                ('confidence', models.FloatField()),
                ('image', models.ImageField(upload_to='detected_objects/')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
