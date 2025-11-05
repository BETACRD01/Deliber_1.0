# notificaciones/signals.py
"""
Signals para envío automático de notificaciones
✅ Detecta cambios de estado en pedidos
✅ Envía notificaciones push + guarda en BD
✅ Mensajes personalizados por estado
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from pedidos.models import Pedido, EstadoPedido

logger = logging.getLogger('notificaciones')


@receiver(pre_save, sender=Pedido)
def detectar_cambio_estado_pedido(sender, instance, **kwargs):
    """
    ✅ Detecta cuando cambia el estado de un pedido

    Guarda el estado anterior en una variable temporal
    para compararlo después del guardado
    """
    if instance.pk:
        try:
            # Obtener el estado anterior del pedido
            pedido_anterior = Pedido.objects.get(pk=instance.pk)
            instance._estado_anterior = pedido_anterior.estado
        except Pedido.DoesNotExist:
            instance._estado_anterior = None
    else:
        # Pedido nuevo, no hay estado anterior
        instance._estado_anterior = None


@receiver(post_save, sender=Pedido)
def enviar_notificacion_cambio_estado(sender, instance, created, **kwargs):
    """
    ✅ Envía notificación cuando cambia el estado del pedido

    Args:
        sender: Clase Pedido
        instance: Instancia del pedido
        created: Si es nuevo pedido
        kwargs: Argumentos adicionales
    """
    from notificaciones.services import crear_y_enviar_notificacion

    # Si es un pedido nuevo (recién creado)
    if created:
        _enviar_notificacion_pedido_creado(instance)
        return

    # Si cambió el estado
    estado_anterior = getattr(instance, '_estado_anterior', None)

    if estado_anterior and estado_anterior != instance.estado:
        logger.info(
            f"📱 Cambio de estado detectado - Pedido #{instance.pk}: "
            f"{estado_anterior} → {instance.estado}"
        )

        # Enviar notificación según el nuevo estado
        _enviar_notificacion_por_estado(instance, estado_anterior)


def _enviar_notificacion_pedido_creado(pedido):
    """
    ✅ Notificación cuando se crea un nuevo pedido

    Args:
        pedido (Pedido): Instancia del pedido
    """
    from notificaciones.services import crear_y_enviar_notificacion

    try:
        usuario = pedido.cliente.user

        titulo = "¡Pedido confirmado! 🎉"
        mensaje = f"Tu pedido #{pedido.pk} ha sido confirmado y está siendo procesado."

        datos_extra = {
            'pedido_id': str(pedido.pk),
            'tipo': 'pedido_creado',
            'estado': pedido.estado,
            'total': str(pedido.total)
        }

        crear_y_enviar_notificacion(
            usuario=usuario,
            titulo=titulo,
            mensaje=mensaje,
            tipo='pedido',
            pedido=pedido,
            datos_extra=datos_extra
        )

        logger.info(f"✅ Notificación enviada: Pedido creado #{pedido.pk}")

    except Exception as e:
        logger.error(
            f"❌ Error enviando notificación de pedido creado: {e}",
            exc_info=True
        )


def _enviar_notificacion_por_estado(pedido, estado_anterior):
    """
    ✅ Envía notificación según el nuevo estado del pedido

    Args:
        pedido (Pedido): Instancia del pedido
        estado_anterior (str): Estado anterior del pedido
    """
    from notificaciones.services import crear_y_enviar_notificacion

    try:
        usuario = pedido.cliente.user
        estado_actual = pedido.estado

        # Preparar datos comunes
        datos_extra = {
            'pedido_id': str(pedido.pk),
            'tipo': f'cambio_estado_{estado_actual}',
            'estado': estado_actual,
            'estado_anterior': estado_anterior,
            'total': str(pedido.total)
        }

        # Definir título y mensaje según el estado
        if estado_actual == EstadoPedido.EN_PREPARACION:
            titulo = "🍳 Pedido en preparación"

            if pedido.tipo == 'proveedor' and pedido.proveedor:
                mensaje = (
                    f"{pedido.proveedor.nombre} está preparando tu pedido "
                    f"#{pedido.pk}. ¡Ya casi está listo!"
                )
            else:
                mensaje = f"Tu pedido #{pedido.pk} está siendo preparado."

            datos_extra['proveedor'] = (
                pedido.proveedor.nombre if pedido.proveedor else 'N/A'
            )

        elif estado_actual == EstadoPedido.EN_RUTA:
            titulo = "🚴 ¡Tu pedido va en camino!"

            if pedido.repartidor:
                nombre_repartidor = pedido.repartidor.user.get_full_name()
                mensaje = (
                    f"{nombre_repartidor} está en camino con tu pedido "
                    f"#{pedido.pk}. ¡Llegará pronto!"
                )
                datos_extra['repartidor'] = nombre_repartidor
            else:
                mensaje = f"Tu pedido #{pedido.pk} está en camino."

            # Agregar tiempo estimado si está disponible
            if hasattr(pedido, 'tiempo_estimado_entrega'):
                tiempo = pedido.tiempo_estimado_entrega
                if tiempo:
                    mensaje += f" Tiempo estimado: {tiempo} min."
                    datos_extra['tiempo_estimado'] = str(tiempo)

        elif estado_actual == EstadoPedido.ENTREGADO:
            titulo = "✅ ¡Pedido entregado!"
            mensaje = (
                f"Tu pedido #{pedido.pk} ha sido entregado. "
                f"¡Esperamos que lo disfrutes! 😊"
            )

            if pedido.repartidor:
                datos_extra['repartidor'] = pedido.repartidor.user.get_full_name()

            # Agregar información de tiempo total
            if hasattr(pedido, 'calcular_tiempo_total_entrega'):
                tiempo_total = pedido.calcular_tiempo_total_entrega()
                if tiempo_total:
                    datos_extra['tiempo_total'] = tiempo_total

        elif estado_actual == EstadoPedido.CANCELADO:
            titulo = "❌ Pedido cancelado"

            motivo = ""
            if pedido.cancelado_por == 'cliente':
                motivo = "Has cancelado tu pedido"
            elif pedido.cancelado_por == 'proveedor':
                motivo = "El proveedor canceló el pedido"
            elif pedido.cancelado_por == 'repartidor':
                motivo = "El repartidor canceló el pedido"
            elif pedido.cancelado_por == 'admin':
                motivo = "El pedido fue cancelado por administración"
            else:
                motivo = "El pedido fue cancelado"

            mensaje = (
                f"{motivo} #{pedido.pk}. "
                f"Si tienes dudas, contáctanos."
            )

            datos_extra['cancelado_por'] = pedido.cancelado_por or 'desconocido'

        else:
            # Estado no reconocido, no enviar notificación
            logger.warning(
                f"⚠️ Estado no reconocido para notificación: {estado_actual}"
            )
            return

        # Enviar notificación
        crear_y_enviar_notificacion(
            usuario=usuario,
            titulo=titulo,
            mensaje=mensaje,
            tipo='pedido',
            pedido=pedido,
            datos_extra=datos_extra
        )

        logger.info(
            f"✅ Notificación enviada: Pedido #{pedido.pk} → {estado_actual}"
        )

    except Exception as e:
        logger.error(
            f"❌ Error enviando notificación de cambio de estado: {e}",
            exc_info=True
        )


# ============================================
# 📢 NOTIFICACIONES ADICIONALES OPCIONALES
# ============================================

def enviar_notificacion_repartidor_asignado(pedido):
    """
    ✅ OPCIONAL: Notificación cuando se asigna un repartidor

    Puedes llamar esta función manualmente después de asignar un repartidor

    Args:
        pedido (Pedido): Instancia del pedido
    """
    from notificaciones.services import crear_y_enviar_notificacion

    try:
        if not pedido.repartidor:
            return

        usuario = pedido.cliente.user
        nombre_repartidor = pedido.repartidor.user.get_full_name()

        titulo = "👤 Repartidor asignado"
        mensaje = (
            f"{nombre_repartidor} ha aceptado tu pedido #{pedido.pk}. "
            f"Pronto estará en camino."
        )

        datos_extra = {
            'pedido_id': str(pedido.pk),
            'tipo': 'repartidor_asignado',
            'repartidor': nombre_repartidor,
            'estado': pedido.estado
        }

        crear_y_enviar_notificacion(
            usuario=usuario,
            titulo=titulo,
            mensaje=mensaje,
            tipo='repartidor',
            pedido=pedido,
            datos_extra=datos_extra
        )

        logger.info(
            f"✅ Notificación enviada: Repartidor asignado a pedido #{pedido.pk}"
        )

    except Exception as e:
        logger.error(
            f"❌ Error enviando notificación de repartidor asignado: {e}",
            exc_info=True
        )


def enviar_notificacion_promocion(usuario, titulo, mensaje):
    """
    ✅ OPCIONAL: Enviar notificación de promoción

    Args:
        usuario (User): Usuario destinatario
        titulo (str): Título de la promoción
        mensaje (str): Mensaje de la promoción
    """
    from notificaciones.services import crear_y_enviar_notificacion

    try:
        # Verificar si el usuario acepta notificaciones de promociones
        if not hasattr(usuario, 'perfil_usuario'):
            return

        perfil = usuario.perfil_usuario

        if not perfil.notificaciones_promociones:
            logger.info(
                f"ℹ️ Usuario {usuario.email} no acepta notificaciones de promociones"
            )
            return

        datos_extra = {
            'tipo': 'promocion',
        }

        crear_y_enviar_notificacion(
            usuario=usuario,
            titulo=titulo,
            mensaje=mensaje,
            tipo='promocion',
            pedido=None,
            datos_extra=datos_extra
        )

        logger.info(
            f"✅ Notificación de promoción enviada a: {usuario.email}"
        )

    except Exception as e:
        logger.error(
            f"❌ Error enviando notificación de promoción: {e}",
            exc_info=True
        )
