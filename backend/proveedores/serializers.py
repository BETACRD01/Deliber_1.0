# -*- coding: utf-8 -*-
# administradores/serializers.py - EXTENSIÓN PARA EDICIÓN
"""
Nuevos Serializers para edición de Proveedores y Repartidores

✅ Validadores robustos y reutilizables
✅ Serializers de edición completos
✅ Validaciones a nivel campo y objeto
✅ Documentación detallada
✅ Optimizado para rendimiento
✅ Manejo de errores específicos
"""

from rest_framework import serializers
from authentication.models import User
from proveedores.models import Proveedor
from repartidores.models import Repartidor

# ════════════════════════════════════════════════════════════════════════════
# AGREGAR AL INICIO DE serializers.py 
# ════════════════════════════════════════════════════════════════════════════
class ProveedorListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar proveedores (datos resumidos)
    """
    tipo_proveedor_display = serializers.CharField(
        source='get_tipo_proveedor_display',
        read_only=True
    )
    email_usuario = serializers.SerializerMethodField()
    celular_usuario = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = Proveedor
        fields = [
            'id',
            'nombre',
            'ruc',
            'tipo_proveedor',
            'tipo_proveedor_display',
            'ciudad',
            'activo',
            'verificado',
            'email_usuario',
            'celular_usuario',
            'nombre_completo',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_email_usuario(self, obj):
        return obj.email_actual
    
    def get_celular_usuario(self, obj):
        return obj.celular_actual
    
    def get_nombre_completo(self, obj):
        return obj.nombre_completo_usuario


class ProveedorDetalleSerializer(serializers.ModelSerializer):
    """
    Serializer para obtener detalle completo de un proveedor
    """
    tipo_proveedor_display = serializers.CharField(
        source='get_tipo_proveedor_display',
        read_only=True
    )
    email_usuario = serializers.SerializerMethodField()
    celular_usuario = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()
    usuario_id = serializers.IntegerField(source='user_id', read_only=True)
    
    class Meta:
        model = Proveedor
        fields = [
            'id',
            'usuario_id',
            'nombre',
            'ruc',
            'tipo_proveedor',
            'tipo_proveedor_display',
            'descripcion',
            'direccion',
            'ciudad',
            'latitud',
            'longitud',
            'activo',
            'verificado',
            'comision_porcentaje',
            'horario_apertura',
            'horario_cierre',
            'logo',
            'email_usuario',
            'celular_usuario',
            'nombre_completo',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_email_usuario(self, obj):
        return obj.email_actual
    
    def get_celular_usuario(self, obj):
        return obj.celular_actual
    
    def get_nombre_completo(self, obj):
        return obj.nombre_completo_usuario


class VerificarProveedorSerializer(serializers.Serializer):
    """
    Serializer para verificar/rechazar un proveedor
    """
    verificado = serializers.BooleanField(
        help_text='True para verificar, False para rechazar'
    )
    motivo = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Motivo de la decisión'
    )


# ============================================
# BLOQUE 0: SERIALIZERS BASICOS REPARTIDOR
# ============================================

class RepartidorListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar repartidores (datos resumidos)
    """
    usuario_nombre = serializers.SerializerMethodField()
    usuario_email = serializers.SerializerMethodField()
    usuario_id = serializers.IntegerField(source='user_id', read_only=True)
    
    class Meta:
        model = Repartidor
        fields = [
            'id',
            'usuario_id',
            'usuario_nombre',
            'usuario_email',
            'cedula',
            'telefono',
            'estado',
            'activo',
            'verificado',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_usuario_nombre(self, obj):
        if obj.user:
            return obj.user.get_full_name()
        return None
    
    def get_usuario_email(self, obj):
        if obj.user:
            return obj.user.email
        return None


class RepartidorDetalleSerializer(serializers.ModelSerializer):
    """
    Serializer para obtener detalle completo de un repartidor
    """
    usuario_nombre = serializers.SerializerMethodField()
    usuario_email = serializers.SerializerMethodField()
    usuario_id = serializers.IntegerField(source='user_id', read_only=True)
    
    class Meta:
        model = Repartidor
        fields = [
            'id',
            'usuario_id',
            'usuario_nombre',
            'usuario_email',
            'cedula',
            'telefono',
            'latitud',
            'longitud',
            'estado',
            'activo',
            'verificado',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_usuario_nombre(self, obj):
        if obj.user:
            return obj.user.get_full_name()
        return None
    
    def get_usuario_email(self, obj):
        if obj.user:
            return obj.user.email
        return None


class VerificarRepartidorSerializer(serializers.Serializer):
    """
    Serializer para verificar/rechazar un repartidor
    """
    verificado = serializers.BooleanField(
        help_text='True para verificar, False para rechazar'
    )
    motivo = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Motivo de la decisión'
    )

# ============================================
# BLOQUE 1: VALIDADORES COMPARTIDOS
# ============================================

class ValidadorRUC:
    """
    Validador para RUC ecuatoriano
    - Valida formato (10 o 13 dígitos)
    - Valida que no esté duplicado
    """
    
    @staticmethod
    def validar_formato(ruc):
        """
        Valida formato básico del RUC
        
        Args:
            ruc (str): RUC a validar
            
        Raises:
            ValidationError: Si el formato es inválido
        """
        if not ruc:
            return True
        
        if not isinstance(ruc, str):
            raise serializers.ValidationError('RUC debe ser texto')
        
        # RUC: 10 dígitos (persona) o 13 dígitos (empresa)
        if len(ruc) != 13 and len(ruc) != 10:
            raise serializers.ValidationError(
                'RUC debe tener 10 (persona) o 13 (empresa) dígitos'
            )
        
        if not ruc.isdigit():
            raise serializers.ValidationError(
                'RUC solo debe contener números'
            )
        
        return True
    
    @staticmethod
    def validar_duplicado(ruc, proveedor_id=None):
        """
        Valida que el RUC no esté duplicado en el sistema
        
        Args:
            ruc (str): RUC a validar
            proveedor_id (int): ID del proveedor actual (para exclusión)
            
        Raises:
            ValidationError: Si el RUC ya existe
        """
        if not ruc:
            return True
        
        query = Proveedor.objects.filter(ruc=ruc)
        
        # Excluir el proveedor actual si se está editando
        if proveedor_id:
            query = query.exclude(id=proveedor_id)
        
        if query.exists():
            raise serializers.ValidationError(
                'Este RUC ya está registrado en el sistema'
            )
        
        return True


class ValidadorCedula:
    """
    Validador para cédula ecuatoriana
    - Valida formato (10 dígitos)
    - Valida que no esté duplicada
    """
    
    @staticmethod
    def validar_formato(cedula):
        """
        Valida formato básico de cédula
        
        Args:
            cedula (str): Cédula a validar
            
        Raises:
            ValidationError: Si el formato es inválido
        """
        if not cedula:
            return True
        
        if not isinstance(cedula, str):
            raise serializers.ValidationError('Cédula debe ser texto')
        
        if len(cedula) != 10:
            raise serializers.ValidationError(
                'Cédula debe tener exactamente 10 dígitos'
            )
        
        if not cedula.isdigit():
            raise serializers.ValidationError(
                'Cédula solo debe contener números'
            )
        
        return True
    
    @staticmethod
    def validar_duplicado(cedula, repartidor_id=None):
        """
        Valida que la cédula no esté duplicada en el sistema
        
        Args:
            cedula (str): Cédula a validar
            repartidor_id (int): ID del repartidor actual (para exclusión)
            
        Raises:
            ValidationError: Si la cédula ya existe
        """
        if not cedula:
            return True
        
        query = Repartidor.objects.filter(cedula=cedula)
        
        # Excluir el repartidor actual si se está editando
        if repartidor_id:
            query = query.exclude(id=repartidor_id)
        
        if query.exists():
            raise serializers.ValidationError(
                'Esta cédula ya está registrada en el sistema'
            )
        
        return True


class ValidadorContacto:
    """
    Validador para datos de contacto
    - Email: validación de unicidad
    - Teléfono: formato ecuatoriano (09XXXXXXXXX)
    """
    
    @staticmethod
    def validar_email_duplicado(email, usuario_id=None):
        """
        Valida que el email no esté duplicado en el sistema
        
        Args:
            email (str): Email a validar
            usuario_id (int): ID del usuario actual (para exclusión)
            
        Raises:
            ValidationError: Si el email ya existe
        """
        if not email:
            return True
        
        query = User.objects.filter(email=email)
        
        # Excluir el usuario actual si se está editando
        if usuario_id:
            query = query.exclude(id=usuario_id)
        
        if query.exists():
            raise serializers.ValidationError(
                'Este email ya está registrado en el sistema'
            )
        
        return True
    
    @staticmethod
    def validar_telefono(telefono):
        """
        Valida formato de teléfono ecuatoriano
        Formato: 09XXXXXXXXX (10 dígitos comenzando con 09)
        
        Args:
            telefono (str): Teléfono a validar
            
        Raises:
            ValidationError: Si el formato es inválido
        """
        if not telefono:
            return True
        
        # Convertir a string y remover espacios
        telefono = str(telefono).strip()
        
        if not telefono.startswith('09'):
            raise serializers.ValidationError(
                'El teléfono debe comenzar con 09'
            )
        
        if len(telefono) != 10:
            raise serializers.ValidationError(
                'El teléfono debe tener exactamente 10 dígitos'
            )
        
        if not telefono.isdigit():
            raise serializers.ValidationError(
                'El teléfono solo debe contener números'
            )
        
        return True


class ValidadorUbicacion:
    """
    Validador para coordenadas geográficas
    - Latitud: -90 a 90
    - Longitud: -180 a 180
    """
    
    @staticmethod
    def validar_latitud(latitud):
        """
        Valida rango de latitud
        
        Args:
            latitud (float): Latitud a validar
            
        Raises:
            ValidationError: Si está fuera del rango
        """
        if latitud is None:
            return True
        
        try:
            lat = float(latitud)
        except (ValueError, TypeError):
            raise serializers.ValidationError('Latitud debe ser un número')
        
        if not (-90 <= lat <= 90):
            raise serializers.ValidationError(
                'Latitud debe estar entre -90 y 90 grados'
            )
        
        return True
    
    @staticmethod
    def validar_longitud(longitud):
        """
        Valida rango de longitud
        
        Args:
            longitud (float): Longitud a validar
            
        Raises:
            ValidationError: Si está fuera del rango
        """
        if longitud is None:
            return True
        
        try:
            lon = float(longitud)
        except (ValueError, TypeError):
            raise serializers.ValidationError('Longitud debe ser un número')
        
        if not (-180 <= lon <= 180):
            raise serializers.ValidationError(
                'Longitud debe estar entre -180 y 180 grados'
            )
        
        return True


# ============================================
# BLOQUE 2: SERIALIZER EDITAR PROVEEDOR
# ============================================

class ProveedorEditarSerializer(serializers.ModelSerializer):
    """
    Serializer para EDITAR información del Proveedor
    
    Campos editables:
    - nombre: Nombre del negocio/proveedor
    - tipo_proveedor: Tipo de negocio (RESTAURANT, TIENDA, etc)
    - ruc: Número de RUC (10 o 13 dígitos)
    - telefono: Teléfono de contacto (09XXXXXXXXX)
    - direccion: Dirección física del negocio
    - latitud: Coordenada de latitud
    - longitud: Coordenada de longitud
    - descripcion: Descripción del negocio
    - horario_atencion: Horario (formato: HH:MM-HH:MM)
    - tiempo_preparacion_promedio: Tiempo en minutos (0-180)
    
    Validaciones:
    ✅ RUC: formato y unicidad
    ✅ Teléfono: formato ecuatoriano
    ✅ Coordenadas: rango válido y coherencia
    ✅ Longitudes de texto: mínimo y máximo
    ✅ Horario: formato correcto
    
    Ejemplo de request:
    PUT /api/admin/proveedores/1/
    {
        "nombre": "Mi Restaurante",
        "tipo_proveedor": "RESTAURANT",
        "ruc": "1234567890123",
        "telefono": "0987654321",
        "direccion": "Av. Principal 123",
        "latitud": -0.2123,
        "longitud": -78.4567,
        "descripcion": "El mejor restaurante",
        "horario_atencion": "08:00-20:00",
        "tiempo_preparacion_promedio": 30
    }
    """
    
    class Meta:
        model = Proveedor
        fields = [
            'nombre',
            'tipo_proveedor',
            'ruc',
            'telefono',
            'direccion',
            'latitud',
            'longitud',
            'descripcion',
            'horario_atencion',
            'tiempo_preparacion_promedio',
        ]
    
    # -------- VALIDADORES DE CAMPOS INDIVIDUALES --------
    
    def validate_nombre(self, value):
        """Valida nombre del proveedor"""
        if value:
            value = value.strip()
            
            if len(value) < 3:
                raise serializers.ValidationError(
                    'El nombre debe tener al menos 3 caracteres'
                )
            
            if len(value) > 150:
                raise serializers.ValidationError(
                    'El nombre no puede exceder 150 caracteres'
                )
        
        return value
    
    def validate_tipo_proveedor(self, value):
        """Valida que el tipo de proveedor sea válido"""
        if value:
            # Obtener tipos válidos del modelo
            tipos_validos = [
                choice[0] for choice in 
                Proveedor._meta.get_field('tipo_proveedor').choices
            ]
            
            if value not in tipos_validos:
                tipos_str = ', '.join(tipos_validos)
                raise serializers.ValidationError(
                    f'Tipo de proveedor no válido. Opciones: {tipos_str}'
                )
        
        return value
    
    def validate_ruc(self, value):
        """Valida formato y unicidad del RUC"""
        if value:
            ValidadorRUC.validar_formato(value)
            
            # Obtener ID del proveedor actual para excluirlo
            proveedor_id = self.instance.id if self.instance else None
            ValidadorRUC.validar_duplicado(value, proveedor_id)
        
        return value
    
    def validate_telefono(self, value):
        """Valida formato del teléfono"""
        if value:
            ValidadorContacto.validar_telefono(value)
        
        return value
    
    def validate_direccion(self, value):
        """Valida dirección del proveedor"""
        if value:
            value = value.strip()
            
            if len(value) < 5:
                raise serializers.ValidationError(
                    'La dirección debe tener al menos 5 caracteres'
                )
            
            if len(value) > 255:
                raise serializers.ValidationError(
                    'La dirección no puede exceder 255 caracteres'
                )
        
        return value
    
    def validate_latitud(self, value):
        """Valida rango de latitud"""
        if value is not None:
            ValidadorUbicacion.validar_latitud(value)
        
        return value
    
    def validate_longitud(self, value):
        """Valida rango de longitud"""
        if value is not None:
            ValidadorUbicacion.validar_longitud(value)
        
        return value
    
    def validate_descripcion(self, value):
        """Valida descripción del proveedor"""
        if value:
            value = value.strip()
            
            if len(value) > 1000:
                raise serializers.ValidationError(
                    'La descripción no puede exceder 1000 caracteres'
                )
        
        return value
    
    def validate_horario_atencion(self, value):
        """Valida formato de horario"""
        if value:
            value = value.strip()
            
            # Formato esperado: "HH:MM-HH:MM" ej: "08:00-20:00"
            if '-' not in value:
                raise serializers.ValidationError(
                    'Formato de horario inválido. Use: HH:MM-HH:MM (ej: 08:00-20:00)'
                )
            
            try:
                partes = value.split('-')
                if len(partes) != 2:
                    raise ValueError()
                
                # Validar formato HH:MM
                for parte in partes:
                    if ':' not in parte:
                        raise ValueError()
                    h, m = parte.split(':')
                    h, m = int(h), int(m)
                    if not (0 <= h <= 23) or not (0 <= m <= 59):
                        raise ValueError()
            
            except (ValueError, IndexError):
                raise serializers.ValidationError(
                    'Formato de horario inválido. Use: HH:MM-HH:MM'
                )
        
        return value
    
    def validate_tiempo_preparacion_promedio(self, value):
        """Valida tiempo de preparación"""
        if value is not None:
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    'El tiempo de preparación debe ser un número'
                )
            
            if value < 0:
                raise serializers.ValidationError(
                    'El tiempo de preparación no puede ser negativo'
                )
            
            if value > 180:  # 3 horas máximo
                raise serializers.ValidationError(
                    'El tiempo de preparación no puede exceder 180 minutos (3 horas)'
                )
        
        return value
    
    # -------- VALIDADOR A NIVEL DE OBJETO --------
    
    def validate(self, data):
        """
        Validaciones a nivel de objeto completo
        - Si se envían coordenadas, ambas deben estar presentes
        """
        # Verificar coherencia de coordenadas
        latitud = data.get('latitud')
        longitud = data.get('longitud')
        
        # Si se envía uno, debe enviarse el otro
        if (latitud is None) != (longitud is None):
            raise serializers.ValidationError({
                'ubicacion': 'Latitud y longitud deben enviarse juntas'
            })
        
        return data


# ============================================
# BLOQUE 3: SERIALIZER EDITAR CONTACTO PROVEEDOR
# ============================================

class ProveedorEditarContactoSerializer(serializers.Serializer):
    """
    Serializer para EDITAR datos de CONTACTO del Proveedor
    
    Este serializer edita la información asociada al usuario (User model)
    
    Campos editables:
    - email: Email del contacto
    - first_name: Nombre del contacto
    - last_name: Apellido del contacto
    
    Validaciones:
    ✅ Email: formato y unicidad
    ✅ Nombre/Apellido: no vacíos, longitud mínima
    
    Ejemplo de request:
    PATCH /api/admin/proveedores/1/editar_contacto/
    {
        "email": "contacto@mirestaurante.com",
        "first_name": "Juan",
        "last_name": "Pérez"
    }
    """
    
    email = serializers.EmailField(
        required=False,
        allow_blank=False,
        help_text='Email del contacto del proveedor'
    )
    
    first_name = serializers.CharField(
        required=False,
        max_length=100,
        allow_blank=False,
        help_text='Nombre del contacto'
    )
    
    last_name = serializers.CharField(
        required=False,
        max_length=100,
        allow_blank=False,
        help_text='Apellido del contacto'
    )
    
    # -------- VALIDADORES DE CAMPOS INDIVIDUALES --------
    
    def validate_email(self, value):
        """Valida que el email sea único en el sistema"""
        if value:
            usuario = self.context.get('usuario')
            usuario_id = usuario.id if usuario else None
            ValidadorContacto.validar_email_duplicado(value, usuario_id)
        
        return value
    
    def validate_first_name(self, value):
        """Valida nombre del contacto"""
        if value:
            value = value.strip()
            
            if len(value) < 2:
                raise serializers.ValidationError(
                    'El nombre debe tener al menos 2 caracteres'
                )
        
        return value
    
    def validate_last_name(self, value):
        """Valida apellido del contacto"""
        if value:
            value = value.strip()
            
            if len(value) < 2:
                raise serializers.ValidationError(
                    'El apellido debe tener al menos 2 caracteres'
                )
        
        return value
    
    # -------- VALIDADOR A NIVEL DE OBJETO --------
    
    def validate(self, data):
        """
        Validaciones a nivel de objeto completo
        - Al menos un campo debe ser proporcionado
        """
        if not data:
            raise serializers.ValidationError(
                'Debe proporcionar al menos un campo para actualizar (email, first_name o last_name)'
            )
        
        return data


# ============================================
# BLOQUE 4: SERIALIZER EDITAR REPARTIDOR
# ============================================

class RepartidorEditarSerializer(serializers.ModelSerializer):
    """
    Serializer para EDITAR información del Repartidor
    
    Campos editables:
    - cedula: Cédula de identidad (10 dígitos)
    - telefono: Teléfono de contacto (09XXXXXXXXX)
    - latitud: Coordenada de latitud
    - longitud: Coordenada de longitud
    
    Validaciones:
    ✅ Cédula: formato y unicidad
    ✅ Teléfono: formato ecuatoriano
    ✅ Coordenadas: rango válido y coherencia
    
    Ejemplo de request:
    PUT /api/admin/repartidores/1/
    {
        "cedula": "1234567890",
        "telefono": "0987654321",
        "latitud": -0.2123,
        "longitud": -78.4567
    }
    """
    
    class Meta:
        model = Repartidor
        fields = [
            'cedula',
            'telefono',
            'latitud',
            'longitud',
        ]
    
    # -------- VALIDADORES DE CAMPOS INDIVIDUALES --------
    
    def validate_cedula(self, value):
        """Valida formato y unicidad de cédula"""
        if value:
            ValidadorCedula.validar_formato(value)
            
            # Obtener ID del repartidor actual para excluirlo
            repartidor_id = self.instance.id if self.instance else None
            ValidadorCedula.validar_duplicado(value, repartidor_id)
        
        return value
    
    def validate_telefono(self, value):
        """Valida formato del teléfono"""
        if value:
            ValidadorContacto.validar_telefono(value)
        
        return value
    
    def validate_latitud(self, value):
        """Valida rango de latitud"""
        if value is not None:
            ValidadorUbicacion.validar_latitud(value)
        
        return value
    
    def validate_longitud(self, value):
        """Valida rango de longitud"""
        if value is not None:
            ValidadorUbicacion.validar_longitud(value)
        
        return value
    
    # -------- VALIDADOR A NIVEL DE OBJETO --------
    
    def validate(self, data):
        """
        Validaciones a nivel de objeto completo
        - Si se envían coordenadas, ambas deben estar presentes
        """
        # Verificar coherencia de coordenadas
        latitud = data.get('latitud')
        longitud = data.get('longitud')
        
        # Si se envía uno, debe enviarse el otro
        if (latitud is None) != (longitud is None):
            raise serializers.ValidationError({
                'ubicacion': 'Latitud y longitud deben enviarse juntas'
            })
        
        return data


# ============================================
# BLOQUE 5: SERIALIZER EDITAR CONTACTO REPARTIDOR
# ============================================

class RepartidorEditarContactoSerializer(serializers.Serializer):
    """
    Serializer para EDITAR datos de CONTACTO del Repartidor
    
    Este serializer edita la información asociada al usuario (User model)
    
    Campos editables:
    - email: Email del repartidor
    - first_name: Nombre del repartidor
    - last_name: Apellido del repartidor
    
    Validaciones:
    ✅ Email: formato y unicidad
    ✅ Nombre/Apellido: no vacíos, longitud mínima
    
    Ejemplo de request:
    PATCH /api/admin/repartidores/1/editar_contacto/
    {
        "email": "repartidor@email.com",
        "first_name": "Carlos",
        "last_name": "González"
    }
    """
    
    email = serializers.EmailField(
        required=False,
        allow_blank=False,
        help_text='Email del repartidor'
    )
    
    first_name = serializers.CharField(
        required=False,
        max_length=100,
        allow_blank=False,
        help_text='Nombre del repartidor'
    )
    
    last_name = serializers.CharField(
        required=False,
        max_length=100,
        allow_blank=False,
        help_text='Apellido del repartidor'
    )
    
    # -------- VALIDADORES DE CAMPOS INDIVIDUALES --------
    
    def validate_email(self, value):
        """Valida que el email sea único en el sistema"""
        if value:
            usuario = self.context.get('usuario')
            usuario_id = usuario.id if usuario else None
            ValidadorContacto.validar_email_duplicado(value, usuario_id)
        
        return value
    
    def validate_first_name(self, value):
        """Valida nombre del repartidor"""
        if value:
            value = value.strip()
            
            if len(value) < 2:
                raise serializers.ValidationError(
                    'El nombre debe tener al menos 2 caracteres'
                )
        
        return value
    
    def validate_last_name(self, value):
        """Valida apellido del repartidor"""
        if value:
            value = value.strip()
            
            if len(value) < 2:
                raise serializers.ValidationError(
                    'El apellido debe tener al menos 2 caracteres'
                )
        
        return value
    
    # -------- VALIDADOR A NIVEL DE OBJETO --------
    
    def validate(self, data):
        """
        Validaciones a nivel de objeto completo
        - Al menos un campo debe ser proporcionado
        """
        if not data:
            raise serializers.ValidationError(
                'Debe proporcionar al menos un campo para actualizar (email, first_name o last_name)'
            )
        
        return data