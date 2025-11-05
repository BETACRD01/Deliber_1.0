# -*- coding: utf-8 -*-
# rifas/apps.py
from django.apps import AppConfig


class RifasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rifas'
    verbose_name = 'Rifas y Sorteos'

    def ready(self):
        """
        Importa signals cuando la app está lista
        """
        try:
            import rifas.signals  # noqa
        except ImportError:
            pass
