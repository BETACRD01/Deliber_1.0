# notificaciones/serializers.py
"""
Serializers para API de notificaciones
✅ Serializers para lectura y escritura
✅ Campos calculados
✅ Información del pedido relacionado
"""

from rest_framework import serializers
from notificaciones.models import Notificacion
from pedidos.models import Pedido


class PedidoMiniSerializer(serializers.ModelSerializer):
    """
    ✅ Serializer mínimo del pedido para notificaciones
    """
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'estado',
            'estado_display',
            'total',
            'creado_en'
        ]
        read_only_fields = fields


class NotificacionSerializer(serializers.ModelSerializer):
    """
    ✅ Serializer principal de notificaciones
    """
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    tiempo_transcurrido = serializers.CharField(read_only=True)
    pedido_info = PedidoMiniSerializer(source='pedido', read_only=True)

    class Meta:
        model = Notificacion
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'titulo',
            'mensaje',
            'datos_extra',
            'leida',
            'enviada_push',
            'pedido',
            'pedido_info',
            'tiempo_transcurrido',
            'creada_en',
            'leida_en'
        ]
        read_only_fields = [
            'id',
            'tipo',
            'titulo',
            'mensaje',
            'datos_extra',
            'enviada_push',
            'pedido',
            'tiempo_transcurrido',
            'creada_en',
            'leida_en'
        ]


class NotificacionListSerializer(serializers.ModelSerializer):
    """
    ✅ Serializer optimizado para listado (sin pedido_info completo)
    """
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    tiempo_transcurrido = serializers.CharField(read_only=True)
    pedido_id = serializers.UUIDField(source='pedido.id', read_only=True, allow_null=True)

    class Meta:
        model = Notificacion
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'titulo',
            'mensaje',
            'leida',
            'pedido_id',
            'tiempo_transcurrido',
            'creada_en'
        ]
        read_only_fields = fields


class MarcarLeidaSerializer(serializers.Serializer):
    """
    ✅ Serializer para marcar notificaciones como leídas
    """
    notificacion_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text='Lista de IDs de notificaciones a marcar como leídas'
    )

    marcar_todas = serializers.BooleanField(
        required=False,
        default=False,
        help_text='Si es True, marca todas las notificaciones como leídas'
    )

    def validate(self, data):
        """Validar que al menos una opción esté presente"""
        if not data.get('marcar_todas') and not data.get('notificacion_ids'):
            raise serializers.ValidationError(
                "Debes proporcionar 'notificacion_ids' o 'marcar_todas=true'"
            )

        return data


class EstadisticasNotificacionesSerializer(serializers.Serializer):
    """
    ✅ Serializer para estadísticas de notificaciones
    """
    total_notificaciones = serializers.IntegerField()
    no_leidas = serializers.IntegerField()
    leidas = serializers.IntegerField()
    por_tipo = serializers.DictField()
    ultima_notificacion = serializers.DateTimeField(allow_null=True)
