from rest_framework import serializers
from .models import Proveedor

class ProveedorSerializer(serializers.ModelSerializer):
    """
    Serializer para Proveedor con datos del usuario vinculado

    ✅ MEJORAS:
    - Incluye datos del User vinculado (email, celular, nombre completo)
    - Marca campos duplicados como deprecados
    - Sincronización automática con User
    - Campo calculado esta_abierto
    - Muestra estado de verificación
    """

    # ============================================
    # ✅ CAMPOS DEL USUARIO VINCULADO (READ-ONLY)
    # ============================================
    email_usuario = serializers.EmailField(
        source='user.email',
        read_only=True,
        help_text='Email del usuario vinculado (source of truth)'
    )

    celular_usuario = serializers.CharField(
        source='user.celular',
        read_only=True,
        help_text='Celular del usuario vinculado'
    )

    nombre_completo = serializers.CharField(
        source='user.get_full_name',
        read_only=True,
        help_text='Nombre completo del usuario'
    )

    verificado = serializers.BooleanField(
        source='user.verificado',
        read_only=True,
        help_text='Estado de verificación del proveedor'
    )

    user_id = serializers.IntegerField(
        source='user.id',
        read_only=True,
        help_text='ID del usuario vinculado'
    )

    # ============================================
    # ⚠️ CAMPOS DEPRECADOS (Mantener por compatibilidad)
    # ============================================
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text='⚠️ DEPRECADO: Usa email_usuario. Se mantiene por compatibilidad'
    )

    telefono = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='⚠️ DEPRECADO: Usa celular_usuario. Se mantiene por compatibilidad'
    )

    # ============================================
    # ✅ CAMPO CALCULADO
    # ============================================
    esta_abierto = serializers.SerializerMethodField(
        help_text='Indica si el proveedor está abierto en este momento'
    )

    class Meta:
        model = Proveedor
        fields = [
            # Identificación
            'id',
            'user_id',  # ✅ NUEVO

            # Información básica
            'nombre',
            'ruc',
            'tipo_proveedor',
            'descripcion',

            # ✅ DATOS DEL USUARIO (NUEVOS)
            'email_usuario',      # ✅ Source of truth
            'celular_usuario',    # ✅ Source of truth
            'nombre_completo',    # ✅ Nombre del usuario
            'verificado',         # ✅ Estado de verificación

            # ⚠️ CAMPOS DEPRECADOS (compatibilidad)
            'email',              # ⚠️ Deprecado
            'telefono',           # ⚠️ Deprecado

            # Ubicación
            'direccion',
            'ciudad',
            'latitud',
            'longitud',

            # Configuración
            'activo',
            'comision_porcentaje',

            # Horarios
            'horario_apertura',
            'horario_cierre',
            'esta_abierto',  # ✅ Calculado

            # Multimedia
            'logo',

            # Auditoría
            'created_at',
            'updated_at'
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'ruc',  # ✅ RUC no se puede cambiar después de crear
            'user_id',
            'email_usuario',
            'celular_usuario',
            'nombre_completo',
            'verificado'
        ]

    # ============================================
    # ✅ MÉTODO PARA CAMPO CALCULADO
    # ============================================
    def get_esta_abierto(self, obj):
        """Calcula si el proveedor está abierto ahora"""
        return obj.esta_abierto()

    # ============================================
    # ✅ VALIDACIÓN CON ADVERTENCIAS
    # ============================================
    def validate(self, data):
        """
        Valida datos y advierte sobre campos deprecados
        """
        # Advertir si se usan campos deprecados
        if 'email' in data or 'telefono' in data:
            import warnings
            warnings.warn(
                "⚠️ Los campos 'email' y 'telefono' están deprecados. "
                "Actualiza estos datos en el perfil de usuario a través de "
                "/api/auth/actualizar-perfil/",
                DeprecationWarning,
                stacklevel=2
            )

        return data

    # ============================================
    # ✅ REPRESENTACIÓN PERSONALIZADA
    # ============================================
    def to_representation(self, instance):
        """
        Personaliza la respuesta para incluir información útil
        """
        representation = super().to_representation(instance)

        # Si no hay usuario vinculado, marcar como problema
        if not instance.user:
            representation['_warning'] = '⚠️ Este proveedor no tiene usuario vinculado'
            representation['email_usuario'] = instance.email or None
            representation['celular_usuario'] = instance.telefono or None
            representation['nombre_completo'] = instance.nombre
            representation['verificado'] = False

        # Agregar URLs útiles si hay logo
        if instance.logo:
            request = self.context.get('request')
            if request:
                representation['logo_url'] = request.build_absolute_uri(instance.logo.url)

        return representation


# ============================================
# ✅ SERIALIZER SIMPLIFICADO (PARA LISTADOS)
# ============================================
class ProveedorListSerializer(serializers.ModelSerializer):
    """
    Serializer ligero para listados de proveedores
    Solo incluye campos esenciales
    """
    verificado = serializers.BooleanField(source='user.verificado', read_only=True)
    esta_abierto = serializers.SerializerMethodField()

    class Meta:
        model = Proveedor
        fields = [
            'id',
            'nombre',
            'tipo_proveedor',
            'ciudad',
            'activo',
            'verificado',
            'esta_abierto',
            'logo',
            'horario_apertura',
            'horario_cierre',
            'comision_porcentaje'
        ]

    def get_esta_abierto(self, obj):
        return obj.esta_abierto()


# ============================================
# ✅ SERIALIZER PARA ACTUALIZACIÓN
# ============================================
class ProveedorUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer específico para actualización
    Solo permite modificar campos seguros
    """

    class Meta:
        model = Proveedor
        fields = [
            'nombre',
            'descripcion',
            'direccion',
            'ciudad',
            'horario_apertura',
            'horario_cierre',
            'latitud',
            'longitud',
            'logo',
            'tipo_proveedor',
            'comision_porcentaje'  # Solo admin puede cambiar esto
        ]

    def validate_comision_porcentaje(self, value):
        """Solo admins pueden cambiar la comisión"""
        request = self.context.get('request')
        if request and not request.user.es_administrador():
            # Si no es admin, mantener el valor original
            instance = self.instance
            if instance:
                return instance.comision_porcentaje
        return value


# ============================================
# ✅ SERIALIZER PARA ADMIN (MÁS COMPLETO)
# ============================================
class ProveedorAdminSerializer(serializers.ModelSerializer):
    """
    Serializer completo para administradores
    Incluye todos los campos y permite modificaciones
    """
    email_usuario = serializers.EmailField(source='user.email', read_only=True)
    celular_usuario = serializers.CharField(source='user.celular', read_only=True)
    nombre_completo = serializers.CharField(source='user.get_full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    fecha_registro = serializers.DateTimeField(source='user.created_at', read_only=True)

    class Meta:
        model = Proveedor
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'user']
