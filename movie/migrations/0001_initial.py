# Generated by Django 4.2.7 on 2023-11-03 17:03

from django.db import migrations, models
import django.db.models.deletion
import movie.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Artist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('biography', models.TextField()),
                ('image', models.ImageField(upload_to=movie.models.artist_path_file)),
            ],
        ),
        migrations.CreateModel(
            name='Cast',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_private', models.BooleanField()),
                ('is_confirm', models.BooleanField()),
                ('poster', models.ImageField(upload_to=movie.models.collection_poster_path_file)),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField()),
                ('title', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_confirm', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('flag', models.ImageField(upload_to=movie.models.country_flag_path_file)),
            ],
        ),
        migrations.CreateModel(
            name='CountryMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Episode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('name', models.CharField(max_length=100)),
                ('video', models.FileField(upload_to=movie.models.episode_path_file)),
                ('time', models.IntegerField()),
                ('synopsis', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Genre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('poster', models.ImageField(upload_to=movie.models.genre_poster_path_file)),
            ],
        ),
        migrations.CreateModel(
            name='GenreMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('trailer', models.FileField(upload_to=movie.models.trailer_path_file)),
                ('synopsis', models.TextField()),
                ('thumbnail', models.ImageField(upload_to=movie.models.media_thumbnail_path_file)),
                ('poster', models.ImageField(upload_to=movie.models.media_poster_path_file)),
                ('value', models.CharField(choices=[('Free', 'Free'), ('Subscription', 'Subscription'), ('Advertising', 'Advertising')], default='Free', max_length=15)),
                ('release_date', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='MediaGallery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=movie.models.gallery_path_file)),
            ],
        ),
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video', models.FileField(upload_to=movie.models.movie_path_file)),
                ('time', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.SmallIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='TvSeries',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('season_number', models.IntegerField()),
                ('media', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='movie.media')),
            ],
        ),
        migrations.CreateModel(
            name='Slider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('title', models.CharField(max_length=250)),
                ('priority', models.IntegerField()),
                ('media', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='movie.media')),
            ],
        ),
        migrations.CreateModel(
            name='SeenMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('episode', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='movie.episode')),
                ('movie', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='movie.movie')),
            ],
        ),
    ]