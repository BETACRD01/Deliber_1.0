from rest_framework import serializers
from django.core.validators import RegexValidator
from django.utils import timezone
from math import radians, cos, sin, sqrt, atan2
from decimal import Decimal

from .models import (
    Repartidor,
    RepartidorVehiculo,
    HistorialUbicacion,
    RepartidorEstadoLog,
    CalificacionRepartidor,
    CalificacionCliente,
    EstadoRepartidor,
)


# ==========================================================
# UTILIDAD: Calcular distancia (kilómetros)
# ==========================================================
def calcular_distancia(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en kilómetros entre dos puntos geográficos
    usando la fórmula de Haversine.

    Args:
        lat1, lon1: Coordenadas del primer punto
        lat2, lon2: Coordenadas del segundo punto

    Returns:
        float: Distancia en kilómetros, o None si faltan datos
    """
    if not all([lat1, lon1, lat2, lon2]):
        return None

    try:
        R = 6371.0  # radio de la Tierra en km
        dlat = radians(float(lat2) - float(lat1))
        dlon = radians(float(lon2) - float(lon1))

        a = (sin(dlat / 2)**2 +
             cos(radians(float(lat1))) * cos(radians(float(lat2))) * sin(dlon / 2)**2)
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return round(R * c, 2)
    except (ValueError, TypeError):
        return None


# ==========================================================
# VEHÍCULO
# ==========================================================
class RepartidorVehiculoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = RepartidorVehiculo
        fields = ['id', 'tipo', 'tipo_display', 'placa', 'activo', 'licencia_foto', 'creado_en']
        read_only_fields = ['id', 'tipo_display', 'creado_en']

    def validate_placa(self, value):
        """Valida formato básico de placa (opcional, ajusta según tu país)."""
        if value and len(value.strip()) < 3:
            raise serializers.ValidationError("La placa debe tener al menos 3 caracteres.")
        return value.strip().upper() if value else value


# ==========================================================
# HISTORIAL DE UBICACIÓN
# ==========================================================
class HistorialUbicacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialUbicacion
        fields = ['id', 'latitud', 'longitud', 'timestamp']
        read_only_fields = ['id', 'timestamp']


# ==========================================================
# CALIFICACIONES (CLIENTE → REPARTIDOR)
# ==========================================================
class CalificacionRepartidorSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.get_full_name', read_only=True)
    cliente_email = serializers.EmailField(source='cliente.email', read_only=True)

    class Meta:
        model = CalificacionRepartidor
        fields = [
            'id', 'cliente_nombre', 'cliente_email',
            'puntuacion', 'comentario', 'pedido_id', 'creado_en'
        ]
        read_only_fields = ['id', 'cliente_nombre', 'cliente_email', 'creado_en']

    def validate_puntuacion(self, value):
        """Valida que la puntuación esté en el rango correcto."""
        if not (1 <= value <= 5):
            raise serializers.ValidationError("La puntuación debe estar entre 1 y 5.")
        return value


class CalificacionRepartidorCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear calificaciones (sin exponer datos sensibles)."""

    class Meta:
        model = CalificacionRepartidor
        fields = ['puntuacion', 'comentario']

    def validate_puntuacion(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("La puntuación debe estar entre 1 y 5.")
        return value

    def validate_comentario(self, value):
        if value and len(value) > 500:
            raise serializers.ValidationError("El comentario no puede exceder 500 caracteres.")
        return value


# ==========================================================
# CALIFICACIONES (REPARTIDOR → CLIENTE)
# ==========================================================
class CalificacionClienteSerializer(serializers.ModelSerializer):
    repartidor_nombre = serializers.CharField(source='repartidor.user.get_full_name', read_only=True)

    class Meta:
        model = CalificacionCliente
        fields = [
            'id', 'repartidor_nombre',
            'puntuacion', 'comentario', 'pedido_id', 'creado_en'
        ]
        read_only_fields = ['id', 'repartidor_nombre', 'creado_en']

    def validate_puntuacion(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("La puntuación debe estar entre 1 y 5.")
        return value


class CalificacionClienteCreateSerializer(serializers.ModelSerializer):
    """Serializer para que repartidores califiquen clientes."""

    class Meta:
        model = CalificacionCliente
        fields = ['puntuacion', 'comentario']

    def validate_puntuacion(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("La puntuación debe estar entre 1 y 5.")
        return value

    def validate_comentario(self, value):
        if value and len(value) > 500:
            raise serializers.ValidationError("El comentario no puede exceder 500 caracteres.")
        return value


# ==========================================================
# PERFIL COMPLETO DEL REPARTIDOR (PROPIO)
# ==========================================================
class RepartidorPerfilSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    vehiculos = RepartidorVehiculoSerializer(many=True, read_only=True)
    calificaciones_recientes = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    total_calificaciones = serializers.SerializerMethodField()

    class Meta:
        model = Repartidor
        fields = [
            'id', 'nombre_completo', 'email', 'foto_perfil',
            'cedula', 'telefono',
            'estado', 'estado_display', 'verificado', 'activo',
            'latitud', 'longitud', 'ultima_localizacion',
            'entregas_completadas', 'calificacion_promedio', 'total_calificaciones',
            'vehiculos', 'calificaciones_recientes',
            'creado_en', 'actualizado_en'
        ]
        read_only_fields = [
            'id', 'nombre_completo', 'email', 'cedula',
            'estado', 'verificado', 'activo',
            'latitud', 'longitud', 'ultima_localizacion',
            'entregas_completadas', 'calificacion_promedio',
            'creado_en', 'actualizado_en'
        ]

    def get_calificaciones_recientes(self, obj):
        """Retorna las últimas 5 calificaciones."""
        calificaciones = obj.calificaciones.order_by('-creado_en')[:5]
        return CalificacionRepartidorSerializer(calificaciones, many=True).data

    def get_total_calificaciones(self, obj):
        """Retorna el total de calificaciones recibidas."""
        return obj.calificaciones.count()


# ==========================================================
# PERFIL PARA EDICIÓN (PROPIO)
# ==========================================================
class RepartidorUpdateSerializer(serializers.ModelSerializer):
    telefono = serializers.CharField(
        required=False,
        validators=[
            RegexValidator(
                r'^\+?[0-9]{7,15}$',
                message="Número de teléfono inválido. Formato: +593987654321 o 0987654321"
            )
        ]
    )

    class Meta:
        model = Repartidor
        fields = ['foto_perfil', 'telefono']
        extra_kwargs = {
            'foto_perfil': {'required': False},
            'telefono': {'required': False},
        }

    def validate_foto_perfil(self, value):
        """Valida tamaño y tipo de imagen."""
        if value:
            # Validar tamaño (máximo 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("La imagen no puede superar 5MB.")

            # Validar extensión
            valid_extensions = ['jpg', 'jpeg', 'png', 'webp']
            ext = value.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise serializers.ValidationError(
                    f"Formato no válido. Usa: {', '.join(valid_extensions)}"
                )

        return value


# ==========================================================
# ESTADO (disponible / ocupado / fuera_servicio)
# ==========================================================
class RepartidorEstadoSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=EstadoRepartidor.choices)

    def validate_estado(self, value):
        """Valida que el repartidor pueda cambiar a ese estado."""
        repartidor = self.context.get('repartidor')

        if not repartidor:
            raise serializers.ValidationError("No se pudo identificar al repartidor.")

        if not repartidor.activo:
            raise serializers.ValidationError(
                "No puedes cambiar de estado: tu cuenta está desactivada."
            )

        if value in (EstadoRepartidor.DISPONIBLE, EstadoRepartidor.OCUPADO):
            if not repartidor.verificado:
                raise serializers.ValidationError(
                    "No puedes cambiar a ese estado: no estás verificado por un administrador."
                )

        return value


# ==========================================================
# UBICACIÓN
# ==========================================================
class RepartidorUbicacionSerializer(serializers.Serializer):
    latitud = serializers.FloatField()
    longitud = serializers.FloatField()

    def validate(self, data):
        """Valida que las coordenadas estén dentro del rango de Ecuador."""
        lat, lon = data['latitud'], data['longitud']

        if not (-5.0 <= lat <= 2.0):
            raise serializers.ValidationError({
                'latitud': 'Fuera del rango de Ecuador (-5° a 2°)'
            })

        if not (-92.0 <= lon <= -75.0):
            raise serializers.ValidationError({
                'longitud': 'Fuera del rango de Ecuador (-92° a -75°)'
            })

        return data


# ==========================================================
# PERFIL PÚBLICO (CLIENTE VE AL REPARTIDOR)
# ==========================================================
class RepartidorPublicoSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='user.get_full_name', read_only=True)
    tipo_vehiculo_activo = serializers.SerializerMethodField()
    placa_vehiculo_activa = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Repartidor
        fields = [
            'id', 'nombre', 'foto_perfil',
            'calificacion_promedio', 'entregas_completadas',
            'estado', 'estado_display',
            'latitud', 'longitud', 'ultima_localizacion',
            'tipo_vehiculo_activo', 'placa_vehiculo_activa'
        ]

    def get_tipo_vehiculo_activo(self, obj):
        """Retorna el tipo de vehículo activo."""
        vehiculo = obj.vehiculos.filter(activo=True).first()
        return vehiculo.get_tipo_display() if vehiculo else None

    def get_placa_vehiculo_activa(self, obj):
        """Retorna la placa del vehículo activo."""
        vehiculo = obj.vehiculos.filter(activo=True).first()
        return vehiculo.placa if vehiculo else None


# ==========================================================
# PERFIL PÚBLICO CON DISTANCIA AL CLIENTE (para tracking)
# ==========================================================
class RepartidorPublicoDistanciaSerializer(RepartidorPublicoSerializer):
    distancia_cliente = serializers.SerializerMethodField()
    tiempo_estimado_minutos = serializers.SerializerMethodField()

    class Meta(RepartidorPublicoSerializer.Meta):
        fields = RepartidorPublicoSerializer.Meta.fields + [
            'distancia_cliente',
            'tiempo_estimado_minutos'
        ]

    def get_distancia_cliente(self, obj):
        """Calcula distancia en km entre repartidor y cliente."""
        lat_cliente = self.context.get('lat_cliente')
        lon_cliente = self.context.get('lon_cliente')

        if lat_cliente is not None and lon_cliente is not None:
            if obj.latitud and obj.longitud:
                return calcular_distancia(
                    obj.latitud,
                    obj.longitud,
                    lat_cliente,
                    lon_cliente
                )

        return None

    def get_tiempo_estimado_minutos(self, obj):
        """Estima tiempo de llegada en minutos (velocidad promedio 30 km/h)."""
        distancia = self.get_distancia_cliente(obj)

        if distancia is not None:
            # Velocidad promedio en ciudad: 30 km/h
            velocidad_kmh = 30
            tiempo_horas = distancia / velocidad_kmh
            tiempo_minutos = int(tiempo_horas * 60)
            return max(tiempo_minutos, 1)  # Mínimo 1 minuto

        return None


# ==========================================================
# LOG DE ESTADO (solo lectura)
# ==========================================================
class RepartidorEstadoLogSerializer(serializers.ModelSerializer):
    estado_anterior_display = serializers.CharField(
        source='get_estado_anterior_display',
        read_only=True
    )
    estado_nuevo_display = serializers.CharField(
        source='get_estado_nuevo_display',
        read_only=True
    )
    timestamp_local = serializers.SerializerMethodField()

    class Meta:
        model = RepartidorEstadoLog
        fields = [
            'id',
            'estado_anterior',
            'estado_anterior_display',
            'estado_nuevo',
            'estado_nuevo_display',
            'motivo',
            'timestamp',
            'timestamp_local'
        ]
        read_only_fields = fields

    def get_timestamp_local(self, obj):
        """Retorna timestamp en zona horaria local."""
        from django.utils.timezone import localtime
        return localtime(obj.timestamp).isoformat()


# ==========================================================
# ESTADÍSTICAS DEL REPARTIDOR
# ==========================================================
class RepartidorEstadisticasSerializer(serializers.ModelSerializer):
    """Serializer para dashboard con métricas del repartidor."""

    total_calificaciones = serializers.IntegerField(read_only=True)
    calificaciones_5_estrellas = serializers.IntegerField(read_only=True)
    tasa_aceptacion = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Repartidor
        fields = [
            'entregas_completadas',
            'calificacion_promedio',
            'total_calificaciones',
            'calificaciones_5_estrellas',
            'tasa_aceptacion'
        ]
