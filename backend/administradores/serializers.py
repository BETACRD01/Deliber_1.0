# -*- coding: utf-8 -*-
# administradores/serializers.py
"""
Serializers para el módulo de administradores
✅ Gestión completa de usuarios (usuarios, proveedores, repartidores)
✅ Logs de acciones administrativas
✅ Configuración del sistema
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from authentication.models import User
from usuarios.models import Perfil
from proveedores.models import Proveedor
from repartidores.models import Repartidor
from pedidos.models import Pedido
from .models import Administrador, AccionAdministrativa, ConfiguracionSistema


# ============================================
# SERIALIZERS: ADMINISTRADOR
# ============================================

class AdministradorSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil de administrador
    """
    # Información del usuario
    email = serializers.EmailField(source='user.email', read_only=True)
    nombre_completo = serializers.CharField(source='user.get_full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    # Estadísticas
    total_acciones_realizadas = serializers.IntegerField(source='total_acciones', read_only=True)
    es_super_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = Administrador
        fields = [
            'id',
            'user',
            'email',
            'nombre_completo',
            'username',
            'cargo',
            'departamento',
            'puede_gestionar_usuarios',
            'puede_gestionar_pedidos',
            'puede_gestionar_proveedores',
            'puede_gestionar_repartidores',
            'puede_gestionar_rifas',
            'puede_ver_reportes',
            'puede_configurar_sistema',
            'activo',
            'total_acciones_realizadas',
            'es_super_admin',
            'creado_en',
            'actualizado_en',
        ]
        read_only_fields = ['creado_en', 'actualizado_en']


# ============================================
# SERIALIZERS: USUARIOS
# ============================================

class UsuarioListSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listar usuarios
    """
    nombre_completo = serializers.CharField(source='get_full_name', read_only=True)
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)

    # Estadísticas básicas
    total_pedidos = serializers.SerializerMethodField()
    esta_bloqueado = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'nombre_completo',
            'first_name',
            'last_name',
            'celular',
            'rol',
            'rol_display',
            'is_active',
            'cuenta_desactivada',
            'verificado',
            'total_pedidos',
            'esta_bloqueado',
            'created_at',
        ]

    def get_total_pedidos(self, obj):
        """Obtiene el total de pedidos del usuario"""
        if obj.rol == User.RolChoices.USUARIO:
            try:
                return obj.perfil_usuario.total_pedidos
            except:
                return 0
        return 0


class UsuarioDetalleSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para ver un usuario específico
    """
    nombre_completo = serializers.CharField(source='get_full_name', read_only=True)
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    edad = serializers.SerializerMethodField()

    # Información del perfil si es usuario regular
    perfil = serializers.SerializerMethodField()

    # Estadísticas
    estadisticas = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'nombre_completo',
            'first_name',
            'last_name',
            'celular',
            'fecha_nacimiento',
            'edad',
            'rol',
            'rol_display',
            'is_active',
            'cuenta_desactivada',
            'fecha_desactivacion',
            'razon_desactivacion',
            'verificado',
            'terminos_aceptados',
            'terminos_fecha_aceptacion',
            'notificaciones_email',
            'notificaciones_marketing',
            'notificaciones_pedidos',
            'notificaciones_push',
            'intentos_login_fallidos',
            'cuenta_bloqueada_hasta',
            'ultimo_login_ip',
            'last_login',
            'created_at',
            'updated_at',
            'perfil',
            'estadisticas',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_edad(self, obj):
        """Calcula la edad"""
        return obj.get_edad()

    def get_perfil(self, obj):
        """Obtiene información del perfil según el rol"""
        if obj.rol == User.RolChoices.USUARIO:
            try:
                perfil = obj.perfil_usuario
                return {
                    'foto_perfil': perfil.foto_perfil.url if perfil.foto_perfil else None,
                    'calificacion': float(perfil.calificacion),
                    'total_pedidos': perfil.total_pedidos,
                    'pedidos_mes_actual': perfil.pedidos_mes_actual,
                    'puede_participar_rifa': perfil.puede_participar_rifa,
                }
            except:
                return None
        return None

    def get_estadisticas(self, obj):
        """Obtiene estadísticas según el rol"""
        if obj.rol == User.RolChoices.USUARIO:
            try:
                from pedidos.models import EstadoPedido
                perfil = obj.perfil_usuario
                pedidos = perfil.pedidos.all()

                return {
                    'total_pedidos': pedidos.count(),
                    'pedidos_entregados': pedidos.filter(estado=EstadoPedido.ENTREGADO).count(),
                    'pedidos_cancelados': pedidos.filter(estado=EstadoPedido.CANCELADO).count(),
                    'pedidos_activos': pedidos.filter(
                        estado__in=[EstadoPedido.CONFIRMADO, EstadoPedido.EN_PREPARACION, EstadoPedido.EN_RUTA]
                    ).count(),
                }
            except:
                return {}

        return {}


class UsuarioEditarSerializer(serializers.ModelSerializer):
    """
    Serializer para editar usuarios
    """
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'celular',
            'fecha_nacimiento',
            'is_active',
            'cuenta_desactivada',
            'notificaciones_email',
            'notificaciones_marketing',
            'notificaciones_pedidos',
            'notificaciones_push',
        ]

    def validate_celular(self, value):
        """Valida el formato del celular"""
        if value and not value.startswith('09'):
            raise serializers.ValidationError('El celular debe comenzar con 09')
        if value and len(value) != 10:
            raise serializers.ValidationError('El celular debe tener 10 dígitos')
        return value


class CambiarRolSerializer(serializers.Serializer):
    """
    Serializer para cambiar el rol de un usuario
    """
    nuevo_rol = serializers.ChoiceField(
        choices=User.RolChoices.choices,
        required=True,
        help_text='Nuevo rol del usuario'
    )

    motivo = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Motivo del cambio de rol'
    )

    def validate(self, data):
        """Validaciones adicionales"""
        usuario = self.context.get('usuario')
        nuevo_rol = data.get('nuevo_rol')

        # No permitir cambiar el rol de un superusuario
        if usuario.is_superuser:
            raise serializers.ValidationError(
                'No se puede cambiar el rol de un superusuario'
            )

        # Validar que el rol sea diferente al actual
        if usuario.rol == nuevo_rol:
            raise serializers.ValidationError(
                f'El usuario ya tiene el rol {usuario.get_rol_display()}'
            )

        return data


class DesactivarUsuarioSerializer(serializers.Serializer):
    """
    Serializer para desactivar usuarios
    """
    razon = serializers.CharField(
        required=True,
        help_text='Razón de la desactivación'
    )

    permanente = serializers.BooleanField(
        default=False,
        help_text='Si es permanente o temporal'
    )


class ResetearPasswordSerializer(serializers.Serializer):
    """
    Serializer para resetear contraseña de un usuario
    """
    nueva_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        help_text='Nueva contraseña (mínimo 8 caracteres)'
    )

    confirmar_password = serializers.CharField(
        required=True,
        write_only=True,
        help_text='Confirmar nueva contraseña'
    )

    def validate(self, data):
        """Validar que las contraseñas coincidan"""
        if data['nueva_password'] != data['confirmar_password']:
            raise serializers.ValidationError({
                'confirmar_password': 'Las contraseñas no coinciden'
            })

        # Validar complejidad de la contraseña
        try:
            validate_password(data['nueva_password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                'nueva_password': list(e.messages)
            })

        return data


# ============================================
# SERIALIZERS: PROVEEDORES
# ============================================

class ProveedorListSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listar proveedores
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    nombre_contacto = serializers.CharField(source='user.get_full_name', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_proveedor_display', read_only=True)

    # Estadísticas básicas
    total_productos = serializers.SerializerMethodField()
    total_pedidos = serializers.SerializerMethodField()

    class Meta:
        model = Proveedor
        fields = [
            'id',
            'nombre',
            'email',
            'nombre_contacto',
            'telefono',
            'tipo_proveedor',
            'tipo_display',
            'verificado',
            'activo',
            'calificacion_promedio',
            'total_productos',
            'total_pedidos',
            'creado_en',
        ]

    def get_total_productos(self, obj):
        """Total de productos activos"""
        return obj.productos.filter(activo=True, deleted_at__isnull=True).count()

    def get_total_pedidos(self, obj):
        """Total de pedidos"""
        return obj.pedidos.count()


class ProveedorDetalleSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para ver un proveedor
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    nombre_contacto = serializers.CharField(source='user.get_full_name', read_only=True)
    celular_contacto = serializers.CharField(source='user.celular', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_proveedor_display', read_only=True)

    # Estadísticas completas
    estadisticas = serializers.SerializerMethodField()

    class Meta:
        model = Proveedor
        fields = [
            'id',
            'user',
            'nombre',
            'email',
            'nombre_contacto',
            'celular_contacto',
            'telefono',
            'direccion',
            'latitud',
            'longitud',
            'tipo_proveedor',
            'tipo_display',
            'descripcion',
            'horario_atencion',
            'tiempo_preparacion_promedio',
            'foto_portada',
            'logo',
            'verificado',
            'activo',
            'destacado',
            'calificacion_promedio',
            'total_resenas',
            'pedidos_completados',
            'creado_en',
            'actualizado_en',
            'estadisticas',
        ]

    def get_estadisticas(self, obj):
        """Estadísticas del proveedor"""
        from pedidos.models import EstadoPedido
        pedidos = obj.pedidos.all()

        return {
            'total_productos': obj.productos.filter(activo=True, deleted_at__isnull=True).count(),
            'total_pedidos': pedidos.count(),
            'pedidos_entregados': pedidos.filter(estado=EstadoPedido.ENTREGADO).count(),
            'pedidos_cancelados': pedidos.filter(estado=EstadoPedido.CANCELADO).count(),
            'pedidos_activos': pedidos.filter(
                estado__in=[EstadoPedido.CONFIRMADO, EstadoPedido.EN_PREPARACION, EstadoPedido.EN_RUTA]
            ).count(),
        }


class VerificarProveedorSerializer(serializers.Serializer):
    """
    Serializer para verificar/rechazar proveedor
    """
    verificado = serializers.BooleanField(
        required=True,
        help_text='True para verificar, False para rechazar'
    )

    motivo = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Motivo de la decisión'
    )


# ============================================
# SERIALIZERS: REPARTIDORES
# ============================================

class RepartidorListSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listar repartidores
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    nombre_completo = serializers.CharField(source='user.get_full_name', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    # Estadísticas básicas
    total_entregas = serializers.IntegerField(source='entregas_completadas', read_only=True)

    class Meta:
        model = Repartidor
        fields = [
            'id',
            'email',
            'nombre_completo',
            'cedula',
            'telefono',
            'estado',
            'estado_display',
            'verificado',
            'activo',
            'calificacion_promedio',
            'total_entregas',
            'ultima_localizacion',
            'creado_en',
        ]


class RepartidorDetalleSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para ver un repartidor
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    nombre_completo = serializers.CharField(source='user.get_full_name', read_only=True)
    celular = serializers.CharField(source='user.celular', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    # Vehículos
    vehiculos = serializers.SerializerMethodField()

    # Estadísticas
    estadisticas = serializers.SerializerMethodField()

    class Meta:
        model = Repartidor
        fields = [
            'id',
            'user',
            'email',
            'nombre_completo',
            'celular',
            'foto_perfil',
            'cedula',
            'telefono',
            'estado',
            'estado_display',
            'verificado',
            'activo',
            'latitud',
            'longitud',
            'ultima_localizacion',
            'entregas_completadas',
            'calificacion_promedio',
            'vehiculos',
            'creado_en',
            'actualizado_en',
            'estadisticas',
        ]

    def get_vehiculos(self, obj):
        """Lista de vehículos del repartidor"""
        vehiculos = obj.vehiculos.filter(activo=True)
        return [{
            'id': v.id,
            'tipo': v.get_tipo_display(),
            'placa': v.placa or 'N/A',
        } for v in vehiculos]

    def get_estadisticas(self, obj):
        """Estadísticas del repartidor"""
        from pedidos.models import EstadoPedido
        pedidos = obj.pedidos.all()

        return {
            'total_pedidos': pedidos.count(),
            'pedidos_entregados': pedidos.filter(estado=EstadoPedido.ENTREGADO).count(),
            'pedidos_activos': pedidos.filter(
                estado__in=[EstadoPedido.CONFIRMADO, EstadoPedido.EN_PREPARACION, EstadoPedido.EN_RUTA]
            ).count(),
            'total_calificaciones': obj.calificaciones.count(),
        }


class VerificarRepartidorSerializer(serializers.Serializer):
    """
    Serializer para verificar/rechazar repartidor
    """
    verificado = serializers.BooleanField(
        required=True,
        help_text='True para verificar, False para rechazar'
    )

    motivo = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Motivo de la decisión'
    )


# ============================================
# SERIALIZERS: ACCIONES ADMINISTRATIVAS
# ============================================

class AccionAdministrativaSerializer(serializers.ModelSerializer):
    """
    Serializer para logs de acciones administrativas
    """
    administrador_nombre = serializers.SerializerMethodField()
    tipo_accion_display = serializers.CharField(source='get_tipo_accion_display', read_only=True)
    resumen = serializers.CharField(read_only=True)

    class Meta:
        model = AccionAdministrativa
        fields = [
            'id',
            'administrador',
            'administrador_nombre',
            'tipo_accion',
            'tipo_accion_display',
            'descripcion',
            'resumen',
            'modelo_afectado',
            'objeto_id',
            'datos_anteriores',
            'datos_nuevos',
            'ip_address',
            'exitosa',
            'mensaje_error',
            'fecha_accion',
        ]
        read_only_fields = ['fecha_accion']

    def get_administrador_nombre(self, obj):
        """Nombre del administrador"""
        if obj.administrador:
            return obj.administrador.user.get_full_name()
        return 'Admin eliminado'


# ============================================
# SERIALIZERS: CONFIGURACIÓN DEL SISTEMA
# ============================================

class ConfiguracionSistemaSerializer(serializers.ModelSerializer):
    """
    Serializer para la configuración del sistema
    """
    modificado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = ConfiguracionSistema
        fields = [
            'id',
            'comision_app_proveedor',
            'comision_app_directo',
            'comision_repartidor_proveedor',
            'comision_repartidor_directo',
            'pedidos_minimos_rifa',
            'pedido_maximo',
            'pedido_minimo',
            'tiempo_maximo_entrega',
            'telefono_soporte',
            'email_soporte',
            'mantenimiento',
            'mensaje_mantenimiento',
            'modificado_por',
            'modificado_por_nombre',
            'actualizado_en',
        ]
        read_only_fields = ['actualizado_en']

    def get_modificado_por_nombre(self, obj):
        """Nombre del administrador que modificó"""
        if obj.modificado_por:
            return obj.modificado_por.user.get_full_name()
        return None

    def validate(self, data):
        """Validaciones"""
        # Validar que las comisiones sumen 100% o menos
        if 'comision_app_proveedor' in data and 'comision_repartidor_proveedor' in data:
            total = data['comision_app_proveedor'] + data['comision_repartidor_proveedor']
            if total > 100:
                raise serializers.ValidationError(
                    'La suma de comisiones de pedidos de proveedor no puede superar 100%'
                )

        if 'comision_app_directo' in data and 'comision_repartidor_directo' in data:
            total = data['comision_app_directo'] + data['comision_repartidor_directo']
            if total > 100:
                raise serializers.ValidationError(
                    'La suma de comisiones de encargos directos no puede superar 100%'
                )

        # Validar pedido máximo > pedido mínimo
        pedido_max = data.get('pedido_maximo', self.instance.pedido_maximo if self.instance else 1000)
        pedido_min = data.get('pedido_minimo', self.instance.pedido_minimo if self.instance else 5)

        if pedido_max <= pedido_min:
            raise serializers.ValidationError(
                'El pedido máximo debe ser mayor al pedido mínimo'
            )

        return data
