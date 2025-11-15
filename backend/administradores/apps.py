# -*- coding: utf-8 -*-
# administradores/apps.py
"""
Configuración de la app de administradores
✅ Inicialización segura sin queries durante app startup
✅ Creación de configuración del sistema via Signals (post_migrate)
✅ Signals para auditoría
"""

from django.apps import AppConfig
import logging

logger = logging.getLogger("administradores")


class AdministradoresConfig(AppConfig):
    """
    Configuración de la app de administradores
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "administradores"
    verbose_name = "Administradores y Gestión"

    def ready(self):
        """
        Código que se ejecuta cuando la app está lista
        NO ejecutar queries aquí - usar post_migrate signal en su lugar
        """
        # Importar signals - se conectan automáticamente sin ejecutar queries
        try:
            import administradores.signals

            logger.info("✅ Signals de administradores cargados")
        except ImportError as e:
            logger.warning(f"⚠️ No se pudo cargar signals de administradores: {e}")

        logger.info("✅ App de Administradores inicializada correctamente")
