# chat/signals.py
"""
Signals para crear chats automáticamente

✅ FUNCIONALIDAD:
- Cuando se asigna un repartidor a un pedido → Crea chats automáticamente
- Pedido con Proveedor → 2 chats (cliente+proveedor)
- Encargo Directo → 1 chat (solo cliente)
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from pedidos.models import Pedido
from .models import Chat
import logging

logger = logging.getLogger('chat')


@receiver(post_save, sender=Pedido)
def crear_chats_pedido(sender, instance, created, **kwargs):
    """
    ✅ SIGNAL: Crea chats cuando se asigna un repartidor

    Se ejecuta cuando:
    - Se crea un pedido con repartidor asignado
    - Se actualiza un pedido y se le asigna un repartidor
    """

    # Prevenir ejecución en fixtures/loaddata
    if kwargs.get('raw', False):
        return

    # Verificar si tiene repartidor
    if not instance.repartidor:
        return

    # Si el pedido ya tiene chats, no crear duplicados
    if instance.chats.exists():
        logger.debug(f"ℹ️ Pedido {instance.pk} ya tiene chats creados")
        return

    try:
        # ✅ CREAR CHATS SEGÚN TIPO DE PEDIDO
        chats = Chat.crear_chats_para_pedido(instance)

        # Logging detallado
        if chats['proveedor_repartidor']:
            logger.info(
                f"✅ Chats creados para pedido {instance.pk}: "
                f"Cliente↔Repartidor + Proveedor↔Repartidor"
            )
        else:
            logger.info(
                f"✅ Chat creado para pedido {instance.pk}: "
                f"Cliente↔Repartidor (encargo directo)"
            )

        # TODO: Enviar notificaciones push a los participantes
        # from .utils import enviar_notificacion_nuevo_chat
        # enviar_notificacion_nuevo_chat(chats)

    except Exception as e:
        logger.error(
            f"❌ Error creando chats para pedido {instance.pk}: {e}",
            exc_info=True
        )
