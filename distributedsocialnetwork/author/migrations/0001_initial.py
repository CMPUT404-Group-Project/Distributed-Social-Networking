# Generated by Django 3.0.3 on 2020-03-07 22:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('id', models.CharField(default='46f5203ce6364c54b6b1aa7825aafae2', editable=False, max_length=32, primary_key=True, serialize=False, unique=True)),
                ('host', models.CharField(default='https://dsnfof.herokuapp.com/', editable=False, max_length=30)),
                ('url', models.CharField(default='https://dsnfof.herokuapp.com/author/46f5203ce6364c54b6b1aa7825aafae2', editable=False, max_length=70)),
                ('displayName', models.CharField(max_length=150, unique=True)),
                ('github', models.CharField(blank=True, default='', max_length=255)),
                ('first_name', models.CharField(max_length=30)),
                ('last_name', models.CharField(max_length=150)),
                ('email', models.EmailField(max_length=255, unique=True)),
                ('is_active', models.BooleanField(default=False)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('last_login', models.DateTimeField(auto_now=True)),
                ('username', models.CharField(blank=True, default='', max_length=1)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
