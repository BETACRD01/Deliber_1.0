# -*- coding: utf-8 -*-
# administradores/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from authentication.models import User
from .models import Administrador
import logging

logger = logging.getLogger('administradores')

@receiver(post_save, sender=User)
def crear_perfil_administrador(sender, instance, created, **kwargs):
    """
    Crea automáticamente un perfil de administrador cuando se crea un usuario admin
    """
    if created and instance.rol == User.RolChoices.ADMINISTRADOR:
        try:
            Administrador.objects.create(
                user=instance,
                cargo='Administrador',
                puede_gestionar_usuarios=True,
                puede_gestionar_pedidos=True,
                puede_gestionar_proveedores=True,
                puede_gestionar_repartidores=True,
                puede_gestionar_rifas=True,
                puede_ver_reportes=True,
            )
            logger.info(f'✅ Perfil de administrador creado para: {instance.email}')
        except Exception as e:
            logger.error(f'❌ Error creando perfil admin: {e}')
