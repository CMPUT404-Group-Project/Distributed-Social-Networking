from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
import uuid


class AuthorManager(BaseUserManager):
    def create_user(self, displayName, first_name, last_name, email, password=None):
        if not displayName:
            raise ValueError('Display name is required.')
        if not first_name:
            raise ValueError('First name is required.')
        if not last_name:
            raise ValueError('Last name is required.')
        if not email:
            raise ValueError('Email is required.')

        user = self.model(
            displayName = displayName,
            first_name = first_name,
            last_name = last_name,
            email = self.normalize_email(email)
            )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, displayName, first_name, last_name, email, password):
        user = self.create_user(
            displayName = displayName,
            password = password,
            first_name = first_name,
            last_name = last_name,
            email = self.normalize_email(email)
            )

        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        
        return user


class Author(AbstractBaseUser):
    # Inheriting Django's AbstractBaseUser
    # See https://docs.djangoproject.com/en/3.0/topics/auth/customizing/
    # Also see https://docs.djangoproject.com/en/3.0/ref/contrib/auth/

    # Required Fields
    generatedUUID = uuid.uuid4().hex
    currentHost = 'https://dsnfof.herokuapp.com/'

    id = models.CharField(max_length=32, default=generatedUUID, editable=False, unique=True, primary_key=True)  # Generated
    host = models.CharField(max_length=30, default=currentHost, editable=False)                                 # Generated
    url = models.CharField(max_length=70, default=currentHost + 'author/' + str(generatedUUID), editable=False) # Generated
    displayName = models.CharField(max_length=150, blank=False, unique=True)                                    # Required
    github = models.CharField(max_length=255, blank=True)                                                       # Optional

    # Other Fields
    first_name = models.CharField(max_length=30, blank=False)                                                   # Required
    last_name = models.CharField(max_length=150, blank=False)                                                   # Required
    email = models.EmailField(max_length=255, blank=False, unique=True)                                         # Required

    is_active = models.BooleanField(default=False)                                                              # Generated
    is_staff = models.BooleanField(default=False)                                                               # Generated
    is_superuser = models.BooleanField(default=False)                                                           # Generated

    date_joined = models.DateTimeField(auto_now_add=True)                                                       # Generated
    last_login = models.DateTimeField(auto_now=True)                                                            # Generated

    username = models.CharField(max_length=1, blank=True, default="")

    USERNAME_FIELD = 'displayName'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']

    objects = AuthorManager()

    def __str__(self):
        return self.displayName

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff