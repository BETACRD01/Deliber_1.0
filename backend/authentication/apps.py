# -*- coding: utf-8 -*-
# authentication/apps.py

from django.apps import AppConfig
class AuthenticationConfig(AppConfig):
    """
    Configuración de la aplicación de autenticación
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    verbose_name = 'Autenticación'
    
    def ready(self):
        """
        Importa signals cuando la app está lista
        Descomenta si creas signals.py
        """
        # from . import signals
        pass
    