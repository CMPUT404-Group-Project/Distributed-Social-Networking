from django.apps import AppConfig
import os


class MainappConfig(AppConfig):
    name = 'mainapp'

    def ready(self):
        from . import updates

        if os.environ.get('RUN_MAIN', None) != 'true':
            updates.start_scheduler()
