from django.apps import AppConfig
from django.core import management


class EasyjetConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'easyjet'

    def ready(self):
        management.call_command('preload_data')