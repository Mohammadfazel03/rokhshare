# Generated by Django 4.2.7 on 2024-06-19 06:18

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('advertise', '0003_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='advertiseseen',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]