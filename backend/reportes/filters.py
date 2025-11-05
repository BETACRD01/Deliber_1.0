# reportes/filters.py
"""
Filtros personalizados para reportes de pedidos
✅ Usa django-filter para filtros avanzados
✅ Soporta rangos de fechas, búsquedas y filtros múltiples
"""
import django_filters
from django.db.models import Q
from pedidos.models import Pedido, EstadoPedido, TipoPedido
from django.utils import timezone
from datetime import timedelta


class PedidoReporteFilter(django_filters.FilterSet):
    """
    Filtro completo para reportes de pedidos
    ✅ Rangos de fechas, estados, tipos, búsquedas
    """

    # ============================================
    # FILTROS DE FECHA
    # ============================================
    fecha_inicio = django_filters.DateFilter(
        field_name='creado_en',
        lookup_expr='date__gte',
        label='Fecha inicio'
    )

    fecha_fin = django_filters.DateFilter(
        field_name='creado_en',
        lookup_expr='date__lte',
        label='Fecha fin'
    )

    # Filtros predefinidos de tiempo
    periodo = django_filters.ChoiceFilter(
        method='filtrar_por_periodo',
        choices=[
            ('hoy', 'Hoy'),
            ('ayer', 'Ayer'),
            ('ultima_semana', 'Última semana'),
            ('ultimo_mes', 'Último mes'),
            ('este_mes', 'Este mes'),
        ],
        label='Período'
    )

    # ============================================
    # FILTROS DE ESTADO Y TIPO
    # ============================================
    estado = django_filters.MultipleChoiceFilter(
        choices=EstadoPedido.choices,
        label='Estado(s)'
    )

    tipo = django_filters.ChoiceFilter(
        choices=TipoPedido.choices,
        label='Tipo de pedido'
    )

    # ============================================
    # FILTROS POR RELACIONES
    # ============================================
    cliente = django_filters.NumberFilter(
        field_name='cliente__id',
        label='ID Cliente'
    )

    cliente_email = django_filters.CharFilter(
        field_name='cliente__user__email',
        lookup_expr='icontains',
        label='Email del cliente'
    )

    proveedor = django_filters.NumberFilter(
        field_name='proveedor__id',
        label='ID Proveedor'
    )

    proveedor_nombre = django_filters.CharFilter(
        field_name='proveedor__nombre',
        lookup_expr='icontains',
        label='Nombre del proveedor'
    )

    repartidor = django_filters.NumberFilter(
        field_name='repartidor__id',
        label='ID Repartidor'
    )

    # ============================================
    # FILTROS FINANCIEROS
    # ============================================
    total_min = django_filters.NumberFilter(
        field_name='total',
        lookup_expr='gte',
        label='Total mínimo'
    )

    total_max = django_filters.NumberFilter(
        field_name='total',
        lookup_expr='lte',
        label='Total máximo'
    )

    metodo_pago = django_filters.CharFilter(
        field_name='metodo_pago',
        lookup_expr='iexact',
        label='Método de pago'
    )

    # ============================================
    # FILTROS BOOLEANOS
    # ============================================
    con_repartidor = django_filters.BooleanFilter(
        method='filtrar_con_repartidor',
        label='Tiene repartidor asignado'
    )

    solo_entregados = django_filters.BooleanFilter(
        method='filtrar_entregados',
        label='Solo pedidos entregados'
    )

    solo_cancelados = django_filters.BooleanFilter(
        method='filtrar_cancelados',
        label='Solo pedidos cancelados'
    )

    solo_activos = django_filters.BooleanFilter(
        method='filtrar_activos',
        label='Solo pedidos activos'
    )

    # ============================================
    # BÚSQUEDA GENERAL
    # ============================================
    buscar = django_filters.CharFilter(
        method='busqueda_general',
        label='Búsqueda general'
    )

    # ============================================
    # ORDENAMIENTO
    # ============================================
    ordenar_por = django_filters.OrderingFilter(
        fields=(
            ('creado_en', 'fecha'),
            ('total', 'total'),
            ('ganancia_app', 'ganancia'),
            ('estado', 'estado'),
        ),
        field_labels={
            'creado_en': 'Fecha de creación',
            'total': 'Total',
            'ganancia_app': 'Ganancia app',
            'estado': 'Estado',
        }
    )

    class Meta:
        model = Pedido
        fields = []

    # ============================================
    # MÉTODOS PERSONALIZADOS
    # ============================================

    def filtrar_por_periodo(self, queryset, name, value):
        """
        Filtra por períodos predefinidos
        """
        hoy = timezone.now().date()

        if value == 'hoy':
            return queryset.filter(creado_en__date=hoy)

        elif value == 'ayer':
            ayer = hoy - timedelta(days=1)
            return queryset.filter(creado_en__date=ayer)

        elif value == 'ultima_semana':
            hace_semana = hoy - timedelta(days=7)
            return queryset.filter(creado_en__date__gte=hace_semana)

        elif value == 'ultimo_mes':
            hace_mes = hoy - timedelta(days=30)
            return queryset.filter(creado_en__date__gte=hace_mes)

        elif value == 'este_mes':
            primer_dia_mes = hoy.replace(day=1)
            return queryset.filter(creado_en__date__gte=primer_dia_mes)

        return queryset

    def filtrar_con_repartidor(self, queryset, name, value):
        """
        Filtra pedidos con o sin repartidor
        """
        if value:
            return queryset.filter(repartidor__isnull=False)
        else:
            return queryset.filter(repartidor__isnull=True)

    def filtrar_entregados(self, queryset, name, value):
        """
        Filtra solo pedidos entregados
        """
        if value:
            return queryset.filter(estado=EstadoPedido.ENTREGADO)
        return queryset

    def filtrar_cancelados(self, queryset, name, value):
        """
        Filtra solo pedidos cancelados
        """
        if value:
            return queryset.filter(estado=EstadoPedido.CANCELADO)
        return queryset

    def filtrar_activos(self, queryset, name, value):
        """
        Filtra solo pedidos activos (confirmado, en preparación, en ruta)
        """
        if value:
            return queryset.filter(
                estado__in=[
                    EstadoPedido.CONFIRMADO,
                    EstadoPedido.EN_PREPARACION,
                    EstadoPedido.EN_RUTA
                ]
            )
        return queryset

    def busqueda_general(self, queryset, name, value):
        """
        Búsqueda en múltiples campos
        """
        return queryset.filter(
            Q(id__icontains=value) |
            Q(descripcion__icontains=value) |
            Q(cliente__user__email__icontains=value) |
            Q(cliente__user__first_name__icontains=value) |
            Q(cliente__user__last_name__icontains=value) |
            Q(proveedor__nombre__icontains=value) |
            Q(repartidor__user__first_name__icontains=value) |
            Q(repartidor__user__last_name__icontains=value) |
            Q(direccion_entrega__icontains=value)
        )


# ============================================
# FILTRO SIMPLIFICADO PARA PROVEEDORES
# ============================================

class PedidoProveedorFilter(django_filters.FilterSet):
    """
    Filtro simplificado para proveedores (solo ven sus pedidos)
    """
    fecha_inicio = django_filters.DateFilter(
        field_name='creado_en',
        lookup_expr='date__gte',
        label='Fecha inicio'
    )

    fecha_fin = django_filters.DateFilter(
        field_name='creado_en',
        lookup_expr='date__lte',
        label='Fecha fin'
    )

    estado = django_filters.MultipleChoiceFilter(
        choices=EstadoPedido.choices,
        label='Estado(s)'
    )

    periodo = django_filters.ChoiceFilter(
        method='filtrar_por_periodo',
        choices=[
            ('hoy', 'Hoy'),
            ('ultima_semana', 'Última semana'),
            ('este_mes', 'Este mes'),
        ],
        label='Período'
    )

    class Meta:
        model = Pedido
        fields = []

    def filtrar_por_periodo(self, queryset, name, value):
        """Reutiliza la lógica del filtro principal"""
        filtro = PedidoReporteFilter()
        return filtro.filtrar_por_periodo(queryset, name, value)


# ============================================
# FILTRO SIMPLIFICADO PARA REPARTIDORES
# ============================================

class PedidoRepartidorFilter(django_filters.FilterSet):
    """
    Filtro simplificado para repartidores (solo ven sus entregas)
    """
    fecha_inicio = django_filters.DateFilter(
        field_name='creado_en',
        lookup_expr='date__gte',
        label='Fecha inicio'
    )

    fecha_fin = django_filters.DateFilter(
        field_name='creado_en',
        lookup_expr='date__lte',
        label='Fecha fin'
    )

    estado = django_filters.MultipleChoiceFilter(
        choices=EstadoPedido.choices,
        label='Estado(s)'
    )

    periodo = django_filters.ChoiceFilter(
        method='filtrar_por_periodo',
        choices=[
            ('hoy', 'Hoy'),
            ('ultima_semana', 'Última semana'),
            ('este_mes', 'Este mes'),
        ],
        label='Período'
    )

    solo_entregados = django_filters.BooleanFilter(
        method='filtrar_entregados',
        label='Solo entregas completadas'
    )

    class Meta:
        model = Pedido
        fields = []

    def filtrar_por_periodo(self, queryset, name, value):
        """Reutiliza la lógica del filtro principal"""
        filtro = PedidoReporteFilter()
        return filtro.filtrar_por_periodo(queryset, name, value)

    def filtrar_entregados(self, queryset, name, value):
        """Reutiliza la lógica del filtro principal"""
        filtro = PedidoReporteFilter()
        return filtro.filtrar_entregados(queryset, name, value)
