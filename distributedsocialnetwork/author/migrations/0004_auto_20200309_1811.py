# Generated by Django 3.0.3 on 2020-03-09 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('author', '0003_auto_20200309_1712'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='url',
            field=models.CharField(editable=False, max_length=100),
        ),
    ]
