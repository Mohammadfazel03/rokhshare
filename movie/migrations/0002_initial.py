# Generated by Django 4.2.7 on 2023-11-03 17:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('movie', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='seenmedia',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='season',
            name='series',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='movie.tvseries'),
        ),
        migrations.AddField(
            model_name='rating',
            name='episode',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='movie.episode'),
        ),
        migrations.AddField(
            model_name='rating',
            name='movie',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='movie.movie'),
        ),
        migrations.AddField(
            model_name='rating',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='movie',
            name='media',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='movie.media'),
        ),
        migrations.AddField(
            model_name='mediagallery',
            name='episode',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='movie.episode'),
        ),
        migrations.AddField(
            model_name='mediagallery',
            name='movie',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='movie.movie'),
        ),
        migrations.AddField(
            model_name='genremedia',
            name='genre',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='movie.genre'),
        ),
        migrations.AddField(
            model_name='genremedia',
            name='media',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='movie.media'),
        ),
        migrations.AddField(
            model_name='episode',
            name='season',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='movie.season'),
        ),
        migrations.AddField(
            model_name='countrymedia',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='movie.country'),
        ),
        migrations.AddField(
            model_name='countrymedia',
            name='media',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='movie.media'),
        ),
        migrations.AddField(
            model_name='comment',
            name='episode',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='movie.episode'),
        ),
        migrations.AddField(
            model_name='comment',
            name='movie',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='movie.movie'),
        ),
        migrations.AddField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='collection',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='cast',
            name='artist',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='movie.artist'),
        ),
        migrations.AddField(
            model_name='cast',
            name='episode',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='movie.episode'),
        ),
        migrations.AddField(
            model_name='cast',
            name='movie',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='movie.movie'),
        ),
    ]
