# repartidores/models.py
from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

# Ajusta este import a tu proyecto real
from authentication.models import User


# ==============================
# Enums (TextChoices)
# ==============================
class EstadoRepartidor(models.TextChoices):
    DISPONIBLE = 'disponible', 'Disponible'
    OCUPADO = 'ocupado', 'Ocupado'
    FUERA_SERVICIO = 'fuera_servicio', 'Fuera de Servicio'


class TipoVehiculo(models.TextChoices):
    MOTOCICLETA = 'motocicleta', 'Motocicleta'
    BICICLETA = 'bicicleta', 'Bicicleta'
    AUTOMOVIL = 'automovil', 'Automóvil'
    CAMIONETA = 'camioneta', 'Camioneta'
    OTRO = 'otro', 'Otro'


# ==============================
# Base con timestamps
# ==============================
class TimeStampedModel(models.Model):
    creado_en = models.DateTimeField(default=timezone.now, editable=False)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ==============================
# Repartidor
# ==============================
class Repartidor(TimeStampedModel):
    """
    Perfil del repartidor:
    - Estado laboral y verificación
    - Ubicación actual (última conocida)
    - Métricas (entregas, calificación)
    - Integridad fuerte (constraints) y rendimiento (índices)
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='repartidor')

    # Identidad y medios
    foto_perfil = models.ImageField(upload_to='repartidores/perfil/', blank=True, null=True)
    cedula = models.CharField(max_length=10, unique=True)
    telefono = models.CharField(max_length=15)

    # Estado laboral
    estado = models.CharField(max_length=20, choices=EstadoRepartidor.choices,
                              default=EstadoRepartidor.FUERA_SERVICIO)
    verificado = models.BooleanField(default=False, help_text="Aprobado por un administrador.")
    activo = models.BooleanField(default=True, help_text="Soft-disable sin borrar datos.")

    # Ubicación (última)
    latitud = models.FloatField(blank=True, null=True)
    longitud = models.FloatField(blank=True, null=True)
    ultima_localizacion = models.DateTimeField(blank=True, null=True)

    # Métricas
    entregas_completadas = models.PositiveIntegerField(default=0)
    calificacion_promedio = models.DecimalField(
        max_digits=3, decimal_places=2, default=5.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )

    class Meta:
        db_table = 'repartidores'
        verbose_name = 'Repartidor'
        verbose_name_plural = 'Repartidores'
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['verificado']),
            models.Index(fields=['activo']),
            models.Index(fields=['ultima_localizacion']),
            models.Index(fields=['user']),
        ]
        constraints = [
            # Si no está verificado, solo puede estar 'fuera_servicio'
            models.CheckConstraint(
                name='rep_estado_req_verificado',
                check=Q(estado=EstadoRepartidor.FUERA_SERVICIO) | Q(verificado=True),
            ),
            # Rango Ecuador (si se informan coords)
            models.CheckConstraint(
                name='rep_lat_ec',
                check=Q(latitud__isnull=True) | (Q(latitud__gte=-5.0) & Q(latitud__lte=2.0)),
            ),
            models.CheckConstraint(
                name='rep_lon_ec',
                check=Q(longitud__isnull=True) | (Q(longitud__gte=-92.0) & Q(longitud__lte=-75.0)),
            ),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email} · {self.estado}"

    # ---------- Validación adicional
    def _validar_puede_cambiar_estado(self, nuevo_estado):
        """Valida si el repartidor puede cambiar a un nuevo estado."""
        if not self.activo:
            raise ValidationError("No puedes cambiar de estado: tu cuenta está desactivada.")

        if nuevo_estado in (EstadoRepartidor.DISPONIBLE, EstadoRepartidor.OCUPADO):
            if not self.verificado:
                raise ValidationError("No puedes cambiar a ese estado: no estás verificado.")

    # ---------- Estados (métodos de dominio)
    def marcar_disponible(self):
        """Marca al repartidor como disponible para recibir pedidos."""
        self._validar_puede_cambiar_estado(EstadoRepartidor.DISPONIBLE)
        anterior = self.estado
        self.estado = EstadoRepartidor.DISPONIBLE
        self.save(update_fields=['estado', 'actualizado_en'])
        RepartidorEstadoLog.log(self, antes=anterior, despues=self.estado, motivo="manual/auto")

    def marcar_ocupado(self):
        """Marca al repartidor como ocupado (tiene un pedido asignado)."""
        self._validar_puede_cambiar_estado(EstadoRepartidor.OCUPADO)
        anterior = self.estado
        self.estado = EstadoRepartidor.OCUPADO
        self.save(update_fields=['estado', 'actualizado_en'])
        RepartidorEstadoLog.log(self, antes=anterior, despues=self.estado, motivo="pedido asignado/aceptado")

    def marcar_fuera_servicio(self, motivo="manual/timeout"):
        """Marca al repartidor como fuera de servicio."""
        anterior = self.estado
        self.estado = EstadoRepartidor.FUERA_SERVICIO
        self.save(update_fields=['estado', 'actualizado_en'])
        RepartidorEstadoLog.log(self, antes=anterior, despues=self.estado, motivo=motivo)

    # ---------- Ubicación
    def actualizar_ubicacion(self, lat, lon, when=None, save_historial=True):
        """
        Actualiza la ubicación del repartidor.
        Solo repartidores activos y verificados pueden actualizar ubicación.
        """
        if not self.activo:
            raise ValidationError("No puedes actualizar ubicación: tu cuenta está desactivada.")

        if not self.verificado:
            raise ValidationError("No puedes actualizar ubicación: no estás verificado.")

        # Validar rangos de Ecuador
        if not (-5.0 <= lat <= 2.0):
            raise ValidationError(f"Latitud fuera del rango de Ecuador: {lat}")

        if not (-92.0 <= lon <= -75.0):
            raise ValidationError(f"Longitud fuera del rango de Ecuador: {lon}")

        self.latitud = float(lat)
        self.longitud = float(lon)
        self.ultima_localizacion = when or timezone.now()
        self.save(update_fields=['latitud', 'longitud', 'ultima_localizacion', 'actualizado_en'])

        if save_historial:
            HistorialUbicacion.objects.create(
                repartidor=self,
                latitud=self.latitud,
                longitud=self.longitud,
                timestamp=self.ultima_localizacion,
            )

    # ---------- Métricas
    def incrementar_entregas(self, unidades=1):
        """Incrementa el contador de entregas completadas de forma atómica."""
        if unidades <= 0:
            raise ValueError("Las unidades deben ser mayores a 0.")

        Repartidor.objects.filter(pk=self.pk).update(
            entregas_completadas=F('entregas_completadas') + unidades,
            actualizado_en=timezone.now()
        )
        self.refresh_from_db(fields=['entregas_completadas'])

    def recalcular_calificacion_promedio(self):
        """Recalcula el promedio de calificaciones recibidas."""
        agg = self.calificaciones.aggregate(avg=models.Avg('puntuacion'))
        promedio = round(float(agg['avg'] or 5.0), 2)
        self.calificacion_promedio = promedio
        self.save(update_fields=['calificacion_promedio', 'actualizado_en'])


# ==============================
# Vehículos (múltiples por repartidor)
# ==============================
class RepartidorVehiculo(TimeStampedModel):
    repartidor = models.ForeignKey(Repartidor, on_delete=models.CASCADE, related_name='vehiculos')
    tipo = models.CharField(max_length=20, choices=TipoVehiculo.choices)
    placa = models.CharField(max_length=15, blank=True, null=True)
    licencia_foto = models.ImageField(upload_to='repartidores/licencias/', blank=True, null=True)
    activo = models.BooleanField(default=True, help_text="Debe existir solo un vehículo activo por repartidor.")

    class Meta:
        db_table = 'repartidores_vehiculos'
        verbose_name = 'Vehículo de Repartidor'
        verbose_name_plural = 'Vehículos de Repartidor'
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['repartidor']),
            models.Index(fields=['tipo']),
            models.Index(fields=['activo']),
        ]
        constraints = [
            # Placa única por repartidor (cuando no es nula)
            models.UniqueConstraint(
                fields=['repartidor', 'placa'],
                condition=Q(placa__isnull=False),
                name='unique_placa_por_repartidor'
            ),
        ]

    def __str__(self):
        estado = 'Activo' if self.activo else 'Inactivo'
        return f"{self.repartidor_id} · {self.tipo} · {self.placa or '-'} · {estado}"


# ==============================
# Historial de ubicaciones
# ==============================
class HistorialUbicacion(models.Model):
    repartidor = models.ForeignKey(Repartidor, on_delete=models.CASCADE, related_name='historial_ubicaciones')
    latitud = models.FloatField()
    longitud = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'repartidores_historial_ubicacion'
        verbose_name = 'Historial de Ubicación'
        verbose_name_plural = 'Historial de Ubicaciones'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['repartidor', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        constraints = [
            models.CheckConstraint(
                name='hist_lat_ec',
                check=Q(latitud__gte=-5.0) & Q(latitud__lte=2.0),
            ),
            models.CheckConstraint(
                name='hist_lon_ec',
                check=Q(longitud__gte=-92.0) & Q(longitud__lte=-75.0),
            ),
        ]

    def __str__(self):
        return f"{self.repartidor_id} @ {self.timestamp:%Y-%m-%d %H:%M:%S}"


# ==============================
# Log de cambios de estado (auditoría)
# ==============================
class RepartidorEstadoLog(models.Model):
    repartidor = models.ForeignKey(Repartidor, on_delete=models.CASCADE, related_name='logs_estado')
    estado_anterior = models.CharField(max_length=20, choices=EstadoRepartidor.choices)
    estado_nuevo = models.CharField(max_length=20, choices=EstadoRepartidor.choices)
    motivo = models.CharField(max_length=120, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'repartidores_estado_log'
        verbose_name = 'Log de Estado de Repartidor'
        verbose_name_plural = 'Logs de Estado de Repartidor'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['repartidor', 'timestamp']),
            models.Index(fields=['estado_nuevo']),
        ]

    def __str__(self):
        return f"{self.repartidor_id}: {self.estado_anterior} → {self.estado_nuevo} @ {self.timestamp:%H:%M:%S}"

    @classmethod
    def log(cls, repartidor, antes, despues, motivo=""):
        """Crea un registro de auditoría del cambio de estado."""
        cls.objects.create(
            repartidor=repartidor,
            estado_anterior=antes,
            estado_nuevo=despues,
            motivo=motivo or None,
        )


# ==============================
# Calificaciones (mutuas) – por pedido
# ==============================
class CalificacionRepartidor(TimeStampedModel):
    """ Calificación del CLIENTE hacia el REPARTIDOR (1 por pedido). """
    repartidor = models.ForeignKey(Repartidor, on_delete=models.CASCADE, related_name='calificaciones')
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calificaciones_a_repartidores')
    pedido_id = models.CharField(max_length=100)
    puntuacion = models.DecimalField(max_digits=2, decimal_places=1,
                                     validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'repartidores_calificaciones'
        verbose_name = 'Calificación a Repartidor'
        verbose_name_plural = 'Calificaciones a Repartidores'
        ordering = ['-creado_en']
        constraints = [
            models.UniqueConstraint(
                fields=['repartidor', 'cliente', 'pedido_id'],
                name='unique_calif_cliente_repartidor_por_pedido'
            ),
            models.CheckConstraint(
                name='calif_rep_rango',
                check=Q(puntuacion__gte=1) & Q(puntuacion__lte=5),
            ),
        ]
        indexes = [
            models.Index(fields=['repartidor']),
            models.Index(fields=['cliente']),
            models.Index(fields=['pedido_id']),
        ]

    def __str__(self):
        return f"{self.repartidor_id}/{self.pedido_id} → {self.puntuacion}"

    def save(self, *args, **kwargs):
        """Al guardar, recalcula automáticamente el promedio del repartidor."""
        super().save(*args, **kwargs)
        self.repartidor.recalcular_calificacion_promedio()


class CalificacionCliente(TimeStampedModel):
    """ Calificación del REPARTIDOR hacia el CLIENTE (1 por pedido). """
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calificaciones_de_repartidores')
    repartidor = models.ForeignKey(Repartidor, on_delete=models.CASCADE, related_name='calificaciones_a_clientes')
    pedido_id = models.CharField(max_length=100)
    puntuacion = models.DecimalField(max_digits=2, decimal_places=1,
                                     validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'clientes_calificaciones'
        verbose_name = 'Calificación a Cliente'
        verbose_name_plural = 'Calificaciones a Clientes'
        ordering = ['-creado_en']
        constraints = [
            models.UniqueConstraint(
                fields=['cliente', 'repartidor', 'pedido_id'],
                name='unique_calif_repartidor_cliente_por_pedido'
            ),
            models.CheckConstraint(
                name='calif_cli_rango',
                check=Q(puntuacion__gte=1) & Q(puntuacion__lte=5),
            ),
        ]
        indexes = [
            models.Index(fields=['cliente']),
            models.Index(fields=['repartidor']),
            models.Index(fields=['pedido_id']),
        ]

    def __str__(self):
        return f"{self.cliente_id}/{self.pedido_id} ← {self.puntuacion}"
