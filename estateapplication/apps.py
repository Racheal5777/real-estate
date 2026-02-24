from django.apps import AppConfig


class EstateapplicationConfig(AppConfig):
    name = 'estateapplication'

    def ready(self):
        # import signal handlers
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
