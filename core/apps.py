"""
EduTrack Core App Configuration
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'EduTrack Core'

    def ready(self):
        try:
            import core.signals  # noqa: F401
        except ImportError:
            import warnings
            warnings.warn('Could not import core.signals.', RuntimeWarning)
