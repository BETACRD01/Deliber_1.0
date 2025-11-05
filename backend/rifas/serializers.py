# -*- coding: utf-8 -*-
# rifas/serializers.py
"""
Serializadores para API REST de Rifas

✅ FUNCIONALIDADES:
- Serialización completa de rifas
- Elegibilidad de usuarios
- Participantes y ganadores
- Estadísticas en tiempo real
- Optimización de queries
"""

from rest_framework import serializers
from django.utils import timezone
from django.db.models import Count, Q
from .models import Rifa, Participacion, EstadoRifa
from authentication.models import User
from pedidos.models import EstadoPedido
import logging

logger = logging.getLogger('rifas')


# ============================================
# 👤 SERIALIZER: USUARIO SIMPLE
# ============================================

class UsuarioSimpleSerializer(serializers.ModelSerializer):
    """
    Serializer básico para mostrar info de usuarios
    (usado en ganadores y participantes)
    """

    nombre_completo = serializers.CharField(
        source='get_full_name',
        read_only=True
    )

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'nombre_completo'
        ]
        read_only_fields = fields


# ============================================
# 🎲 SERIALIZER: RIFA (LISTADO)
# ============================================

class RifaListSerializer(serializers.ModelSerializer):
    """
    Serializer para listado de rifas (sin detalles pesados)
    Optimizado para performance en listas
    """

    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )

    mes_nombre = serializers.CharField(read_only=True)

    dias_restantes = serializers.IntegerField(read_only=True)

    total_participantes = serializers.SerializerMethodField()

    ganador = UsuarioSimpleSerializer(read_only=True)

    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = Rifa
        fields = [
            'id',
            'titulo',
            'premio',
            'valor_premio',
            'imagen_url',
            'fecha_inicio',
            'fecha_fin',
            'mes',
            'anio',
            'mes_nombre',
            'estado',
            'estado_display',
            'dias_restantes',
            'total_participantes',
            'ganador',
            'fecha_sorteo'
        ]
        read_only_fields = fields

    def get_total_participantes(self, obj):
        """Calcula total de participantes elegibles"""
        # Usamos el método del modelo que ya está optimizado
        return obj.total_participantes

    def get_imagen_url(self, obj):
        """URL completa de la imagen"""
        if obj.imagen:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None


# ============================================
# 🎯 SERIALIZER: ELEGIBILIDAD DE USUARIO
# ============================================

class ElegibilidadSerializer(serializers.Serializer):
    """
    Serializer para verificar elegibilidad de un usuario
    """

    elegible = serializers.BooleanField()
    pedidos = serializers.IntegerField()
    faltantes = serializers.IntegerField()
    razon = serializers.CharField()

    class Meta:
        fields = [
            'elegible',
            'pedidos',
            'faltantes',
            'razon'
        ]


# ============================================
# 👥 SERIALIZER: PARTICIPANTE
# ============================================

class ParticipanteSerializer(serializers.Serializer):
    """
    Serializer para participantes elegibles de una rifa
    """

    usuario = UsuarioSimpleSerializer()
    pedidos_completados = serializers.IntegerField()
    elegible = serializers.BooleanField()

    class Meta:
        fields = [
            'usuario',
            'pedidos_completados',
            'elegible'
        ]


# ============================================
# 🎲 SERIALIZER: RIFA (DETALLE COMPLETO)
# ============================================

class RifaDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo con todos los detalles de la rifa
    Incluye estadísticas y participantes
    """

    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )

    mes_nombre = serializers.CharField(read_only=True)

    dias_restantes = serializers.IntegerField(read_only=True)

    esta_activa = serializers.BooleanField(read_only=True)

    total_participantes = serializers.SerializerMethodField()

    ganador = UsuarioSimpleSerializer(read_only=True)

    creado_por = UsuarioSimpleSerializer(read_only=True)

    imagen_url = serializers.SerializerMethodField()

    # Elegibilidad del usuario actual
    mi_elegibilidad = serializers.SerializerMethodField()

    # Estadísticas adicionales
    estadisticas = serializers.SerializerMethodField()

    class Meta:
        model = Rifa
        fields = [
            'id',
            'titulo',
            'descripcion',
            'premio',
            'valor_premio',
            'imagen_url',
            'fecha_inicio',
            'fecha_fin',
            'fecha_sorteo',
            'pedidos_minimos',
            'mes',
            'anio',
            'mes_nombre',
            'estado',
            'estado_display',
            'esta_activa',
            'dias_restantes',
            'total_participantes',
            'ganador',
            'creado_por',
            'creado_en',
            'actualizado_en',
            'mi_elegibilidad',
            'estadisticas'
        ]
        read_only_fields = fields

    def get_total_participantes(self, obj):
        """Total de participantes elegibles"""
        return obj.total_participantes

    def get_imagen_url(self, obj):
        """URL completa de la imagen"""
        if obj.imagen:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None

    def get_mi_elegibilidad(self, obj):
        """
        Verifica elegibilidad del usuario autenticado
        Solo se incluye si hay un usuario autenticado
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None

        elegibilidad = obj.usuario_es_elegible(request.user)
        return ElegibilidadSerializer(elegibilidad).data

    def get_estadisticas(self, obj):
        """Estadísticas adicionales de la rifa"""
        return {
            'total_participantes': obj.total_participantes,
            'dias_restantes': obj.dias_restantes,
            'pedidos_minimos_requeridos': obj.pedidos_minimos,
            'tiene_ganador': obj.ganador is not None,
            'fecha_sorteo': obj.fecha_sorteo,
            'valor_premio': float(obj.valor_premio)
        }


# ============================================
# 📝 SERIALIZER: CREAR/ACTUALIZAR RIFA (ADMIN)
# ============================================

class RifaWriteSerializer(serializers.ModelSerializer):
    """
    Serializer para crear/actualizar rifas (solo admin)
    """

    class Meta:
        model = Rifa
        fields = [
            'titulo',
            'descripcion',
            'premio',
            'valor_premio',
            'imagen',
            'fecha_inicio',
            'fecha_fin',
            'pedidos_minimos',
            'estado'
        ]

    def validate_fecha_fin(self, value):
        """Validar que fecha_fin sea posterior a fecha_inicio"""
        fecha_inicio = self.initial_data.get('fecha_inicio')

        if fecha_inicio:
            from datetime import datetime
            if isinstance(fecha_inicio, str):
                fecha_inicio = datetime.fromisoformat(fecha_inicio.replace('Z', '+00:00'))

            if value <= fecha_inicio:
                raise serializers.ValidationError(
                    "La fecha de fin debe ser posterior a la fecha de inicio"
                )

        return value

    def validate(self, attrs):
        """Validaciones adicionales"""
        fecha_inicio = attrs.get('fecha_inicio')
        fecha_fin = attrs.get('fecha_fin')

        # Validar que sea del mismo mes
        if fecha_inicio and fecha_fin:
            if fecha_inicio.month != fecha_fin.month or fecha_inicio.year != fecha_fin.year:
                raise serializers.ValidationError({
                    'fecha_fin': 'La rifa debe estar dentro del mismo mes'
                })

        # Validar pedidos mínimos
        pedidos_minimos = attrs.get('pedidos_minimos', 3)
        if pedidos_minimos < 1:
            raise serializers.ValidationError({
                'pedidos_minimos': 'Debe requerir al menos 1 pedido'
            })

        return attrs

    def create(self, validated_data):
        """Crear rifa asignando el usuario creador"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['creado_por'] = request.user

        return super().create(validated_data)


# ============================================
# 🎟️ SERIALIZER: PARTICIPACIÓN
# ============================================

class ParticipacionSerializer(serializers.ModelSerializer):
    """
    Serializer para participaciones en rifas
    """

    rifa = RifaListSerializer(read_only=True)
    usuario = UsuarioSimpleSerializer(read_only=True)

    class Meta:
        model = Participacion
        fields = [
            'id',
            'rifa',
            'usuario',
            'ganador',
            'pedidos_completados',
            'fecha_registro'
        ]
        read_only_fields = fields


class ParticipacionSimpleSerializer(serializers.ModelSerializer):
    """
    Serializer simple para participaciones (sin datos anidados)
    """

    rifa_titulo = serializers.CharField(source='rifa.titulo', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)

    class Meta:
        model = Participacion
        fields = [
            'id',
            'rifa_titulo',
            'usuario_nombre',
            'ganador',
            'pedidos_completados',
            'fecha_registro'
        ]
        read_only_fields = fields


# ============================================
# 🎯 SERIALIZER: REALIZAR SORTEO (ADMIN)
# ============================================

class RealizarSorteoSerializer(serializers.Serializer):
    """
    Serializer para endpoint de realizar sorteo
    """

    confirmar = serializers.BooleanField(
        required=True,
        help_text="Debe ser true para confirmar el sorteo"
    )

    def validate_confirmar(self, value):
        """Validar que se confirme el sorteo"""
        if not value:
            raise serializers.ValidationError(
                "Debe confirmar el sorteo estableciendo 'confirmar' en true"
            )
        return value


class SorteoResultadoSerializer(serializers.Serializer):
    """
    Serializer para el resultado del sorteo
    """

    success = serializers.BooleanField()
    message = serializers.CharField()
    ganador = UsuarioSimpleSerializer(allow_null=True)
    rifa = RifaListSerializer()
    total_participantes = serializers.IntegerField()
    fecha_sorteo = serializers.DateTimeField()


# ============================================
# 📊 SERIALIZER: HISTORIAL DE GANADORES
# ============================================

class HistorialGanadoresSerializer(serializers.Serializer):
    """
    Serializer para historial de ganadores
    """

    rifa_id = serializers.UUIDField(source='id')
    titulo = serializers.CharField()
    mes_nombre = serializers.CharField()
    anio = serializers.IntegerField()
    premio = serializers.CharField()
    valor_premio = serializers.DecimalField(max_digits=10, decimal_places=2)
    ganador = UsuarioSimpleSerializer()
    fecha_sorteo = serializers.DateTimeField()
    total_participantes = serializers.IntegerField()

    class Meta:
        fields = [
            'rifa_id',
            'titulo',
            'mes_nombre',
            'anio',
            'premio',
            'valor_premio',
            'ganador',
            'fecha_sorteo',
            'total_participantes'
        ]


# ============================================
# 📊 SERIALIZER: ESTADÍSTICAS GENERALES
# ============================================

class EstadisticasRifasSerializer(serializers.Serializer):
    """
    Serializer para estadísticas generales del sistema de rifas
    """

    rifa_activa = RifaListSerializer(allow_null=True)

    total_rifas_realizadas = serializers.IntegerField()
    total_ganadores = serializers.IntegerField()
    valor_total_premios = serializers.DecimalField(max_digits=12, decimal_places=2)

    ultimos_ganadores = HistorialGanadoresSerializer(many=True)

    mi_participaciones = serializers.IntegerField()
    mis_victorias = serializers.IntegerField()

    class Meta:
        fields = [
            'rifa_activa',
            'total_rifas_realizadas',
            'total_ganadores',
            'valor_total_premios',
            'ultimos_ganadores',
            'mi_participaciones',
            'mis_victorias'
        ]


# ============================================
# 🎯 SERIALIZER: LISTA DE PARTICIPANTES (ADMIN)
# ============================================

class ListaParticipantesSerializer(serializers.Serializer):
    """
    Serializer para lista completa de participantes elegibles
    Solo accesible por admin
    """

    total = serializers.IntegerField()
    participantes = serializers.ListField(
        child=ParticipanteSerializer()
    )

    class Meta:
        fields = [
            'total',
            'participantes'
        ]


# ============================================
# 📱 SERIALIZER: RIFA ACTIVA (APP MÓVIL)
# ============================================

class RifaActivaAppSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para app móvil
    Solo la información esencial de la rifa activa
    """

    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )

    mes_nombre = serializers.CharField(read_only=True)
    dias_restantes = serializers.IntegerField(read_only=True)
    total_participantes = serializers.IntegerField(read_only=True)

    imagen_url = serializers.SerializerMethodField()

    # Elegibilidad del usuario
    puedo_participar = serializers.SerializerMethodField()
    mis_pedidos = serializers.SerializerMethodField()
    pedidos_faltantes = serializers.SerializerMethodField()

    class Meta:
        model = Rifa
        fields = [
            'id',
            'titulo',
            'descripcion',
            'premio',
            'valor_premio',
            'imagen_url',
            'fecha_fin',
            'mes_nombre',
            'dias_restantes',
            'total_participantes',
            'pedidos_minimos',
            'puedo_participar',
            'mis_pedidos',
            'pedidos_faltantes'
        ]

    def get_imagen_url(self, obj):
        """URL de imagen"""
        if obj.imagen:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None

    def get_puedo_participar(self, obj):
        """Verifica si el usuario puede participar"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        elegibilidad = obj.usuario_es_elegible(request.user)
        return elegibilidad['elegible']

    def get_mis_pedidos(self, obj):
        """Pedidos completados del usuario"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0

        elegibilidad = obj.usuario_es_elegible(request.user)
        return elegibilidad['pedidos']

    def get_pedidos_faltantes(self, obj):
        """Pedidos que le faltan al usuario"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return obj.pedidos_minimos

        elegibilidad = obj.usuario_es_elegible(request.user)
        return elegibilidad['faltantes']
