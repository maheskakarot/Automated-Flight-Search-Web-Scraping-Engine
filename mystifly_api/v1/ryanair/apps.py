from django.apps import AppConfig


class RyanairConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'v1.ryanair'

    def ready(self):
        try:
            from v1.ryanair import views
            views.load_data_into_cache()
        except:
            pass