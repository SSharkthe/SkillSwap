from django.apps import AppConfig


class SkillswapConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'skillswap'

    def ready(self):
        from . import signals  # noqa: F401