# -*- coding: utf-8 -*-
# authentication/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from phonenumber_field.modelfields import PhoneNumberField
import re
import logging

logger = logging.getLogger('authentication')



class User(AbstractUser):
    """
    Modelo de usuario personalizado - Solo usuarios comunes
    """

    # ==========================================
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
    celular = PhoneNumberField(
        region='EC',  # Región por defecto si no ponen el +
        blank=True, 
        null=True,
        verbose_name='Número de celular',
        help_text='Formato internacional (ej: +593991234567 o +52...)'
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

    notificaciones_push = models.BooleanField(
        default=True,
        verbose_name='Notificaciones push',
        help_text='Notificaciones push en la aplicación móvil'
    )

    # ==========================================
    # RECUPERACIÓN DE CONTRASEÑA (SEGURA)
    # ==========================================
    reset_password_code = models.CharField(
        max_length=128,
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
        db_index=True
    )

    reset_password_attempts = models.IntegerField(
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

    # ==========================================
    # ESTADO DE CUENTA
    # ==========================================
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
            models.Index(fields=['cuenta_desactivada']),
            models.Index(fields=['reset_password_expire']),
        ]

    def __str__(self):
        return f"{self.email} - {self.get_full_name()}"

    # ==========================================
    # MÉTODOS DE VERIFICACIÓN Y VALIDACIÓN
    # ==========================================

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
        if self.cuenta_bloqueada_hasta:
            return timezone.now() < self.cuenta_bloqueada_hasta
        return False

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

    # ==========================================
    # MÉTODOS DE DESACTIVACIÓN DE CUENTA
    # ==========================================

    def desactivar_cuenta(self, razon=None):
        """Desactiva la cuenta del usuario"""
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

    # ==========================================
    # MÉTODOS DE SEGURIDAD - LOGIN
    # ==========================================

    def registrar_login_fallido(self):
        """Registra un intento de login fallido"""
        from django.conf import settings

        self.intentos_login_fallidos += 1

        # Solo bloquear cuenta si está habilitado (producción)
        if getattr(settings, 'ENABLE_LOGIN_BLOCKING', True):
            # Bloquear cuenta después de 5 intentos fallidos
            if self.intentos_login_fallidos >= 5:
                self.cuenta_bloqueada_hasta = timezone.now() + timedelta(minutes=15)
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

    # ==========================================
    # MÉTODOS DE VALIDACIÓN
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
    def validar_password(password):
        """Valida que la contraseña sea medianamente segura"""
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres')

        if not re.search(r'[a-zA-Z]', password):
            raise ValidationError('La contraseña debe contener al menos una letra')

        if not re.search(r'\d', password):
            raise ValidationError('La contraseña debe contener al menos un número')

        return True
    # ==========================================
    # ROLES Y GESTIÓN DE ACCESO
    # ==========================================
    class RolChoices(models.TextChoices):
        """Opciones de roles disponibles en el sistema"""
        USUARIO = 'USUARIO', 'Usuario Normal'
        PROVEEDOR = 'PROVEEDOR', 'Proveedor'
        REPARTIDOR = 'REPARTIDOR', 'Repartidor'
        ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'

    rol = models.CharField(
        max_length=20,
        choices=RolChoices.choices,
        default=RolChoices.USUARIO,
        verbose_name='Rol Principal',
        help_text='Rol principal del usuario',
        db_index=True
    )

    rol_activo = models.CharField(
        max_length=20,
        choices=RolChoices.choices,
        default=RolChoices.USUARIO,
        verbose_name='Rol Activo',
        help_text='Rol con el que está operando actualmente',
        db_index=True
    )

    roles_adicionales = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Roles Adicionales',
        help_text='Lista de roles adicionales activos (además del rol principal)'
    )

    verificado = models.BooleanField(
        default=False,
        verbose_name='Usuario Verificado',
        help_text='Si el usuario ha sido verificado por un administrador',
        db_index=True
    )

    # ==========================================
    # MÉTODOS PARA GESTIÓN DE ROLES
    # ==========================================
    
    def tiene_rol(self, rol):
        """
        Verifica si el usuario tiene un rol específico
        
        Args:
            rol (str): Rol a verificar (ej: 'PROVEEDOR')
        
        Returns:
            bool: True si tiene el rol
        """
        if self.rol == rol:
            return True
        return rol in self.roles_adicionales

    def obtener_todos_los_roles(self):
        """
        Retorna una lista de todos los roles que tiene el usuario
        
        Returns:
            list: Lista de roles activos
        """
        roles = [self.rol]
        if isinstance(self.roles_adicionales, list):
            roles.extend(self.roles_adicionales)
        return list(set(roles))  # Eliminar duplicados

    def puede_cambiar_rol_a(self, nuevo_rol):
        """
        Valida si el usuario puede cambiar a un rol específico
        
        Args:
            nuevo_rol (str): Nuevo rol
        
        Returns:
            tuple: (puede_cambiar: bool, razón: str)
        """
        # No puede cambiar a rol ADMINISTRADOR
        if nuevo_rol == self.RolChoices.ADMINISTRADOR:
            return (False, "No puedes cambiar a rol ADMINISTRADOR")
        
        # Debe estar verificado para cambiar de rol
        if not self.verificado:
            return (False, "Debes estar verificado para cambiar de rol")
        
        # Debe estar activo
        if not self.is_active:
            return (False, "Tu cuenta debe estar activa")
        
        # No debe estar desactivada por el usuario
        if self.cuenta_desactivada:
            return (False, "Tu cuenta está desactivada")
        
        return (True, "Puedes cambiar de rol")

    def cambiar_rol_activo(self, nuevo_rol):
        """
        Cambia el rol activo del usuario
        
        Args:
            nuevo_rol (str): Nuevo rol a activar
        
        Returns:
            dict: Resultado del cambio
        
        Raises:
            ValidationError: Si no puede cambiar
        """
        puede_cambiar, razon = self.puede_cambiar_rol_a(nuevo_rol)
        if not puede_cambiar:
            raise ValidationError(razon)
        
        # Verificar que el usuario tenga el rol
        if not self.tiene_rol(nuevo_rol):
            raise ValidationError(f"No tienes el rol {nuevo_rol}")
        
        rol_anterior = self.rol_activo
        self.rol_activo = nuevo_rol
        self.save(update_fields=['rol_activo', 'updated_at'])
        
        logger.info(
            f"✅ Rol activo cambiado para {self.email}: "
            f"{rol_anterior} → {nuevo_rol}"
        )
        
        return {
            'exitoso': True,
            'rol_anterior': rol_anterior,
            'rol_nuevo': nuevo_rol,
            'mensaje': f'Rol cambiado a {nuevo_rol}'
        }

    def agregar_rol(self, nuevo_rol):
        """
        Agrega un rol adicional al usuario
        
        Args:
            nuevo_rol (str): Rol a agregar
        
        Returns:
            bool: True si se agregó
        """
        if self.tiene_rol(nuevo_rol):
            return False  # Ya tiene ese rol
        
        if nuevo_rol == self.RolChoices.ADMINISTRADOR:
            raise ValidationError("No puedes agregar rol ADMINISTRADOR")
        
        if not isinstance(self.roles_adicionales, list):
            self.roles_adicionales = []
        
        self.roles_adicionales.append(nuevo_rol)
        self.save(update_fields=['roles_adicionales', 'updated_at'])
        
        logger.info(f"✅ Rol {nuevo_rol} agregado a {self.email}")
        return True

    def remover_rol(self, rol_a_remover):
        """
        Remueve un rol adicional del usuario
        
        Args:
            rol_a_remover (str): Rol a remover
        
        Returns:
            bool: True si se removió
        """
        if rol_a_remover == self.rol:
            raise ValidationError("No puedes remover tu rol principal")
        
        if not isinstance(self.roles_adicionales, list):
            self.roles_adicionales = []
        
        if rol_a_remover not in self.roles_adicionales:
            return False
        
        self.roles_adicionales.remove(rol_a_remover)
        
        # Si el rol removido era el activo, cambiar al principal
        if self.rol_activo == rol_a_remover:
            self.rol_activo = self.rol
        
        self.save(update_fields=['roles_adicionales', 'rol_activo', 'updated_at'])
        
        logger.info(f"✅ Rol {rol_a_remover} removido de {self.email}")
        return True

    def es_administrador(self):
        """Verifica si el usuario es administrador"""
        return self.rol == self.RolChoices.ADMINISTRADOR or self.is_superuser

    def es_proveedor(self):
        """Verifica si el usuario es proveedor"""
        return self.tiene_rol(self.RolChoices.PROVEEDOR)

    def es_repartidor(self):
        """Verifica si el usuario es repartidor"""
        return self.tiene_rol(self.RolChoices.REPARTIDOR)

    def es_usuario_normal(self):
        """Verifica si es solo usuario normal"""
        return (self.rol == self.RolChoices.USUARIO and 
                len(self.roles_adicionales) == 0)