# -*- coding: utf-8 -*-
# rifas/models.py
"""
Sistema de Rifas Mensuales

✅ FUNCIONALIDAD:
- Rifa mensual automática que se reinicia cada mes
- Participación requiere 3+ pedidos entregados
- Solo admin puede crear/gestionar rifas
- Sorteo automático al finalizar el mes
"""

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q, Count
from authentication.models import User
from pedidos.models import Pedido, EstadoPedido
import uuid
import random
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('rifas')


# ============================================
# 📋 ENUMS
# ============================================

class EstadoRifa(models.TextChoices):
    """Estados de la rifa"""
    ACTIVA = 'activa', 'Activa'
    FINALIZADA = 'finalizada', 'Finalizada'
    CANCELADA = 'cancelada', 'Cancelada'


# ============================================
# 🎲 MODELO: RIFA
# ============================================

class Rifa(models.Model):
    """
    Rifa mensual del sistema

    ✅ REGLAS:
    - Dura 1 mes calendario (ej: 1 nov - 30 nov)
    - Usuarios con 3+ pedidos entregados pueden participar
    - Se reinicia automáticamente cada mes
    - Admin gestiona desde Django Admin
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # ============================================
    # INFORMACIÓN BÁSICA
    # ============================================

    titulo = models.CharField(
        max_length=200,
        verbose_name='Título',
        help_text='Ej: Rifa Noviembre 2024'
    )

    descripcion = models.TextField(
        verbose_name='Descripción',
        help_text='Descripción del premio y condiciones'
    )

    imagen = models.ImageField(
        upload_to='rifas/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Imagen del Premio',
        help_text='Imagen promocional de la rifa'
    )

    # ============================================
    # PREMIO
    # ============================================

    premio = models.CharField(
        max_length=300,
        verbose_name='Premio',
        help_text='Descripción del premio'
    )

    valor_premio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Valor del Premio',
        help_text='Valor estimado del premio en dólares'
    )

    # ============================================
    # FECHAS (MENSUAL)
    # ============================================

    fecha_inicio = models.DateTimeField(
        verbose_name='Fecha de Inicio',
        help_text='Inicio de la rifa (1ro del mes)'
    )

    fecha_fin = models.DateTimeField(
        verbose_name='Fecha de Fin',
        help_text='Fin de la rifa (último día del mes)'
    )

    fecha_sorteo = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha del Sorteo',
        help_text='Cuándo se realizó el sorteo'
    )

    # ============================================
    # REQUISITOS
    # ============================================

    pedidos_minimos = models.PositiveIntegerField(
        default=3,
        verbose_name='Pedidos Mínimos',
        help_text='Cantidad mínima de pedidos para participar'
    )

    # ============================================
    # ESTADO
    # ============================================

    estado = models.CharField(
        max_length=20,
        choices=EstadoRifa.choices,
        default=EstadoRifa.ACTIVA,
        verbose_name='Estado',
        db_index=True
    )

    # ============================================
    # GANADOR
    # ============================================

    ganador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rifas_ganadas',
        verbose_name='Ganador',
        help_text='Usuario ganador del sorteo'
    )

    # ============================================
    # METADATA
    # ============================================

    mes = models.PositiveIntegerField(
        verbose_name='Mes',
        help_text='Mes de la rifa (1-12)',
        db_index=True
    )

    anio = models.PositiveIntegerField(
        verbose_name='Año',
        help_text='Año de la rifa',
        db_index=True
    )

    # ============================================
    # AUDITORÍA
    # ============================================

    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='rifas_creadas',
        verbose_name='Creado Por',
        help_text='Admin que creó la rifa'
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    class Meta:
        db_table = 'rifas'
        verbose_name = 'Rifa'
        verbose_name_plural = 'Rifas'
        ordering = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['estado', 'fecha_inicio']),
            models.Index(fields=['mes', 'anio']),
            models.Index(fields=['-fecha_inicio']),
        ]
        constraints = [
            # Solo una rifa activa por mes
            models.UniqueConstraint(
                fields=['mes', 'anio', 'estado'],
                condition=Q(estado=EstadoRifa.ACTIVA),
                name='una_rifa_activa_por_mes'
            ),
        ]

    def __str__(self):
        return f"{self.titulo} - {self.get_estado_display()}"

    # ============================================
    # ✅ VALIDACIONES
    # ============================================

    def clean(self):
        """Validaciones personalizadas"""
        super().clean()

        errors = {}

        # Validar fechas
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_inicio >= self.fecha_fin:
                errors['fecha_fin'] = 'La fecha de fin debe ser posterior a la de inicio'

        # Validar que sea del mismo mes
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_inicio.month != self.fecha_fin.month:
                errors['fecha_fin'] = 'La rifa debe ser dentro del mismo mes'

        # Validar pedidos mínimos
        if self.pedidos_minimos < 1:
            errors['pedidos_minimos'] = 'Debe requerir al menos 1 pedido'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Override save para calcular mes/año"""
        if self.fecha_inicio:
            self.mes = self.fecha_inicio.month
            self.anio = self.fecha_inicio.year

        self.full_clean()
        super().save(*args, **kwargs)

    # ============================================
    # ✅ MÉTODOS DE NEGOCIO
    # ============================================

    @classmethod
    def crear_rifa_mensual(cls, mes=None, anio=None, creado_por=None):
        """
        Crea la rifa del mes automáticamente

        Args:
            mes (int): Mes (1-12), actual por defecto
            anio (int): Año, actual por defecto
            creado_por (User): Admin que crea la rifa

        Returns:
            Rifa: Instancia creada
        """
        now = timezone.now()

        if mes is None:
            mes = now.month
        if anio is None:
            anio = now.year

        # Verificar si ya existe rifa activa para ese mes
        rifa_existente = cls.objects.filter(
            mes=mes,
            anio=anio,
            estado=EstadoRifa.ACTIVA
        ).first()

        if rifa_existente:
            logger.info(f"Ya existe rifa activa para {mes}/{anio}")
            return rifa_existente

        # Calcular fechas del mes
        fecha_inicio = timezone.make_aware(datetime(anio, mes, 1, 0, 0, 0))

        # Último día del mes
        if mes == 12:
            siguiente_mes = datetime(anio + 1, 1, 1)
        else:
            siguiente_mes = datetime(anio, mes + 1, 1)

        fecha_fin = siguiente_mes - timedelta(seconds=1)

        # Nombres de meses en español
        meses = [
            '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]

        # Crear rifa
        rifa = cls.objects.create(
            titulo=f"Rifa {meses[mes]} {anio}",
            descripcion=f"Rifa mensual de {meses[mes]} {anio}. Participa automáticamente al tener 3 o más pedidos completados este mes.",
            premio="Premio sorpresa del mes",  # Admin puede editar
            valor_premio=50.00,  # Admin puede editar
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            pedidos_minimos=3,
            mes=mes,
            anio=anio,
            estado=EstadoRifa.ACTIVA,
            creado_por=creado_por
        )

        logger.info(f"✅ Rifa creada: {rifa.titulo}")
        return rifa

    def obtener_participantes_elegibles(self):
        """
        Obtiene usuarios elegibles para participar

        Returns:
            QuerySet: Usuarios con 3+ pedidos entregados
        """
        # Obtener usuarios con pedidos entregados en el rango de la rifa
        usuarios_elegibles = User.objects.filter(
            rol=User.RolChoices.USUARIO,
            is_active=True,
            cuenta_desactivada=False
        ).annotate(
            pedidos_completados=Count(
                'perfil_usuario__pedidos',
                filter=Q(
                    perfil_usuario__pedidos__estado=EstadoPedido.ENTREGADO,
                    perfil_usuario__pedidos__fecha_entregado__gte=self.fecha_inicio,
                    perfil_usuario__pedidos__fecha_entregado__lte=self.fecha_fin
                )
            )
        ).filter(
            pedidos_completados__gte=self.pedidos_minimos
        ).distinct()

        return usuarios_elegibles

    def usuario_es_elegible(self, usuario):
        """
        Verifica si un usuario específico es elegible

        Args:
            usuario (User): Usuario a verificar

        Returns:
            dict: {'elegible': bool, 'pedidos': int, 'faltantes': int}
        """
        if usuario.rol != User.RolChoices.USUARIO:
            return {
                'elegible': False,
                'pedidos': 0,
                'faltantes': self.pedidos_minimos,
                'razon': 'Solo usuarios regulares pueden participar'
            }

        # Contar pedidos entregados en el rango
        pedidos_completados = Pedido.objects.filter(
            cliente__user=usuario,
            estado=EstadoPedido.ENTREGADO,
            fecha_entregado__gte=self.fecha_inicio,
            fecha_entregado__lte=self.fecha_fin
        ).count()

        elegible = pedidos_completados >= self.pedidos_minimos
        faltantes = max(0, self.pedidos_minimos - pedidos_completados)

        return {
            'elegible': elegible,
            'pedidos': pedidos_completados,
            'faltantes': faltantes,
            'razon': 'Cumples los requisitos' if elegible else f'Te faltan {faltantes} pedidos'
        }

    def realizar_sorteo(self):
        """
        Realiza el sorteo y selecciona un ganador aleatorio

        Returns:
            User: Usuario ganador
        """
        if self.estado != EstadoRifa.ACTIVA:
            raise ValidationError('Solo se puede sortear una rifa activa')

        if self.ganador:
            raise ValidationError('Esta rifa ya tiene un ganador')

        # Obtener participantes elegibles
        participantes = list(self.obtener_participantes_elegibles())

        if not participantes:
            logger.warning(f"⚠️ No hay participantes elegibles para la rifa {self.titulo}")
            self.estado = EstadoRifa.FINALIZADA
            self.fecha_sorteo = timezone.now()
            self.save()
            return None

        # Seleccionar ganador aleatorio
        ganador = random.choice(participantes)

        self.ganador = ganador
        self.estado = EstadoRifa.FINALIZADA
        self.fecha_sorteo = timezone.now()
        self.save()

        logger.info(
            f"🎉 Ganador del sorteo {self.titulo}: "
            f"{ganador.get_full_name()} ({ganador.email})"
        )

        # Crear registro de participación del ganador
        Participacion.objects.create(
            rifa=self,
            usuario=ganador,
            ganador=True
        )

        return ganador

    def cancelar_rifa(self, motivo=None):
        """Cancela la rifa"""
        if self.estado == EstadoRifa.FINALIZADA:
            raise ValidationError('No se puede cancelar una rifa finalizada')

        self.estado = EstadoRifa.CANCELADA
        self.save()

        logger.warning(f"❌ Rifa cancelada: {self.titulo}. Motivo: {motivo}")

    @classmethod
    def obtener_rifa_activa(cls):
        """
        Obtiene la rifa activa actual

        Returns:
            Rifa: Rifa activa o None
        """
        return cls.objects.filter(
            estado=EstadoRifa.ACTIVA
        ).order_by('-fecha_inicio').first()

    @classmethod
    def obtener_historial_ganadores(cls, limit=10):
        """
        Obtiene historial de ganadores recientes

        Args:
            limit (int): Cantidad de registros

        Returns:
            QuerySet: Rifas finalizadas con ganador
        """
        return cls.objects.filter(
            estado=EstadoRifa.FINALIZADA,
            ganador__isnull=False
        ).select_related('ganador').order_by('-fecha_sorteo')[:limit]

    # ============================================
    # ✅ PROPIEDADES
    # ============================================

    @property
    def esta_activa(self):
        """Verifica si la rifa está activa"""
        return self.estado == EstadoRifa.ACTIVA

    @property
    def dias_restantes(self):
        """Calcula días restantes"""
        if self.estado != EstadoRifa.ACTIVA:
            return 0

        diff = self.fecha_fin - timezone.now()
        return max(0, diff.days)

    @property
    def total_participantes(self):
        """Cuenta participantes elegibles"""
        return self.obtener_participantes_elegibles().count()

    @property
    def mes_nombre(self):
        """Nombre del mes en español"""
        meses = [
            '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]
        return meses[self.mes]


# ============================================
# 🎟️ MODELO: PARTICIPACIÓN (OPCIONAL)
# ============================================

class Participacion(models.Model):
    """
    Registro de participación en rifas

    Guarda historial de quién participó en cada rifa
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    rifa = models.ForeignKey(
        Rifa,
        on_delete=models.CASCADE,
        related_name='participaciones',
        verbose_name='Rifa'
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='participaciones_rifas',
        verbose_name='Usuario'
    )

    ganador = models.BooleanField(
        default=False,
        verbose_name='Ganador',
        help_text='Indica si este usuario ganó'
    )

    pedidos_completados = models.PositiveIntegerField(
        default=0,
        verbose_name='Pedidos Completados',
        help_text='Cantidad de pedidos al momento del sorteo'
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Registro'
    )

    class Meta:
        db_table = 'rifas_participaciones'
        verbose_name = 'Participación'
        verbose_name_plural = 'Participaciones'
        ordering = ['-fecha_registro']
        unique_together = [['rifa', 'usuario']]
        indexes = [
            models.Index(fields=['rifa', 'usuario']),
            models.Index(fields=['ganador']),
        ]

    def __str__(self):
        ganador_str = " 🏆 GANADOR" if self.ganador else ""
        return f"{self.usuario.email} - {self.rifa.titulo}{ganador_str}"

    def save(self, *args, **kwargs):
        """Calcular pedidos completados al guardar"""
        if not self.pedidos_completados:
            elegibilidad = self.rifa.usuario_es_elegible(self.usuario)
            self.pedidos_completados = elegibilidad['pedidos']

        super().save(*args, **kwargs)
