# Generated by Django 3.0.3 on 2020-03-07 22:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4,
                                        editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100)),
                ('source', models.URLField(max_length=100)),
                ('origin', models.URLField(max_length=100)),
                ('description', models.CharField(max_length=120)),
                ('contentType', models.CharField(choices=[('text/markdown', 'text/markdown'), ('text/plain', 'text/plain'), ('application/base64', 'application/base64'), (
                    'image/png;base64', 'image/png;base64'), ('image/jpeg;base64', 'image/jpeg;base64')], default='text/plain', max_length=20)),
                ('content', models.TextField()),
                ('categories', models.CharField(blank=True, max_length=200)),
                ('published', models.DateTimeField()),
                ('visibility', models.CharField(choices=[('PUBLIC', 'Public'), ('FOAF', 'Friends of Friends'), (
                    'FRIENDS', 'Friends Only'), ('PRIVATE', 'Private'), ('SERVERONLY', 'Server Only')], default='PUBLIC', max_length=10)),
                ('visibleTo', models.CharField(blank=True, max_length=200)),
                ('unlisted', models.BooleanField(default=False)),
                ('author', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-published'],
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('comment', models.TextField()),
                ('published', models.DateTimeField()),
                ('contentType', models.CharField(choices=[('text/markdown', 'text/markdown'), ('text/plain', 'text/plain'), ('application/base64', 'application/base64'), (
                    'image/png;base64', 'image/png;base64'), ('image/jpeg;base64', 'image/jpeg;base64')], default='text/plain', max_length=20)),
                ('id', models.UUIDField(default=uuid.uuid4,
                                        primary_key=True, serialize=False)),
                ('author', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('post_id', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, to='post.Post')),
            ],
        ),
    ]
