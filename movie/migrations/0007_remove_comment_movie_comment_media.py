# Generated by Django 4.2.7 on 2024-03-27 08:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('movie', '0006_remove_collection_collections_remove_rating_movie_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='movie',
        ),
        migrations.AddField(
            model_name='comment',
            name='media',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='movie.media'),
        ),
    ]