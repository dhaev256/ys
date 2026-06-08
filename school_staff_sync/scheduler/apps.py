from django.apps import AppConfig


class SchedulerConfig(AppConfig):
    name = 'scheduler'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import scheduler.signals  # noqa: F401 — registers signal handlers
