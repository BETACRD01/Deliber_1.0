# -*- coding: utf-8 -*-
# authentication/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from allauth.socialaccount.models import SocialAccount
from datetime import date
import re
import logging

logger = logging.getLogger('authentication')


class User(AbstractUser):
    """
    Modelo de usuario personalizado con sistema de roles
    """

    # ==========================================
    # ROLES DEL SISTEMA
    # ==========================================
    class RolChoices(models.TextChoices):
        USUARIO = 'USUARIO', 'Usuario'
        REPARTIDOR = 'REPARTIDOR', 'Repartidor'
        PROVEEDOR = 'PROVEEDOR', 'Proveedor'
        ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'

    rol = models.CharField(
        max_length=20,
        choices=RolChoices.choices,
        default=RolChoices.USUARIO,
        verbose_name='Rol del usuario',
        help_text='Define los permisos y accesos del usuario'
    )

    # =================================class Repartidor(TimeStampedModel)========
    # CAMPOS BÁSICOS DE USUARIO
    # ==========================================
    first_name = models.CharField(
        max_length=150,
        verbose_name='Nombre',
        help_text='Nombre del usuario'
    )

    last_name = models.CharField(
        max_length=150,
        verbose_name='Apellido',
        help_text='Apellido del usuario'
    )

    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Usuario',
        help_text='Nombre de usuario único',
        error_messages={
            'unique': 'Este nombre de usuario ya está en uso.',
        }
    )

    # ==========================================
    # EMAIL (CAMPO PRINCIPAL PARA LOGIN)
    # ==========================================
    email = models.EmailField(
        unique=True,
        verbose_name='Correo electrónico',
        help_text='Email único para login',
        error_messages={
            'unique': 'Este correo electrónico ya está registrado.',
        }
    )

    # ==========================================
    # CELULAR
    # ==========================================
    celular = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^09\d{8}$',
                message='El celular debe comenzar con 09 y tener 10 dígitos'
            )
        ],
        verbose_name='Número de celular',
        help_text='Formato: 09XXXXXXXX (Ecuador)'
    )

    # ==========================================
    # CAMPOS OPCIONALES
    # ==========================================
    fecha_nacimiento = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha de nacimiento',
        help_text='Opcional: Fecha de nacimiento del usuario'
    )

    # ==========================================
    # TÉRMINOS Y CONDICIONES
    # ==========================================
    terminos_aceptados = models.BooleanField(
        default=False,
        verbose_name='Términos y condiciones',
        help_text='Usuario acepta términos y condiciones'
    )

    terminos_fecha_aceptacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de aceptación de términos',
        help_text='Fecha y hora cuando el usuario aceptó los términos'
    )

    terminos_version_aceptada = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        default='1.0',
        verbose_name='Versión de términos aceptada',
        help_text='Versión de los términos y condiciones aceptados'
    )

    terminos_ip_aceptacion = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='IP de aceptación',
        help_text='Dirección IP desde donde se aceptaron los términos'
    )

    # ==========================================
    # PREFERENCIAS DE NOTIFICACIONES
    # ==========================================
    notificaciones_email = models.BooleanField(
        default=True,
        verbose_name='Recibir notificaciones por email',
        help_text='Si está desactivado, no recibirá correos de la plataforma'
    )

    notificaciones_marketing = models.BooleanField(
        default=True,
        verbose_name='Recibir emails de marketing',
        help_text='Promociones, ofertas especiales y novedades'
    )

    notificaciones_pedidos = models.BooleanField(
        default=True,
        verbose_name='Notificaciones de pedidos',
        help_text='Actualizaciones sobre el estado de pedidos'
    )

    notificaciones_push = models.BooleanField(
        default=True,
        verbose_name='Notificaciones push',
        help_text='Notificaciones push en la aplicación móvil'
    )

    # ==========================================
    # AUTENTICACIÓN CON GOOGLE (django-allauth)
    # ==========================================
    google_picture = models.URLField(
        blank=True,
        null=True,
        verbose_name='Foto de Google',
        help_text='URL de la foto de perfil de Google'
    )

    # ==========================================
    # CAMPOS ESPECÍFICOS PARA REPARTIDORES
    # ==========================================
    vehiculo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Vehículo',
        help_text='Tipo de vehículo del repartidor'
    )

    placa_vehiculo = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{3}-\d{3,4}$',
                message='Formato de placa inválido. Use: ABC-1234 o ABC-123'
            )
        ],
        verbose_name='Placa del vehículo',
        help_text='Placa del vehículo (formato ecuatoriano: ABC-1234)'
    )

    licencia_conducir = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Licencia de conducir',
        help_text='Número de licencia de conducir'
    )

    disponible = models.BooleanField(
        default=True,
        verbose_name='Disponible',
        help_text='Indica si el repartidor está disponible'
    )

    # ==========================================
    # CAMPOS ESPECÍFICOS PARA PROVEEDORES
    # ==========================================
    nombre_negocio = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Nombre del negocio',
        help_text='Nombre comercial del proveedor'
    )

    ruc = models.CharField(
        max_length=13,
        blank=True,
        null=True,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{13}$',
                message='El RUC debe tener exactamente 13 dígitos'
            )
        ],
        verbose_name='RUC',
        help_text='Registro Único de Contribuyentes (13 dígitos)'
    )

    direccion_negocio = models.TextField(
        blank=True,
        null=True,
        verbose_name='Dirección del negocio',
        help_text='Dirección física del negocio'
    )

    categoria_negocio = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Categoría del negocio',
        help_text='Tipo de productos/servicios que ofrece'
    )

    verificado = models.BooleanField(
        default=False,
        verbose_name='Verificado',
        help_text='Indica si el proveedor ha sido verificado por el admin'
    )

    # ==========================================
    # ✅ RECUPERACIÓN DE CONTRASEÑA CON CÓDIGO (ACTUALIZADO - SEGURO)
    # ==========================================
    reset_password_code = models.CharField(
        max_length=128,  # ✅ CAMBIADO: Para almacenar hash (antes era 6)
        blank=True,
        null=True,
        verbose_name='Código de recuperación (hasheado)',
        help_text='Hash del código de 6 dígitos para resetear contraseña'
    )

    reset_password_expire = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Expiración del código',
        help_text='Fecha límite para usar el código (15 minutos)',
        db_index=True  # ✅ AGREGADO: Índice para búsquedas rápidas
    )

    reset_password_attempts = models.IntegerField(  # ✅ NUEVO CAMPO
        default=0,
        verbose_name='Intentos de verificación del código',
        help_text='Contador de intentos fallidos al verificar código de recuperación'
    )

    # ==========================================
    # AUDITORÍA Y TIMESTAMPS
    # ==========================================
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    cuenta_desactivada = models.BooleanField(
        default=False,
        verbose_name='Cuenta desactivada',
        help_text='Usuario desactivó su cuenta voluntariamente'
    )

    fecha_desactivacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de desactivación',
        help_text='Fecha cuando el usuario desactivó su cuenta'
    )

    razon_desactivacion = models.TextField(
        blank=True,
        null=True,
        verbose_name='Razón de desactivación',
        help_text='Motivo por el cual el usuario desactivó su cuenta'
    )

    # ==========================================
    # SEGURIDAD Y LOGS
    # ==========================================
    intentos_login_fallidos = models.IntegerField(
        default=0,
        verbose_name='Intentos de login fallidos',
        help_text='Contador de intentos fallidos de inicio de sesión'
    )

    cuenta_bloqueada_hasta = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Cuenta bloqueada hasta',
        help_text='Fecha hasta la cual la cuenta está temporalmente bloqueada'
    )

    ultimo_login_ip = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='IP del último login',
        help_text='Dirección IP del último inicio de sesión exitoso'
    )

    # ==========================================
    # CONFIGURACIÓN DEL MODELO
    # ==========================================
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'celular']

    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['celular']),
            models.Index(fields=['rol']),
            models.Index(fields=['cuenta_desactivada']),
            models.Index(fields=['ruc']),
            models.Index(fields=['verificado', 'rol']),
            models.Index(fields=['disponible', 'rol']),
            # ✅ NOTA: reset_password_expire ya tiene db_index=True en el campo,
            # no hace falta agregarlo aquí también
        ]

    def __str__(self):
        return f"{self.email} - {self.get_full_name()} ({self.get_rol_display()})"

    # ==========================================
    # MÉTODOS PARA VERIFICAR ROLES
    # ==========================================
    def es_usuario(self):
        """Verifica si es un usuario regular"""
        return self.rol == self.RolChoices.USUARIO

    def es_repartidor(self):
        """Verifica si es repartidor"""
        return self.rol == self.RolChoices.REPARTIDOR

    def es_proveedor(self):
        """Verifica si es proveedor"""
        return self.rol == self.RolChoices.PROVEEDOR

    def es_administrador(self):
        """Verifica si es administrador"""
        return self.rol == self.RolChoices.ADMINISTRADOR or self.is_superuser

    def puede_crear_rifas(self):
        """Solo administradores pueden crear rifas"""
        return self.es_administrador()

    def puede_gestionar_usuarios(self):
        """Solo administradores pueden gestionar usuarios"""
        return self.es_administrador()

    def puede_verificar_proveedores(self):
        """Solo administradores pueden verificar proveedores"""
        return self.es_administrador()

    def puede_recibir_emails(self):
        """Verifica si el usuario puede recibir emails"""
        return (
            self.is_active and
            not self.cuenta_desactivada and
            self.notificaciones_email
        )

    def puede_recibir_marketing(self):
        """Verifica si el usuario acepta emails de marketing"""
        return self.puede_recibir_emails() and self.notificaciones_marketing

    def esta_bloqueado(self):
        """Verifica si la cuenta está temporalmente bloqueada"""
        from django.utils import timezone
        if self.cuenta_bloqueada_hasta:
            return timezone.now() < self.cuenta_bloqueada_hasta
        return False

    # ==========================================
    # VALIDACIONES PERSONALIZADAS
    # ==========================================
    def clean(self):
        """Validaciones antes de guardar"""
        super().clean()

        # Validar edad mayor de 18 años (si se proporciona)
        if self.fecha_nacimiento:
            edad = self.get_edad()
            if edad and edad < 18:
                raise ValidationError({
                    'fecha_nacimiento': 'Debes ser mayor de 18 años para registrarte'
                })

        # Validar campos requeridos para repartidores
        if self.rol == self.RolChoices.REPARTIDOR:
            if not self.vehiculo:
                raise ValidationError({
                    'vehiculo': 'El vehículo es requerido para repartidores'
                })
            if not self.licencia_conducir:
                raise ValidationError({
                    'licencia_conducir': 'La licencia de conducir es requerida para repartidores'
                })

        # Validar campos requeridos para proveedores
        if self.rol == self.RolChoices.PROVEEDOR:
            if not self.nombre_negocio:
                raise ValidationError({
                    'nombre_negocio': 'El nombre del negocio es requerido para proveedores'
                })
            if not self.ruc:
                raise ValidationError({
                    'ruc': 'El RUC es requerido para proveedores'
                })

            # Validar RUC ecuatoriano
            if self.ruc:
                self._validar_ruc_interno(self.ruc)

    def _validar_ruc_interno(self, ruc):
        """Validación interna del RUC"""
        if len(ruc) != 13:
            raise ValidationError('El RUC debe tener exactamente 13 dígitos')

        if not ruc.isdigit():
            raise ValidationError('El RUC debe contener solo números')

        provincia = int(ruc[:2])
        if provincia < 1 or provincia > 24:
            raise ValidationError('Código de provincia inválido en el RUC')

        tercero = int(ruc[2])
        if tercero < 0 or tercero > 9:
            raise ValidationError('Tercer dígito del RUC inválido')

        return True

    # ==========================================
    # MÉTODOS PERSONALIZADOS
    # ==========================================
    def es_autenticacion_google(self):
        """Verifica si el usuario usa Google para login"""
        return SocialAccount.objects.filter(user=self, provider='google').exists()

    def get_edad(self):
        """Calcula la edad del usuario"""
        if not self.fecha_nacimiento:
            return None

        today = date.today()
        edad = today.year - self.fecha_nacimiento.year

        if today.month < self.fecha_nacimiento.month or \
           (today.month == self.fecha_nacimiento.month and today.day < self.fecha_nacimiento.day):
            edad -= 1

        return edad

    def desactivar_cuenta(self, razon=None):
        """Desactiva la cuenta del usuario"""
        from django.utils import timezone
        self.cuenta_desactivada = True
        self.fecha_desactivacion = timezone.now()
        if razon:
            self.razon_desactivacion = razon
        self.notificaciones_email = False
        self.notificaciones_marketing = False
        self.save()

        logger.info(f"Cuenta desactivada: {self.email} - Razón: {razon}")

    def reactivar_cuenta(self):
        """Reactiva la cuenta del usuario"""
        self.cuenta_desactivada = False
        self.fecha_desactivacion = None
        self.razon_desactivacion = None
        self.notificaciones_email = True
        self.save()

        logger.info(f"Cuenta reactivada: {self.email}")

    def registrar_login_fallido(self):
        """Registra un intento de login fallido"""
        from django.utils import timezone
        from django.conf import settings

        self.intentos_login_fallidos += 1

        # Solo bloquear cuenta si está habilitado (producción)
        if getattr(settings, 'ENABLE_LOGIN_BLOCKING', True):
            # Bloquear cuenta después de 5 intentos fallidos
            if self.intentos_login_fallidos >= 5:
                self.cuenta_bloqueada_hasta = timezone.now() + timezone.timedelta(minutes=15)
                logger.warning(
                    f"Cuenta bloqueada por múltiples intentos fallidos: {self.email} "
                    f"({self.intentos_login_fallidos} intentos)"
                )

        self.save(update_fields=['intentos_login_fallidos', 'cuenta_bloqueada_hasta'])

        logger.debug(
            f"Login fallido registrado para {self.email}: "
            f"{self.intentos_login_fallidos} intentos"
        )

    def registrar_login_exitoso(self, ip_address=None):
        """Registra un login exitoso y resetea contadores"""
        self.intentos_login_fallidos = 0
        self.cuenta_bloqueada_hasta = None
        if ip_address:
            self.ultimo_login_ip = ip_address
        self.save(update_fields=['intentos_login_fallidos', 'cuenta_bloqueada_hasta', 'ultimo_login_ip'])

        logger.info(f"Login exitoso: {self.email} desde IP {ip_address}")

    def save(self, *args, **kwargs):
        """Override save para limpiar espacios en blanco"""
        if self.first_name:
            self.first_name = self.first_name.strip()
        if self.last_name:
            self.last_name = self.last_name.strip()
        if self.username:
            self.username = self.username.strip().lower()
        if self.email:
            self.email = self.email.strip().lower()

        super().save(*args, **kwargs)

    # ==========================================
    # MÉTODOS ESTÁTICOS
    # ==========================================
    @staticmethod
    def validar_ruc_ecuatoriano(ruc):
        """Valida que el RUC sea válido según algoritmo ecuatoriano"""
        if len(ruc) != 13:
            raise ValidationError('El RUC debe tener exactamente 13 dígitos')

        if not ruc.isdigit():
            raise ValidationError('El RUC debe contener solo números')

        provincia = int(ruc[:2])
        if provincia < 1 or provincia > 24:
            raise ValidationError('Código de provincia inválido en el RUC')

        tercero = int(ruc[2])
        if tercero < 0 or tercero > 9:
            raise ValidationError('Tercer dígito del RUC inválido')

        return True

    @staticmethod
    def validar_password(password):
        """Valida que la contraseña sea medianamente segura"""
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres')

        if not re.search(r'[a-zA-Z]', password):
            raise ValidationError('La contraseña debe contener al menos una letra')

        if not re.search(r'\d', password):
            raise ValidationError('La contraseña debe contener al menos un número')

        return True
