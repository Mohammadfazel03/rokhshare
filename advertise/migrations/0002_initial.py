# Generated by Django 4.2.7 on 2023-11-03 17:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('movie', '0001_initial'),
        ('advertise', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='advertiseseen',
            name='episode',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='movie.episode'),
        ),
        migrations.AddField(
            model_name='advertiseseen',
            name='movie',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='movie.movie'),
        ),
    ]
