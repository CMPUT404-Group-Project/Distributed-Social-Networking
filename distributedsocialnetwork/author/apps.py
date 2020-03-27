from django.apps import AppConfig
import os


class AuthorConfig(AppConfig):
    name = 'author'

    def ready(self):
        print("HEEEEEEEEYYYYYY")
