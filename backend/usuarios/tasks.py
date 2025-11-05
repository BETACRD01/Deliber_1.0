# usuarios/tasks.py

"""
Tareas asíncronas de Celery para envío de notificaciones push
Compatible con FirebaseService unificado
"""
from celery import shared_task
from utils.firebase_service import FirebaseService
import logging

logger = logging.getLogger(__name__)


# ==========================================
# TAREAS DE ENVÍO INDIVIDUAL
# ==========================================

@shared_task(bind=True, max_retries=3)
def tarea_enviar_notificacion(self, user_id, titulo, mensaje, data=None, imagen_url=None):
    """
    Tarea asíncrona para enviar notificación push a un usuario

    Args:
        user_id (int): ID del usuario
        titulo (str): Título de la notificación
        mensaje (str): Cuerpo del mensaje
        data (dict, optional): Datos adicionales para la app
        imagen_url (str, optional): URL de imagen

    Returns:
        dict: Resultado del envío

    Ejemplo:
        tarea_enviar_notificacion.delay(
            user_id=123,
            titulo='¡Pedido confirmado!',
            mensaje='Tu pedido #12345 está en preparación',
            data={'pedido_id': '12345', 'tipo': 'pedido_confirmado'}
        )
    """
    try:
        logger.info(f'📨 Tarea iniciada: Enviar notificación a usuario {user_id}')

        result = FirebaseService.enviar_a_usuario(
            user_id=user_id,
            titulo=titulo,
            mensaje=mensaje,
            data=data,
            imagen_url=imagen_url
        )

        if result['success']:
            logger.info(f'✅ Tarea completada: Notificación enviada a {result.get("usuario")}')
        else:
            logger.warning(f'⚠️ Tarea finalizada con advertencia: {result.get("message")}')

        return result

    except Exception as exc:
        logger.error(f'❌ Error en tarea de notificación: {str(exc)}')

        # Reintentar hasta 3 veces con delay exponencial (60s, 120s, 240s)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


# ==========================================
# TAREAS DE ENVÍO MASIVO
# ==========================================

@shared_task(bind=True, max_retries=2)
def tarea_enviar_notificacion_masiva(self, user_ids, titulo, mensaje, data=None, imagen_url=None):
    """
    Tarea asíncrona para enviar notificaciones a múltiples usuarios

    Args:
        user_ids (list): Lista de IDs de usuarios
        titulo (str): Título de la notificación
        mensaje (str): Cuerpo del mensaje
        data (dict, optional): Datos adicionales
        imagen_url (str, optional): URL de imagen

    Returns:
        dict: Estadísticas del envío

    Ejemplo:
        tarea_enviar_notificacion_masiva.delay(
            user_ids=[123, 456, 789],
            titulo='¡Nueva promoción!',
            mensaje='50% de descuento en todos los productos',
            data={'tipo': 'promocion', 'codigo': 'PROMO50'}
        )
    """
    try:
        logger.info(f'📨 Tarea masiva iniciada: {len(user_ids)} usuario(s)')

        result = FirebaseService.enviar_a_usuarios(
            user_ids=user_ids,
            titulo=titulo,
            mensaje=mensaje,
            data=data,
            imagen_url=imagen_url
        )

        if result['success']:
            logger.info(
                f'✅ Tarea masiva completada: '
                f'{result["success_count"]}/{result["total"]} enviadas'
            )
        else:
            logger.warning(f'⚠️ Tarea masiva con errores: {result.get("error")}')

        return result

    except Exception as exc:
        logger.error(f'❌ Error en tarea masiva: {str(exc)}')
        raise self.retry(exc=exc, countdown=120)


# ==========================================
# TAREAS ESPECÍFICAS PARA PEDIDOS
# ==========================================

@shared_task
def tarea_notificar_pedido_nuevo(pedido_id):
    """
    Notifica al usuario cuando se crea un nuevo pedido

    Args:
        pedido_id (int): ID del pedido

    Returns:
        AsyncResult: Resultado de la tarea asíncrona

    Uso:
        # En tu view o signal de creación de pedido:
        from usuarios.tasks import tarea_notificar_pedido_nuevo
        tarea_notificar_pedido_nuevo.delay(pedido.id)
    """
    try:
        from pedidos.models import Pedido

        pedido = Pedido.objects.select_related('usuario').get(id=pedido_id)

        logger.info(f'📦 Notificando pedido nuevo: #{pedido.numero_pedido}')

        return tarea_enviar_notificacion.delay(
            user_id=pedido.usuario.id,
            titulo="¡Pedido creado! 🎉",
            mensaje=f"Tu pedido #{pedido.numero_pedido} ha sido registrado exitosamente",
            data={
                'tipo': 'pedido_nuevo',
                'pedido_id': str(pedido.id),
                'numero_pedido': pedido.numero_pedido,
                'estado': pedido.estado,
                'accion': 'abrir_detalle'
            }
        )

    except Exception as e:
        logger.error(f'❌ Error notificando pedido nuevo {pedido_id}: {e}', exc_info=True)
        raise


@shared_task
def tarea_notificar_cambio_estado(pedido_id, estado_anterior, estado_nuevo):
    """
    Notifica al usuario cuando cambia el estado de su pedido

    Args:
        pedido_id (int): ID del pedido
        estado_anterior (str): Estado previo
        estado_nuevo (str): Estado actual

    Uso:
        # En tu view o signal de actualización de estado:
        tarea_notificar_cambio_estado.delay(
            pedido_id=pedido.id,
            estado_anterior='pendiente',
            estado_nuevo='confirmado'
        )
    """
    try:
        from pedidos.models import Pedido

        pedido = Pedido.objects.select_related('usuario').get(id=pedido_id)

        # Mapeo de estados a mensajes amigables
        mensajes = {
            'pendiente': '⏳ Tu pedido está pendiente de confirmación',
            'confirmado': '✅ Tu pedido ha sido confirmado',
            'en_preparacion': '👨‍🍳 Tu pedido está siendo preparado',
            'en_camino': '🚗 Tu pedido está en camino',
            'entregado': '🎉 ¡Tu pedido ha sido entregado!',
            'cancelado': '❌ Tu pedido ha sido cancelado'
        }

        titulo = f"Estado del pedido #{pedido.numero_pedido}"
        mensaje = mensajes.get(estado_nuevo, f'Estado actualizado: {estado_nuevo}')

        logger.info(f'📊 Notificando cambio de estado: {estado_anterior} → {estado_nuevo}')

        return tarea_enviar_notificacion.delay(
            user_id=pedido.usuario.id,
            titulo=titulo,
            mensaje=mensaje,
            data={
                'tipo': 'cambio_estado',
                'pedido_id': str(pedido.id),
                'numero_pedido': pedido.numero_pedido,
                'estado_anterior': estado_anterior,
                'estado_nuevo': estado_nuevo,
                'accion': 'abrir_detalle'
            }
        )

    except Exception as e:
        logger.error(f'❌ Error notificando cambio de estado: {e}', exc_info=True)
        raise


@shared_task
def tarea_notificar_pedido_confirmado(pedido_id):
    """
    Notificación específica cuando un pedido es confirmado
    Usa el método dedicado de FirebaseService

    Args:
        pedido_id (int): ID del pedido
    """
    try:
        from pedidos.models import Pedido

        pedido = Pedido.objects.select_related('usuario__perfil_usuario').get(id=pedido_id)
        perfil = pedido.usuario.perfil_usuario

        logger.info(f'✅ Notificando pedido confirmado: #{pedido.numero_pedido}')

        result = FirebaseService.notificar_pedido_confirmado(perfil, pedido)

        if result['success']:
            logger.info(f'✅ Notificación de confirmación enviada exitosamente')
        else:
            logger.warning(f'⚠️ No se pudo enviar notificación: {result.get("message")}')

        return result

    except Exception as e:
        logger.error(f'❌ Error notificando pedido confirmado: {e}', exc_info=True)


@shared_task
def tarea_notificar_pedido_en_camino(pedido_id, repartidor_nombre):
    """
    Notificación específica cuando un pedido está en camino

    Args:
        pedido_id (int): ID del pedido
        repartidor_nombre (str): Nombre del repartidor
    """
    try:
        from pedidos.models import Pedido

        pedido = Pedido.objects.select_related('usuario__perfil_usuario').get(id=pedido_id)
        perfil = pedido.usuario.perfil_usuario

        logger.info(f'🚚 Notificando pedido en camino: #{pedido.numero_pedido}')

        result = FirebaseService.notificar_pedido_en_camino(perfil, pedido, repartidor_nombre)

        if result['success']:
            logger.info(f'✅ Notificación de envío enviada exitosamente')

        return result

    except Exception as e:
        logger.error(f'❌ Error notificando pedido en camino: {e}', exc_info=True)


@shared_task
def tarea_notificar_pedido_entregado(pedido_id):
    """
    Notificación específica cuando un pedido es entregado

    Args:
        pedido_id (int): ID del pedido
    """
    try:
        from pedidos.models import Pedido

        pedido = Pedido.objects.select_related('usuario__perfil_usuario').get(id=pedido_id)
        perfil = pedido.usuario.perfil_usuario

        logger.info(f'📦 Notificando pedido entregado: #{pedido.numero_pedido}')

        result = FirebaseService.notificar_pedido_entregado(perfil, pedido)

        if result['success']:
            logger.info(f'✅ Notificación de entrega enviada exitosamente')

        return result

    except Exception as e:
        logger.error(f'❌ Error notificando pedido entregado: {e}', exc_info=True)


@shared_task
def tarea_notificar_pedido_cancelado(pedido_id, razon=''):
    """
    Notificación específica cuando un pedido es cancelado

    Args:
        pedido_id (int): ID del pedido
        razon (str, optional): Razón de cancelación
    """
    try:
        from pedidos.models import Pedido

        pedido = Pedido.objects.select_related('usuario__perfil_usuario').get(id=pedido_id)
        perfil = pedido.usuario.perfil_usuario

        logger.info(f'❌ Notificando pedido cancelado: #{pedido.numero_pedido}')

        result = FirebaseService.notificar_pedido_cancelado(perfil, pedido, razon)

        if result['success']:
            logger.info(f'✅ Notificación de cancelación enviada exitosamente')

        return result

    except Exception as e:
        logger.error(f'❌ Error notificando pedido cancelado: {e}', exc_info=True)


# ==========================================
# TAREAS DE PROMOCIONES
# ==========================================

@shared_task
def tarea_notificar_promocion(user_ids, titulo, mensaje, imagen_url=None):
    """
    Envía notificación de promoción a usuarios específicos

    Args:
        user_ids (list): Lista de IDs de usuarios
        titulo (str): Título de la promoción
        mensaje (str): Descripción de la promoción
        imagen_url (str, optional): URL de imagen promocional

    Uso:
        tarea_notificar_promocion.delay(
            user_ids=[123, 456, 789],
            titulo='¡Black Friday!',
            mensaje='50% de descuento en todo',
            imagen_url='https://...'
        )
    """
    try:
        from usuarios.models import Perfil

        logger.info(f'🎁 Enviando promoción a {len(user_ids)} usuario(s)')

        # Filtrar usuarios con promociones habilitadas
        perfiles = Perfil.objects.filter(
            user_id__in=user_ids,
            notificaciones_promociones=True,
            fcm_token__isnull=False
        ).exclude(fcm_token='')

        tokens = [p.fcm_token for p in perfiles]

        if not tokens:
            logger.warning('⚠️ No hay usuarios con promociones habilitadas')
            return {'success': False, 'message': 'Sin destinatarios'}

        result = FirebaseService.enviar_notificacion_multiple(
            tokens=tokens,
            titulo=titulo,
            mensaje=mensaje,
            imagen_url=imagen_url,
            data={
                'tipo': 'promocion',
                'accion': 'ver_promociones'
            }
        )

        # Limpiar tokens inválidos
        if result.get('tokens_invalidos'):
            Perfil.objects.filter(
                fcm_token__in=result['tokens_invalidos']
            ).update(fcm_token=None, fcm_token_actualizado=None)

        logger.info(f'✅ Promoción enviada: {result["success"]}/{result["total"]}')

        return result

    except Exception as e:
        logger.error(f'❌ Error enviando promoción: {e}', exc_info=True)


# ==========================================
# TAREAS DE LIMPIEZA Y MANTENIMIENTO
# ==========================================

@shared_task
def tarea_limpiar_tokens_invalidos():
    """
    Tarea periódica para limpiar tokens FCM inválidos

    Configura en Celery Beat:
        CELERY_BEAT_SCHEDULE = {
            'limpiar-tokens-invalidos': {
                'task': 'usuarios.tasks.tarea_limpiar_tokens_invalidos',
                'schedule': crontab(hour=3, minute=0),  # Diario a las 3 AM
            },
        }
    """
    try:
        from usuarios.models import Perfil

        logger.info('🧹 Iniciando limpieza de tokens inválidos')

        # Obtener todos los perfiles con token
        perfiles_con_token = Perfil.objects.filter(
            fcm_token__isnull=False
        ).exclude(fcm_token='')

        tokens_invalidos = []

        for perfil in perfiles_con_token:
            if not FirebaseService.validar_token(perfil.fcm_token):
                tokens_invalidos.append(perfil.fcm_token)
                perfil.eliminar_fcm_token()

        logger.info(f'✅ Limpieza completada: {len(tokens_invalidos)} tokens eliminados')

        return {
            'tokens_validados': perfiles_con_token.count(),
            'tokens_eliminados': len(tokens_invalidos)
        }

    except Exception as e:
        logger.error(f'❌ Error en limpieza de tokens: {e}', exc_info=True)


@shared_task
def tarea_enviar_recordatorio_pedidos_pendientes():
    """
    Envía recordatorio a usuarios con pedidos pendientes hace más de X horas

    Configura en Celery Beat para ejecutar cada cierto tiempo
    """
    try:
        from pedidos.models import Pedido
        from django.utils import timezone
        from datetime import timedelta

        logger.info('🔔 Verificando pedidos pendientes')

        # Pedidos pendientes con más de 2 horas
        hace_2_horas = timezone.now() - timedelta(hours=2)

        pedidos_pendientes = Pedido.objects.filter(
            estado='pendiente',
            fecha_creacion__lt=hace_2_horas
        ).select_related('usuario')

        for pedido in pedidos_pendientes:
            tarea_enviar_notificacion.delay(
                user_id=pedido.usuario.id,
                titulo='Pedido pendiente de confirmación',
                mensaje=f'Tu pedido #{pedido.numero_pedido} está esperando confirmación',
                data={
                    'tipo': 'recordatorio',
                    'pedido_id': str(pedido.id),
                    'accion': 'ver_detalle'
                }
            )

        logger.info(f'✅ {pedidos_pendientes.count()} recordatorios enviados')

        return {'recordatorios_enviados': pedidos_pendientes.count()}

    except Exception as e:
        logger.error(f'❌ Error enviando recordatorios: {e}', exc_info=True)
