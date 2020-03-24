# Generated by Django 3.0.3 on 2020-03-23 02:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('node', '0003_auto_20200322_1912'),
    ]

    operations = [
        migrations.AlterField(
            model_name='node',
            name='node_auth_password',
            field=models.CharField(default='', help_text='The password we use when connecting to the foreign server.', max_length=100),
        ),
        migrations.AlterField(
            model_name='node',
            name='node_auth_username',
            field=models.CharField(default='', help_text='The username we use when connecting to the foreign server.', max_length=100),
        ),
        migrations.AlterField(
            model_name='node',
            name='server_password',
            field=models.CharField(help_text='The password the foreign server uses to connect to us.', max_length=100),
        ),
        migrations.AlterField(
            model_name='node',
            name='server_username',
            field=models.CharField(help_text='The username the foreign server uses to connect to us.', max_length=10),
        ),
    ]