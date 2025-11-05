from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from authentication.models import User
import logging

logger = logging.getLogger('proveedores')


class Proveedor(models.Model):
    """
    Modelo para gestionar proveedores de la plataforma

    ✅ ACTUALIZADO CON:
    - Relación OneToOne con User
    - Sincronización automática vía signals
    - Validaciones mejoradas
    - Métodos helper para acceso a datos de User
    - Soft delete support
    """
    # ============================================
    # ✅ RELACIÓN CON USER
    # ============================================
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='proveedor',
        null=True,
        blank=True,
        verbose_name='Usuario',
        help_text='Usuario vinculado al proveedor (creado al registrarse)'
    )

    # Validador para teléfono
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="El teléfono debe tener el formato: '+593999999999'. Hasta 15 dígitos."
    )

    # ============================================
    # INFORMACIÓN BÁSICA
    # ============================================
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre del Proveedor',
        help_text='Nombre completo o razón social'
    )

    ruc = models.CharField(
        max_length=13,
        unique=True,
        verbose_name='RUC/Cédula',
        help_text='RUC o cédula del proveedor (13 dígitos)',
        db_index=True
    )

    # ============================================
    # CONTACTO (⚠️ DEPRECADOS - Usar User)
    # ============================================
    telefono = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        verbose_name='Teléfono',
        help_text='⚠️ DEPRECADO: Se sincroniza con user.celular'
    )

    email = models.EmailField(
        blank=True,
        verbose_name='Email',
        help_text='⚠️ DEPRECADO: Se sincroniza con user.email'
    )

    # ============================================
    # DIRECCIÓN
    # ============================================
    direccion = models.TextField(
        blank=True,
        verbose_name='Dirección'
    )

    ciudad = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Ciudad',
        db_index=True
    )

    # ============================================
    # INFORMACIÓN ADICIONAL
    # ============================================
    tipo_proveedor = models.CharField(
        max_length=50,
        choices=[
            ('restaurante', 'Restaurante'),
            ('farmacia', 'Farmacia'),
            ('supermercado', 'Supermercado'),
            ('tienda', 'Tienda'),
            ('otro', 'Otro'),
        ],
        default='restaurante',
        verbose_name='Tipo de Proveedor',
        db_index=True
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción del negocio'
    )

    # ============================================
    # CONFIGURACIÓN
    # ============================================
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si el proveedor está activo en la plataforma',
        db_index=True
    )

    verificado = models.BooleanField(
        default=False,
        verbose_name='Verificado',
        help_text='Si el proveedor ha sido verificado por un administrador',
        db_index=True
    )

    comision_porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        verbose_name='Comisión (%)',
        help_text='Porcentaje de comisión por pedido'
    )

    # ============================================
    # HORARIOS
    # ============================================
    horario_apertura = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Hora de Apertura'
    )

    horario_cierre = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Hora de Cierre'
    )

    # ============================================
    # GEOLOCALIZACIÓN
    # ============================================
    latitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Latitud'
    )

    longitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Longitud'
    )

    # ============================================
    # LOGO/IMAGEN
    # ============================================
    logo = models.ImageField(
        upload_to='proveedores/logos/',
        null=True,
        blank=True,
        verbose_name='Logo'
    )

    # ============================================
    # AUDITORÍA
    # ============================================
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    # ============================================
    # ✅ SOFT DELETE (OPCIONAL)
    # ============================================
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Eliminación',
        help_text='Si está lleno, el proveedor está eliminado (soft delete)'
    )

    # ============================================
    # META
    # ============================================
    class Meta:
        db_table = 'proveedores'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ruc']),
            models.Index(fields=['activo']),
            models.Index(fields=['tipo_proveedor']),
            models.Index(fields=['verificado']),
            models.Index(fields=['user']),
            models.Index(fields=['ciudad']),
            models.Index(fields=['deleted_at']),  # ✅ Para soft delete
        ]
        constraints = [
            # ✅ NUEVO: Asegurar que user sea único si no es null
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(user__isnull=False),
                name='unique_user_proveedor'
            )
        ]

    # ============================================
    # ✅ MÉTODOS BÁSICOS
    # ============================================
    def __str__(self):
        if self.user:
            return f"{self.nombre} - {self.user.email}"
        return f"{self.nombre} - {self.ruc}"

    def __repr__(self):
        return f"<Proveedor: {self.nombre} (ID: {self.id}, User: {self.user_id})>"

    # ============================================
    # ✅ PROPIEDADES PARA ACCESO A DATOS DE USER
    # ============================================
    @property
    def email_actual(self):
        """
        Retorna el email actual (prioriza User sobre campo local)
        """
        if self.user:
            return self.user.email
        return self.email

    @property
    def celular_actual(self):
        """
        Retorna el celular actual (prioriza User sobre campo local)
        """
        if self.user:
            return self.user.celular
        return self.telefono

    @property
    def nombre_completo_usuario(self):
        """
        Retorna el nombre completo del usuario vinculado
        """
        if self.user:
            return self.user.get_full_name()
        return None

    @property
    def esta_sincronizado(self):
        """
        Verifica si los datos están sincronizados con User
        """
        if not self.user:
            return True  # No hay user, no hay desincronización

        email_sync = self.email == self.user.email
        telefono_sync = self.telefono == self.user.celular

        return email_sync and telefono_sync

    # ============================================
    # ✅ MÉTODOS HELPER
    # ============================================
    def esta_abierto(self):
        """
        Verifica si el proveedor está abierto en este momento
        """
        if not self.horario_apertura or not self.horario_cierre:
            return True  # Si no hay horarios definidos, siempre está abierto

        from datetime import datetime
        now = datetime.now().time()
        return self.horario_apertura <= now <= self.horario_cierre

    def get_nombre_usuario(self):
        """
        Obtiene el nombre del usuario vinculado
        """
        if self.user:
            return self.user.get_full_name()
        return "Sin usuario vinculado"

    def get_email_usuario(self):
        """
        Obtiene el email del usuario vinculado
        """
        if self.user:
            return self.user.email
        return self.email

    def get_celular_usuario(self):
        """
        Obtiene el celular del usuario vinculado
        """
        if self.user:
            return self.user.celular
        return self.telefono

    def sincronizar_con_user(self, campos=None):
        """
        ✅ Sincroniza datos manualmente desde User

        Args:
            campos (list): Lista de campos a sincronizar ['email', 'telefono']
                          Si es None, sincroniza todos
        """
        if not self.user:
            logger.warning(f"Proveedor {self.id} no tiene usuario vinculado")
            return False

        cambios = False

        if campos is None or 'email' in campos:
            if self.email != self.user.email:
                self.email = self.user.email
                cambios = True

        if campos is None or 'telefono' in campos:
            if self.telefono != self.user.celular:
                self.telefono = self.user.celular
                cambios = True

        if cambios:
            self.save(update_fields=['email', 'telefono'])
            logger.info(f"✅ Proveedor {self.id} sincronizado con User {self.user.id}")

        return cambios

    def verificar(self):
        """
        ✅ Verifica el proveedor y su usuario
        """
        self.verificado = True
        self.save(update_fields=['verificado'])

        if self.user and not self.user.verificado:
            self.user.verificado = True
            self.user.save(update_fields=['verificado'])
            logger.info(f"✅ Usuario {self.user.id} verificado al verificar proveedor {self.id}")

    def desverificar(self):
        """
        ✅ Quita verificación del proveedor y su usuario
        """
        self.verificado = False
        self.save(update_fields=['verificado'])

        if self.user and self.user.verificado:
            self.user.verificado = False
            self.user.save(update_fields=['verificado'])
            logger.info(f"⚠️ Usuario {self.user.id} desverificado al desverificar proveedor {self.id}")

    def soft_delete(self):
        """
        ✅ Eliminación suave (no borra, marca como eliminado)
        """
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.activo = False
        self.save(update_fields=['deleted_at', 'activo'])
        logger.warning(f"🗑️ Proveedor {self.id} marcado como eliminado")

    def restore(self):
        """
        ✅ Restaura un proveedor eliminado suavemente
        """
        self.deleted_at = None
        self.activo = True
        self.save(update_fields=['deleted_at', 'activo'])
        logger.info(f"♻️ Proveedor {self.id} restaurado")

    # ============================================
    # ✅ VALIDACIONES
    # ============================================
    def clean(self):
        """
        Validaciones antes de guardar
        """
        super().clean()

        # Validar RUC (13 dígitos)
        if self.ruc:
            if not self.ruc.isdigit():
                raise ValidationError({
                    'ruc': 'El RUC debe contener solo números'
                })
            if len(self.ruc) != 13:
                raise ValidationError({
                    'ruc': 'El RUC debe tener exactamente 13 dígitos'
                })

        # Validar horarios
        if self.horario_apertura and self.horario_cierre:
            if self.horario_apertura >= self.horario_cierre:
                raise ValidationError({
                    'horario_cierre': 'El horario de cierre debe ser posterior al de apertura'
                })

        # Validar comisión
        if self.comision_porcentaje < 0 or self.comision_porcentaje > 100:
            raise ValidationError({
                'comision_porcentaje': 'La comisión debe estar entre 0 y 100'
            })

    def save(self, *args, **kwargs):
        """
        ✅ Override save para sincronización automática
        """
        # Ejecutar validaciones
        self.full_clean()

        # ✅ Sincronización automática si hay usuario
        if self.user:
            # Solo sincronizar si los campos están vacíos o si se fuerza
            force_sync = kwargs.pop('force_sync', False)

            if force_sync or not self.email:
                self.email = self.user.email

            if force_sync or not self.telefono:
                self.telefono = self.user.celular

        super().save(*args, **kwargs)


# ============================================
# ✅ SIGNALS PARA SINCRONIZACIÓN AUTOMÁTICA
# ============================================

@receiver(pre_save, sender=Proveedor)
def proveedor_pre_save(sender, instance, **kwargs):
    """
    ✅ Signal antes de guardar Proveedor
    Sincroniza datos desde User si está vinculado
    """
    if instance.user:
        # Sincronizar email
        if instance.email != instance.user.email:
            old_email = instance.email
            instance.email = instance.user.email
            logger.debug(
                f"🔄 [PRE_SAVE] Email sincronizado: {old_email} → {instance.email}"
            )

        # Sincronizar teléfono
        if instance.telefono != instance.user.celular:
            old_telefono = instance.telefono
            instance.telefono = instance.user.celular
            logger.debug(
                f"🔄 [PRE_SAVE] Teléfono sincronizado: {old_telefono} → {instance.telefono}"
            )


@receiver(post_save, sender=Proveedor)
def proveedor_post_save(sender, instance, created, **kwargs):
    """
    ✅ Signal después de guardar Proveedor
    Logging y notificaciones
    """

    # ✅ PREVENIR RECURSIÓN
    if getattr(instance, '_syncing', False):
        return

    if kwargs.get('raw', False):
        return

    if created:
        logger.info(
            f"✅ [POST_SAVE] Proveedor creado: {instance.nombre} "
            f"(ID: {instance.id}, User: {instance.user_id})"
        )

        # Si tiene usuario, asegurar que esté verificado en ambos lados
        if instance.user and instance.verificado and not instance.user.verificado:
            try:
                # ✅ Marcar que estamos sincronizando para evitar loop
                instance.user._syncing = True
                instance.user.verificado = True
                instance.user.save(update_fields=['verificado'])

                logger.info(f"✅ Usuario {instance.user.id} verificado automáticamente")
            except Exception as e:
                logger.error(f"❌ Error verificando usuario {instance.user.id}: {e}")
            finally:
                # ✅ Limpiar flag
                instance.user._syncing = False
    else:
        logger.debug(
            f"🔄 [POST_SAVE] Proveedor actualizado: {instance.nombre} (ID: {instance.id})"
        )

@receiver(post_save, sender=User)
def user_post_save_sync_proveedor(sender, instance, created, **kwargs):
    """
    ✅ Signal cuando se actualiza User
    Sincroniza cambios al Proveedor vinculado

    PREVENCIÓN DE RECURSIÓN:
    - Usa update() para evitar disparar signals de Proveedor
    - Verifica flag _syncing para evitar loops
    - Solo procesa si update_fields está presente y relevante
    """

    # ✅ PREVENIR RECURSIÓN: Ignorar si venimos de una sincronización
    if getattr(instance, '_syncing', False):
        return

    # ✅ PREVENIR RECURSIÓN: Si es raw (fixtures, loaddata), ignorar
    if kwargs.get('raw', False):
        return

    # ✅ OPTIMIZACIÓN: Si update_fields está presente, verificar si son campos relevantes
    update_fields = kwargs.get('update_fields')
    if update_fields is not None:
        campos_relevantes = {'email', 'celular', 'verificado'}
        if not campos_relevantes.intersection(update_fields):
            # No se actualizó ningún campo relevante
            return

    # Solo si es proveedor y tiene proveedor vinculado
    if not instance.es_proveedor():
        return

    if not hasattr(instance, 'proveedor'):
        return

    try:
        proveedor = instance.proveedor
    except Proveedor.DoesNotExist:
        logger.warning(
            f"⚠️ [USER_SYNC] Usuario {instance.id} es PROVEEDOR pero no tiene proveedor vinculado"
        )
        return

    # Preparar campos a actualizar
    campos_actualizar = {}
    cambios_realizados = []

    # Sincronizar email
    if proveedor.email != instance.email:
        campos_actualizar['email'] = instance.email
        cambios_realizados.append(f"email: {proveedor.email} → {instance.email}")
        logger.debug(
            f"🔄 [USER_SYNC] Email de proveedor {proveedor.id} "
            f"sincronizado desde user {instance.id}"
        )

    # Sincronizar celular
    if proveedor.telefono != instance.celular:
        campos_actualizar['telefono'] = instance.celular
        cambios_realizados.append(f"teléfono: {proveedor.telefono} → {instance.celular}")
        logger.debug(
            f"🔄 [USER_SYNC] Teléfono de proveedor {proveedor.id} "
            f"sincronizado desde user {instance.id}"
        )

    # Sincronizar verificación
    if proveedor.verificado != instance.verificado:
        campos_actualizar['verificado'] = instance.verificado
        cambios_realizados.append(f"verificado: {proveedor.verificado} → {instance.verificado}")
        logger.info(
            f"🔄 [USER_SYNC] Verificación de proveedor {proveedor.id} "
            f"sincronizada: {instance.verificado}"
        )

    # ✅ Guardar cambios si hubo
    if campos_actualizar:
        try:
            # ✅ Usar update() para evitar disparar signals de Proveedor
            rows_updated = Proveedor.objects.filter(id=proveedor.id).update(
                **campos_actualizar
            )

            if rows_updated > 0:
                logger.info(
                    f"✅ [USER_SYNC] Proveedor {proveedor.id} sincronizado con User {instance.id}. "
                    f"Cambios: {', '.join(cambios_realizados)}"
                )
            else:
                logger.warning(
                    f"⚠️ [USER_SYNC] No se pudo actualizar proveedor {proveedor.id} "
                    f"(posiblemente fue eliminado)"
                )

        except Exception as e:
            logger.error(
                f"❌ [USER_SYNC] Error sincronizando proveedor {proveedor.id} "
                f"con User {instance.id}: {e}",
                exc_info=True
            )


# ============================================
# ✅ MANAGER PERSONALIZADO (OPCIONAL)
# ============================================

class ProveedorManager(models.Manager):
    """
    Manager personalizado para Proveedor
    """

    def activos(self):
        """Retorna solo proveedores activos"""
        return self.filter(activo=True, deleted_at__isnull=True)

    def verificados(self):
        """Retorna solo proveedores verificados"""
        return self.filter(verificado=True, deleted_at__isnull=True)

    def activos_y_verificados(self):
        """Retorna proveedores activos y verificados"""
        return self.filter(activo=True, verificado=True, deleted_at__isnull=True)

    def sin_usuario(self):
        """Retorna proveedores sin usuario vinculado"""
        return self.filter(user__isnull=True)

    def con_usuario(self):
        """Retorna proveedores con usuario vinculado"""
        return self.filter(user__isnull=False)

    def desincronizados(self):
        """
        ✅ Retorna proveedores con datos desincronizados
        """
        from django.db.models import Q
        return self.filter(
            user__isnull=False
        ).exclude(
            Q(email=models.F('user__email')) &
            Q(telefono=models.F('user__celular'))
        )
