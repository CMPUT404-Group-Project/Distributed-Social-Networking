# Generated by Django 3.0.3 on 2020-03-07 01:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('author', '0021_auto_20200306_0407'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='id',
            field=models.CharField(default='7b3223dc5a62497188e558cd0cf6eb99', editable=False, max_length=32, primary_key=True, serialize=False, unique=True),
        ),
        migrations.AlterField(
            model_name='author',
            name='url',
            field=models.CharField(default='https://dsnfof.herokuapp.com/author/7b3223dc5a62497188e558cd0cf6eb99', editable=False, max_length=70),
        ),
    ]
