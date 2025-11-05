# notificaciones/apps.py
"""
Configuración de la aplicación de notificaciones
✅ Carga automática de signals
"""

from django.apps import AppConfig


class NotificacionesConfig(AppConfig):
    """
    ✅ Configuración de la app de notificaciones
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notificaciones'
    verbose_name = 'Notificaciones'

    def ready(self):
        """
        ✅ Se ejecuta cuando Django inicia
        Importa los signals para que se registren automáticamente
        """
        try:
            import notificaciones.signals  # noqa
            print("✅ Signals de notificaciones cargados correctamente")
        except Exception as e:
            print(f"❌ Error cargando signals de notificaciones: {e}")
