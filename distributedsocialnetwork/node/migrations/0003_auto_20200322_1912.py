# Generated by Django 3.0.3 on 2020-03-22 19:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('node', '0002_auto_20200320_2117'),
    ]

    operations = [
        migrations.AddField(
            model_name='node',
            name='node_auth_password',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='node',
            name='node_auth_username',
            field=models.CharField(default='', max_length=100),
        ),
    ]
