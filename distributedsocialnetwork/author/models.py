from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class Author(AbstractUser):
    # Inheriting Django's AbstractUser
    # See https://docs.djangoproject.com/en/3.0/ref/contrib/auth/

    # Overwritting Django AbstractUser Fields
    email = models.EmailField(blank=True)

    # Custom Fields
    generatedUUID = uuid.uuid4().hex
    currentHost = 'https://dsnfof.herokuapp.com/'

    id = models.CharField(max_length=32, primary_key=True, default=generatedUUID, editable=False, unique=True)
    host = models.CharField(max_length=30, default=currentHost, editable=False)
    displayName = models.CharField(max_length=150, blank=False)
    url = models.CharField(max_length=70, default=currentHost + 'author/' + str(generatedUUID), editable=False)
    github = models.CharField(max_length=150, blank=True)