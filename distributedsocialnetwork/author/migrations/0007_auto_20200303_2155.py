# Generated by Django 3.0.3 on 2020-03-03 21:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('author', '0006_auto_20200303_2153'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='id',
            field=models.CharField(default='782cb14cef5447c799e371e4d7451be1', editable=False, max_length=32, primary_key=True, serialize=False, unique=True),
        ),
        migrations.AlterField(
            model_name='author',
            name='url',
            field=models.CharField(default='https://dsnfof.herokuapp.com/author/782cb14cef5447c799e371e4d7451be1', editable=False, max_length=70),
        ),
    ]
