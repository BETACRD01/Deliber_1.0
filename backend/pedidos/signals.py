# pedidos/signals.py (CORREGIDO Y SINCRONIZADO)
"""
Señales para la aplicación de Pedidos.

✅ CORRECCIONES APLICADAS:
- Eliminados accesos a campos inexistentes (total_pedidos, total_ventas, comision_total)
- Implementado cálculo dinámico de estadísticas
- Protección contra recursión infinita
- Manejo robusto de errores
- Logging mejorado
"""
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Count, Sum, F
import logging

from .models import Pedido, EstadoPedido, TipoPedido

logger = logging.getLogger('pedidos.signals')


# ==========================================================
# 🔒 PROTECCIÓN CONTRA RECURSIÓN
# ==========================================================
# Flag global para evitar recursión infinita en signals
_signals_en_proceso = set()


def esta_procesando(signal_name, instance_id):
    """Verifica si un signal ya está siendo procesado"""
    key = f"{signal_name}_{instance_id}"
    return key in _signals_en_proceso


def marcar_procesando(signal_name, instance_id):
    """Marca un signal como en proceso"""
    key = f"{signal_name}_{instance_id}"
    _signals_en_proceso.add(key)


def desmarcar_procesando(signal_name, instance_id):
    """Desmarca un signal como procesado"""
    key = f"{signal_name}_{instance_id}"
    _signals_en_proceso.discard(key)


# ==========================================================
# 📊 SEÑALES DE AUDITORÍA Y LOGGING
# ==========================================================

@receiver(post_save, sender=Pedido)
def pedido_creado_o_actualizado(sender, instance, created, **kwargs):
    """
    ✅ CORREGIDO: Evita recursión y logging mejorado

    Se ejecuta cada vez que se crea o actualiza un pedido.
    Útil para logging, auditoría y notificaciones.
    """
    # ✅ Prevenir recursión
    if esta_procesando('post_save_audit', instance.id):
        return

    try:
        marcar_procesando('post_save_audit', instance.id)

        if created:
            logger.info(
                f"[PEDIDO CREADO] #{instance.id} - "
                f"Tipo: {instance.get_tipo_display()} - "
                f"Cliente: {instance.cliente.user.email} - "
                f"Total: ${instance.total} - "
                f"Estado: {instance.get_estado_display()}"
            )

            # Notificar a administradores sobre nuevo pedido
            try:
                from notificaciones.services import notificar_admin_nuevo_pedido
                notificar_admin_nuevo_pedido(instance)
            except ImportError:
                logger.debug("Módulo de notificaciones no disponible")
            except Exception as e:
                logger.warning(f"Error al notificar admin: {e}")
        else:
            logger.info(
                f"[PEDIDO ACTUALIZADO] #{instance.id} - "
                f"Estado: {instance.get_estado_display()}"
            )
    finally:
        desmarcar_procesando('post_save_audit', instance.id)


@receiver(pre_save, sender=Pedido)
def validar_cambio_estado(sender, instance, **kwargs):
    """
    ✅ CORREGIDO: Logging mejorado y protección contra recursión

    Se ejecuta antes de guardar un pedido.
    Valida cambios de estado y registra el historial.
    """
    # ✅ Prevenir recursión
    if esta_procesando('pre_save_validate', instance.id or 0):
        return

    if not instance.pk:  # Pedido nuevo
        return

    try:
        marcar_procesando('pre_save_validate', instance.id)

        pedido_anterior = Pedido.objects.get(pk=instance.pk)

        # Detectar cambio de estado
        if pedido_anterior.estado != instance.estado:
            logger.info(
                f"[CAMBIO DE ESTADO] Pedido #{instance.id}: "
                f"{pedido_anterior.get_estado_display()} → "
                f"{instance.get_estado_display()}"
            )

            # Registrar en historial si existe el modelo
            try:
                from .models import HistorialPedido
                HistorialPedido.objects.create(
                    pedido=instance,
                    estado_anterior=pedido_anterior.estado,
                    estado_nuevo=instance.estado,
                    fecha_cambio=timezone.now()
                )
                logger.debug(f"Historial de cambio registrado para pedido #{instance.id}")
            except ImportError:
                logger.debug("Modelo HistorialPedido no disponible")
            except Exception as e:
                logger.warning(f"Error al registrar historial: {e}")

        # Detectar asignación de repartidor
        if not pedido_anterior.repartidor and instance.repartidor:
            logger.info(
                f"[REPARTIDOR ASIGNADO] Pedido #{instance.id} → "
                f"{instance.repartidor.user.get_full_name()}"
            )

            # Notificar al cliente
            try:
                from notificaciones.services import notificar_cliente_repartidor_asignado
                notificar_cliente_repartidor_asignado(instance)
            except ImportError:
                logger.debug("Servicio de notificaciones no disponible")
            except Exception as e:
                logger.warning(f"Error al notificar cliente: {e}")

    except Pedido.DoesNotExist:
        logger.warning(f"No se pudo obtener pedido anterior con ID {instance.pk}")
    finally:
        desmarcar_procesando('pre_save_validate', instance.id)


# ==========================================================
# 📦 SEÑALES DE ESTADO ENTREGADO (CORREGIDO)
# ==========================================================

@receiver(post_save, sender=Pedido)
def procesar_pedido_entregado(sender, instance, created, **kwargs):
    """
    ✅ CORREGIDO: Eliminados accesos a campos inexistentes

    Ejecuta lógica adicional cuando un pedido es marcado como entregado.
    Ahora calcula estadísticas dinámicamente en lugar de actualizar campos.
    """
    # ✅ Prevenir recursión y procesar solo pedidos entregados
    if created or instance.estado != EstadoPedido.ENTREGADO:
        return

    if esta_procesando('entregado', instance.id):
        return

    # Verificar que no se haya procesado antes
    if not instance.fecha_entregado:
        return

    tiempo_desde_entrega = timezone.now() - instance.fecha_entregado

    # Solo procesar si fue marcado recientemente (últimos 10 segundos)
    if tiempo_desde_entrega.total_seconds() > 10:
        return

    try:
        marcar_procesando('entregado', instance.id)

        logger.info(
            f"[PEDIDO ENTREGADO] #{instance.id} - "
            f"Repartidor: {instance.repartidor.user.get_full_name() if instance.repartidor else 'N/A'} - "
            f"Comisión: ${instance.comision_repartidor}"
        )

        # ✅ CORREGIDO: Actualizar estadísticas del repartidor
        if instance.repartidor:
            try:
                repartidor = instance.repartidor

                # ✅ Usar método que SÍ existe en el modelo
                repartidor.incrementar_entregas(unidades=1)

                # ✅ NUEVO: Calcular estadísticas dinámicamente
                estadisticas_repartidor = Pedido.objects.filter(
                    repartidor=repartidor,
                    estado=EstadoPedido.ENTREGADO
                ).aggregate(
                    total_entregas=Count('id'),
                    total_comisiones=Sum('comision_repartidor')
                )

                logger.info(
                    f"[ESTADÍSTICAS REPARTIDOR] {repartidor.user.email} - "
                    f"Entregas completadas: {repartidor.entregas_completadas} - "
                    f"Total histórico: {estadisticas_repartidor['total_entregas']} - "
                    f"Comisiones acumuladas: ${estadisticas_repartidor['total_comisiones'] or 0}"
                )

            except AttributeError as e:
                logger.error(
                    f"Error al acceder al repartidor del pedido #{instance.id}: {e}"
                )
            except Exception as e:
                logger.warning(
                    f"No se pudieron actualizar estadísticas del repartidor: {e}"
                )

        # ✅ CORREGIDO: Calcular estadísticas del proveedor dinámicamente
        if instance.proveedor:
            try:
                proveedor = instance.proveedor

                # ✅ NUEVO: Calcular estadísticas sin campos adicionales
                estadisticas_proveedor = Pedido.objects.filter(
                    proveedor=proveedor,
                    estado=EstadoPedido.ENTREGADO
                ).aggregate(
                    total_pedidos=Count('id'),
                    total_ventas=Sum('total'),
                    comision_total=Sum('comision_proveedor')
                )

                logger.info(
                    f"[ESTADÍSTICAS PROVEEDOR] {proveedor.nombre} - "
                    f"Pedidos entregados: {estadisticas_proveedor['total_pedidos']} - "
                    f"Ventas totales: ${estadisticas_proveedor['total_ventas'] or 0} - "
                    f"Comisiones: ${estadisticas_proveedor['comision_total'] or 0}"
                )

            except AttributeError as e:
                logger.error(
                    f"Error al acceder al proveedor del pedido #{instance.id}: {e}"
                )
            except Exception as e:
                logger.warning(
                    f"No se pudieron calcular estadísticas del proveedor: {e}"
                )

        # Enviar notificación de agradecimiento al cliente
        try:
            from notificaciones.services import enviar_agradecimiento_cliente
            enviar_agradecimiento_cliente(instance)
        except ImportError:
            logger.debug("Servicio de agradecimiento no disponible")
        except Exception as e:
            logger.warning(f"Error al enviar agradecimiento: {e}")

        # Solicitar calificación del servicio
        try:
            from calificaciones.services import solicitar_calificacion
            solicitar_calificacion(instance)
        except ImportError:
            logger.debug("Servicio de calificaciones no disponible")
        except Exception as e:
            logger.warning(f"Error al solicitar calificación: {e}")

    finally:
        desmarcar_procesando('entregado', instance.id)


# ==========================================================
# ❌ SEÑALES DE PEDIDO CANCELADO (MEJORADO)
# ==========================================================

@receiver(post_save, sender=Pedido)
def procesar_pedido_cancelado(sender, instance, created, **kwargs):
    """
    ✅ MEJORADO: Manejo robusto de cancelación

    Ejecuta lógica cuando un pedido es cancelado.
    """
    # Solo procesar cancelaciones, no creaciones
    if created or instance.estado != EstadoPedido.CANCELADO:
        return

    # ✅ Prevenir recursión
    if esta_procesando('cancelado', instance.id):
        return

    try:
        marcar_procesando('cancelado', instance.id)

        logger.warning(
            f"[PEDIDO CANCELADO] #{instance.id} - "
            f"Cancelado por: {instance.cancelado_por or 'No especificado'} - "
            f"Cliente: {instance.cliente.user.email} - "
            f"Estado anterior: detectado en pre_save"
        )

        # ✅ Liberar repartidor si estaba asignado
        if instance.repartidor:
            try:
                repartidor = instance.repartidor

                # Asegurarse de que el repartidor quede disponible
                if not repartidor.disponible:
                    repartidor.marcar_disponible()
                    logger.info(
                        f"✅ Repartidor {repartidor.user.email} liberado tras "
                        f"cancelación del pedido #{instance.id}"
                    )
                else:
                    logger.debug(
                        f"Repartidor {repartidor.user.email} ya estaba disponible"
                    )

            except AttributeError as e:
                logger.error(f"Error al acceder al repartidor: {e}")
            except Exception as e:
                logger.error(f"Error al liberar repartidor: {e}")

        # Notificar a las partes involucradas
        try:
            from notificaciones.services import notificar_cancelacion
            notificar_cancelacion(instance)
        except ImportError:
            logger.debug("Servicio de notificaciones no disponible")
        except Exception as e:
            logger.warning(f"Error al notificar cancelación: {e}")

        # Registrar en sistema de analíticas
        try:
            from analytics.services import registrar_cancelacion
            registrar_cancelacion(instance)
        except ImportError:
            logger.debug("Sistema de analytics no disponible")
        except Exception as e:
            logger.warning(f"Error al registrar en analytics: {e}")

    finally:
        desmarcar_procesando('cancelado', instance.id)


# ==========================================================
# 🔔 SEÑALES DE NOTIFICACIONES POR ESTADO (MEJORADO)
# ==========================================================

@receiver(post_save, sender=Pedido)
def notificar_cambios_estado(sender, instance, created, **kwargs):
    """
    ✅ MEJORADO: Evita notificaciones duplicadas

    Envía notificaciones push/email según el estado del pedido.
    """
    # No notificar en creación (ya se hace en otro signal)
    if created:
        return

    # ✅ Prevenir recursión y notificaciones duplicadas
    if esta_procesando('notificar', instance.id):
        return

    try:
        marcar_procesando('notificar', instance.id)

        from notificaciones.services import enviar_notificacion_estado

        # Mapeo de estados a mensajes
        mensajes_estado = {
            EstadoPedido.CONFIRMADO: "Tu pedido ha sido confirmado 📦",
            EstadoPedido.EN_PREPARACION: "Tu pedido está siendo preparado 👨‍🍳",
            EstadoPedido.EN_RUTA: "Tu pedido está en camino 🚚",
            EstadoPedido.ENTREGADO: "¡Tu pedido ha sido entregado! 🎉",
            EstadoPedido.CANCELADO: "Tu pedido ha sido cancelado ❌",
        }

        mensaje = mensajes_estado.get(instance.estado)
        if mensaje:
            enviar_notificacion_estado(
                usuario=instance.cliente.user,
                pedido=instance,
                mensaje=mensaje
            )
            logger.debug(
                f"Notificación enviada para pedido #{instance.id}: {mensaje}"
            )

    except ImportError:
        logger.debug("Servicio de notificaciones no disponible")
    except Exception as e:
        logger.error(f"Error al enviar notificación: {e}")
    finally:
        desmarcar_procesando('notificar', instance.id)


# ==========================================================
# 📈 SEÑALES DE MÉTRICAS Y ANALYTICS (MEJORADO)
# ==========================================================

@receiver(post_save, sender=Pedido)
def actualizar_metricas_tiempo_real(sender, instance, created, **kwargs):
    """
    ✅ MEJORADO: Actualización segura de métricas

    Actualiza métricas en tiempo real para el dashboard.
    """
    # ✅ Prevenir recursión
    if esta_procesando('metricas', instance.id):
        return

    try:
        marcar_procesando('metricas', instance.id)

        from analytics.services import actualizar_metricas

        if created:
            # Incrementar contador de pedidos del día
            actualizar_metricas('pedidos_hoy', incremento=1)
            actualizar_metricas('ventas_hoy', incremento=float(instance.total))
            logger.debug(
                f"Métricas actualizadas para nuevo pedido #{instance.id}"
            )

        # Actualizar métricas por estado
        if instance.estado == EstadoPedido.ENTREGADO:
            actualizar_metricas('pedidos_entregados', incremento=1)
            logger.debug(f"Métrica de pedidos entregados actualizada")
        elif instance.estado == EstadoPedido.CANCELADO:
            actualizar_metricas('pedidos_cancelados', incremento=1)
            logger.debug(f"Métrica de pedidos cancelados actualizada")

    except ImportError:
        logger.debug("Sistema de analytics no disponible")
    except Exception as e:
        logger.error(f"Error al actualizar métricas: {e}")
    finally:
        desmarcar_procesando('metricas', instance.id)


# ==========================================================
# 🗑️ SEÑAL DE ELIMINACIÓN (AUDITORÍA)
# ==========================================================

@receiver(post_delete, sender=Pedido)
def pedido_eliminado(sender, instance, **kwargs):
    """
    ✅ MEJORADO: Auditoría detallada

    Registra cuando un pedido es eliminado del sistema.
    NOTA: Solo admins deberían poder eliminar pedidos.
    """
    logger.warning(
        f"[PEDIDO ELIMINADO] #{instance.id} - "
        f"Estado: {instance.get_estado_display()} - "
        f"Cliente: {instance.cliente.user.email} - "
        f"Total: ${instance.total} - "
        f"Creado: {instance.creado_en.strftime('%Y-%m-%d %H:%M')}"
    )

    # Registrar en sistema de auditoría
    try:
        from auditoria.services import registrar_eliminacion
        registrar_eliminacion(
            modelo='Pedido',
            instancia_id=instance.id,
            datos={
                'cliente': instance.cliente.user.email,
                'total': str(instance.total),
                'estado': instance.estado,
                'tipo': instance.tipo,
                'proveedor': instance.proveedor.nombre if instance.proveedor else None,
                'repartidor': instance.repartidor.user.email if instance.repartidor else None,
                'creado_en': instance.creado_en.isoformat(),
            }
        )
        logger.info("Eliminación registrada en sistema de auditoría")
    except ImportError:
        logger.debug("Sistema de auditoría no disponible")
    except Exception as e:
        logger.error(f"Error al registrar eliminación en auditoría: {e}")


# ==========================================================
# 💡 SEÑALES PERSONALIZADAS (OPCIONAL)
# ==========================================================

# Puedes crear señales personalizadas para eventos específicos
from django.dispatch import Signal

# Señal personalizada para cuando un pedido llega tarde
pedido_retrasado = Signal()


@receiver(pedido_retrasado)
def manejar_pedido_retrasado(sender, pedido, tiempo_retraso, **kwargs):
    """
    ✅ NUEVO: Maneja la lógica cuando un pedido se retrasa.
    """
    logger.warning(
        f"[PEDIDO RETRASADO] #{pedido.id} - "
        f"Retraso: {tiempo_retraso} minutos - "
        f"Estado: {pedido.get_estado_display()}"
    )

    # Notificar al cliente
    try:
        from notificaciones.services import notificar_retraso
        notificar_retraso(pedido, tiempo_retraso)
        logger.info(f"Cliente notificado sobre retraso del pedido #{pedido.id}")
    except ImportError:
        logger.debug("Servicio de notificaciones no disponible")
    except Exception as e:
        logger.warning(f"Error al notificar retraso: {e}")

    # Aplicar compensación automática si es necesario
    if tiempo_retraso > 30:  # Más de 30 minutos
        logger.info(
            f"Aplicando compensación por retraso al pedido #{pedido.id} "
            f"({tiempo_retraso} min)"
        )
        # Lógica de compensación (descuento, cupón, etc.)
        try:
            from compensaciones.services import aplicar_compensacion_retraso
            aplicar_compensacion_retraso(pedido, tiempo_retraso)
        except ImportError:
            logger.debug("Sistema de compensaciones no disponible")
        except Exception as e:
            logger.warning(f"Error al aplicar compensación: {e}")


# ==========================================================
# 🔧 UTILIDADES PARA ACTIVAR SEÑALES PERSONALIZADAS
# ==========================================================

def verificar_pedidos_retrasados():
    """
    ✅ MEJORADO: Verificación segura de pedidos retrasados

    Función que puede ser llamada por un cron job o tarea de Celery
    para verificar pedidos retrasados.
    """
    from datetime import timedelta

    # Buscar pedidos en ruta por más de 60 minutos
    tiempo_limite = timezone.now() - timedelta(minutes=60)

    try:
        pedidos_retrasados = Pedido.objects.filter(
            estado=EstadoPedido.EN_RUTA,
            actualizado_en__lt=tiempo_limite
        ).select_related('cliente__user', 'repartidor__user')

        contador = 0
        for pedido in pedidos_retrasados:
            tiempo_retraso = (timezone.now() - pedido.actualizado_en).total_seconds() / 60

            # Emitir señal personalizada
            pedido_retrasado.send(
                sender=Pedido,
                pedido=pedido,
                tiempo_retraso=int(tiempo_retraso)
            )
            contador += 1

        logger.info(
            f"Verificación de pedidos retrasados completada: "
            f"{contador} pedidos encontrados"
        )
        return contador

    except Exception as e:
        logger.error(f"Error al verificar pedidos retrasados: {e}", exc_info=True)
        return 0


# ==========================================================
# 📊 FUNCIONES AUXILIARES PARA ESTADÍSTICAS
# ==========================================================

def obtener_estadisticas_repartidor(repartidor_id):
    """
    ✅ NUEVO: Obtiene estadísticas de un repartidor

    Calcula dinámicamente sin depender de campos adicionales en el modelo.
    """
    try:
        estadisticas = Pedido.objects.filter(
            repartidor_id=repartidor_id,
            estado=EstadoPedido.ENTREGADO
        ).aggregate(
            total_entregas=Count('id'),
            total_comisiones=Sum('comision_repartidor'),
            promedio_comision=Sum('comision_repartidor') / Count('id')
        )

        return estadisticas
    except Exception as e:
        logger.error(f"Error al calcular estadísticas de repartidor: {e}")
        return {
            'total_entregas': 0,
            'total_comisiones': 0,
            'promedio_comision': 0
        }


def obtener_estadisticas_proveedor(proveedor_id):
    """
    ✅ NUEVO: Obtiene estadísticas de un proveedor

    Calcula dinámicamente sin depender de campos adicionales en el modelo.
    """
    try:
        estadisticas = Pedido.objects.filter(
            proveedor_id=proveedor_id,
            estado=EstadoPedido.ENTREGADO
        ).aggregate(
            total_pedidos=Count('id'),
            total_ventas=Sum('total'),
            total_comisiones=Sum('comision_proveedor'),
            ticket_promedio=Sum('total') / Count('id')
        )

        return estadisticas
    except Exception as e:
        logger.error(f"Error al calcular estadísticas de proveedor: {e}")
        return {
            'total_pedidos': 0,
            'total_ventas': 0,
            'total_comisiones': 0,
            'ticket_promedio': 0
        }
