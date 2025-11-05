# notificaciones/models.py
"""
Modelo de Notificaciones para historial en la aplicación
✅ Guarda todas las notificaciones enviadas (push y en app)
✅ Sistema de lectura/no leída
✅ Relación con pedidos
"""

from django.db import models
from django.utils import timezone
from authentication.models import User
import uuid
import logging

logger = logging.getLogger('notificaciones')


class TipoNotificacion(models.TextChoices):
    """Tipos de notificación"""
    PEDIDO = 'pedido', 'Pedido'
    PROMOCION = 'promocion', 'Promoción'
    SISTEMA = 'sistema', 'Sistema'
    REPARTIDOR = 'repartidor', 'Repartidor'


class Notificacion(models.Model):
    """
    ✅ Modelo de Notificación

    Almacena el historial de todas las notificaciones enviadas.
    Se guarda tanto si se envió push como si solo es in-app.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # ============================================
    # RELACIONES
    # ============================================
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Usuario',
        help_text='Usuario que recibe la notificación'
    )

    pedido = models.ForeignKey(
        'pedidos.Pedido',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificaciones',
        verbose_name='Pedido relacionado',
        help_text='Pedido asociado (si aplica)'
    )

    # ============================================
    # CONTENIDO
    # ============================================
    tipo = models.CharField(
        max_length=20,
        choices=TipoNotificacion.choices,
        default=TipoNotificacion.PEDIDO,
        verbose_name='Tipo'
    )

    titulo = models.CharField(
        max_length=100,
        verbose_name='Título',
        help_text='Título de la notificación'
    )

    mensaje = models.TextField(
        verbose_name='Mensaje',
        help_text='Contenido de la notificación'
    )

    # ============================================
    # DATOS ADICIONALES (JSON)
    # ============================================
    datos_extra = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Datos adicionales',
        help_text='Información extra en formato JSON'
    )

    # ============================================
    # ESTADO
    # ============================================
    leida = models.BooleanField(
        default=False,
        verbose_name='Leída',
        db_index=True
    )

    enviada_push = models.BooleanField(
        default=False,
        verbose_name='Enviada por push',
        help_text='Indica si se envió notificación push'
    )

    error_envio = models.TextField(
        blank=True,
        null=True,
        verbose_name='Error de envío',
        help_text='Mensaje de error si falló el envío push'
    )

    # ============================================
    # FECHAS
    # ============================================
    creada_en = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación',
        db_index=True
    )

    leida_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de lectura'
    )

    class Meta:
        db_table = 'notificaciones'
        ordering = ['-creada_en']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'

        indexes = [
            models.Index(fields=['usuario', '-creada_en']),
            models.Index(fields=['usuario', 'leida']),
            models.Index(fields=['tipo', '-creada_en']),
            models.Index(fields=['pedido']),
        ]

    def __str__(self):
        return f"{self.titulo} - {self.usuario.email}"

    def __repr__(self):
        return (
            f"<Notificacion id={self.id} tipo={self.tipo} "
            f"usuario={self.usuario_id} leida={self.leida}>"
        )

    # ============================================
    # MÉTODOS
    # ============================================

    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        if not self.leida:
            self.leida = True
            self.leida_en = timezone.now()
            self.save(update_fields=['leida', 'leida_en'])

            logger.info(
                f"✅ Notificación marcada como leída: {self.id} - {self.usuario.email}"
            )

    def marcar_como_no_leida(self):
        """Marca la notificación como no leída"""
        if self.leida:
            self.leida = False
            self.leida_en = None
            self.save(update_fields=['leida', 'leida_en'])

            logger.info(
                f"📬 Notificación marcada como no leída: {self.id} - {self.usuario.email}"
            )

    @classmethod
    def marcar_todas_leidas(cls, usuario):
        """
        Marca todas las notificaciones de un usuario como leídas

        Args:
            usuario (User): Usuario

        Returns:
            int: Cantidad de notificaciones actualizadas
        """
        count = cls.objects.filter(
            usuario=usuario,
            leida=False
        ).update(
            leida=True,
            leida_en=timezone.now()
        )

        logger.info(
            f"✅ {count} notificaciones marcadas como leídas para {usuario.email}"
        )

        return count

    @classmethod
    def obtener_no_leidas(cls, usuario):
        """
        Obtiene notificaciones no leídas de un usuario

        Args:
            usuario (User): Usuario

        Returns:
            QuerySet: Notificaciones no leídas
        """
        return cls.objects.filter(
            usuario=usuario,
            leida=False
        ).select_related('pedido')

    @classmethod
    def contar_no_leidas(cls, usuario):
        """
        Cuenta notificaciones no leídas

        Args:
            usuario (User): Usuario

        Returns:
            int: Cantidad de notificaciones no leídas
        """
        return cls.objects.filter(
            usuario=usuario,
            leida=False
        ).count()

    @classmethod
    def eliminar_antiguas(cls, dias=30):
        """
        Elimina notificaciones leídas con más de X días

        Args:
            dias (int): Días de antigüedad

        Returns:
            int: Cantidad eliminada
        """
        from datetime import timedelta

        fecha_limite = timezone.now() - timedelta(days=dias)

        count, _ = cls.objects.filter(
            leida=True,
            creada_en__lt=fecha_limite
        ).delete()

        logger.info(
            f"🗑️ {count} notificaciones antiguas eliminadas (>{dias} días)"
        )

        return count

    @property
    def tiempo_transcurrido(self):
        """Retorna tiempo desde creación con formato legible"""
        diff = timezone.now() - self.creada_en
        minutos = int(diff.total_seconds() // 60)

        if minutos < 1:
            return "Ahora"
        elif minutos < 60:
            return f"Hace {minutos} min"
        elif minutos < 1440:
            horas = minutos // 60
            return f"Hace {horas}h"
        else:
            dias = minutos // 1440
            return f"Hace {dias}d"
