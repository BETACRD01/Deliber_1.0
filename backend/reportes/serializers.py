# reportes/serializers.py
"""
Serializers para el sistema de reportes de pedidos
✅ Optimizado para reportes con select_related y prefetch_related
✅ Incluye datos agregados y estadísticas
"""
from rest_framework import serializers
from pedidos.models import Pedido, EstadoPedido, TipoPedido
from usuarios.models import Perfil
from repartidores.models import Repartidor
from proveedores.models import Proveedor
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone


# ============================================
# SERIALIZER: PEDIDO PARA REPORTE (DETALLADO)
# ============================================

class PedidoReporteSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para reportes de pedidos
    ✅ Incluye información relacionada optimizada
    """
    # Cliente
    cliente_id = serializers.IntegerField(source='cliente.id', read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.user.get_full_name', read_only=True)
    cliente_email = serializers.EmailField(source='cliente.user.email', read_only=True)
    cliente_celular = serializers.CharField(source='cliente.user.celular', read_only=True)

    # Proveedor
    proveedor_id = serializers.IntegerField(source='proveedor.id', read_only=True, allow_null=True)
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True, allow_null=True)
    proveedor_tipo = serializers.CharField(source='proveedor.tipo_proveedor', read_only=True, allow_null=True)

    # Repartidor
    repartidor_id = serializers.IntegerField(source='repartidor.id', read_only=True, allow_null=True)
    repartidor_nombre = serializers.SerializerMethodField()
    repartidor_celular = serializers.CharField(source='repartidor.user.celular', read_only=True, allow_null=True)

    # Estados y tipos legibles
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    # Propiedades calculadas
    tiempo_transcurrido = serializers.CharField(read_only=True)
    distancia_estimada = serializers.FloatField(read_only=True, allow_null=True)
    tiempo_entrega_total = serializers.SerializerMethodField()

    # Porcentajes de comisión
    porcentaje_repartidor = serializers.DecimalField(
        source='porcentaje_comision_repartidor',
        max_digits=5,
        decimal_places=2,
        read_only=True
    )
    porcentaje_proveedor = serializers.DecimalField(
        source='porcentaje_comision_proveedor',
        max_digits=5,
        decimal_places=2,
        read_only=True
    )
    porcentaje_app = serializers.DecimalField(
        source='porcentaje_ganancia_app',
        max_digits=5,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Pedido
        fields = [
            # IDs
            'id',

            # Información básica
            'tipo', 'tipo_display',
            'estado', 'estado_display',
            'descripcion',
            'total',
            'metodo_pago',

            # Cliente
            'cliente_id',
            'cliente_nombre',
            'cliente_email',
            'cliente_celular',

            # Proveedor
            'proveedor_id',
            'proveedor_nombre',
            'proveedor_tipo',

            # Repartidor
            'repartidor_id',
            'repartidor_nombre',
            'repartidor_celular',

            # Ubicaciones
            'direccion_entrega',
            'direccion_origen',
            'distancia_estimada',

            # Comisiones
            'comision_repartidor',
            'comision_proveedor',
            'ganancia_app',
            'porcentaje_repartidor',
            'porcentaje_proveedor',
            'porcentaje_app',

            # Fechas
            'creado_en',
            'actualizado_en',
            'fecha_entregado',
            'tiempo_transcurrido',
            'tiempo_entrega_total',

            # Estados de control
            'aceptado_por_repartidor',
            'confirmado_por_proveedor',
            'cancelado_por',
        ]

    def get_repartidor_nombre(self, obj):
        """Obtiene el nombre del repartidor"""
        if obj.repartidor:
            return obj.repartidor.user.get_full_name()
        return None

    def get_tiempo_entrega_total(self, obj):
        """Calcula el tiempo total de entrega"""
        return obj.calcular_tiempo_total_entrega()


# ============================================
# SERIALIZER: PEDIDO RESUMIDO (PARA LISTADOS)
# ============================================

class PedidoReporteResumidoSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listados grandes
    ✅ Menos campos para mejor performance
    """
    cliente_nombre = serializers.CharField(source='cliente.user.get_full_name', read_only=True)
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True, allow_null=True)
    repartidor_nombre = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'id',
            'tipo', 'tipo_display',
            'estado', 'estado_display',
            'cliente_nombre',
            'proveedor_nombre',
            'repartidor_nombre',
            'total',
            'ganancia_app',
            'creado_en',
            'fecha_entregado',
        ]

    def get_repartidor_nombre(self, obj):
        if obj.repartidor:
            return obj.repartidor.user.get_full_name()
        return None


# ============================================
# SERIALIZER: ESTADÍSTICAS GENERALES
# ============================================

class EstadisticasGeneralesSerializer(serializers.Serializer):
    """
    Serializer para estadísticas globales del sistema
    """
    # Totales
    total_pedidos = serializers.IntegerField()
    pedidos_hoy = serializers.IntegerField()
    pedidos_mes_actual = serializers.IntegerField()

    # Por estado
    pedidos_confirmados = serializers.IntegerField()
    pedidos_en_preparacion = serializers.IntegerField()
    pedidos_en_ruta = serializers.IntegerField()
    pedidos_entregados = serializers.IntegerField()
    pedidos_cancelados = serializers.IntegerField()

    # Por tipo
    pedidos_proveedor = serializers.IntegerField()
    pedidos_directos = serializers.IntegerField()

    # Financiero
    ingresos_totales = serializers.DecimalField(max_digits=10, decimal_places=2)
    ingresos_hoy = serializers.DecimalField(max_digits=10, decimal_places=2)
    ingresos_mes_actual = serializers.DecimalField(max_digits=10, decimal_places=2)
    ganancia_app_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    ganancia_app_hoy = serializers.DecimalField(max_digits=10, decimal_places=2)
    ganancia_app_mes = serializers.DecimalField(max_digits=10, decimal_places=2)

    # Promedios
    ticket_promedio = serializers.DecimalField(max_digits=8, decimal_places=2)
    comision_promedio_repartidor = serializers.DecimalField(max_digits=8, decimal_places=2)

    # Métricas de eficiencia
    tasa_entrega = serializers.DecimalField(max_digits=5, decimal_places=2)  # % de pedidos entregados
    tasa_cancelacion = serializers.DecimalField(max_digits=5, decimal_places=2)  # % de pedidos cancelados


# ============================================
# SERIALIZER: ESTADÍSTICAS POR PROVEEDOR
# ============================================

class EstadisticasProveedorSerializer(serializers.Serializer):
    """
    Estadísticas específicas para un proveedor
    """
    proveedor_id = serializers.IntegerField()
    proveedor_nombre = serializers.CharField()

    total_pedidos = serializers.IntegerField()
    pedidos_entregados = serializers.IntegerField()
    pedidos_cancelados = serializers.IntegerField()
    pedidos_activos = serializers.IntegerField()

    ingresos_totales = serializers.DecimalField(max_digits=10, decimal_places=2)
    comisiones_totales = serializers.DecimalField(max_digits=10, decimal_places=2)

    ticket_promedio = serializers.DecimalField(max_digits=8, decimal_places=2)
    tasa_entrega = serializers.DecimalField(max_digits=5, decimal_places=2)


# ============================================
# SERIALIZER: ESTADÍSTICAS POR REPARTIDOR
# ============================================

class EstadisticasRepartidorSerializer(serializers.Serializer):
    """
    Estadísticas específicas para un repartidor
    """
    repartidor_id = serializers.IntegerField()
    repartidor_nombre = serializers.CharField()

    total_entregas = serializers.IntegerField()
    entregas_hoy = serializers.IntegerField()
    entregas_mes = serializers.IntegerField()

    comisiones_totales = serializers.DecimalField(max_digits=10, decimal_places=2)
    comisiones_hoy = serializers.DecimalField(max_digits=10, decimal_places=2)
    comisiones_mes = serializers.DecimalField(max_digits=10, decimal_places=2)

    calificacion_promedio = serializers.DecimalField(max_digits=3, decimal_places=2)
    ticket_promedio = serializers.DecimalField(max_digits=8, decimal_places=2)


# ============================================
# SERIALIZER: MÉTRICAS DIARIAS
# ============================================

class MetricasDiariasSerializer(serializers.Serializer):
    """
    Métricas agregadas por día (para gráficos)
    """
    fecha = serializers.DateField()
    total_pedidos = serializers.IntegerField()
    pedidos_entregados = serializers.IntegerField()
    pedidos_cancelados = serializers.IntegerField()
    ingresos = serializers.DecimalField(max_digits=10, decimal_places=2)
    ganancia_app = serializers.DecimalField(max_digits=10, decimal_places=2)
    ticket_promedio = serializers.DecimalField(max_digits=8, decimal_places=2)


# ============================================
# SERIALIZER: TOP PROVEEDORES
# ============================================

class TopProveedoresSerializer(serializers.Serializer):
    """
    Top proveedores por ventas
    """
    proveedor_id = serializers.IntegerField()
    proveedor_nombre = serializers.CharField()
    proveedor_tipo = serializers.CharField()
    total_pedidos = serializers.IntegerField()
    ingresos_totales = serializers.DecimalField(max_digits=10, decimal_places=2)


# ============================================
# SERIALIZER: TOP REPARTIDORES
# ============================================

class TopRepartidoresSerializer(serializers.Serializer):
    """
    Top repartidores por entregas
    """
    repartidor_id = serializers.IntegerField()
    repartidor_nombre = serializers.CharField()
    total_entregas = serializers.IntegerField()
    comisiones_totales = serializers.DecimalField(max_digits=10, decimal_places=2)
    calificacion_promedio = serializers.DecimalField(max_digits=3, decimal_places=2)


# ============================================
# SERIALIZER: EXPORTACIÓN EXCEL
# ============================================

class ExportarReporteSerializer(serializers.Serializer):
    """
    Parámetros para exportar reportes
    """
    fecha_inicio = serializers.DateField(required=False, allow_null=True)
    fecha_fin = serializers.DateField(required=False, allow_null=True)
    estado = serializers.ChoiceField(
        choices=EstadoPedido.choices,
        required=False,
        allow_null=True,
        allow_blank=True
    )
    tipo = serializers.ChoiceField(
        choices=TipoPedido.choices,
        required=False,
        allow_null=True,
        allow_blank=True
    )
    proveedor_id = serializers.IntegerField(required=False, allow_null=True)
    repartidor_id = serializers.IntegerField(required=False, allow_null=True)
    formato = serializers.ChoiceField(
        choices=['excel', 'csv'],
        default='excel'
    )
