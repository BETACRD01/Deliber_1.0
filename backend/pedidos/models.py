# pedidos/models.py (CORREGIDO Y OPTIMIZADO)
"""
Modelo de Pedidos con validaciones robustas y métodos optimizados.

✅ CORRECCIONES APLICADAS:
- Validaciones mejoradas con mensajes descriptivos
- Métodos optimizados para evitar N+1 queries
- Propiedades cacheadas para performance
- Managers personalizados con querysets útiles
- Documentación completa
- Logging mejorado
"""
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q, F, Count, Sum
from django.utils.functional import cached_property
from usuarios.models import Perfil
from repartidores.models import Repartidor, EstadoRepartidor
from proveedores.models import Proveedor
import logging

logger = logging.getLogger('pedidos')


# ==========================================================
# 📋 ENUMS Y CHOICES
# ==========================================================

class TipoPedido(models.TextChoices):
    """Tipos de pedido disponibles"""
    PROVEEDOR = 'proveedor', 'Pedido de Proveedor'
    DIRECTO = 'directo', 'Encargo Directo'


class EstadoPedido(models.TextChoices):
    """Estados del ciclo de vida de un pedido"""
    CONFIRMADO = 'confirmado', 'Confirmado'
    EN_PREPARACION = 'en_preparacion', 'En preparación'
    EN_RUTA = 'en_ruta', 'En ruta'
    ENTREGADO = 'entregado', 'Entregado'
    CANCELADO = 'cancelado', 'Cancelado'


# ==========================================================
# 🔧 MANAGER PERSONALIZADO
# ==========================================================

class PedidoManager(models.Manager):
    """
    ✅ NUEVO: Manager personalizado con querysets optimizados
    """

    def get_queryset(self):
        """Queryset base optimizado con select_related"""
        return super().get_queryset().select_related(
            'cliente__user',
            'proveedor',
            'repartidor__user'
        )

    def activos(self):
        """Retorna pedidos en estados activos"""
        return self.filter(
            estado__in=[
                EstadoPedido.CONFIRMADO,
                EstadoPedido.EN_PREPARACION,
                EstadoPedido.EN_RUTA
            ]
        )

    def disponibles_para_repartidores(self):
        """Pedidos confirmados sin repartidor asignado"""
        return self.filter(
            estado=EstadoPedido.CONFIRMADO,
            repartidor__isnull=True
        )

    def entregados(self):
        """Pedidos completados"""
        return self.filter(estado=EstadoPedido.ENTREGADO)

    def cancelados(self):
        """Pedidos cancelados"""
        return self.filter(estado=EstadoPedido.CANCELADO)

    def del_dia(self):
        """Pedidos creados hoy"""
        hoy = timezone.now().date()
        return self.filter(creado_en__date=hoy)

    def por_proveedor(self, proveedor_id):
        """Pedidos de un proveedor específico"""
        return self.filter(proveedor_id=proveedor_id)

    def por_repartidor(self, repartidor_id):
        """Pedidos de un repartidor específico"""
        return self.filter(repartidor_id=repartidor_id)

    def por_cliente(self, cliente_id):
        """Pedidos de un cliente específico"""
        return self.filter(cliente_id=cliente_id)

    def con_retraso(self, minutos=60):
        """
        ✅ NUEVO: Pedidos en ruta con retraso

        Args:
            minutos (int): Minutos de tolerancia antes de considerar retraso
        """
        from datetime import timedelta
        tiempo_limite = timezone.now() - timedelta(minutes=minutos)

        return self.filter(
            estado=EstadoPedido.EN_RUTA,
            actualizado_en__lt=tiempo_limite
        )

    def estadisticas_del_dia(self):
        """
        ✅ NUEVO: Estadísticas agregadas del día

        Returns:
            dict: Estadísticas completas
        """
        hoy = timezone.now().date()
        pedidos_hoy = self.filter(creado_en__date=hoy)

        return pedidos_hoy.aggregate(
            total_pedidos=Count('id'),
            pedidos_entregados=Count('id', filter=Q(estado=EstadoPedido.ENTREGADO)),
            pedidos_cancelados=Count('id', filter=Q(estado=EstadoPedido.CANCELADO)),
            pedidos_activos=Count('id', filter=Q(
                estado__in=[EstadoPedido.CONFIRMADO, EstadoPedido.EN_PREPARACION, EstadoPedido.EN_RUTA]
            )),
            ingresos_totales=Sum('total', filter=Q(estado=EstadoPedido.ENTREGADO)),
            ganancia_app=Sum('ganancia_app', filter=Q(estado=EstadoPedido.ENTREGADO))
        )


# ==========================================================
# 📦 MODELO PRINCIPAL
# ==========================================================

class Pedido(models.Model):
    """
    ✅ MEJORADO: Modelo de Pedido con validaciones robustas

    Representa un pedido de cliente que puede ser:
    - Pedido de Proveedor: Cliente pide a un proveedor específico
    - Encargo Directo: Cliente solicita comprar algo sin proveedor

    Ciclo de vida:
    CONFIRMADO → EN_PREPARACION → EN_RUTA → ENTREGADO
                              ↘ CANCELADO ↙
    """

    # ==========================================================
    # RELACIONES
    # ==========================================================
    cliente = models.ForeignKey(
        Perfil,
        on_delete=models.CASCADE,
        related_name='pedidos',
        verbose_name='Cliente',
        help_text='Cliente que realiza el pedido'
    )

    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos',
        verbose_name='Proveedor',
        help_text='Proveedor del pedido (null para encargos directos)'
    )

    repartidor = models.ForeignKey(
        Repartidor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos',
        verbose_name='Repartidor',
        help_text='Repartidor asignado al pedido'
    )

    # ==========================================================
    # INFORMACIÓN BÁSICA
    # ==========================================================
    tipo = models.CharField(
        max_length=20,
        choices=TipoPedido.choices,
        default=TipoPedido.PROVEEDOR,
        verbose_name='Tipo de Pedido',
        help_text='Tipo: Pedido de Proveedor o Encargo Directo'
    )

    estado = models.CharField(
        max_length=20,
        choices=EstadoPedido.choices,
        default=EstadoPedido.CONFIRMADO,
        verbose_name='Estado',
        help_text='Estado actual del pedido'
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción del pedido (requerido para encargos directos)'
    )

    total = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Total',
        help_text='Monto total del pedido'
    )

    # ==========================================================
    # ✅ CAMPOS DE UBICACIÓN
    # ==========================================================
    # Origen (proveedor/punto de recogida)
    direccion_origen = models.TextField(
        blank=True,
        null=True,
        verbose_name='Dirección de Origen',
        help_text='Dirección del proveedor o punto de recogida'
    )

    latitud_origen = models.FloatField(
        blank=True,
        null=True,
        verbose_name='Latitud Origen',
        help_text='Latitud del punto de origen (-5.0 a 2.0 para Ecuador)'
    )

    longitud_origen = models.FloatField(
        blank=True,
        null=True,
        verbose_name='Longitud Origen',
        help_text='Longitud del punto de origen (-92.0 a -75.0 para Ecuador)'
    )

    # Destino (cliente)
    direccion_entrega = models.TextField(
        verbose_name='Dirección de Entrega',
        help_text='Dirección donde se entregará el pedido'
    )

    latitud_destino = models.FloatField(
        blank=True,
        null=True,
        verbose_name='Latitud Destino',
        help_text='Latitud de la dirección de entrega'
    )

    longitud_destino = models.FloatField(
        blank=True,
        null=True,
        verbose_name='Longitud Destino',
        help_text='Longitud de la dirección de entrega'
    )

    # ==========================================================
    # PAGO Y COMISIONES
    # ==========================================================
    metodo_pago = models.CharField(
        max_length=30,
        default='efectivo',
        verbose_name='Método de Pago',
        help_text='Forma de pago del pedido'
    )

    comision_repartidor = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name='Comisión Repartidor',
        help_text='Monto que recibe el repartidor'
    )

    comision_proveedor = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name='Comisión Proveedor',
        help_text='Monto que recibe el proveedor'
    )

    ganancia_app = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name='Ganancia App',
        help_text='Comisión de la aplicación'
    )

    # ==========================================================
    # FECHAS Y AUDITORÍA
    # ==========================================================
    creado_en = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Creación',
        db_index=True
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    fecha_entregado = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Entrega',
        help_text='Fecha y hora en que se entregó el pedido'
    )

    # ==========================================================
    # CONTROL DE ESTADO
    # ==========================================================
    aceptado_por_repartidor = models.BooleanField(
        default=False,
        verbose_name='Aceptado por Repartidor',
        help_text='Indica si un repartidor aceptó el pedido'
    )

    confirmado_por_proveedor = models.BooleanField(
        default=False,
        verbose_name='Confirmado por Proveedor',
        help_text='Indica si el proveedor confirmó la preparación'
    )

    cancelado_por = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Cancelado Por',
        help_text='Actor que canceló el pedido (cliente, proveedor, repartidor, admin)'
    )

    # ==========================================================
    # MANAGER PERSONALIZADO
    # ==========================================================
    objects = PedidoManager()

    # ==========================================================
    # META
    # ==========================================================
    class Meta:
        db_table = 'pedidos'
        ordering = ['-creado_en']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

        indexes = [
            models.Index(fields=['-creado_en']),
            models.Index(fields=['estado']),
            models.Index(fields=['tipo']),
            models.Index(fields=['cliente']),
            models.Index(fields=['proveedor']),
            models.Index(fields=['repartidor']),
            # ✅ Índice compuesto para búsquedas comunes
            models.Index(fields=['estado', 'repartidor']),
            models.Index(fields=['estado', 'creado_en']),
            # ✅ Índice para búsquedas geográficas
            models.Index(fields=['latitud_destino', 'longitud_destino']),
        ]

        constraints = [
            # ✅ Validar rango de coordenadas de destino (Ecuador)
            models.CheckConstraint(
                check=Q(latitud_destino__isnull=True) |
                      (Q(latitud_destino__gte=-5.0) & Q(latitud_destino__lte=2.0)),
                name='pedido_lat_destino_ecuador'
            ),
            models.CheckConstraint(
                check=Q(longitud_destino__isnull=True) |
                      (Q(longitud_destino__gte=-92.0) & Q(longitud_destino__lte=-75.0)),
                name='pedido_lon_destino_ecuador'
            ),
            # ✅ Validar rango de coordenadas de origen
            models.CheckConstraint(
                check=Q(latitud_origen__isnull=True) |
                      (Q(latitud_origen__gte=-5.0) & Q(latitud_origen__lte=2.0)),
                name='pedido_lat_origen_ecuador'
            ),
            models.CheckConstraint(
                check=Q(longitud_origen__isnull=True) |
                      (Q(longitud_origen__gte=-92.0) & Q(longitud_origen__lte=-75.0)),
                name='pedido_lon_origen_ecuador'
            ),
            # ✅ Total debe ser positivo
            models.CheckConstraint(
                check=Q(total__gt=0),
                name='pedido_total_positivo'
            ),
        ]

    # ==========================================================
    # MÉTODOS BÁSICOS
    # ==========================================================
    def __str__(self):
        return f"Pedido #{self.pk} ({self.get_tipo_display()}) - {self.get_estado_display()}"

    def __repr__(self):
        return (
            f"<Pedido id={self.pk} tipo={self.tipo} estado={self.estado} "
            f"cliente={self.cliente_id} total={self.total}>"
        )

    # ==========================================================
    # ✅ VALIDACIONES
    # ==========================================================
    def clean(self):
        """✅ MEJORADO: Validaciones a nivel de modelo con mensajes descriptivos"""
        super().clean()

        errors = {}

        # Validar tipo proveedor
        if self.tipo == TipoPedido.PROVEEDOR and not self.proveedor:
            errors['proveedor'] = (
                "Un pedido de tipo 'Proveedor' debe tener un proveedor asignado."
            )

        # Validar tipo directo
        if self.tipo == TipoPedido.DIRECTO:
            if not self.descripcion or len(self.descripcion.strip()) < 10:
                errors['descripcion'] = (
                    "Un encargo directo debe incluir una descripción "
                    "de al menos 10 caracteres."
                )
            if self.proveedor:
                errors['proveedor'] = (
                    "Un encargo directo no debe tener proveedor asignado."
                )

        # Validar total
        if self.total < 0:
            errors['total'] = "El total no puede ser negativo."

        if self.total > 1000:
            errors['total'] = (
                "El total no puede superar $1000. "
                "Para montos mayores, contacte con soporte."
            )

        # ✅ Validar que coordenadas de destino estén completas
        if (self.latitud_destino is not None) != (self.longitud_destino is not None):
            errors['coordenadas'] = (
                "Debe proporcionar tanto latitud como longitud de destino, o ninguna."
            )

        # ✅ Validar que coordenadas de origen estén completas
        if (self.latitud_origen is not None) != (self.longitud_origen is not None):
            errors['coordenadas_origen'] = (
                "Debe proporcionar tanto latitud como longitud de origen, o ninguna."
            )

        # ✅ Validar dirección de entrega
        if not self.direccion_entrega or len(self.direccion_entrega.strip()) < 10:
            errors['direccion_entrega'] = (
                "La dirección de entrega debe tener al menos 10 caracteres."
            )

        if errors:
            raise ValidationError(errors)

    # ==========================================================
    # ✅ TRANSICIONES DEL FLUJO (MEJORADAS)
    # ==========================================================

    def aceptar_por_repartidor(self, repartidor):
        """
        ✅ MEJORADO: Repartidor acepta el pedido con validaciones robustas

        Args:
            repartidor (Repartidor): Instancia del repartidor que acepta

        Raises:
            ValidationError: Si el pedido no puede ser aceptado
        """
        # Validar estado del pedido
        if self.estado in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]:
            raise ValidationError(
                f"No se puede aceptar un pedido en estado '{self.get_estado_display()}'."
            )

        # Validar que no esté ya asignado
        if self.repartidor and self.repartidor != repartidor:
            raise ValidationError(
                f"El pedido ya fue tomado por {self.repartidor.user.get_full_name()}."
            )

        # Validar disponibilidad del repartidor
        if repartidor.estado != EstadoRepartidor.DISPONIBLE:
            raise ValidationError(
                f"El repartidor no está disponible. Estado: {repartidor.get_estado_display()}"
            )

        # Asignar repartidor
        self.repartidor = repartidor
        self.aceptado_por_repartidor = True

        # Cambiar estado según tipo de pedido
        if self.tipo == TipoPedido.PROVEEDOR:
            self.estado = EstadoPedido.EN_PREPARACION
            logger.info(
                f"✅ Pedido #{self.pk} aceptado por repartidor {repartidor.user.email}. "
                f"Estado: EN_PREPARACION"
            )
        else:
            self.estado = EstadoPedido.EN_RUTA
            logger.info(
                f"✅ Pedido #{self.pk} (directo) aceptado por repartidor {repartidor.user.email}. "
                f"Estado: EN_RUTA"
            )

        self.save(update_fields=[
            'repartidor',
            'aceptado_por_repartidor',
            'estado',
            'actualizado_en'
        ])

        # Marcar repartidor como ocupado
        repartidor.marcar_ocupado()

        # Notificar (se hace en signal)

    def confirmar_por_proveedor(self):
        """
        ✅ MEJORADO: El proveedor confirma la preparación del pedido

        Raises:
            ValidationError: Si el pedido no puede ser confirmado
        """
        # Validar tipo de pedido
        if self.tipo != TipoPedido.PROVEEDOR:
            raise ValidationError(
                "Solo los pedidos de tipo 'Proveedor' pueden ser confirmados."
            )

        # Validar estado
        if self.estado in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]:
            raise ValidationError(
                f"No se puede confirmar un pedido en estado '{self.get_estado_display()}'."
            )

        self.confirmado_por_proveedor = True
        self.estado = EstadoPedido.EN_PREPARACION

        self.save(update_fields=[
            'confirmado_por_proveedor',
            'estado',
            'actualizado_en'
        ])

        logger.info(
            f"✅ Pedido #{self.pk} confirmado por proveedor {self.proveedor.nombre}"
        )

        # Notificar (se hace en signal)

    def marcar_en_preparacion(self):
        """
        ✅ MEJORADO: Marca el pedido como en preparación

        Raises:
            ValidationError: Si la transición no es válida
        """
        if self.tipo != TipoPedido.PROVEEDOR:
            raise ValidationError(
                "Solo los pedidos de tipo 'Proveedor' pasan por preparación."
            )

        if self.estado in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]:
            raise ValidationError(
                f"No se puede cambiar el estado desde '{self.get_estado_display()}'."
            )

        self.estado = EstadoPedido.EN_PREPARACION
        self.save(update_fields=['estado', 'actualizado_en'])

        logger.info(f"✅ Pedido #{self.pk} marcado como EN_PREPARACION")

    def marcar_en_ruta(self):
        """
        ✅ MEJORADO: El repartidor inicia el trayecto al cliente

        Raises:
            ValidationError: Si no hay repartidor o estado inválido
        """
        if not self.repartidor:
            raise ValidationError(
                "No hay repartidor asignado. No se puede marcar como 'En ruta'."
            )

        if self.estado in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]:
            raise ValidationError(
                f"No se puede cambiar el estado desde '{self.get_estado_display()}'."
            )

        self.estado = EstadoPedido.EN_RUTA
        self.save(update_fields=['estado', 'actualizado_en'])

        logger.info(
            f"✅ Pedido #{self.pk} marcado como EN_RUTA. "
            f"Repartidor: {self.repartidor.user.email}"
        )

    def marcar_entregado(self):
        """
        ✅ MEJORADO: Marca el pedido como entregado y distribuye ganancias

        Raises:
            ValidationError: Si no cumple requisitos para entrega
        """
        if not self.repartidor:
            raise ValidationError(
                "No se puede entregar un pedido sin repartidor asignado."
            )

        if self.estado == EstadoPedido.CANCELADO:
            raise ValidationError(
                "No se puede entregar un pedido cancelado."
            )

        if self.estado == EstadoPedido.ENTREGADO:
            raise ValidationError(
                "El pedido ya fue marcado como entregado anteriormente."
            )

        self.estado = EstadoPedido.ENTREGADO
        self.fecha_entregado = timezone.now()

        self.save(update_fields=['estado', 'fecha_entregado', 'actualizado_en'])

        logger.info(
            f"✅ Pedido #{self.pk} marcado como ENTREGADO. "
            f"Repartidor: {self.repartidor.user.email}, Total: ${self.total}"
        )

        # Liberar repartidor
        if self.repartidor:
            try:
                self.repartidor.marcar_fuera_servicio("pedido completado")
            except Exception as e:
                logger.warning(
                    f"No se pudo actualizar estado del repartidor: {e}"
                )

        # Distribuir ganancias
        self._distribuir_ganancias()

        # Notificar (se hace en signal)

    def cancelar(self, motivo, actor):
        """
        ✅ MEJORADO: Cancela el pedido con logging detallado

        Args:
            motivo (str): Razón de la cancelación
            actor (str): Quien cancela (cliente, proveedor, repartidor, admin)

        Raises:
            ValidationError: Si el pedido no puede ser cancelado
        """
        if self.estado in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]:
            raise ValidationError(
                f"El pedido no puede cancelarse porque está en estado "
                f"'{self.get_estado_display()}'."
            )

        estado_anterior = self.estado
        self.estado = EstadoPedido.CANCELADO
        self.cancelado_por = actor

        self.save(update_fields=['estado', 'cancelado_por', 'actualizado_en'])

        logger.warning(
            f"❌ Pedido #{self.pk} cancelado por {actor}. "
            f"Motivo: {motivo}. Estado anterior: {estado_anterior}"
        )

        # Liberar repartidor si estaba asignado
        if self.repartidor:
            try:
                self.repartidor.marcar_disponible()
                logger.info(
                    f"✅ Repartidor {self.repartidor.user.email} liberado"
                )
            except Exception as e:
                logger.error(
                    f"Error al liberar repartidor: {e}"
                )

        # Notificar (se hace en signal)

    # ==========================================================
    # ✅ LÓGICA DE NEGOCIO (MEJORADA)
    # ==========================================================

    def _distribuir_ganancias(self):
        """
        ✅ MEJORADO: Distribuye el total del pedido con validación

        Distribución:
        - Pedido de Proveedor: 25% repartidor, 65% proveedor, 10% app
        - Encargo Directo: 85% repartidor, 15% app
        """
        total = float(self.total)

        if self.tipo == TipoPedido.PROVEEDOR:
            # 25% repartidor, 65% proveedor, 10% app
            self.comision_repartidor = round(total * 0.25, 2)
            self.comision_proveedor = round(total * 0.65, 2)
            self.ganancia_app = round(total * 0.10, 2)

            logger.info(
                f"💰 Ganancias distribuidas (Proveedor) - Pedido #{self.pk}: "
                f"Repartidor: ${self.comision_repartidor}, "
                f"Proveedor: ${self.comision_proveedor}, "
                f"App: ${self.ganancia_app}"
            )
        else:
            # Encargo directo: 85% repartidor, 15% app
            self.comision_repartidor = round(total * 0.85, 2)
            self.ganancia_app = round(total * 0.15, 2)
            self.comision_proveedor = 0

            logger.info(
                f"💰 Ganancias distribuidas (Directo) - Pedido #{self.pk}: "
                f"Repartidor: ${self.comision_repartidor}, "
                f"App: ${self.ganancia_app}"
            )

        # ✅ Validar que la suma sea correcta (con tolerancia de 2 centavos)
        suma = self.comision_repartidor + self.comision_proveedor + self.ganancia_app
        diferencia = abs(total - float(suma))

        if diferencia > 0.02:
            logger.warning(
                f"⚠️ Discrepancia en distribución de ganancias - Pedido #{self.pk}: "
                f"Total: ${total}, Suma: ${suma}, Diferencia: ${diferencia}"
            )

        self.save(update_fields=[
            'comision_repartidor',
            'comision_proveedor',
            'ganancia_app',
            'actualizado_en'
        ])

    def _notificar(self, mensaje):
        """
        ✅ MEJORADO: Enviar notificación con manejo robusto de errores

        Args:
            mensaje (str): Mensaje a enviar
        """
        try:
            from notificaciones.services import enviar_notificacion_push
            enviar_notificacion_push(self.cliente.user, mensaje)
            logger.debug(f"Notificación enviada: {mensaje}")
        except ImportError:
            logger.debug("Módulo de notificaciones no disponible")
        except Exception as e:
            logger.warning(f"Error al enviar notificación: {e}")

    # ==========================================================
    # ✅ PROPIEDADES ÚTILES (MEJORADAS Y CACHEADAS)
    # ==========================================================

    @property
    def puede_ser_cancelado(self):
        """Verifica si el pedido puede ser cancelado"""
        return self.estado not in [
            EstadoPedido.ENTREGADO,
            EstadoPedido.CANCELADO
        ]

    @cached_property
    def tiempo_transcurrido(self):
        """
        ✅ MEJORADO: Retorna tiempo transcurrido con formato mejorado

        Returns:
            str: Tiempo formateado (ej: "5 min", "2 horas", "3 días")
        """
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

    @property
    def es_pedido_activo(self):
        """Verifica si el pedido está en un estado activo"""
        return self.estado in [
            EstadoPedido.CONFIRMADO,
            EstadoPedido.EN_PREPARACION,
            EstadoPedido.EN_RUTA
        ]

    @property
    def tiene_ubicacion_completa(self):
        """Verifica si el pedido tiene coordenadas de destino completas"""
        return (
            self.latitud_destino is not None and
            self.longitud_destino is not None
        )

    @property
    def tiene_ubicacion_origen(self):
        """✅ NUEVO: Verifica si tiene coordenadas de origen"""
        return (
            self.latitud_origen is not None and
            self.longitud_origen is not None
        )

    @cached_property
    def distancia_estimada(self):
        """
        ✅ NUEVO: Calcula distancia aproximada entre origen y destino

        Returns:
            float: Distancia en kilómetros (None si no hay coordenadas)
        """
        if not (self.tiene_ubicacion_completa and self.tiene_ubicacion_origen):
            return None

        from math import radians, sin, cos, sqrt, atan2

        # Radio de la Tierra en km
        R = 6371.0

        # Convertir a radianes
        lat1 = radians(self.latitud_origen)
        lon1 = radians(self.longitud_origen)
        lat2 = radians(self.latitud_destino)
        lon2 = radians(self.longitud_destino)

        # Fórmula de Haversine
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distancia = R * c
        return round(distancia, 2)

    @property
    def tiempo_estimado_entrega(self):
        """
        ✅ NUEVO: Estima tiempo de entrega en minutos

        Returns:
            int: Minutos estimados (None si no se puede calcular)
        """
        distancia = self.distancia_estimada
        if not distancia:
            return None

        # Estimación: 30 km/h promedio en ciudad
        velocidad_promedio = 30  # km/h
        tiempo_horas = distancia / velocidad_promedio
        tiempo_minutos = int(tiempo_horas * 60)

        # Agregar tiempo base según tipo
        if self.tipo == TipoPedido.PROVEEDOR:
            tiempo_minutos += 20  # 20 min preparación
        else:
            tiempo_minutos += 10  # 10 min encargo

        return tiempo_minutos

    @property
    def esta_retrasado(self):
        """
        ✅ NUEVO: Determina si el pedido está retrasado

        Returns:
            bool: True si está retrasado
        """
        if self.estado != EstadoPedido.EN_RUTA:
            return False

        # Calcular tiempo desde que salió en ruta
        tiempo_en_ruta = timezone.now() - self.actualizado_en
        minutos_transcurridos = tiempo_en_ruta.total_seconds() / 60

        # Considerar retrasado si lleva más de 60 minutos
        tiempo_limite = self.tiempo_estimado_entrega or 60
        return minutos_transcurridos > tiempo_limite

    @property
    def porcentaje_comision_repartidor(self):
        """✅ NUEVO: Calcula porcentaje de comisión del repartidor"""
        if self.total > 0:
            return round((float(self.comision_repartidor) / float(self.total)) * 100, 2)
        return 0

    @property
    def porcentaje_comision_proveedor(self):
        """✅ NUEVO: Calcula porcentaje de comisión del proveedor"""
        if self.total > 0:
            return round((float(self.comision_proveedor) / float(self.total)) * 100, 2)
        return 0

    @property
    def porcentaje_ganancia_app(self):
        """✅ NUEVO: Calcula porcentaje de ganancia de la app"""
        if self.total > 0:
            return round((float(self.ganancia_app) / float(self.total)) * 100, 2)
        return 0

    # ==========================================================
    # ✅ MÉTODOS ÚTILES (NUEVOS)
    # ==========================================================

    def obtener_historial_estados(self):
        """
        ✅ NUEVO: Obtiene el historial de cambios de estado

        Returns:
            QuerySet: Historial ordenado por fecha (si existe el modelo)
        """
        try:
            return self.historialpedido_set.all().order_by('-fecha_cambio')
        except AttributeError:
            logger.debug("Modelo HistorialPedido no disponible")
            return []

    def calcular_tiempo_total_entrega(self):
        """
        ✅ NUEVO: Calcula tiempo total desde creación hasta entrega

        Returns:
            str: Tiempo formateado (None si no está entregado)
        """
        if self.estado != EstadoPedido.ENTREGADO or not self.fecha_entregado:
            return None

        diff = self.fecha_entregado - self.creado_en
        minutos = int(diff.total_seconds() // 60)

        if minutos < 60:
            return f"{minutos} minutos"
        else:
            horas = minutos // 60
            mins = minutos % 60
            return f"{horas}h {mins}min"

    def puede_ser_editado(self):
        """
        ✅ NUEVO: Determina si el pedido puede ser editado

        Returns:
            bool: True si puede editarse
        """
        # Solo se puede editar si está confirmado y no tiene repartidor
        return (
            self.estado == EstadoPedido.CONFIRMADO and
            self.repartidor is None
        )

    def obtener_resumen(self):
        """
        ✅ NUEVO: Genera un resumen completo del pedido

        Returns:
            dict: Resumen con información clave
        """
        return {
            'id': self.pk,
            'tipo': self.get_tipo_display(),
            'estado': self.get_estado_display(),
            'cliente': self.cliente.user.get_full_name(),
            'proveedor': self.proveedor.nombre if self.proveedor else 'N/A',
            'repartidor': self.repartidor.user.get_full_name() if self.repartidor else 'Sin asignar',
            'total': f"${self.total}",
            'tiempo_transcurrido': self.tiempo_transcurrido,
            'distancia_km': self.distancia_estimada,
            'tiempo_estimado_min': self.tiempo_estimado_entrega,
            'esta_retrasado': self.esta_retrasado,
            'creado_en': self.creado_en.strftime('%Y-%m-%d %H:%M:%S'),
            'actualizado_en': self.actualizado_en.strftime('%Y-%m-%d %H:%M:%S'),
        }

    def validar_transicion_estado(self, nuevo_estado):
        """
        ✅ NUEVO: Valida si una transición de estado es válida

        Args:
            nuevo_estado (str): Estado al que se quiere transicionar

        Returns:
            tuple: (es_valida, mensaje_error)
        """
        transiciones_validas = {
            EstadoPedido.CONFIRMADO: [EstadoPedido.EN_PREPARACION, EstadoPedido.CANCELADO],
            EstadoPedido.EN_PREPARACION: [EstadoPedido.EN_RUTA, EstadoPedido.CANCELADO],
            EstadoPedido.EN_RUTA: [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO],
        }

        # Estados finales no pueden cambiar
        if self.estado in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]:
            return False, f"No se puede cambiar desde el estado '{self.get_estado_display()}'"

        # Verificar si la transición es válida
        estados_permitidos = transiciones_validas.get(self.estado, [])
        if nuevo_estado not in estados_permitidos:
            return False, (
                f"No se puede cambiar de '{self.get_estado_display()}' "
                f"a '{dict(EstadoPedido.choices).get(nuevo_estado)}'"
            )

        # Validaciones adicionales según estado destino
        if nuevo_estado == EstadoPedido.EN_RUTA and not self.repartidor:
            return False, "No se puede marcar 'En ruta' sin repartidor asignado"

        return True, "Transición válida"

    @classmethod
    def obtener_estadisticas_globales(cls):
        """
        ✅ NUEVO: Obtiene estadísticas globales del sistema

        Returns:
            dict: Estadísticas agregadas
        """
        return cls.objects.aggregate(
            total_pedidos=Count('id'),
            pedidos_hoy=Count('id', filter=Q(creado_en__date=timezone.now().date())),
            pedidos_activos=Count('id', filter=Q(
                estado__in=[EstadoPedido.CONFIRMADO, EstadoPedido.EN_PREPARACION, EstadoPedido.EN_RUTA]
            )),
            pedidos_entregados=Count('id', filter=Q(estado=EstadoPedido.ENTREGADO)),
            pedidos_cancelados=Count('id', filter=Q(estado=EstadoPedido.CANCELADO)),
            ingresos_totales=Sum('total', filter=Q(estado=EstadoPedido.ENTREGADO)),
            ganancia_app_total=Sum('ganancia_app', filter=Q(estado=EstadoPedido.ENTREGADO)),
        )


# ==========================================================
# 📊 MODELO OPCIONAL: HISTORIAL DE PEDIDOS
# ==========================================================

class HistorialPedido(models.Model):
    """
    ✅ NUEVO: Modelo opcional para tracking de cambios de estado

    Registra cada cambio de estado de un pedido para auditoría.
    """
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='historial',
        verbose_name='Pedido'
    )

    estado_anterior = models.CharField(
        max_length=20,
        choices=EstadoPedido.choices,
        verbose_name='Estado Anterior'
    )

    estado_nuevo = models.CharField(
        max_length=20,
        choices=EstadoPedido.choices,
        verbose_name='Estado Nuevo'
    )

    fecha_cambio = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha del Cambio',
        db_index=True
    )

    usuario = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario que Realizó el Cambio'
    )

    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones',
        help_text='Notas adicionales sobre el cambio'
    )

    class Meta:
        db_table = 'pedidos_historial'
        ordering = ['-fecha_cambio']
        verbose_name = 'Historial de Pedido'
        verbose_name_plural = 'Historial de Pedidos'
        indexes = [
            models.Index(fields=['pedido', '-fecha_cambio']),
        ]

    def __str__(self):
        return (
            f"Pedido #{self.pedido_id}: {self.get_estado_anterior_display()} → "
            f"{self.get_estado_nuevo_display()}"
        )


# ==========================================================
# 📈 MODELO OPCIONAL: MÉTRICAS DE PEDIDOS
# ==========================================================

class MetricasPedido(models.Model):
    """
    ✅ NUEVO: Modelo opcional para almacenar métricas agregadas

    Permite cachear estadísticas para consultas rápidas en dashboards.
    """
    fecha = models.DateField(
        unique=True,
        verbose_name='Fecha',
        db_index=True
    )

    total_pedidos = models.IntegerField(
        default=0,
        verbose_name='Total de Pedidos'
    )

    pedidos_entregados = models.IntegerField(
        default=0,
        verbose_name='Pedidos Entregados'
    )

    pedidos_cancelados = models.IntegerField(
        default=0,
        verbose_name='Pedidos Cancelados'
    )

    ingresos_dia = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Ingresos del Día'
    )

    ganancia_app = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Ganancia de la App'
    )

    ticket_promedio = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Ticket Promedio'
    )

    tiempo_promedio_entrega = models.IntegerField(
        default=0,
        verbose_name='Tiempo Promedio de Entrega (minutos)'
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    class Meta:
        db_table = 'pedidos_metricas'
        ordering = ['-fecha']
        verbose_name = 'Métrica de Pedidos'
        verbose_name_plural = 'Métricas de Pedidos'

    def __str__(self):
        return f"Métricas {self.fecha}"

    @classmethod
    def calcular_y_guardar(cls, fecha=None):
        """
        ✅ NUEVO: Calcula y guarda métricas para una fecha

        Args:
            fecha (date): Fecha a calcular (hoy por defecto)

        Returns:
            MetricasPedido: Instancia creada/actualizada
        """
        if fecha is None:
            fecha = timezone.now().date()

        # Obtener pedidos del día
        pedidos_dia = Pedido.objects.filter(creado_en__date=fecha)

        # Calcular métricas
        stats = pedidos_dia.aggregate(
            total_pedidos=Count('id'),
            pedidos_entregados=Count('id', filter=Q(estado=EstadoPedido.ENTREGADO)),
            pedidos_cancelados=Count('id', filter=Q(estado=EstadoPedido.CANCELADO)),
            ingresos_dia=Sum('total', filter=Q(estado=EstadoPedido.ENTREGADO)),
            ganancia_app=Sum('ganancia_app', filter=Q(estado=EstadoPedido.ENTREGADO)),
        )

        # Calcular ticket promedio
        if stats['pedidos_entregados'] and stats['ingresos_dia']:
            ticket_promedio = stats['ingresos_dia'] / stats['pedidos_entregados']
        else:
            ticket_promedio = 0

        # Calcular tiempo promedio de entrega
        pedidos_entregados = pedidos_dia.filter(
            estado=EstadoPedido.ENTREGADO,
            fecha_entregado__isnull=False
        )

        if pedidos_entregados.exists():
            tiempos = []
            for pedido in pedidos_entregados:
                diff = pedido.fecha_entregado - pedido.creado_en
                tiempos.append(diff.total_seconds() / 60)
            tiempo_promedio = int(sum(tiempos) / len(tiempos))
        else:
            tiempo_promedio = 0

        # Crear o actualizar métrica
        metrica, created = cls.objects.update_or_create(
            fecha=fecha,
            defaults={
                'total_pedidos': stats['total_pedidos'] or 0,
                'pedidos_entregados': stats['pedidos_entregados'] or 0,
                'pedidos_cancelados': stats['pedidos_cancelados'] or 0,
                'ingresos_dia': stats['ingresos_dia'] or 0,
                'ganancia_app': stats['ganancia_app'] or 0,
                'ticket_promedio': ticket_promedio,
                'tiempo_promedio_entrega': tiempo_promedio,
            }
        )

        logger.info(
            f"{'✅ Métricas creadas' if created else '🔄 Métricas actualizadas'} "
            f"para {fecha}: {stats['total_pedidos']} pedidos"
        )

        return metrica
