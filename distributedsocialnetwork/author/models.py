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

        # generated_uuid = 'https://dsnfof.herokuapp.com/' + uuid.uuid4().hex
        # # user.id = generated_uuid
        # # user.url = generated_uuid

        user = self.model(
            displayName=displayName,
            first_name=first_name,
            last_name=last_name,
            email=self.normalize_email(email),
        )

        # id = generated_uuid,
        # url = generated_uuid
        user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(self, displayName, first_name, last_name, email, password):
        user = self.create_user(
            displayName=displayName,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=self.normalize_email(email)
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
    #
    currentHost = 'https://dsnfof.herokuapp.com/'

    id = models.CharField(max_length=100, editable=False,
                          unique=True, primary_key=True)
    host = models.CharField(
        max_length=100, default=currentHost, editable=False)
    url = models.CharField(max_length=70, editable=False)
    displayName = models.CharField(max_length=150, blank=False, unique=True)
    github = models.CharField(max_length=255, default="", blank=True)
    first_name = models.CharField(max_length=30, blank=False)
    last_name = models.CharField(max_length=150, blank=False)
    email = models.EmailField(max_length=255, blank=False, unique=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
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

    def set_id(self, request):
        generated_uuid = request.get_host() + '/author/' + uuid.uuid4().hex
        self.id = generated_uuid
        self.url = generated_uuid
