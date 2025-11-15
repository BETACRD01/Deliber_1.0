# -*- coding: utf-8 -*-
# usuarios/models.py

from django.db import models, transaction
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    RegexValidator,
    FileExtensionValidator,
)

from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage
from authentication.models import User
from django.utils import timezone
import uuid
import logging
import os

logger = logging.getLogger("usuarios")


# ============================================
# VALIDADORES PERSONALIZADOS
# ============================================


def validar_tamano_imagen(imagen):
    """
    Valida que la imagen no exceda 5MB
    """
    limite_mb = 5
    limite_bytes = limite_mb * 1024 * 1024

    if imagen.size > limite_bytes:
        tamano_actual = imagen.size / (1024 * 1024)
        raise ValidationError(
            f"La imagen no puede superar {limite_mb}MB "
            f"(tamaño actual: {tamano_actual:.1f}MB)"
        )


def validar_coordenadas_ecuador(latitud, longitud):
    """
    Valida que las coordenadas estén dentro del territorio ecuatoriano
    Incluye validación de puntos en tierra firme
    """
    # Validar rangos básicos
    if not (-5.0 <= latitud <= 2.0):
        raise ValidationError(
            {
                "latitud": f"Fuera del territorio ecuatoriano: {latitud}° (rango: -5° a 2°)"
            }
        )

    if not (-92.0 <= longitud <= -75.0):
        raise ValidationError(
            {
                "longitud": f"Fuera del territorio ecuatoriano: {longitud}° (rango: -92° a -75°)"
            }
        )

    # ✅ NUEVO: Validar que no sea exactamente (0.0, 0.0)
    if latitud == 0.0 and longitud == 0.0:
        raise ValidationError(
            {
                "latitud": "Coordenadas inválidas (0,0)",
                "longitud": "Por favor, selecciona tu ubicación en el mapa",
            }
        )

    # ✅ NUEVO: Validar regiones conocidas de Ecuador
    # Región Costa: -3.5 a 2.0 lat, -81 a -75 lon
    # Región Sierra: -4.5 a 1.5 lat, -79.5 a -77 lon
    # Región Oriente: -5 a 0.5 lat, -78 a -75 lon

    es_costa = (-3.5 <= latitud <= 2.0) and (-81.0 <= longitud <= -75.0)
    es_sierra = (-4.5 <= latitud <= 1.5) and (-79.5 <= longitud <= -77.0)
    es_oriente = (-5.0 <= latitud <= 0.5) and (-78.0 <= longitud <= -75.0)
    es_galapagos = (-1.5 <= latitud <= 1.5) and (-92.0 <= longitud <= -89.0)

    if not (es_costa or es_sierra or es_oriente or es_galapagos):
        raise ValidationError(
            {
                "latitud": "Las coordenadas parecen estar fuera de Ecuador continental",
                "longitud": "Verifica tu ubicación en el mapa",
            }
        )


# ============================================
# MODELO: PERFIL
# ============================================


class Perfil(models.Model):
    """
    Perfil extendido del usuario para app de delivery
    ✅ CON SOPORTE PARA NOTIFICACIONES PUSH (FCM)
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="perfil_usuario"
    )

    foto_perfil = models.ImageField(
        upload_to="perfiles/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="Foto de perfil",
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validar_tamano_imagen,
        ],
    )

    fecha_nacimiento = models.DateField(
        blank=True, null=True, verbose_name="Fecha de nacimiento"
    )

    # ============================================
    # ✅ SISTEMA DE NOTIFICACIONES PUSH (FCM)
    # ============================================
    fcm_token = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="Token FCM para notificaciones push",
        help_text="Token de Firebase Cloud Messaging del dispositivo",
    )

    fcm_token_actualizado = models.DateTimeField(
        null=True, blank=True, verbose_name="Última actualización del token FCM"
    )

    # Sistema de calificaciones (para repartidores)
    calificacion = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        verbose_name="Calificación promedio",
    )

    total_resenas = models.IntegerField(default=0, verbose_name="Total de reseñas")

    # Estadísticas básicas
    total_pedidos = models.IntegerField(
        default=0, verbose_name="Total de pedidos realizados"
    )

    # Sistema de rifas mensuales (oculto para el usuario)
    pedidos_mes_actual = models.IntegerField(
        default=0,
        verbose_name="Pedidos del mes actual",
        help_text="Se resetea cada mes. Mínimo 3 para participar en rifa",
    )

    ultima_actualizacion_mes = models.DateField(
        auto_now_add=True, verbose_name="Última actualización de mes"
    )

    participa_en_sorteos = models.BooleanField(
        default=True, verbose_name="Participa en sorteos automáticos"
    )

    # Preferencias de notificaciones
    notificaciones_pedido = models.BooleanField(
        default=True, verbose_name="Notificaciones de estado del pedido"
    )

    notificaciones_promociones = models.BooleanField(
        default=True, verbose_name="Recibir ofertas y promociones"
    )

    # Auditoría
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "perfiles_usuario"
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"
        indexes = [
            models.Index(fields=["calificacion"]),
            models.Index(fields=["pedidos_mes_actual"]),
            models.Index(fields=["fcm_token"]),
            models.Index(fields=["user", "participa_en_sorteos"]),
        ]

    def __str__(self):
        return f"Perfil de {self.user.email}"

    # ============================================
    # ✅ MÉTODOS PARA NOTIFICACIONES PUSH (MEJORADOS)
    # ============================================

    def actualizar_fcm_token(self, token):
        """
        Actualiza el token FCM del dispositivo
        ✅ MEJORADO: Valida unicidad y limpia tokens duplicados

        Args:
            token (str): Token FCM del dispositivo

        Returns:
            bool: True si se actualizó correctamente
        """
        if not token or not token.strip():
            logger.warning(f"Token FCM vacío: {self.user.email}")
            return False

        try:
            with transaction.atomic():
                # Verificar si el token ya está asignado a otro usuario
                if self.fcm_token != token:
                    # Limpiar token duplicado de otro usuario
                    Perfil.objects.select_for_update().filter(fcm_token=token).exclude(
                        user=self.user
                    ).update(fcm_token=None, fcm_token_actualizado=None)

                # Actualizar token
                self.fcm_token = token
                self.fcm_token_actualizado = timezone.now()
                self.save(
                    update_fields=[
                        "fcm_token",
                        "fcm_token_actualizado",
                        "actualizado_en",
                    ]
                )

            logger.info(f"✅ Token FCM actualizado: {self.user.email}")
            return True

        except Exception as e:
            logger.error(f"❌ Error actualizando token FCM: {e}", exc_info=True)
            return False

    def eliminar_fcm_token(self):
        """
        Elimina el token FCM (cuando el usuario cierra sesión)
        """
        if self.fcm_token:
            logger.info(f"🔒 Eliminando token FCM: {self.user.email}")

        self.fcm_token = None
        self.fcm_token_actualizado = None
        self.save(
            update_fields=["fcm_token", "fcm_token_actualizado", "actualizado_en"]
        )

    @property
    def puede_recibir_notificaciones(self):
        """Verifica si puede recibir notificaciones push"""
        return bool(self.fcm_token) and self.notificaciones_pedido

    # ============================================
    # MÉTODOS PARA CALIFICACIONES
    # ============================================

    def actualizar_calificacion(self, nueva_calificacion):
        """
        Actualiza la calificación promedio del perfil

        Args:
            nueva_calificacion (int): Calificación de 1 a 5
        """
        if not (1 <= nueva_calificacion <= 5):
            raise ValidationError("La calificación debe estar entre 1 y 5")

        total = (self.calificacion * self.total_resenas) + nueva_calificacion
        self.total_resenas += 1
        self.calificacion = round(total / self.total_resenas, 2)
        self.save(update_fields=["calificacion", "total_resenas", "actualizado_en"])

        logger.info(
            f"Calificación actualizada: {self.user.email} - {self.calificacion}/5.0"
        )

    # ============================================
    # MÉTODOS PARA ESTADÍSTICAS DE PEDIDOS
    # ============================================
    def incrementar_pedidos(self):
        """
        Incrementa el contador de pedidos totales y del mes actual
        Se llama automáticamente cuando se confirma/entrega un pedido
        """
        from datetime import date

        # Verificar si cambió el mes
        hoy = date.today()
        if (
            self.ultima_actualizacion_mes.month != hoy.month
            or self.ultima_actualizacion_mes.year != hoy.year
        ):
            # Resetear contador mensual si cambió el mes
            self.pedidos_mes_actual = 0
            self.ultima_actualizacion_mes = hoy

        # Incrementar contadores
        self.total_pedidos += 1
        self.pedidos_mes_actual += 1
        self.save(
            update_fields=[
                "total_pedidos",
                "pedidos_mes_actual",
                "ultima_actualizacion_mes",
                "actualizado_en",
            ]
        )

        logger.info(
            f"Pedido incrementado: {self.user.email} - "
            f"Total: {self.total_pedidos} | Mes: {self.pedidos_mes_actual}"
        )

    def resetear_mes(self):
        """
        Resetea el contador mensual
        (Llamado por el admin o comando de management cada 30 días)
        """
        from datetime import date

        self.pedidos_mes_actual = 0
        self.ultima_actualizacion_mes = date.today()
        self.save(
            update_fields=[
                "pedidos_mes_actual",
                "ultima_actualizacion_mes",
                "actualizado_en",
            ]
        )

        logger.info(f"Contador mensual reseteado: {self.user.email}")

    # ============================================
    # PROPIEDADES CALCULADAS
    # ============================================
    # ============================================
    # PROPIEDADES CALCULADAS
    # ============================================
    @property
    def tiene_telefono(self):
        """Verifica si tiene teléfono registrado"""
        return bool(self.user.celular)

    @property
    def telefono(self):
        """
        ✅ Propiedad que retorna el celular del User
        Mantiene compatibilidad con código existente
        """
        return self.user.celular if hasattr(self.user, "celular") else None

    @property
    def puede_participar_rifa(self):
        """Verifica si el usuario puede participar en la rifa mensual"""
        return self.participa_en_sorteos and self.pedidos_mes_actual >= 3

    @property
    def es_cliente_frecuente(self):
        """Determina si es un cliente frecuente (más de 10 pedidos)"""
        return self.total_pedidos >= 10

    @property
    def edad(self):
        """Calcula la edad del usuario"""
        if self.fecha_nacimiento:
            today = timezone.now().date()
            return (
                today.year
                - self.fecha_nacimiento.year
                - (
                    (today.month, today.day)
                    < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
                )
            )
        return None

    # ============================================
    # VALIDACIONES
    # ============================================

    def clean(self):
        """Validaciones personalizadas"""
        if self.fecha_nacimiento and self.fecha_nacimiento > timezone.now().date():
            raise ValidationError(
                {"fecha_nacimiento": "La fecha de nacimiento no puede ser futura."}
            )

        if self.edad and self.edad < 13:
            raise ValidationError(
                {
                    "fecha_nacimiento": "Debes tener al menos 13 años para usar la aplicación."
                }
            )


# ============================================
# MODELO: DIRECCIÓN FAVORITA (✅ CORREGIDO)
# ============================================


class DireccionFavorita(models.Model):
    """
    Direcciones guardadas por el usuario para entregas
    ✅ CORREGIDO: Race conditions eliminadas, copy-paste error corregido
    """

    TIPO_DIRECCION_CHOICES = [
        ("casa", "Casa"),
        ("trabajo", "Trabajo"),
        ("otro", "Otro"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="direcciones_favoritas"
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_DIRECCION_CHOICES,
        default="otro",
        verbose_name="Tipo de dirección",
    )

    etiqueta = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Etiqueta",
        help_text="Ej: Mi casa, Oficina",
    )

    direccion = models.TextField(verbose_name="Dirección completa")

    referencia = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Referencia",
        help_text="Ej: Casa blanca, portón negro",
    )

    # Coordenadas para el mapa
    latitud = models.FloatField(
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)]
    )

    longitud = models.FloatField(
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)]
    )

    # Información de ubicación
    ciudad = models.CharField(max_length=100, blank=True, verbose_name="Ciudad")

    # Configuración
    es_predeterminada = models.BooleanField(
        default=False, verbose_name="Usar como dirección predeterminada"
    )

    activa = models.BooleanField(default=True, verbose_name="Dirección activa")

    # Estadísticas de uso
    veces_usada = models.IntegerField(default=0, verbose_name="Veces utilizada")

    ultimo_uso = models.DateTimeField(blank=True, null=True, verbose_name="Último uso")

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "direcciones_favoritas"
        verbose_name = "Dirección Favorita"
        verbose_name_plural = "Direcciones Favoritas"
        ordering = ["-es_predeterminada", "-ultimo_uso", "-created_at"]
        unique_together = [["user", "etiqueta"]]
        indexes = [
            models.Index(fields=["user", "activa"]),
            models.Index(fields=["es_predeterminada"]),
            models.Index(fields=["user", "activa", "es_predeterminada"]),
        ]

    def __str__(self):
        return f"{self.etiqueta} - {self.user.email}"

    def clean(self):
        """Validaciones personalizadas"""
        # Validar coordenadas dentro de Ecuador
        validar_coordenadas_ecuador(self.latitud, self.longitud)

        # Validar dirección predeterminada única
        if self.es_predeterminada:
            otras_predeterminadas = DireccionFavorita.objects.filter(
                user=self.user, es_predeterminada=True, activa=True
            ).exclude(pk=self.pk)

            if otras_predeterminadas.exists():
                raise ValidationError("Ya existe una dirección predeterminada.")

    def save(self, *args, **kwargs):
        """
        ✅ CORREGIDO: Validaciones con select_for_update y copy-paste error eliminado
        """
        self.full_clean()

        with transaction.atomic():
            # ✅ CORREGIDO: Cambiado de MetodoPago a DireccionFavorita
            # Si es la primera dirección, hacerla predeterminada
            if (
                not self.pk
                and not DireccionFavorita.objects.filter(
                    user=self.user, activa=True
                ).exists()
            ):
                self.es_predeterminada = True

            # Si se marca como predeterminada, desmarcar otras
            if self.es_predeterminada:
                DireccionFavorita.objects.select_for_update().filter(
                    user=self.user, es_predeterminada=True
                ).exclude(pk=self.pk).update(es_predeterminada=False)

            # ✅ CORREGIDO: super().save() DENTRO de la transacción
            super().save(*args, **kwargs)

        logger.info(f"📍 Dirección guardada: {self.user.email} - {self.etiqueta}")

    def marcar_como_usada(self):
        """Actualiza las estadísticas cuando se usa la dirección"""
        self.veces_usada += 1
        self.ultimo_uso = timezone.now()
        self.save(update_fields=["veces_usada", "ultimo_uso"])

    def desactivar(self):
        """Desactiva la dirección sin eliminarla"""
        self.activa = False
        if self.es_predeterminada:
            self.es_predeterminada = False
        self.save(update_fields=["activa", "es_predeterminada"])

    @property
    def direccion_completa(self):
        """Retorna la dirección con referencia"""
        if self.referencia:
            return f"{self.direccion} - {self.referencia}"
        return self.direccion


# ============================================
# MODELO: MÉTODO DE PAGO (✅ CORREGIDO)
# ============================================


class MetodoPago(models.Model):
    """
    Métodos de pago del usuario
    ✅ CORREGIDO: super().save() dentro de transacción
    """

    TIPO_PAGO_CHOICES = [
        ("efectivo", "Efectivo"),
        ("transferencia", "Transferencia"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="metodos_pago"
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_PAGO_CHOICES,
        default="efectivo",
        verbose_name="Tipo de pago",
    )

    alias = models.CharField(
        max_length=50,
        verbose_name="Nombre",
        help_text="Ej: Pago en efectivo, Transferencia Banco Pichincha",
    )

    # ============================================
    # COMPROBANTE DE TRANSFERENCIA
    # ============================================
    comprobante_pago = models.ImageField(
        upload_to="comprobantes/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="Comprobante de transferencia",
        help_text="Imagen del comprobante (obligatorio para transferencias)",
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "pdf"]),
            validar_tamano_imagen,
        ],
    )

    # ============================================
    # OBSERVACIONES (MAX 100 CARACTERES)
    # ============================================
    observaciones = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Observaciones",
        help_text="Describe cualquier problema que haya ocurrido (máx. 100 caracteres)",
    )

    es_predeterminado = models.BooleanField(
        default=False, verbose_name="Método predeterminado"
    )

    activo = models.BooleanField(default=True, verbose_name="Método activo")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "metodos_pago"
        verbose_name = "Método de Pago"
        verbose_name_plural = "Métodos de Pago"
        ordering = ["-es_predeterminado", "-created_at"]
        unique_together = [["user", "alias"]]
        indexes = [
            models.Index(fields=["user", "activo"]),
            models.Index(fields=["tipo"]),
            models.Index(fields=["user", "tipo", "activo"]),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.user.email}"

    # ============================================
    # ✅ VALIDACIONES MEJORADAS
    # ============================================

    def clean(self):
        """Validaciones personalizadas"""
        # Si es transferencia, el comprobante es OBLIGATORIO
        if self.tipo == "transferencia" and not self.comprobante_pago:
            raise ValidationError(
                {"comprobante_pago": "Debes subir el comprobante de transferencia"}
            )

        # Si es efectivo, NO debe tener comprobante
        if self.tipo == "efectivo" and self.comprobante_pago:
            raise ValidationError(
                {"comprobante_pago": "El pago en efectivo no requiere comprobante"}
            )

        # Validar longitud de observaciones
        if self.observaciones and len(self.observaciones) > 100:
            raise ValidationError(
                {"observaciones": "Las observaciones no pueden exceder 100 caracteres"}
            )

    def save(self, *args, **kwargs):
        """
        ✅ CORREGIDO: TODO dentro de transacción atómica
        """
        self.full_clean()

        with transaction.atomic():
            # Si es el primer método, hacerlo predeterminado
            if (
                not self.pk
                and not MetodoPago.objects.filter(user=self.user, activo=True).exists()
            ):
                self.es_predeterminado = True

            # Si se marca como predeterminado, desmarcar otros
            if self.es_predeterminado:
                MetodoPago.objects.select_for_update().filter(
                    user=self.user, es_predeterminado=True
                ).exclude(pk=self.pk).update(es_predeterminado=False)

            # ✅ CORREGIDO: super().save() DENTRO de la transacción
            super().save(*args, **kwargs)

        logger.info(
            f"💳 Método de pago guardado: {self.user.email} - {self.get_tipo_display()} - "
            f"Comprobante: {'Sí' if self.comprobante_pago else 'No'}"
        )

    # ============================================
    # PROPIEDADES ÚTILES
    # ============================================

    @property
    def tiene_comprobante(self) -> bool:
        """Verifica si tiene comprobante subido"""
        return bool(self.comprobante_pago)

    @property
    def requiere_verificacion(self) -> bool:
        """Indica si requiere verificación del admin/repartidor"""
        return self.tipo == "transferencia"


# ============================================
# SEÑALES
# ============================================
@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """
    Crea automáticamente el perfil cuando se registra un usuario
    ✅ MEJORADO: Previene duplicados y errores
    """
    if created:
        try:
            # Verificar si ya existe (por si acaso)
            perfil, creado = Perfil.objects.get_or_create(
                user=instance,
                defaults={
                    "calificacion": 5.0,
                    "total_pedidos": 0,
                    "pedidos_mes_actual": 0,
                    "participa_en_sorteos": True,
                    "notificaciones_pedido": True,
                    "notificaciones_promociones": True,
                },
            )

            if creado:
                logger.info(f"✅ Perfil creado automáticamente: {instance.email}")
            else:
                logger.warning(f"⚠️ El perfil ya existía para: {instance.email}")

        except Exception as e:
            logger.error(
                f"❌ Error creando perfil para {instance.email}: {e}", exc_info=True
            )
            # No lanzar excepción para no bloquear el registro del usuario


# ============================================
# ✅ SEÑALES PARA ELIMINAR ARCHIVOS HUÉRFANOS (MEJORADAS)
# ============================================


@receiver(pre_save, sender=Perfil)
def eliminar_foto_perfil_anterior(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_perfil = Perfil.objects.get(pk=instance.pk)

        # ✅ NUEVO: Detectar si el usuario borró la foto
        if old_perfil.foto_perfil:
            # Si cambió o se borró, eliminar archivo
            if old_perfil.foto_perfil != instance.foto_perfil:
                if default_storage.exists(old_perfil.foto_perfil.name):
                    default_storage.delete(old_perfil.foto_perfil.name)
                    logger.info(
                        f"🗑️ Foto anterior eliminada: {old_perfil.foto_perfil.name}"
                    )
    except Perfil.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"❌ Error eliminando foto: {e}", exc_info=True)


@receiver(pre_delete, sender=Perfil)
def eliminar_foto_perfil_al_borrar(sender, instance, **kwargs):
    """
    ✅ MEJORADO: Elimina la foto al borrar el perfil usando storage
    """
    if instance.foto_perfil:
        try:
            if default_storage.exists(instance.foto_perfil.name):
                default_storage.delete(instance.foto_perfil.name)
                logger.info(f"🗑️ Foto de perfil eliminada: {instance.foto_perfil.name}")
        except Exception as e:
            logger.error(f"❌ Error eliminando foto: {e}", exc_info=True)


@receiver(pre_save, sender=MetodoPago)
def eliminar_comprobante_anterior(sender, instance, **kwargs):
    """
    ✅ MEJORADO: Elimina el comprobante antiguo usando storage
    """
    if not instance.pk:
        return

    try:
        old_metodo = MetodoPago.objects.get(pk=instance.pk)
        if (
            old_metodo.comprobante_pago
            and old_metodo.comprobante_pago != instance.comprobante_pago
        ):
            if default_storage.exists(old_metodo.comprobante_pago.name):
                default_storage.delete(old_metodo.comprobante_pago.name)
                logger.info(
                    f"🗑️ Comprobante anterior eliminado: {old_metodo.comprobante_pago.name}"
                )
    except MetodoPago.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"❌ Error eliminando comprobante anterior: {e}", exc_info=True)


@receiver(pre_delete, sender=MetodoPago)
def eliminar_comprobante_al_borrar(sender, instance, **kwargs):
    """
    ✅ MEJORADO: Elimina el comprobante al borrar el método de pago usando storage
    """
    if instance.comprobante_pago:
        try:
            if default_storage.exists(instance.comprobante_pago.name):
                default_storage.delete(instance.comprobante_pago.name)
                logger.info(
                    f"🗑️ Comprobante eliminado: {instance.comprobante_pago.name}"
                )
        except Exception as e:
            logger.error(f"❌ Error eliminando comprobante: {e}", exc_info=True)


# ============================================
# MODELO: UBICACIÓN DE USUARIO (Tiempo real "lite")
# ============================================
from django.db import models
from django.utils import timezone

# ya tienes: from authentication.models import User
# ya tienes: validar_coordenadas_ecuador


class UbicacionUsuario(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="ubicacion_actual"
    )
    latitud = models.FloatField()
    longitud = models.FloatField()
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ubicaciones_usuario"
        verbose_name = "Ubicación de Usuario"
        verbose_name_plural = "Ubicaciones de Usuarios"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["actualizado_en"]),
        ]

    def __str__(self):
        return f"Ubicación de {self.user.email} ({self.latitud}, {self.longitud})"

    def clean(self):
        # Reusar tu validador (rango Ecuador)
        validar_coordenadas_ecuador(self.latitud, self.longitud)


# AGREGAR ESTO AL FINAL DE usuarios/models.py
class SolicitudCambioRol(models.Model):
    """
    Modelo para gestionar solicitudes de cambio de rol
    Los usuarios solicitan cambiar a PROVEEDOR o REPARTIDOR
    El admin acepta o rechaza
    """

    ESTADO_CHOICES = [
        ("PENDIENTE", "Pendiente de Revisión"),
        ("ACEPTADA", "Aceptada"),
        ("RECHAZADA", "Rechazada"),
    ]

    ROL_SOLICITADO_CHOICES = [
        ("PROVEEDOR", "Quiero ser Proveedor"),
        ("REPARTIDOR", "Quiero ser Repartidor"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="solicitudes_cambio_rol",
        verbose_name="Usuario",
    )

    rol_solicitado = models.CharField(
        max_length=20, choices=ROL_SOLICITADO_CHOICES, verbose_name="Rol Solicitado"
    )

    motivo = models.TextField(
        verbose_name="Motivo de la Solicitud",
        help_text="¿Por qué deseas cambiar de rol?",
        max_length=500,
    )

    # =============================================
    # DATOS ESPECÍFICOS PARA PROVEEDOR
    # =============================================
    ruc = models.CharField(
        max_length=13,
        blank=True,
        null=True,
        verbose_name="RUC",
        help_text="RUC de 13 dígitos (solo para proveedores)",
        db_index=True,
    )

    nombre_comercial = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nombre Comercial",
    )

    tipo_negocio = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ("restaurante", "Restaurante"),
            ("farmacia", "Farmacia"),
            ("supermercado", "Supermercado"),
            ("tienda", "Tienda"),
            ("otro", "Otro"),
        ],
        verbose_name="Tipo de Negocio",
    )

    descripcion_negocio = models.TextField(
        blank=True,
        verbose_name="Descripción del Negocio",
    )

    horario_apertura = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Hora de Apertura",
    )

    horario_cierre = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Hora de Cierre",
    )

    # =============================================
    # DATOS ESPECÍFICOS PARA REPARTIDOR
    # =============================================
    cedula_identidad = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Cédula de Identidad",
    )

    tipo_vehiculo = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ("bicicleta", "Bicicleta"),
            ("moto", "Moto"),
            ("auto", "Auto"),
            ("camion", "Camión"),
            ("otro", "Otro"),
        ],
        verbose_name="Tipo de Vehículo",
    )

    zona_cobertura = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Zona de Cobertura",
    )

    disponibilidad = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Disponibilidad",
        help_text="Horarios de disponibilidad (formato JSON)",
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="PENDIENTE",
        verbose_name="Estado",
        db_index=True,
    )

    # =============================================
    # INFORMACIÓN DEL ADMINISTRADOR
    # =============================================
    admin_responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes_rol_procesadas",
        verbose_name="Admin Responsable",
    )

    motivo_respuesta = models.TextField(
        blank=True,
        verbose_name="Motivo de la Respuesta",
        help_text="Comentario del admin al aceptar/rechazar",
    )

    # =============================================
    # AUDITORÍA
    # =============================================
    creado_en = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Solicitud", db_index=True
    )

    respondido_en = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de Respuesta", db_index=True
    )

    class Meta:
        db_table = "solicitudes_cambio_rol"
        verbose_name = "Solicitud de Cambio de Rol"
        verbose_name_plural = "Solicitudes de Cambio de Rol"
        ordering = ["-creado_en"]
        indexes = [
            models.Index(fields=["user", "estado"]),
            models.Index(fields=["estado", "-creado_en"]),
            models.Index(fields=["admin_responsable", "-respondido_en"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "rol_solicitado"],
                condition=models.Q(estado="PENDIENTE"),
                name="una_solicitud_pendiente_por_rol",
            )
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_rol_solicitado_display()} - {self.get_estado_display()}"

    def aceptar(self, admin, motivo=""):
        """
        Acepta la solicitud y agrega el rol al usuario

        Args:
            admin: Usuario administrador que acepta
            motivo: Motivo de la aceptación (opcional)
        """
        self.estado = "ACEPTADA"
        self.admin_responsable = admin
        self.motivo_respuesta = motivo
        self.respondido_en = timezone.now()
        self.save(
            update_fields=[
                "estado",
                "admin_responsable",
                "motivo_respuesta",
                "respondido_en",
            ]
        )

        # Agregar rol al usuario
        self.user.agregar_rol(self.rol_solicitado)

        logger.info(
            f"✅ Solicitud aceptada: {self.user.email} agregado como {self.rol_solicitado} "
            f"por {admin.email}"
        )

    def rechazar(self, admin, motivo=""):
        """
        Rechaza la solicitud

        Args:
            admin: Usuario administrador que rechaza
            motivo: Motivo del rechazo
        """
        self.estado = "RECHAZADA"
        self.admin_responsable = admin
        self.motivo_respuesta = motivo
        self.respondido_en = timezone.now()
        self.save(
            update_fields=[
                "estado",
                "admin_responsable",
                "motivo_respuesta",
                "respondido_en",
            ]
        )

        logger.warning(
            f"❌ Solicitud rechazada: {self.user.email} no será {self.rol_solicitado} "
            f"por {admin.email}. Motivo: {motivo}"
        )

    # =============================================
    # PROPIEDADES ÚTILES
    # =============================================
    @property
    def esta_pendiente(self):
        """Verifica si la solicitud está pendiente"""
        return self.estado == "PENDIENTE"

    @property
    def fue_aceptada(self):
        """Verifica si fue aceptada"""
        return self.estado == "ACEPTADA"

    @property
    def fue_rechazada(self):
        """Verifica si fue rechazada"""
        return self.estado == "RECHAZADA"

    @property
    def dias_pendiente(self):
        """Calcula días que lleva pendiente"""
        if self.estado == "PENDIENTE":
            return (timezone.now() - self.creado_en).days
        return None


def aceptar(self, admin, motivo_respuesta=""):
    """
    Acepta la solicitud usando el gestor centralizado
    """
    from usuarios.solicitudes import GestorSolicitudCambioRol

    return GestorSolicitudCambioRol.aceptar_solicitud(
        solicitud=self, admin=admin, motivo_respuesta=motivo_respuesta
    )


def rechazar(self, admin, motivo_respuesta):
    """
    Rechaza la solicitud usando el gestor centralizado
    """
    from usuarios.solicitudes import GestorSolicitudCambioRol

    return GestorSolicitudCambioRol.rechazar_solicitud(
        solicitud=self, admin=admin, motivo_respuesta=motivo_respuesta
    )
