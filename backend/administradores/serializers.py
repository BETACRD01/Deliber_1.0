# -*- coding: utf-8 -*-
# administradores/serializers.py
"""
Serializers para gestión administrativa
✅ Serializers de usuarios, proveedores y repartidores
✅ Serializers de logs y configuración del sistema
✅ Validaciones de permisos y seguridad
"""

from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
import logging

from authentication.models import User
from usuarios.models import Perfil
from proveedores.models import Proveedor
from repartidores.models import Repartidor
from .models import Administrador, AccionAdministrativa, ConfiguracionSistema

logger = logging.getLogger('administradores')


# ============================================
# SERIALIZER: ADMINISTRADOR
# ============================================

class AdministradorSerializer(serializers.ModelSerializer):
    """
    Serializer para perfil de administrador
    Retorna información del admin y sus permisos
    """
    usuario_email = serializers.CharField(source='user.email', read_only=True)
    usuario_nombre = serializers.CharField(source='user.get_full_name', read_only=True)
    es_super_admin = serializers.BooleanField(read_only=True)
    total_acciones = serializers.IntegerField(read_only=True)

    class Meta:
        model = Administrador
        fields = [
            'id', 'usuario_email', 'usuario_nombre', 'cargo', 'departamento',
            # Permisos
            'puede_gestionar_usuarios', 'puede_gestionar_pedidos',
            'puede_gestionar_proveedores', 'puede_gestionar_repartidores',
            'puede_gestionar_rifas', 'puede_ver_reportes', 'puede_configurar_sistema',
            # Estado
            'activo', 'es_super_admin', 'total_acciones',
            'creado_en', 'actualizado_en'
        ]
        read_only_fields = [
            'id', 'usuario_email', 'usuario_nombre', 'es_super_admin',
            'total_acciones', 'creado_en', 'actualizado_en'
        ]


# ============================================
# SERIALIZER: USUARIO - LISTAR
# ============================================

class UsuarioListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar usuarios (vista simplificada)
    Usado en listados y búsquedas
    """
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    edad = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'celular', 'rol', 'rol_display', 'edad',
            'is_active', 'cuenta_desactivada', 'verificado', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'rol_display']

    def get_edad(self, obj):
        """Calcula la edad del usuario"""
        return obj.get_edad() if hasattr(obj, 'get_edad') else None


# ============================================
# SERIALIZER: USUARIO - DETALLE
# ============================================

class UsuarioDetalleSerializer(serializers.ModelSerializer):
    """
    Serializer para detalle completo de usuario
    Incluye toda la información personal y de seguridad
    """
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    edad = serializers.SerializerMethodField()
    perfil = serializers.SerializerMethodField()
    intentos_login_fallidos = serializers.IntegerField(read_only=True)
    cuenta_bloqueada = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'celular', 'fecha_nacimiento', 'edad',
            'rol', 'rol_display',
            # Términos
            'terminos_aceptados', 'terminos_fecha_aceptacion',
            # Notificaciones
            'notificaciones_email', 'notificaciones_marketing', 'notificaciones_push',
            # Estado
            'is_active', 'cuenta_desactivada', 'verificado',
            'intentos_login_fallidos', 'cuenta_bloqueada',
            # Auditoría
            'created_at', 'updated_at', 'perfil'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'rol_display', 'edad',
            'intentos_login_fallidos', 'cuenta_bloqueada', 'perfil'
        ]

    def get_edad(self, obj):
        """Calcula la edad del usuario"""
        return obj.get_edad() if hasattr(obj, 'get_edad') else None

    def get_perfil(self, obj):
        """Información del perfil de usuario si existe"""
        try:
            perfil = obj.perfil_usuario
            return {
                'id': perfil.id,
                'total_pedidos': perfil.total_pedidos,
                'calificacion_promedio': float(perfil.calificacion_promedio) if perfil.calificacion_promedio else 0
            }
        except:
            return None

    def get_cuenta_bloqueada(self, obj):
        """Verifica si la cuenta está bloqueada"""
        return obj.esta_bloqueado() if hasattr(obj, 'esta_bloqueado') else False


# ============================================
# SERIALIZER: USUARIO - EDITAR
# ============================================

class UsuarioEditarSerializer(serializers.ModelSerializer):
    """
    Serializer para editar información de usuario por admin
    Permite cambiar datos personales y preferencias
    """
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'celular', 'fecha_nacimiento',
            'notificaciones_email', 'notificaciones_marketing', 'notificaciones_push',
            'verificado'
        ]

    def validate_celular(self, value):
        """Validar que el celular sea único (excepto el del usuario actual)"""
        user = self.instance
        if User.objects.filter(celular=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Este número de celular ya está registrado")
        return value


# ============================================
# SERIALIZER: CAMBIAR ROL
# ============================================

class CambiarRolSerializer(serializers.Serializer):
    """
    Serializer para cambiar el rol de un usuario
    """
    nuevo_rol = serializers.ChoiceField(
        choices=User.RolChoices.choices,
        label="Nuevo rol"
    )
    motivo = serializers.CharField(
        required=False,
        allow_blank=True,
        label="Motivo del cambio"
    )

    def validate(self, data):
        """Validaciones combinadas"""
        usuario = self.context.get('usuario')
        nuevo_rol = data.get('nuevo_rol')

        if not usuario:
            raise serializers.ValidationError("Usuario no especificado")

        # No permitir cambiar a ADMINISTRADOR directamente desde aquí
        if nuevo_rol == User.RolChoices.ADMINISTRADOR:
            raise serializers.ValidationError(
                "No se puede cambiar directamente a ADMINISTRADOR. "
                "Usar proceso de creación de admin."
            )

        return data


# ============================================
# SERIALIZER: DESACTIVAR USUARIO
# ============================================

class DesactivarUsuarioSerializer(serializers.Serializer):
    """
    Serializer para desactivar un usuario
    """
    razon = serializers.CharField(
        max_length=500,
        label="Razón de desactivación"
    )
    permanente = serializers.BooleanField(
        default=False,
        label="¿Desactivación permanente?"
    )


# ============================================
# SERIALIZER: RESETEAR PASSWORD
# ============================================

class ResetearPasswordSerializer(serializers.Serializer):
    """
    Serializer para resetear contraseña de usuario por admin
    """
    nueva_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label="Nueva contraseña"
    )
    confirmar_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label="Confirmar contraseña"
    )

    def validate(self, data):
        """Validaciones combinadas"""
        if data['nueva_password'] != data['confirmar_password']:
            raise serializers.ValidationError({
                "confirmar_password": "Las contraseñas no coinciden"
            })

        # Validar que sea segura
        try:
            User.validar_password(data['nueva_password'])
        except Exception as e:
            raise serializers.ValidationError({
                "nueva_password": str(e)
            })

        return data


# ============================================
# SERIALIZER: PROVEEDOR - LISTAR
# ============================================

class ProveedorListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar proveedores (vista simplificada)
    """
    usuario_email = serializers.CharField(source='user.email', read_only=True)
    usuario_nombre = serializers.CharField(source='user.get_full_name', read_only=True)
    estado_display = serializers.SerializerMethodField()

    class Meta:
        model = Proveedor
        fields = [
            'id', 'usuario_email', 'usuario_nombre', 'nombre',
            'tipo_proveedor', 'verificado', 'activo',
            'calificacion_promedio', 'total_ventas',
            'creado_en'
        ]
        read_only_fields = ['id', 'creado_en']

    def get_estado_display(self, obj):
        """Estado descriptivo del proveedor"""
        if not obj.activo:
            return 'Desactivado'
        elif not obj.verificado:
            return 'Pendiente de verificación'
        return 'Activo'


# ============================================
# SERIALIZER: PROVEEDOR - DETALLE
# ============================================

class ProveedorDetalleSerializer(serializers.ModelSerializer):
    """
    Serializer para detalle completo de proveedor
    """
    usuario_email = serializers.CharField(source='user.email', read_only=True)
    usuario_nombre = serializers.CharField(source='user.get_full_name', read_only=True)
    usuario_celular = serializers.CharField(source='user.celular', read_only=True)

    class Meta:
        model = Proveedor
        fields = [
            'id', 'usuario_email', 'usuario_nombre', 'usuario_celular',
            'nombre', 'descripcion', 'tipo_proveedor',
            'telefono', 'direccion', 'ciudad',
            'documento_identidad', 'numero_documento',
            'documento_verificacion',
            'verificado', 'activo',
            'calificacion_promedio', 'total_ventas', 'total_pedidos',
            'comision_app', 'cuenta_bancaria',
            'creado_en', 'actualizado_en'
        ]
        read_only_fields = [
            'id', 'creado_en', 'actualizado_en',
            'calificacion_promedio', 'total_ventas', 'total_pedidos'
        ]


# ============================================
# SERIALIZER: VERIFICAR PROVEEDOR
# ============================================

class VerificarProveedorSerializer(serializers.Serializer):
    """
    Serializer para verificar o rechazar un proveedor
    """
    verificado = serializers.BooleanField(
        label="¿Verificar proveedor?"
    )
    motivo = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        label="Motivo de decisión"
    )


# ============================================
# SERIALIZER: REPARTIDOR - LISTAR
# ============================================

class RepartidorListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar repartidores (vista simplificada)
    """
    usuario_email = serializers.CharField(source='user.email', read_only=True)
    usuario_nombre = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Repartidor
        fields = [
            'id', 'usuario_email', 'usuario_nombre',
            'estado', 'verificado', 'activo',
            'entregas_completadas', 'calificacion_promedio',
            'ganancias_totales', 'creado_en'
        ]
        read_only_fields = ['id', 'creado_en']


# ============================================
# SERIALIZER: REPARTIDOR - DETALLE
# ============================================

class RepartidorDetalleSerializer(serializers.ModelSerializer):
    """
    Serializer para detalle completo de repartidor
    """
    usuario_email = serializers.CharField(source='user.email', read_only=True)
    usuario_nombre = serializers.CharField(source='user.get_full_name', read_only=True)
    usuario_celular = serializers.CharField(source='user.celular', read_only=True)
    usuario_fecha_nacimiento = serializers.CharField(source='user.fecha_nacimiento', read_only=True)

    class Meta:
        model = Repartidor
        fields = [
            'id', 'usuario_email', 'usuario_nombre', 'usuario_celular',
            'usuario_fecha_nacimiento',
            'cedula', 'tipo_documento',
            'placa_vehiculo', 'tipo_vehiculo',
            'foto_cedula', 'foto_vehiculo', 'documento_verificacion',
            'estado', 'verificado', 'activo',
            'entregas_completadas', 'entregas_canceladas',
            'calificacion_promedio', 'ganancias_totales',
            'numero_cuenta', 'titular_cuenta', 'banco',
            'creado_en', 'actualizado_en'
        ]
        read_only_fields = [
            'id', 'creado_en', 'actualizado_en',
            'entregas_completadas', 'entregas_canceladas',
            'calificacion_promedio', 'ganancias_totales'
        ]


# ============================================
# SERIALIZER: VERIFICAR REPARTIDOR
# ============================================

class VerificarRepartidorSerializer(serializers.Serializer):
    """
    Serializer para verificar o rechazar un repartidor
    """
    verificado = serializers.BooleanField(
        label="¿Verificar repartidor?"
    )
    motivo = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        label="Motivo de decisión"
    )


# ============================================
# SERIALIZER: ACCIÓN ADMINISTRATIVA
# ============================================

class AccionAdministrativaSerializer(serializers.ModelSerializer):
    """
    Serializer para logs de acciones administrativas
    """
    admin_email = serializers.CharField(source='administrador.user.email', read_only=True)
    admin_nombre = serializers.CharField(source='administrador.user.get_full_name', read_only=True)
    tipo_accion_display = serializers.CharField(source='get_tipo_accion_display', read_only=True)
    resumen = serializers.CharField(read_only=True)

    class Meta:
        model = AccionAdministrativa
        fields = [
            'id', 'admin_email', 'admin_nombre',
            'tipo_accion', 'tipo_accion_display',
            'descripcion', 'resumen',
            'modelo_afectado', 'objeto_id',
            'datos_anteriores', 'datos_nuevos',
            'ip_address', 'exitosa', 'mensaje_error',
            'fecha_accion'
        ]
        read_only_fields = [
            'id', 'admin_email', 'admin_nombre', 'tipo_accion_display',
            'resumen', 'fecha_accion'
        ]


# ============================================
# SERIALIZER: CONFIGURACIÓN DEL SISTEMA
# ============================================

class ConfiguracionSistemaSerializer(serializers.ModelSerializer):
    """
    Serializer para configuración global del sistema
    Solo accesible por super administradores
    """
    modificado_por_email = serializers.CharField(
        source='modificado_por.user.email',
        read_only=True
    )

    class Meta:
        model = ConfiguracionSistema
        fields = [
            # Comisiones
            'comision_app_proveedor', 'comision_app_directo',
            'comision_repartidor_proveedor', 'comision_repartidor_directo',
            # Rifas
            'pedidos_minimos_rifa',
            # Límites
            'pedido_maximo', 'pedido_minimo',
            # Tiempos
            'tiempo_maximo_entrega',
            # Contacto
            'telefono_soporte', 'email_soporte',
            # Estado
            'mantenimiento', 'mensaje_mantenimiento',
            # Auditoría
            'modificado_por_email', 'actualizado_en'
        ]
        read_only_fields = [
            'modificado_por_email', 'actualizado_en'
        ]

    def validate_comision_app_proveedor(self, value):
        """Validar porcentaje válido"""
        if not 0 <= value <= 100:
            raise serializers.ValidationError("El porcentaje debe estar entre 0 y 100")
        return value

    def validate_comision_app_directo(self, value):
        """Validar porcentaje válido"""
        if not 0 <= value <= 100:
            raise serializers.ValidationError("El porcentaje debe estar entre 0 y 100")
        return value

    def validate_comision_repartidor_proveedor(self, value):
        """Validar porcentaje válido"""
        if not 0 <= value <= 100:
            raise serializers.ValidationError("El porcentaje debe estar entre 0 y 100")
        return value

    def validate_comision_repartidor_directo(self, value):
        """Validar porcentaje válido"""
        if not 0 <= value <= 100:
            raise serializers.ValidationError("El porcentaje debe estar entre 0 y 100")
        return value

    def validate_pedido_maximo(self, value):
        """Validar que sea positivo"""
        if value <= 0:
            raise serializers.ValidationError("El monto máximo debe ser positivo")
        return value

    def validate_pedido_minimo(self, value):
        """Validar que sea positivo"""
        if value <= 0:
            raise serializers.ValidationError("El monto mínimo debe ser positivo")
        return value

    def validate(self, data):
        """Validaciones combinadas"""
        # Validar que mínimo < máximo
        minimo = data.get('pedido_minimo', self.instance.pedido_minimo if self.instance else 0)
        maximo = data.get('pedido_maximo', self.instance.pedido_maximo if self.instance else 1000)

        if minimo >= maximo:
            raise serializers.ValidationError({
                "pedido_minimo": "El monto mínimo debe ser menor que el máximo"
            })

        return data