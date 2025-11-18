# -*- coding: utf-8 -*-
# administradores/models.py
"""
Modelo de Administrador con perfil extendido y auditoría
✅ Perfil de administrador con permisos específicos
✅ Log de acciones administrativas
✅ Configuraciones del sistema
✅ Gestión de solicitudes de cambio de rol
"""

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from authentication.models import User
import uuid
import logging

logger = logging.getLogger("administradores")


# ============================================
# MODELO: PERFIL DE ADMINISTRADOR
# ============================================


class Administrador(models.Model):
    """
    Perfil extendido para usuarios administradores
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil_admin",
        verbose_name="Usuario",
    )

    # Información adicional
    cargo = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Cargo",
        help_text="Ej: Administrador General, Supervisor",
    )

    departamento = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Departamento",
        help_text="Ej: Operaciones, Finanzas",
    )

    # Permisos específicos
    puede_gestionar_usuarios = models.BooleanField(
        default=True, verbose_name="Puede gestionar usuarios"
    )

    puede_gestionar_pedidos = models.BooleanField(
        default=True, verbose_name="Puede gestionar pedidos"
    )

    puede_gestionar_proveedores = models.BooleanField(
        default=True, verbose_name="Puede gestionar proveedores"
    )

    puede_gestionar_repartidores = models.BooleanField(
        default=True, verbose_name="Puede gestionar repartidores"
    )

    puede_gestionar_rifas = models.BooleanField(
        default=True, verbose_name="Puede gestionar rifas"
    )

    puede_ver_reportes = models.BooleanField(
        default=True, verbose_name="Puede ver reportes"
    )

    puede_configurar_sistema = models.BooleanField(
        default=False,
        verbose_name="Puede configurar sistema",
        help_text="Solo super administradores",
    )

    puede_gestionar_solicitudes = models.BooleanField(
        default=True,
        verbose_name="Puede gestionar solicitudes",
        help_text="Puede aceptar/rechazar solicitudes de cambio de rol",
    )

    # Auditoría
    activo = models.BooleanField(
        default=True, verbose_name="Activo", help_text="Si el administrador está activo"
    )

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "administradores"
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"
        ordering = ["-creado_en"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["activo"]),
        ]

    def __str__(self):
        return f"Admin: {self.user.get_full_name()} - {self.cargo}"

    def clean(self):
        """Validaciones"""
        # Validar que el usuario sea administrador
        if self.user.rol != User.RolChoices.ADMINISTRADOR:
            raise ValidationError(
                {"user": "El usuario debe tener rol de ADMINISTRADOR"}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # ============================================
    # MÉTODOS DE PERMISOS
    # ============================================

    def tiene_permiso(self, permiso):
        """
        Verifica si tiene un permiso específico

        Args:
            permiso (str): Nombre del permiso

        Returns:
            bool: True si tiene el permiso
        """
        permisos_map = {
            "gestionar_usuarios": self.puede_gestionar_usuarios,
            "gestionar_pedidos": self.puede_gestionar_pedidos,
            "gestionar_proveedores": self.puede_gestionar_proveedores,
            "gestionar_repartidores": self.puede_gestionar_repartidores,
            "gestionar_rifas": self.puede_gestionar_rifas,
            "ver_reportes": self.puede_ver_reportes,
            "configurar_sistema": self.puede_configurar_sistema,
            "gestionar_solicitudes": self.puede_gestionar_solicitudes,
        }

        return permisos_map.get(permiso, False)

    @property
    def es_super_admin(self):
        """Verifica si es super administrador"""
        return self.user.is_superuser or self.puede_configurar_sistema

    @property
    def total_acciones(self):
        """Total de acciones registradas"""
        return self.acciones.count()


# ============================================
# MODELO: LOG DE ACCIONES ADMINISTRATIVAS
# ============================================


class AccionAdministrativa(models.Model):
    """
    Registro de todas las acciones realizadas por administradores
    """

    TIPO_ACCION_CHOICES = [
        # Usuarios
        ("crear_usuario", "Crear Usuario"),
        ("editar_usuario", "Editar Usuario"),
        ("desactivar_usuario", "Desactivar Usuario"),
        ("activar_usuario", "Activar Usuario"),
        ("cambiar_rol", "Cambiar Rol"),
        ("resetear_password", "Resetear Contraseña"),
        # Proveedores
        ("verificar_proveedor", "Verificar Proveedor"),
        ("rechazar_proveedor", "Rechazar Proveedor"),
        ("desactivar_proveedor", "Desactivar Proveedor"),
        # Repartidores
        ("verificar_repartidor", "Verificar Repartidor"),
        ("rechazar_repartidor", "Rechazar Repartidor"),
        ("desactivar_repartidor", "Desactivar Repartidor"),
        # Pedidos
        ("cancelar_pedido", "Cancelar Pedido"),
        ("reasignar_pedido", "Reasignar Pedido"),
        ("editar_pedido", "Editar Pedido"),
        # Rifas
        ("crear_rifa", "Crear Rifa"),
        ("realizar_sorteo", "Realizar Sorteo"),
        ("cancelar_rifa", "Cancelar Rifa"),
        # Solicitudes de Cambio de Rol
        ("aceptar_solicitud_rol", "Aceptar Solicitud de Rol"),
        ("rechazar_solicitud_rol", "Rechazar Solicitud de Rol"),
        # Sistema
        ("configurar_sistema", "Configurar Sistema"),
        ("notificacion_masiva", "Notificación Masiva"),
        ("exportar_datos", "Exportar Datos"),
        # Cambios de Rol
        ("revertir_cambio_rol", "Revertir Cambio de Rol"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    administrador = models.ForeignKey(
        Administrador,
        on_delete=models.SET_NULL,
        null=True,
        related_name="acciones",
        verbose_name="Administrador",
    )

    tipo_accion = models.CharField(
        max_length=50,
        choices=TIPO_ACCION_CHOICES,
        verbose_name="Tipo de Acción",
        db_index=True,
    )

    descripcion = models.TextField(
        verbose_name="Descripción", help_text="Descripción detallada de la acción"
    )

    # Datos de la acción
    modelo_afectado = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Modelo Afectado",
        help_text="Ej: User, Pedido, Proveedor",
    )

    objeto_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="ID del Objeto",
        help_text="ID del objeto afectado",
    )

    datos_anteriores = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Datos Anteriores",
        help_text="Estado anterior del objeto (opcional)",
    )

    datos_nuevos = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Datos Nuevos",
        help_text="Nuevo estado del objeto (opcional)",
    )

    # Metadatos
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name="Dirección IP"
    )

    user_agent = models.TextField(blank=True, verbose_name="User Agent")

    exitosa = models.BooleanField(default=True, verbose_name="Acción Exitosa")

    mensaje_error = models.TextField(
        blank=True, verbose_name="Mensaje de Error", help_text="Si la acción falló"
    )

    # Auditoría
    fecha_accion = models.DateTimeField(
        default=timezone.now, verbose_name="Fecha de la Acción", db_index=True
    )

    class Meta:
        db_table = "acciones_administrativas"
        verbose_name = "Acción Administrativa"
        verbose_name_plural = "Acciones Administrativas"
        ordering = ["-fecha_accion"]
        indexes = [
            models.Index(fields=["administrador", "-fecha_accion"]),
            models.Index(fields=["tipo_accion", "-fecha_accion"]),
            models.Index(fields=["modelo_afectado", "objeto_id"]),
            models.Index(fields=["-fecha_accion"]),
        ]

    def __str__(self):
        admin_nombre = (
            self.administrador.user.get_full_name()
            if self.administrador
            else "Admin eliminado"
        )
        return f"{admin_nombre} - {self.get_tipo_accion_display()} - {self.fecha_accion.strftime('%Y-%m-%d %H:%M')}"

    @classmethod
    def registrar_accion(cls, administrador, tipo_accion, descripcion, **kwargs):
        """
        Método helper para registrar acciones

        Args:
            administrador: Instancia de Administrador
            tipo_accion: Tipo de acción (choice)
            descripcion: Descripción de la acción
            **kwargs: Campos adicionales

        Returns:
            AccionAdministrativa: Instancia creada
        """
        try:
            accion = cls.objects.create(
                administrador=administrador,
                tipo_accion=tipo_accion,
                descripcion=descripcion,
                modelo_afectado=kwargs.get("modelo_afectado", ""),
                objeto_id=kwargs.get("objeto_id", ""),
                datos_anteriores=kwargs.get("datos_anteriores", {}),
                datos_nuevos=kwargs.get("datos_nuevos", {}),
                ip_address=kwargs.get("ip_address"),
                user_agent=kwargs.get("user_agent", ""),
                exitosa=kwargs.get("exitosa", True),
                mensaje_error=kwargs.get("mensaje_error", ""),
            )

            logger.info(
                f"✅ Acción registrada: {administrador.user.email} - "
                f"{tipo_accion} - {descripcion}"
            )

            return accion

        except Exception as e:
            logger.error(f"❌ Error registrando acción administrativa: {e}")
            return None

    @property
    def resumen(self):
        """Resumen corto de la acción"""
        return f"{self.get_tipo_accion_display()}: {self.descripcion[:50]}"


# ============================================
# MODELO: CONFIGURACIÓN DEL SISTEMA
# ============================================


class ConfiguracionSistema(models.Model):
    """
    Configuraciones globales del sistema
    Solo accesible por super administradores
    """

    # Comisiones
    comision_app_proveedor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        verbose_name="Comisión App - Pedidos Proveedor (%)",
        help_text="Porcentaje que se lleva la app de pedidos de proveedor",
    )

    comision_app_directo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15.00,
        verbose_name="Comisión App - Encargos Directos (%)",
        help_text="Porcentaje que se lleva la app de encargos directos",
    )

    comision_repartidor_proveedor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=25.00,
        verbose_name="Comisión Repartidor - Pedidos Proveedor (%)",
    )

    comision_repartidor_directo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=85.00,
        verbose_name="Comisión Repartidor - Encargos Directos (%)",
    )

    # Rifas
    pedidos_minimos_rifa = models.PositiveIntegerField(
        default=3,
        verbose_name="Pedidos Mínimos para Rifa",
        help_text="Cantidad mínima de pedidos para participar en rifa",
    )

    # Límites
    pedido_maximo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1000.00,
        verbose_name="Monto Máximo por Pedido",
        help_text="Monto máximo permitido por pedido",
    )

    pedido_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=5.00,
        verbose_name="Monto Mínimo por Pedido",
    )

    # Tiempos
    tiempo_maximo_entrega = models.PositiveIntegerField(
        default=60,
        verbose_name="Tiempo Máximo de Entrega (minutos)",
        help_text="Tiempo límite para marcar un pedido como retrasado",
    )

    # Contacto
    telefono_soporte = models.CharField(
        max_length=15, blank=True, verbose_name="Teléfono de Soporte"
    )

    email_soporte = models.EmailField(blank=True, verbose_name="Email de Soporte")

    # Estado
    mantenimiento = models.BooleanField(
        default=False,
        verbose_name="Modo Mantenimiento",
        help_text="Si está activado, solo admins pueden acceder",
    )

    mensaje_mantenimiento = models.TextField(
        blank=True, verbose_name="Mensaje de Mantenimiento"
    )

    # Auditoría
    modificado_por = models.ForeignKey(
        Administrador,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Modificado Por",
    )

    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "configuracion_sistema"
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"

    def __str__(self):
        return f"Configuración del Sistema (actualizado: {self.actualizado_en.strftime('%Y-%m-%d %H:%M')})"

    def save(self, *args, **kwargs):
        # Solo permitir una instancia
        if not self.pk and ConfiguracionSistema.objects.exists():
            raise ValidationError("Solo puede existir una configuración del sistema")

        super().save(*args, **kwargs)

    @classmethod
    def obtener(cls):
        """Obtiene la configuración del sistema (singleton)"""
        config, created = cls.objects.get_or_create(pk=1)

        if created:
            logger.info("✅ Configuración del sistema creada con valores por defecto")

        return config

    @property
    def esta_en_mantenimiento(self):
        """Verifica si el sistema está en mantenimiento"""
        return self.mantenimiento
