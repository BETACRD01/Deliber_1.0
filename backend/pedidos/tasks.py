# pedidos/tasks.py
"""
Tareas asíncronas con Celery para la aplicación de Pedidos.

Estas tareas se ejecutan en segundo plano y permiten procesar
operaciones pesadas sin bloquear las peticiones HTTP.

Configuración requerida en settings.py:
---------------------------------------
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Guayaquil'

Para ejecutar el worker:
------------------------
celery -A tu_proyecto worker -l info

Para ejecutar el beat (tareas periódicas):
------------------------------------------
celery -A tu_proyecto beat -l info
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from datetime import timedelta
import logging

logger = logging.getLogger('pedidos.tasks')


# ==========================================================
# 📊 TAREAS DE MONITOREO Y ESTADÍSTICAS
# ==========================================================

@shared_task(name='pedidos.verificar_pedidos_retrasados')
def verificar_pedidos_retrasados():
    """
    Verifica pedidos que están en ruta por más tiempo del esperado.
    Se ejecuta cada 15 minutos.

    Configurar en celery beat:
    CELERY_BEAT_SCHEDULE = {
        'verificar-pedidos-retrasados': {
            'task': 'pedidos.verificar_pedidos_retrasados',
            'schedule': crontab(minute='*/15'),
        },
    }
    """
    from .models import Pedido, EstadoPedido
    from .signals import pedido_retrasado

    tiempo_limite = timezone.now() - timedelta(minutes=45)

    pedidos = Pedido.objects.filter(
        estado=EstadoPedido.EN_RUTA,
        actualizado_en__lt=tiempo_limite
    ).select_related('cliente__user', 'repartidor__user')

    contador = 0
    for pedido in pedidos:
        tiempo_retraso = (timezone.now() - pedido.actualizado_en).total_seconds() / 60

        logger.warning(
            f"Pedido #{pedido.id} retrasado {int(tiempo_retraso)} minutos"
        )

        # Emitir señal personalizada
        pedido_retrasado.send(
            sender=Pedido,
            pedido=pedido,
            tiempo_retraso=int(tiempo_retraso)
        )

        contador += 1

    logger.info(f"Verificación completada: {contador} pedidos retrasados encontrados")
    return {'pedidos_retrasados': contador}


@shared_task(name='pedidos.verificar_pedidos_sin_repartidor')
def verificar_pedidos_sin_repartidor():
    """
    Verifica pedidos confirmados que llevan más de 10 minutos
    sin ser aceptados por un repartidor.
    Se ejecuta cada 5 minutos.
    """
    from .models import Pedido, EstadoPedido

    tiempo_limite = timezone.now() - timedelta(minutes=10)

    pedidos = Pedido.objects.filter(
        estado=EstadoPedido.CONFIRMADO,
        repartidor__isnull=True,
        creado_en__lt=tiempo_limite
    ).select_related('cliente__user')

    contador = pedidos.count()

    if contador > 0:
        logger.warning(
            f"Hay {contador} pedidos sin asignar por más de 10 minutos"
        )

        # Notificar a administradores
        try:
            from notificaciones.services import notificar_admin_pedidos_sin_asignar
            notificar_admin_pedidos_sin_asignar(pedidos)
        except ImportError:
            pass

        # Aumentar incentivo para repartidores (opcional)
        for pedido in pedidos:
            logger.info(f"Pedido #{pedido.id} esperando asignación")

    return {'pedidos_sin_asignar': contador}


@shared_task(name='pedidos.limpiar_pedidos_antiguos_cancelados')
def limpiar_pedidos_antiguos_cancelados():
    """
    Archiva o elimina pedidos cancelados con más de 90 días.
    Se ejecuta diariamente a las 3 AM.

    Configurar en celery beat:
    CELERY_BEAT_SCHEDULE = {
        'limpiar-pedidos-antiguos': {
            'task': 'pedidos.limpiar_pedidos_antiguos_cancelados',
            'schedule': crontab(hour=3, minute=0),
        },
    }
    """
    from .models import Pedido, EstadoPedido

    fecha_limite = timezone.now() - timedelta(days=90)

    pedidos_antiguos = Pedido.objects.filter(
        estado=EstadoPedido.CANCELADO,
        creado_en__lt=fecha_limite
    )

    cantidad = pedidos_antiguos.count()

    # Opción 1: Archivar en otra tabla
    # for pedido in pedidos_antiguos:
    #     PedidoArchivado.objects.create_from_pedido(pedido)

    # Opción 2: Eliminar directamente (comentado por seguridad)
    # pedidos_antiguos.delete()

    logger.info(
        f"Limpieza programada: {cantidad} pedidos cancelados antiguos encontrados"
    )

    return {'pedidos_antiguos': cantidad}


# ==========================================================
# 📈 TAREAS DE REPORTES Y ANALÍTICAS
# ==========================================================

@shared_task(name='pedidos.generar_reporte_diario')
def generar_reporte_diario():
    """
    Genera un reporte diario de pedidos y lo envía a los administradores.
    Se ejecuta diariamente a las 11 PM.

    Configurar en celery beat:
    CELERY_BEAT_SCHEDULE = {
        'reporte-diario': {
            'task': 'pedidos.generar_reporte_diario',
            'schedule': crontab(hour=23, minute=0),
        },
    }
    """
    from .models import Pedido, EstadoPedido, TipoPedido

    hoy = timezone.now().date()
    inicio_dia = timezone.make_aware(
        timezone.datetime.combine(hoy, timezone.datetime.min.time())
    )
    fin_dia = timezone.now()

    # Estadísticas del día
    pedidos_hoy = Pedido.objects.filter(
        creado_en__range=[inicio_dia, fin_dia]
    )

    estadisticas = {
        'fecha': hoy.isoformat(),
        'total_pedidos': pedidos_hoy.count(),
        'pedidos_entregados': pedidos_hoy.filter(estado=EstadoPedido.ENTREGADO).count(),
        'pedidos_cancelados': pedidos_hoy.filter(estado=EstadoPedido.CANCELADO).count(),
        'pedidos_activos': pedidos_hoy.filter(
            estado__in=[EstadoPedido.CONFIRMADO, EstadoPedido.EN_PREPARACION, EstadoPedido.EN_RUTA]
        ).count(),
        'ingresos_totales': float(
            pedidos_hoy.filter(estado=EstadoPedido.ENTREGADO).aggregate(
                total=Sum('total')
            )['total'] or 0
        ),
        'ganancia_app': float(
            pedidos_hoy.filter(estado=EstadoPedido.ENTREGADO).aggregate(
                total=Sum('ganancia_app')
            )['total'] or 0
        ),
        'pedidos_proveedor': pedidos_hoy.filter(tipo=TipoPedido.PROVEEDOR).count(),
        'pedidos_directo': pedidos_hoy.filter(tipo=TipoPedido.DIRECTO).count(),
        'ticket_promedio': float(
            pedidos_hoy.filter(estado=EstadoPedido.ENTREGADO).aggregate(
                avg=Avg('total')
            )['avg'] or 0
        ),
    }

    logger.info(f"Reporte diario generado: {estadisticas}")

    # Enviar reporte por email
    try:
        from reportes.services import enviar_reporte_diario
        enviar_reporte_diario(estadisticas)
    except ImportError:
        pass

    return estadisticas


@shared_task(name='pedidos.generar_reporte_semanal')
def generar_reporte_semanal():
    """
    Genera un reporte semanal con análisis detallado.
    Se ejecuta los lunes a las 8 AM.

    Configurar en celery beat:
    CELERY_BEAT_SCHEDULE = {
        'reporte-semanal': {
            'task': 'pedidos.generar_reporte_semanal',
            'schedule': crontab(day_of_week=1, hour=8, minute=0),
        },
    }
    """
    from .models import Pedido, EstadoPedido

    hace_una_semana = timezone.now() - timedelta(days=7)

    pedidos_semana = Pedido.objects.filter(
        creado_en__gte=hace_una_semana
    )

    estadisticas = {
        'periodo': f"{hace_una_semana.date()} - {timezone.now().date()}",
        'total_pedidos': pedidos_semana.count(),
        'tasa_entrega': calcular_tasa_entrega(pedidos_semana),
        'tasa_cancelacion': calcular_tasa_cancelacion(pedidos_semana),
        'ingresos_semanales': float(
            pedidos_semana.filter(estado=EstadoPedido.ENTREGADO).aggregate(
                total=Sum('total')
            )['total'] or 0
        ),
        'top_proveedores': obtener_top_proveedores(pedidos_semana),
        'top_repartidores': obtener_top_repartidores(pedidos_semana),
    }

    logger.info(f"Reporte semanal generado: {estadisticas}")

    # Enviar reporte
    try:
        from reportes.services import enviar_reporte_semanal
        enviar_reporte_semanal(estadisticas)
    except ImportError:
        pass

    return estadisticas


# ==========================================================
# 📧 TAREAS DE NOTIFICACIONES
# ==========================================================

@shared_task(name='pedidos.enviar_recordatorio_calificacion')
def enviar_recordatorio_calificacion(pedido_id):
    """
    Envía un recordatorio al cliente para que califique el servicio.
    Se ejecuta 24 horas después de la entrega.
    """
    from .models import Pedido

    try:
        pedido = Pedido.objects.get(id=pedido_id)

        # Verificar que no haya sido calificado
        if not hasattr(pedido, 'calificacion'):
            logger.info(f"Enviando recordatorio de calificación para pedido #{pedido_id}")

            try:
                from notificaciones.services import enviar_recordatorio_calificacion
                enviar_recordatorio_calificacion(pedido)
            except ImportError:
                pass

            return {'enviado': True}
        else:
            logger.info(f"Pedido #{pedido_id} ya tiene calificación")
            return {'enviado': False, 'razon': 'ya_calificado'}

    except Pedido.DoesNotExist:
        logger.error(f"Pedido #{pedido_id} no encontrado")
        return {'enviado': False, 'razon': 'no_existe'}


@shared_task(name='pedidos.notificar_pedido_listo_para_recoger')
def notificar_pedido_listo_para_recoger(pedido_id):
    """
    Notifica al repartidor que el pedido está listo para recoger.
    """
    from .models import Pedido, EstadoPedido

    try:
        pedido = Pedido.objects.get(id=pedido_id)

        if pedido.estado == EstadoPedido.EN_PREPARACION and pedido.repartidor:
            logger.info(f"Notificando a repartidor que pedido #{pedido_id} está listo")

            try:
                from notificaciones.services import notificar_repartidor_pedido_listo
                notificar_repartidor_pedido_listo(pedido)
            except ImportError:
                pass

            return {'notificado': True}
        else:
            return {'notificado': False, 'razon': 'estado_invalido_o_sin_repartidor'}

    except Pedido.DoesNotExist:
        logger.error(f"Pedido #{pedido_id} no encontrado")
        return {'notificado': False, 'razon': 'no_existe'}


# ==========================================================
# 🔄 TAREAS DE SINCRONIZACIÓN
# ==========================================================

@shared_task(name='pedidos.sincronizar_estado_con_proveedor')
def sincronizar_estado_con_proveedor(pedido_id):
    """
    Sincroniza el estado del pedido con el sistema del proveedor externo.
    Útil para integraciones con APIs de terceros.
    """
    from .models import Pedido

    try:
        pedido = Pedido.objects.get(id=pedido_id)

        if pedido.proveedor:
            logger.info(
                f"Sincronizando estado del pedido #{pedido_id} "
                f"con proveedor {pedido.proveedor.nombre}"
            )

            # Llamar a API del proveedor
            try:
                from integraciones.proveedores import sincronizar_pedido
                resultado = sincronizar_pedido(pedido)
                return {'sincronizado': True, 'resultado': resultado}
            except ImportError:
                return {'sincronizado': False, 'razon': 'integracion_no_disponible'}
        else:
            return {'sincronizado': False, 'razon': 'sin_proveedor'}

    except Pedido.DoesNotExist:
        logger.error(f"Pedido #{pedido_id} no encontrado")
        return {'sincronizado': False, 'razon': 'no_existe'}


# ==========================================================
# 🧹 TAREAS DE MANTENIMIENTO
# ==========================================================

@shared_task(name='pedidos.recalcular_comisiones')
def recalcular_comisiones():
    """
    Recalcula las comisiones de todos los pedidos entregados
    que no tengan comisiones calculadas.
    Se ejecuta semanalmente.
    """
    from .models import Pedido, EstadoPedido

    pedidos_sin_comisiones = Pedido.objects.filter(
        estado=EstadoPedido.ENTREGADO,
        comision_repartidor=0,
        comision_proveedor=0,
        ganancia_app=0
    )

    contador = 0
    for pedido in pedidos_sin_comisiones:
        try:
            pedido._distribuir_ganancias()
            contador += 1
            logger.info(f"Comisiones recalculadas para pedido #{pedido.id}")
        except Exception as e:
            logger.error(f"Error al recalcular comisiones del pedido #{pedido.id}: {e}")

    return {'pedidos_actualizados': contador}


@shared_task(name='pedidos.actualizar_cache_estadisticas')
def actualizar_cache_estadisticas():
    """
    Actualiza el cache de estadísticas generales del sistema.
    Se ejecuta cada hora.
    """
    from django.core.cache import cache
    from .models import Pedido, EstadoPedido

    try:
        estadisticas = {
            'total_pedidos': Pedido.objects.count(),
            'pedidos_activos': Pedido.objects.filter(
                estado__in=[EstadoPedido.CONFIRMADO, EstadoPedido.EN_PREPARACION, EstadoPedido.EN_RUTA]
            ).count(),
            'pedidos_hoy': Pedido.objects.filter(
                creado_en__date=timezone.now().date()
            ).count(),
        }

        cache.set('pedidos_estadisticas', estadisticas, timeout=3600)
        logger.info("Cache de estadísticas actualizado")

        return estadisticas
    except Exception as e:
        logger.error(f"Error al actualizar cache: {e}")
        return {'error': str(e)}


# ==========================================================
# 🛠️ FUNCIONES AUXILIARES
# ==========================================================

def calcular_tasa_entrega(queryset):
    """Calcula el porcentaje de pedidos entregados"""
    from .models import EstadoPedido

    total = queryset.count()
    if total == 0:
        return 0

    entregados = queryset.filter(estado=EstadoPedido.ENTREGADO).count()
    return round((entregados / total) * 100, 2)


def calcular_tasa_cancelacion(queryset):
    """Calcula el porcentaje de pedidos cancelados"""
    from .models import EstadoPedido

    total = queryset.count()
    if total == 0:
        return 0

    cancelados = queryset.filter(estado=EstadoPedido.CANCELADO).count()
    return round((cancelados / total) * 100, 2)


def obtener_top_proveedores(queryset, limite=5):
    """Obtiene los proveedores con más pedidos"""
    from .models import EstadoPedido

    top = queryset.filter(
        estado=EstadoPedido.ENTREGADO,
        proveedor__isnull=False
    ).values(
        'proveedor__nombre'
    ).annotate(
        total_pedidos=Count('id'),
        total_ventas=Sum('total')
    ).order_by('-total_pedidos')[:limite]

    return list(top)


def obtener_top_repartidores(queryset, limite=5):
    """Obtiene los repartidores con más entregas"""
    from .models import EstadoPedido

    top = queryset.filter(
        estado=EstadoPedido.ENTREGADO,
        repartidor__isnull=False
    ).values(
        'repartidor__user__first_name',
        'repartidor__user__last_name'
    ).annotate(
        total_entregas=Count('id'),
        total_ganado=Sum('comision_repartidor')
    ).order_by('-total_entregas')[:limite]

    return list(top)


# ==========================================================
# 🚀 TAREAS PARA PROGRAMAR DESPUÉS DE EVENTOS
# ==========================================================

@shared_task(name='pedidos.programar_recordatorio_calificacion')
def programar_recordatorio_calificacion(pedido_id):
    """
    Programa un recordatorio de calificación 24 horas después.
    Se llama desde la señal de pedido entregado.
    """
    enviar_recordatorio_calificacion.apply_async(
        args=[pedido_id],
        countdown=86400  # 24 horas en segundos
    )
    logger.info(f"Recordatorio programado para pedido #{pedido_id} en 24 horas")
    return {'programado': True, 'pedido_id': pedido_id}
