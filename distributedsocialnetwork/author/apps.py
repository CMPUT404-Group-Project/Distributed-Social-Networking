from django.apps import AppConfig
import os


class AuthorConfig(AppConfig):
    name = 'author'

    # https://stackoverflow.com/a/60244694
    def ready(self):
        from . import updates

        if os.environ.get('RUN_MAIN', None) != 'true':
            updates.start_scheduler
