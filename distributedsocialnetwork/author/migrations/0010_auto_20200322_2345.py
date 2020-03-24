# Generated by Django 3.0.3 on 2020-03-22 23:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('author', '0009_auto_20200322_2204'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='bio',
            field=models.CharField(blank=True, default='', max_length=160),
        ),
        migrations.AlterField(
            model_name='author',
            name='email',
            field=models.EmailField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='author',
            name='first_name',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AlterField(
            model_name='author',
            name='last_name',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
    ]