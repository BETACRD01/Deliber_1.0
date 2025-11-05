# -*- coding: utf-8 -*-
# administradores/apps.py
"""
Configuración de la app de administradores
✅ Inicialización automática de perfiles de admin
✅ Creación de configuración del sistema por defecto
✅ Signals para auditoría
"""

from django.apps import AppConfig
import logging

logger = logging.getLogger('administradores')


class AdministradoresConfig(AppConfig):
    """
    Configuración de la app de administradores
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'administradores'
    verbose_name = 'Administradores y Gestión'

    def ready(self):
        """
        Código que se ejecuta cuando la app está lista
        """
        # Importar signals si los hay (comentado hasta implementar)
        # try:
        #     import administradores.signals
        #     logger.info('✅ Signals de administradores cargados')
        # except ImportError:
        #     pass

        # Inicializar configuración del sistema
        self._inicializar_configuracion()

        logger.info('✅ App de Administradores inicializada correctamente')

    def _inicializar_configuracion(self):
        """
        Inicializa la configuración del sistema de forma segura
        """
        try:
            from django.db import connection
            from django.db.utils import OperationalError, ProgrammingError

            # Verificar que las tablas existan
            with connection.cursor() as cursor:
                # Para PostgreSQL
                cursor.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'configuracion_sistema'
                    );
                    """
                )
                existe = cursor.fetchone()[0]

                if not existe:
                    logger.debug('⏳ Tabla configuracion_sistema no existe aún (migraciones pendientes)')
                    return

            # Importar modelo después de verificar
            from .models import ConfiguracionSistema

            # Crear configuración por defecto si no existe
            config, created = ConfiguracionSistema.objects.get_or_create(
                pk=1,
                defaults={
                    'comision_app_proveedor': 10.00,
                    'comision_app_directo': 15.00,
                    'comision_repartidor_proveedor': 25.00,
                    'comision_repartidor_directo': 85.00,
                    'pedidos_minimos_rifa': 3,
                    'pedido_maximo': 1000.00,
                    'pedido_minimo': 5.00,
                    'tiempo_maximo_entrega': 60,
                    'mantenimiento': False,
                }
            )

            if created:
                logger.info('✅ Configuración del sistema creada con valores por defecto')
            else:
                logger.debug('✓ Configuración del sistema ya existe')

        except (OperationalError, ProgrammingError) as e:
            # Las tablas aún no existen (migraciones pendientes)
            logger.debug(f'⏳ Configuración del sistema no inicializada: {e}')
        except Exception as e:
            logger.error(f'❌ Error inicializando configuración del sistema: {e}')
