# Thanks to user Tanner Swett's answer https://stackoverflow.com/a/60244694
# From Zeokav's question https://stackoverflow.com/q/44896618

from django.apps import AppConfig
import os


class MainappConfig(AppConfig):
    name = 'distributedsocialnetwork'

    # Runs at startup, runs scheduled tasks in another thread (ie. pull updates from other endpoints)
    def ready(self):
        from . import updates

        if os.environ.get('RUN_MAIN', None) != 'true':
            updates.start_scheduler()
