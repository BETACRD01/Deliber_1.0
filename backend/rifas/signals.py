# Crear: rifas/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Rifa, Participacion
import logging

logger = logging.getLogger('rifas')

@receiver(post_save, sender=Rifa)
def rifa_post_save(sender, instance, created, **kwargs):
    """Signal después de guardar rifa"""
    if created:
        logger.info(f"🎲 Nueva rifa creada: {instance.titulo}")
    else:
        if instance.ganador:
            logger.info(f"🏆 Ganador asignado a {instance.titulo}: {instance.ganador.email}")

@receiver(post_save, sender=Participacion)
def participacion_ganador(sender, instance, created, **kwargs):
    """Notificar cuando hay un ganador"""
    if instance.ganador:
        logger.info(f"🎉 GANADOR: {instance.usuario.email} ganó {instance.rifa.titulo}")
        # Aquí puedes agregar envío de email, notificación push, etc.
