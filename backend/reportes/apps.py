from django.apps import AppConfig


class ReportesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reportes'
    verbose_name = 'Reportes de Pedidos'

    def ready(self):
        """
        Código que se ejecuta cuando la app está lista
        """
        import logging
        logger = logging.getLogger('reportes')
        logger.info('✅ App de Reportes inicializada')
