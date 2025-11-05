# pagos/models.py
"""
Modelo de Pagos para sistema de delivery.

✅ CARACTERÍSTICAS:
- Soporte para múltiples métodos de pago
- Tracking completo de transacciones
- Sistema de reembolsos
- Validaciones robustas
- Preparado para pasarelas externas
- Historial de cambios de estado
"""
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum, Count
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
import logging

logger = logging.getLogger('pagos')


# ==========================================================
# 📋 ENUMS Y CHOICES
# ==========================================================

class TipoMetodoPago(models.TextChoices):
    """Tipos de métodos de pago disponibles"""
    EFECTIVO = 'efectivo', 'Efectivo'
    TRANSFERENCIA = 'transferencia', 'Transferencia Bancaria'
    TARJETA_CREDITO = 'tarjeta_credito', 'Tarjeta de Crédito'
    TARJETA_DEBITO = 'tarjeta_debito', 'Tarjeta de Débito'


class EstadoPago(models.TextChoices):
    """Estados del ciclo de vida de un pago"""
    PENDIENTE = 'pendiente', 'Pendiente'
    PROCESANDO = 'procesando', 'Procesando'
    COMPLETADO = 'completado', 'Completado'
    FALLIDO = 'fallido', 'Fallido'
    REEMBOLSADO = 'reembolsado', 'Reembolsado'
    CANCELADO = 'cancelado', 'Cancelado'


class TipoTransaccion(models.TextChoices):
    """Tipos de transacciones"""
    PAGO = 'pago', 'Pago'
    REEMBOLSO = 'reembolso', 'Reembolso'
    AJUSTE = 'ajuste', 'Ajuste'
    PROPINA = 'propina', 'Propina'


# ==========================================================
# 🔧 MANAGER PERSONALIZADO
# ==========================================================

class PagoManager(models.Manager):
    """Manager personalizado con querysets optimizados"""

    def get_queryset(self):
        """Queryset base optimizado"""
        return super().get_queryset().select_related(
            'pedido',
            'pedido__cliente__user',
            'metodo_pago'
        )

    def pendientes(self):
        """Pagos pendientes de procesar"""
        return self.filter(estado=EstadoPago.PENDIENTE)

    def procesando(self):
        """Pagos en proceso"""
        return self.filter(estado=EstadoPago.PROCESANDO)

    def completados(self):
        """Pagos completados exitosamente"""
        return self.filter(estado=EstadoPago.COMPLETADO)

    def fallidos(self):
        """Pagos que fallaron"""
        return self.filter(estado=EstadoPago.FALLIDO)

    def reembolsados(self):
        """Pagos reembolsados"""
        return self.filter(estado=EstadoPago.REEMBOLSADO)

    def del_dia(self):
        """Pagos creados hoy"""
        hoy = timezone.now().date()
        return self.filter(creado_en__date=hoy)

    def por_metodo(self, metodo):
        """
        Pagos por método específico

        Args:
            metodo (str): Tipo de método de pago
        """
        return self.filter(metodo_pago__tipo=metodo)

    def efectivo(self):
        """Pagos en efectivo"""
        return self.por_metodo(TipoMetodoPago.EFECTIVO)

    def transferencias(self):
        """Pagos por transferencia"""
        return self.por_metodo(TipoMetodoPago.TRANSFERENCIA)

    def tarjetas(self):
        """Pagos con tarjeta (crédito o débito)"""
        return self.filter(
            metodo_pago__tipo__in=[
                TipoMetodoPago.TARJETA_CREDITO,
                TipoMetodoPago.TARJETA_DEBITO
            ]
        )

    def requieren_verificacion(self):
        """
        Pagos que requieren verificación manual
        (transferencias pendientes)
        """
        return self.filter(
            estado=EstadoPago.PENDIENTE,
            metodo_pago__tipo=TipoMetodoPago.TRANSFERENCIA
        )

    def estadisticas_del_dia(self):
        """Estadísticas agregadas del día"""
        hoy = timezone.now().date()
        pagos_hoy = self.filter(creado_en__date=hoy)

        return pagos_hoy.aggregate(
            total_pagos=Count('id'),
            pagos_completados=Count('id', filter=Q(estado=EstadoPago.COMPLETADO)),
            pagos_pendientes=Count('id', filter=Q(estado=EstadoPago.PENDIENTE)),
            pagos_fallidos=Count('id', filter=Q(estado=EstadoPago.FALLIDO)),
            monto_total=Sum('monto', filter=Q(estado=EstadoPago.COMPLETADO)),
            monto_efectivo=Sum('monto', filter=Q(
                estado=EstadoPago.COMPLETADO,
                metodo_pago__tipo=TipoMetodoPago.EFECTIVO
            )),
            monto_transferencias=Sum('monto', filter=Q(
                estado=EstadoPago.COMPLETADO,
                metodo_pago__tipo=TipoMetodoPago.TRANSFERENCIA
            )),
            monto_tarjetas=Sum('monto', filter=Q(
                estado=EstadoPago.COMPLETADO,
                metodo_pago__tipo__in=[
                    TipoMetodoPago.TARJETA_CREDITO,
                    TipoMetodoPago.TARJETA_DEBITO
                ]
            ))
        )


# ==========================================================
# 💳 MODELO: MÉTODO DE PAGO
# ==========================================================

class MetodoPago(models.Model):
    """
    Catálogo de métodos de pago disponibles

    Permite configurar y habilitar/deshabilitar métodos de pago
    """
    tipo = models.CharField(
        max_length=20,
        choices=TipoMetodoPago.choices,
        unique=True,
        verbose_name='Tipo',
        help_text='Tipo de método de pago'
    )

    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre',
        help_text='Nombre descriptivo del método'
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción del método de pago'
    )

    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='¿El método está habilitado?'
    )

    requiere_verificacion = models.BooleanField(
        default=False,
        verbose_name='Requiere Verificación',
        help_text='¿Requiere verificación manual? (ej: transferencias)'
    )

    permite_reembolso = models.BooleanField(
        default=True,
        verbose_name='Permite Reembolso',
        help_text='¿Se pueden hacer reembolsos con este método?'
    )

    # Configuración para pasarelas externas
    pasarela_nombre = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Nombre de Pasarela',
        help_text='Nombre de la pasarela externa (Stripe, Kushki, etc.)'
    )

    pasarela_api_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='API Key',
        help_text='Clave API de la pasarela (encriptada)'
    )

    pasarela_configuracion = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Configuración Pasarela',
        help_text='Configuración adicional en JSON'
    )

    # Auditoría
    creado_en = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Creación'
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    class Meta:
        db_table = 'pagos_metodo_pago'
        ordering = ['tipo']
        verbose_name = 'Método de Pago'
        verbose_name_plural = 'Métodos de Pago'

    def __str__(self):
        return f"{self.nombre} {'✓' if self.activo else '✗'}"

    def __repr__(self):
        return f"<MetodoPago tipo={self.tipo} activo={self.activo}>"

    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        # Validar que pasarelas tengan configuración
        if self.pasarela_nombre and not self.pasarela_api_key:
            raise ValidationError({
                'pasarela_api_key': 'Debe proporcionar API Key para la pasarela'
            })


# ==========================================================
# 💰 MODELO PRINCIPAL: PAGO
# ==========================================================

class Pago(models.Model):
    """
    Modelo principal de Pago

    Representa un pago asociado a un pedido
    """
    # Identificador único
    referencia = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name='Referencia',
        help_text='Identificador único del pago',
        db_index=True
    )

    # Relaciones
    pedido = models.OneToOneField(
        'pedidos.Pedido',
        on_delete=models.PROTECT,
        related_name='pago',
        verbose_name='Pedido',
        help_text='Pedido asociado al pago'
    )

    metodo_pago = models.ForeignKey(
        MetodoPago,
        on_delete=models.PROTECT,
        related_name='pagos',
        verbose_name='Método de Pago'
    )

    # Montos
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto',
        help_text='Monto total del pago'
    )

    monto_reembolsado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Monto Reembolsado',
        help_text='Monto que ha sido reembolsado'
    )

    # Estado
    estado = models.CharField(
        max_length=20,
        choices=EstadoPago.choices,
        default=EstadoPago.PENDIENTE,
        verbose_name='Estado',
        help_text='Estado actual del pago',
        db_index=True
    )

    # Información de tarjeta (últimos 4 dígitos)
    tarjeta_ultimos_digitos = models.CharField(
        max_length=4,
        blank=True,
        verbose_name='Últimos 4 Dígitos',
        help_text='Últimos 4 dígitos de la tarjeta'
    )

    tarjeta_marca = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Marca de Tarjeta',
        help_text='Visa, Mastercard, etc.'
    )

    # Información de transferencia
    transferencia_comprobante = models.FileField(
        upload_to='pagos/comprobantes/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Comprobante',
        help_text='Comprobante de transferencia bancaria'
    )

    transferencia_numero_operacion = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Número de Operación',
        help_text='Número de operación de la transferencia'
    )

    transferencia_banco = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Banco Origen',
        help_text='Banco desde donde se realizó la transferencia'
    )

    # Referencias externas (pasarelas)
    pasarela_id_transaccion = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='ID Transacción Pasarela',
        help_text='ID de transacción de la pasarela externa',
        db_index=True
    )

    pasarela_respuesta = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Respuesta Pasarela',
        help_text='Respuesta completa de la pasarela en JSON'
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadata',
        help_text='Información adicional en JSON'
    )

    notas = models.TextField(
        blank=True,
        verbose_name='Notas',
        help_text='Notas internas sobre el pago'
    )

    # Fechas
    creado_en = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Creación',
        db_index=True
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    fecha_completado = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Completado',
        help_text='Fecha en que se completó el pago'
    )

    fecha_reembolso = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Reembolso',
        help_text='Fecha del último reembolso'
    )

    # Verificación manual
    verificado_por = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagos_verificados',
        verbose_name='Verificado Por',
        help_text='Usuario admin que verificó el pago'
    )

    fecha_verificacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Verificación'
    )

    # Manager
    objects = PagoManager()

    class Meta:
        db_table = 'pagos'
        ordering = ['-creado_en']
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

        indexes = [
            models.Index(fields=['-creado_en']),
            models.Index(fields=['estado']),
            models.Index(fields=['metodo_pago']),
            models.Index(fields=['referencia']),
            models.Index(fields=['pasarela_id_transaccion']),
            models.Index(fields=['estado', 'creado_en']),
        ]

        constraints = [
            # Monto debe ser positivo
            models.CheckConstraint(
                check=Q(monto__gt=0),
                name='pago_monto_positivo'
            ),
            # Reembolso no puede ser mayor que el monto
            models.CheckConstraint(
                check=Q(monto_reembolsado__lte=models.F('monto')),
                name='pago_reembolso_valido'
            ),
        ]

    def __str__(self):
        return (
            f"Pago #{self.pk} - {self.metodo_pago.nombre} "
            f"${self.monto} ({self.get_estado_display()})"
        )

    def __repr__(self):
        return (
            f"<Pago id={self.pk} referencia={self.referencia} "
            f"estado={self.estado} monto={self.monto}>"
        )

    # ==========================================================
    # ✅ VALIDACIONES
    # ==========================================================

    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        errors = {}

        # Validar monto
        if self.monto <= 0:
            errors['monto'] = 'El monto debe ser mayor a 0'

        # Validar que monto coincida con el pedido
        if self.pedido and abs(float(self.monto) - float(self.pedido.total)) > 0.01:
            errors['monto'] = (
                f'El monto del pago (${self.monto}) no coincide con '
                f'el total del pedido (${self.pedido.total})'
            )

        # Validar transferencia
        if self.metodo_pago and self.metodo_pago.tipo == TipoMetodoPago.TRANSFERENCIA:
            if self.estado == EstadoPago.COMPLETADO and not self.verificado_por:
                errors['verificado_por'] = (
                    'Las transferencias deben ser verificadas por un administrador'
                )

        # Validar reembolso
        if self.monto_reembolsado > self.monto:
            errors['monto_reembolsado'] = (
                'El monto reembolsado no puede ser mayor al monto del pago'
            )

        if errors:
            raise ValidationError(errors)

    # ==========================================================
    # 🔄 TRANSICIONES DE ESTADO
    # ==========================================================

    def marcar_procesando(self):
        """Marca el pago como procesando"""
        if self.estado != EstadoPago.PENDIENTE:
            raise ValidationError(
                f"No se puede procesar un pago en estado '{self.get_estado_display()}'"
            )

        self.estado = EstadoPago.PROCESANDO
        self.save(update_fields=['estado', 'actualizado_en'])

        logger.info(f"✅ Pago {self.referencia} marcado como PROCESANDO")

        # Crear transacción
        self._crear_transaccion(
            tipo=TipoTransaccion.PAGO,
            monto=self.monto,
            exitosa=None,  # Aún en proceso
            descripcion='Pago en proceso'
        )

    def marcar_completado(self, verificado_por=None, pasarela_respuesta=None):
        """
        Marca el pago como completado

        Args:
            verificado_por (User): Usuario que verificó (para transferencias)
            pasarela_respuesta (dict): Respuesta de la pasarela externa
        """
        if self.estado in [EstadoPago.COMPLETADO, EstadoPago.REEMBOLSADO]:
            raise ValidationError(
                f"El pago ya está en estado '{self.get_estado_display()}'"
            )

        self.estado = EstadoPago.COMPLETADO
        self.fecha_completado = timezone.now()

        if verificado_por:
            self.verificado_por = verificado_por
            self.fecha_verificacion = timezone.now()

        if pasarela_respuesta:
            self.pasarela_respuesta = pasarela_respuesta

        self.save(update_fields=[
            'estado',
            'fecha_completado',
            'verificado_por',
            'fecha_verificacion',
            'pasarela_respuesta',
            'actualizado_en'
        ])

        logger.info(
            f"✅ Pago {self.referencia} completado. "
            f"Monto: ${self.monto}, Método: {self.metodo_pago.tipo}"
        )

        # Crear transacción exitosa
        self._crear_transaccion(
            tipo=TipoTransaccion.PAGO,
            monto=self.monto,
            exitosa=True,
            descripcion='Pago completado exitosamente'
        )

        # Notificar (se hace en signal)

    def marcar_fallido(self, motivo, pasarela_respuesta=None):
        """
        Marca el pago como fallido

        Args:
            motivo (str): Razón del fallo
            pasarela_respuesta (dict): Respuesta de error de la pasarela
        """
        if self.estado == EstadoPago.COMPLETADO:
            raise ValidationError("No se puede marcar como fallido un pago completado")

        self.estado = EstadoPago.FALLIDO
        self.notas = f"{self.notas}\n\nFallo: {motivo}".strip()

        if pasarela_respuesta:
            self.pasarela_respuesta = pasarela_respuesta

        self.save(update_fields=[
            'estado',
            'notas',
            'pasarela_respuesta',
            'actualizado_en'
        ])

        logger.warning(
            f"❌ Pago {self.referencia} falló. Motivo: {motivo}"
        )

        # Crear transacción fallida
        self._crear_transaccion(
            tipo=TipoTransaccion.PAGO,
            monto=self.monto,
            exitosa=False,
            descripcion=f'Pago fallido: {motivo}'
        )

        # Notificar (se hace en signal)

    def marcar_cancelado(self, motivo):
        """
        Cancela el pago

        Args:
            motivo (str): Razón de la cancelación
        """
        if self.estado in [EstadoPago.COMPLETADO, EstadoPago.REEMBOLSADO]:
            raise ValidationError(
                f"No se puede cancelar un pago en estado '{self.get_estado_display()}'"
            )

        self.estado = EstadoPago.CANCELADO
        self.notas = f"{self.notas}\n\nCancelado: {motivo}".strip()

        self.save(update_fields=['estado', 'notas', 'actualizado_en'])

        logger.info(f"🚫 Pago {self.referencia} cancelado. Motivo: {motivo}")

    def procesar_reembolso(self, monto=None, motivo=''):
        """
        Procesa un reembolso total o parcial

        Args:
            monto (Decimal): Monto a reembolsar (None = total)
            motivo (str): Razón del reembolso

        Raises:
            ValidationError: Si el reembolso no es válido
        """
        # Validaciones
        if self.estado != EstadoPago.COMPLETADO:
            raise ValidationError(
                "Solo se pueden reembolsar pagos completados"
            )

        if not self.metodo_pago.permite_reembolso:
            raise ValidationError(
                f"El método '{self.metodo_pago.nombre}' no permite reembolsos"
            )

        # Determinar monto a reembolsar
        if monto is None:
            monto = self.monto - self.monto_reembolsado
        else:
            monto = Decimal(str(monto))

        # Validar monto
        monto_disponible = self.monto - self.monto_reembolsado
        if monto > monto_disponible:
            raise ValidationError(
                f"No se puede reembolsar ${monto}. "
                f"Disponible: ${monto_disponible}"
            )

        if monto <= 0:
            raise ValidationError("El monto del reembolso debe ser mayor a 0")

        # Procesar reembolso
        self.monto_reembolsado += monto
        self.fecha_reembolso = timezone.now()

        # Si es reembolso total, cambiar estado
        if self.monto_reembolsado >= self.monto:
            self.estado = EstadoPago.REEMBOLSADO

        self.notas = f"{self.notas}\n\nReembolso: ${monto} - {motivo}".strip()

        self.save(update_fields=[
            'monto_reembolsado',
            'fecha_reembolso',
            'estado',
            'notas',
            'actualizado_en'
        ])

        logger.info(
            f"💰 Reembolso procesado - Pago {self.referencia}: "
            f"${monto} (Total reembolsado: ${self.monto_reembolsado})"
        )

        # Crear transacción de reembolso
        self._crear_transaccion(
            tipo=TipoTransaccion.REEMBOLSO,
            monto=monto,
            exitosa=True,
            descripcion=f'Reembolso: {motivo}'
        )

        return monto

    # ==========================================================
    # 🔧 MÉTODOS AUXILIARES
    # ==========================================================

    def _crear_transaccion(self, tipo, monto, exitosa, descripcion=''):
        """
        Crea un registro de transacción

        Args:
            tipo (str): Tipo de transacción
            monto (Decimal): Monto
            exitosa (bool): Si fue exitosa (None = en proceso)
            descripcion (str): Descripción
        """
        try:
            Transaccion.objects.create(
                pago=self,
                tipo=tipo,
                monto=monto,
                exitosa=exitosa,
                descripcion=descripcion,
                metadata={
                    'estado_pago': self.estado,
                    'metodo': self.metodo_pago.tipo
                }
            )
        except Exception as e:
            logger.error(f"Error al crear transacción: {e}")

    # ==========================================================
    # 📊 PROPIEDADES
    # ==========================================================

    @property
    def monto_pendiente_reembolso(self):
        """Monto disponible para reembolso"""
        return self.monto - self.monto_reembolsado

    @property
    def fue_reembolsado_parcialmente(self):
        """Verifica si hubo reembolso parcial"""
        return self.monto_reembolsado > 0 and self.monto_reembolsado < self.monto

    @property
    def fue_reembolsado_totalmente(self):
        """Verifica si fue reembolsado totalmente"""
        return self.monto_reembolsado >= self.monto

    @property
    def requiere_verificacion_manual(self):
        """Verifica si requiere verificación manual"""
        return (
            self.metodo_pago.requiere_verificacion and
            self.estado == EstadoPago.PENDIENTE
        )

    @property
    def es_tarjeta(self):
        """Verifica si es pago con tarjeta"""
        return self.metodo_pago.tipo in [
            TipoMetodoPago.TARJETA_CREDITO,
            TipoMetodoPago.TARJETA_DEBITO
        ]

    @property
    def es_efectivo(self):
        """Verifica si es pago en efectivo"""
        return self.metodo_pago.tipo == TipoMetodoPago.EFECTIVO

    @property
    def es_transferencia(self):
        """Verifica si es transferencia"""
        return self.metodo_pago.tipo == TipoMetodoPago.TRANSFERENCIA

    @property
    def tiempo_desde_creacion(self):
        """Tiempo transcurrido desde la creación"""
        diff = timezone.now() - self.creado_en
        minutos = int(diff.total_seconds() // 60)

        if minutos < 1:
            return "Hace un momento"
        elif minutos < 60:
            return f"{minutos} min"
        elif minutos < 1440:
            horas = minutos // 60
            return f"{horas} hora{'s' if horas != 1 else ''}"
        else:
            dias = minutos // 1440
            return f"{dias} día{'s' if dias != 1 else ''}"

    def obtener_resumen(self):
        """Genera resumen completo del pago"""
        return {
            'referencia': str(self.referencia),
            'pedido_id': self.pedido_id,
            'metodo': self.metodo_pago.nombre,
            'monto': f"${self.monto}",
            'estado': self.get_estado_display(),
            'reembolsado': f"${self.monto_reembolsado}",
            'pendiente_reembolso': f"${self.monto_pendiente_reembolso}",
            'creado_en': self.creado_en.strftime('%Y-%m-%d %H:%M:%S'),
            'completado_en': self.fecha_completado.strftime('%Y-%m-%d %H:%M:%S') if self.fecha_completado else None,
        }


# ==========================================================
# 📝 MODELO: TRANSACCIÓN
# ==========================================================

class Transaccion(models.Model):
    """
    Historial de transacciones de un pago

    Registra todos los intentos y eventos de un pago
    """
    pago = models.ForeignKey(
        Pago,
        on_delete=models.CASCADE,
        related_name='transacciones',
        verbose_name='Pago'
    )

    tipo = models.CharField(
        max_length=20,
        choices=TipoTransaccion.choices,
        verbose_name='Tipo',
        help_text='Tipo de transacción'
    )

    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Monto'
    )

    exitosa = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='Exitosa',
        help_text='Si fue exitosa (null = en proceso)'
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )

    codigo_respuesta = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Código de Respuesta',
        help_text='Código de respuesta de la pasarela'
    )

    mensaje_respuesta = models.TextField(
        blank=True,
        verbose_name='Mensaje de Respuesta',
        help_text='Mensaje detallado de la pasarela'
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadata',
        help_text='Información adicional de la transacción'
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP',
        help_text='IP desde donde se realizó la transacción'
    )

    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent',
        help_text='Información del navegador/dispositivo'
    )

    creado_en = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha',
        db_index=True
    )

    class Meta:
        db_table = 'pagos_transacciones'
        ordering = ['-creado_en']
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'

        indexes = [
            models.Index(fields=['pago', '-creado_en']),
            models.Index(fields=['tipo']),
            models.Index(fields=['exitosa']),
        ]

    def __str__(self):
        estado = '✓' if self.exitosa else ('✗' if self.exitosa is False else '⏳')
        return (
            f"{estado} {self.get_tipo_display()} - "
            f"${self.monto} ({self.creado_en.strftime('%H:%M:%S')})"
        )

    def __repr__(self):
        return (
            f"<Transaccion pago_id={self.pago_id} tipo={self.tipo} "
            f"monto={self.monto} exitosa={self.exitosa}>"
        )


# ==========================================================
# 📊 MODELO: ESTADÍSTICAS DE PAGOS
# ==========================================================

class EstadisticasPago(models.Model):
    """
    Modelo para cachear estadísticas diarias de pagos

    Mejora el performance de reportes y dashboards
    """
    fecha = models.DateField(
        unique=True,
        verbose_name='Fecha',
        db_index=True
    )

    # Contadores
    total_pagos = models.IntegerField(
        default=0,
        verbose_name='Total de Pagos'
    )

    pagos_completados = models.IntegerField(
        default=0,
        verbose_name='Pagos Completados'
    )

    pagos_pendientes = models.IntegerField(
        default=0,
        verbose_name='Pagos Pendientes'
    )

    pagos_fallidos = models.IntegerField(
        default=0,
        verbose_name='Pagos Fallidos'
    )

    pagos_reembolsados = models.IntegerField(
        default=0,
        verbose_name='Pagos Reembolsados'
    )

    # Montos por método
    monto_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Monto Total'
    )

    monto_efectivo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Monto Efectivo'
    )

    monto_transferencias = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Monto Transferencias'
    )

    monto_tarjetas = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Monto Tarjetas'
    )

    monto_reembolsado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Monto Reembolsado'
    )

    # Métricas
    ticket_promedio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Ticket Promedio'
    )

    tasa_exito = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Tasa de Éxito (%)',
        help_text='Porcentaje de pagos exitosos'
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    class Meta:
        db_table = 'pagos_estadisticas'
        ordering = ['-fecha']
        verbose_name = 'Estadística de Pagos'
        verbose_name_plural = 'Estadísticas de Pagos'

    def __str__(self):
        return f"Estadísticas {self.fecha}"

    @classmethod
    def calcular_y_guardar(cls, fecha=None):
        """
        Calcula y guarda estadísticas para una fecha

        Args:
            fecha (date): Fecha a calcular (hoy por defecto)

        Returns:
            EstadisticasPago: Instancia creada/actualizada
        """
        if fecha is None:
            fecha = timezone.now().date()

        # Obtener pagos del día
        pagos_dia = Pago.objects.filter(creado_en__date=fecha)

        # Calcular estadísticas
        stats = pagos_dia.aggregate(
            total_pagos=Count('id'),
            pagos_completados=Count('id', filter=Q(estado=EstadoPago.COMPLETADO)),
            pagos_pendientes=Count('id', filter=Q(estado=EstadoPago.PENDIENTE)),
            pagos_fallidos=Count('id', filter=Q(estado=EstadoPago.FALLIDO)),
            pagos_reembolsados=Count('id', filter=Q(estado=EstadoPago.REEMBOLSADO)),
            monto_total=Sum('monto', filter=Q(estado=EstadoPago.COMPLETADO)),
            monto_efectivo=Sum('monto', filter=Q(
                estado=EstadoPago.COMPLETADO,
                metodo_pago__tipo=TipoMetodoPago.EFECTIVO
            )),
            monto_transferencias=Sum('monto', filter=Q(
                estado=EstadoPago.COMPLETADO,
                metodo_pago__tipo=TipoMetodoPago.TRANSFERENCIA
            )),
            monto_tarjetas=Sum('monto', filter=Q(
                estado=EstadoPago.COMPLETADO,
                metodo_pago__tipo__in=[
                    TipoMetodoPago.TARJETA_CREDITO,
                    TipoMetodoPago.TARJETA_DEBITO
                ]
            )),
            monto_reembolsado=Sum('monto_reembolsado')
        )

        # Calcular ticket promedio
        if stats['pagos_completados'] and stats['monto_total']:
            ticket_promedio = stats['monto_total'] / stats['pagos_completados']
        else:
            ticket_promedio = Decimal('0.00')

        # Calcular tasa de éxito
        if stats['total_pagos'] > 0:
            tasa_exito = (stats['pagos_completados'] / stats['total_pagos']) * 100
        else:
            tasa_exito = Decimal('0.00')

        # Crear o actualizar estadística
        estadistica, created = cls.objects.update_or_create(
            fecha=fecha,
            defaults={
                'total_pagos': stats['total_pagos'] or 0,
                'pagos_completados': stats['pagos_completados'] or 0,
                'pagos_pendientes': stats['pagos_pendientes'] or 0,
                'pagos_fallidos': stats['pagos_fallidos'] or 0,
                'pagos_reembolsados': stats['pagos_reembolsados'] or 0,
                'monto_total': stats['monto_total'] or Decimal('0.00'),
                'monto_efectivo': stats['monto_efectivo'] or Decimal('0.00'),
                'monto_transferencias': stats['monto_transferencias'] or Decimal('0.00'),
                'monto_tarjetas': stats['monto_tarjetas'] or Decimal('0.00'),
                'monto_reembolsado': stats['monto_reembolsado'] or Decimal('0.00'),
                'ticket_promedio': ticket_promedio,
                'tasa_exito': tasa_exito,
            }
        )

        logger.info(
            f"{'✅ Estadísticas creadas' if created else '🔄 Estadísticas actualizadas'} "
            f"para {fecha}: {stats['total_pagos']} pagos, ${stats['monto_total'] or 0}"
        )

        return estadistica
