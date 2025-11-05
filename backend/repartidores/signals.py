# repartidores/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
import logging

from .models import (
    Repartidor,
    RepartidorVehiculo,
    CalificacionRepartidor,
    EstadoRepartidor
)

logger = logging.getLogger('repartidores')


# ==========================================================
# SEÑAL: Actualizar calificación promedio automáticamente
# ==========================================================
@receiver(post_save, sender=CalificacionRepartidor)
def actualizar_calificacion_repartidor(sender, instance, created, **kwargs):
    """
    Cuando se crea o actualiza una calificación, recalcula
    automáticamente el promedio del repartidor.
    """
    if created:
        logger.info(
            f"Nueva calificación para repartidor {instance.repartidor_id}: "
            f"{instance.puntuacion} estrellas"
        )

    # Recalcular promedio
    instance.repartidor.recalcular_calificacion_promedio()


# ==========================================================
# SEÑAL: Validar solo un vehículo activo por repartidor
# ==========================================================
@receiver(pre_save, sender=RepartidorVehiculo)
def validar_vehiculo_unico_activo(sender, instance, **kwargs):
    """
    Asegura que solo haya un vehículo activo por repartidor.
    Si se activa uno nuevo, desactiva los demás.
    """
    if instance.activo:
        # Desactivar otros vehículos activos del mismo repartidor
        RepartidorVehiculo.objects.filter(
            repartidor=instance.repartidor,
            activo=True
        ).exclude(pk=instance.pk).update(activo=False)

        logger.info(
            f"Vehículo {instance.tipo} ({instance.placa}) "
            f"activado para repartidor {instance.repartidor_id}"
        )


# ==========================================================
# SEÑAL: Log automático al cambiar estado del repartidor
# ==========================================================
@receiver(pre_save, sender=Repartidor)
def validar_cambio_estado(sender, instance, **kwargs):
    """
    Valida que el cambio de estado sea válido según las reglas de negocio.
    """
    if instance.pk:  # Solo para actualizaciones, no creaciones
        try:
            old_instance = Repartidor.objects.get(pk=instance.pk)

            # Si el estado cambió
            if old_instance.estado != instance.estado:
                # Validar que esté verificado si pasa a disponible/ocupado
                if instance.estado in (EstadoRepartidor.DISPONIBLE, EstadoRepartidor.OCUPADO):
                    if not instance.verificado:
                        raise ValidationError(
                            f"No se puede cambiar a {instance.estado}: "
                            "el repartidor no está verificado"
                        )

                    if not instance.activo:
                        raise ValidationError(
                            f"No se puede cambiar a {instance.estado}: "
                            "el repartidor no está activo"
                        )

                logger.info(
                    f"Estado de repartidor {instance.id} cambiado: "
                    f"{old_instance.estado} → {instance.estado}"
                )

        except Repartidor.DoesNotExist:
            pass


# ==========================================================
# SEÑAL: Desactivar repartidor cuando su cuenta se desactiva
# ==========================================================
@receiver(pre_save, sender=Repartidor)
def auto_desactivar_estado(sender, instance, **kwargs):
    """
    Si se desactiva la cuenta del repartidor, automáticamente
    lo pone fuera de servicio.
    """
    if instance.pk:
        try:
            old_instance = Repartidor.objects.get(pk=instance.pk)

            # Si pasó de activo a inactivo
            if old_instance.activo and not instance.activo:
                instance.estado = EstadoRepartidor.FUERA_SERVICIO
                logger.warning(
                    f"Repartidor {instance.id} desactivado, "
                    f"estado cambiado a FUERA_SERVICIO"
                )

        except Repartidor.DoesNotExist:
            pass
