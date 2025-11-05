# repartidores/apps.py
from django.apps import AppConfig


class RepartidoresConfig(AppConfig):
    """
    Configuración de la aplicación de repartidores.
    Gestiona el registro de señales y configuración inicial.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'repartidores'
    verbose_name = 'Gestión de Repartidores'

    def ready(self):
        """
        Método ejecutado cuando Django inicializa la aplicación.
        Se usa para registrar signals, checks, etc.
        """
        # Importar signals si existen
        try:
            import repartidores.signals
        except ImportError:
            pass

        # Registrar checks personalizados si existen
        try:
            from . import checks
        except ImportError:
            pass
