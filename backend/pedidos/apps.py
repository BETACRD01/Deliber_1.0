from django.apps import AppConfig


class PedidosConfig(AppConfig):
    """
    Configuración de la aplicación de Pedidos.

    Gestiona el ciclo de vida completo de los pedidos en el sistema,
    incluyendo pedidos de proveedores y encargos directos.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pedidos'
    verbose_name = 'Gestión de Pedidos'

    def ready(self):
        """
        Se ejecuta cuando Django inicia y la aplicación está lista.
        Aquí se pueden registrar señales, tareas programadas, etc.
        """
        # Importar señales si existen
        try:
            import pedidos.signals  # noqa
        except ImportError:
            pass

        # Registrar tareas periódicas si se usa Celery
        try:
            import pedidos.tasks  # noqa
        except ImportError:
            pass
