# pagos/filters.py
"""
Filtros personalizados para el módulo de Pagos (django-filter).

✅ CARACTERÍSTICAS:
- Filtros avanzados para pagos
- Búsquedas por rangos de fecha
- Filtros por método, estado, monto
- Filtros personalizados para transacciones
- Optimización de queries
"""
import django_filters
from django.db.models import Q
from django.utils import timezone
from .models import (
    Pago, Transaccion, MetodoPago,
    EstadoPago, TipoMetodoPago, TipoTransaccion
)


# ==========================================================
# 💰 FILTRO: PAGO
# ==========================================================

class PagoFilter(django_filters.FilterSet):
    """
    Filtro avanzado para pagos

    Uso:
    ?estado=completado
    ?metodo_pago=1
    ?metodo_pago_tipo=efectivo
    ?monto_min=10
    ?monto_max=100
    ?fecha_desde=2025-01-01
    ?fecha_hasta=2025-01-31
    ?cliente=5
    ?pedido=10
    ?requiere_verificacion=true
    ?fue_reembolsado=true
    ?buscar=ABC123
    """

    # ==========================================================
    # FILTROS BÁSICOS
    # ==========================================================

    estado = django_filters.MultipleChoiceFilter(
        field_name='estado',
        choices=EstadoPago.choices,
        help_text='Filtra por uno o múltiples estados'
    )

    metodo_pago = django_filters.ModelChoiceFilter(
        field_name='metodo_pago',
        queryset=MetodoPago.objects.all(),
        help_text='Filtra por método de pago'
    )

    metodo_pago_tipo = django_filters.ChoiceFilter(
        field_name='metodo_pago__tipo',
        choices=TipoMetodoPago.choices,
        help_text='Filtra por tipo de método (efectivo, transferencia, tarjetas)'
    )

    # ==========================================================
    # FILTROS POR MONTO
    # ==========================================================

    monto_min = django_filters.NumberFilter(
        field_name='monto',
        lookup_expr='gte',
        help_text='Monto mínimo'
    )

    monto_max = django_filters.NumberFilter(
        field_name='monto',
        lookup_expr='lte',
        help_text='Monto máximo'
    )

    monto_exacto = django_filters.NumberFilter(
        field_name='monto',
        lookup_expr='exact',
        help_text='Monto exacto'
    )

    # ==========================================================
    # FILTROS POR FECHA
    # ==========================================================

    fecha_desde = django_filters.DateFilter(
        field_name='creado_en',
        lookup_expr='date__gte',
        help_text='Fecha de creación desde (YYYY-MM-DD)'
    )

    fecha_hasta = django_filters.DateFilter(
        field_name='creado_en',
        lookup_expr='date__lte',
        help_text='Fecha de creación hasta (YYYY-MM-DD)'
    )

    fecha_exacta = django_filters.DateFilter(
        field_name='creado_en',
        lookup_expr='date',
        help_text='Fecha exacta (YYYY-MM-DD)'
    )

    fecha_completado_desde = django_filters.DateFilter(
        field_name='fecha_completado',
        lookup_expr='date__gte',
        help_text='Fecha de completado desde'
    )

    fecha_completado_hasta = django_filters.DateFilter(
        field_name='fecha_completado',
        lookup_expr='date__lte',
        help_text='Fecha de completado hasta'
    )

    # ==========================================================
    # FILTROS POR RELACIONES
    # ==========================================================

    cliente = django_filters.NumberFilter(
        field_name='pedido__cliente__id',
        help_text='ID del cliente'
    )

    cliente_email = django_filters.CharFilter(
        field_name='pedido__cliente__user__email',
        lookup_expr='icontains',
        help_text='Email del cliente (búsqueda parcial)'
    )

    pedido = django_filters.NumberFilter(
        field_name='pedido__id',
        help_text='ID del pedido'
    )

    verificado_por = django_filters.NumberFilter(
        field_name='verificado_por__id',
        help_text='ID del usuario que verificó'
    )

    # ==========================================================
    # FILTROS BOOLEANOS
    # ==========================================================

    requiere_verificacion = django_filters.BooleanFilter(
        method='filter_requiere_verificacion',
        help_text='Filtra pagos que requieren verificación manual'
    )

    fue_verificado = django_filters.BooleanFilter(
        field_name='verificado_por',
        lookup_expr='isnull',
        exclude=True,
        help_text='Filtra pagos que ya fueron verificados'
    )

    fue_reembolsado = django_filters.BooleanFilter(
        method='filter_fue_reembolsado',
        help_text='Filtra pagos que fueron reembolsados (total o parcial)'
    )

    es_efectivo = django_filters.BooleanFilter(
        method='filter_es_efectivo',
        help_text='Filtra pagos en efectivo'
    )

    es_tarjeta = django_filters.BooleanFilter(
        method='filter_es_tarjeta',
        help_text='Filtra pagos con tarjeta'
    )

    es_transferencia = django_filters.BooleanFilter(
        method='filter_es_transferencia',
        help_text='Filtra pagos por transferencia'
    )

    # ==========================================================
    # FILTROS ESPECIALES
    # ==========================================================

    referencia = django_filters.CharFilter(
        field_name='referencia',
        lookup_expr='iexact',
        help_text='Busca por referencia UUID exacta'
    )

    referencia_parcial = django_filters.CharFilter(
        field_name='referencia',
        lookup_expr='icontains',
        help_text='Busca por referencia UUID (parcial)'
    )

    pasarela_id = django_filters.CharFilter(
        field_name='pasarela_id_transaccion',
        lookup_expr='icontains',
        help_text='ID de transacción de la pasarela'
    )

    transferencia_numero = django_filters.CharFilter(
        field_name='transferencia_numero_operacion',
        lookup_expr='icontains',
        help_text='Número de operación de transferencia'
    )

    # ==========================================================
    # BÚSQUEDA GENERAL
    # ==========================================================

    buscar = django_filters.CharFilter(
        method='filter_buscar',
        help_text='Búsqueda general (referencia, pedido, cliente, notas)'
    )

    # ==========================================================
    # FILTROS DE TIEMPO RELATIVO
    # ==========================================================

    hoy = django_filters.BooleanFilter(
        method='filter_hoy',
        help_text='Pagos creados hoy'
    )

    esta_semana = django_filters.BooleanFilter(
        method='filter_esta_semana',
        help_text='Pagos de esta semana'
    )

    este_mes = django_filters.BooleanFilter(
        method='filter_este_mes',
        help_text='Pagos de este mes'
    )

    # ==========================================================
    # MÉTODOS DE FILTRADO PERSONALIZADO
    # ==========================================================

    def filter_requiere_verificacion(self, queryset, name, value):
        """Filtra pagos que requieren verificación manual"""
        if value:
            return queryset.filter(
                metodo_pago__requiere_verificacion=True,
                estado=EstadoPago.PENDIENTE,
                verificado_por__isnull=True
            )
        return queryset.exclude(
            metodo_pago__requiere_verificacion=True,
            estado=EstadoPago.PENDIENTE,
            verificado_por__isnull=True
        )

    def filter_fue_reembolsado(self, queryset, name, value):
        """Filtra pagos reembolsados"""
        if value:
            return queryset.filter(monto_reembolsado__gt=0)
        return queryset.filter(monto_reembolsado=0)

    def filter_es_efectivo(self, queryset, name, value):
        """Filtra pagos en efectivo"""
        if value:
            return queryset.filter(metodo_pago__tipo=TipoMetodoPago.EFECTIVO)
        return queryset.exclude(metodo_pago__tipo=TipoMetodoPago.EFECTIVO)

    def filter_es_tarjeta(self, queryset, name, value):
        """Filtra pagos con tarjeta"""
        if value:
            return queryset.filter(
                metodo_pago__tipo__in=[
                    TipoMetodoPago.TARJETA_CREDITO,
                    TipoMetodoPago.TARJETA_DEBITO
                ]
            )
        return queryset.exclude(
            metodo_pago__tipo__in=[
                TipoMetodoPago.TARJETA_CREDITO,
                TipoMetodoPago.TARJETA_DEBITO
            ]
        )

    def filter_es_transferencia(self, queryset, name, value):
        """Filtra pagos por transferencia"""
        if value:
            return queryset.filter(metodo_pago__tipo=TipoMetodoPago.TRANSFERENCIA)
        return queryset.exclude(metodo_pago__tipo=TipoMetodoPago.TRANSFERENCIA)

    def filter_buscar(self, queryset, name, value):
        """Búsqueda general en múltiples campos"""
        return queryset.filter(
            Q(referencia__icontains=value) |
            Q(pedido__id__icontains=value) |
            Q(pedido__cliente__user__email__icontains=value) |
            Q(pedido__cliente__user__first_name__icontains=value) |
            Q(pedido__cliente__user__last_name__icontains=value) |
            Q(notas__icontains=value) |
            Q(pasarela_id_transaccion__icontains=value) |
            Q(transferencia_numero_operacion__icontains=value)
        )

    def filter_hoy(self, queryset, name, value):
        """Filtra pagos de hoy"""
        if value:
            hoy = timezone.now().date()
            return queryset.filter(creado_en__date=hoy)
        return queryset

    def filter_esta_semana(self, queryset, name, value):
        """Filtra pagos de esta semana"""
        if value:
            from datetime import timedelta
            hoy = timezone.now().date()
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            return queryset.filter(creado_en__date__gte=inicio_semana)
        return queryset

    def filter_este_mes(self, queryset, name, value):
        """Filtra pagos de este mes"""
        if value:
            hoy = timezone.now().date()
            return queryset.filter(
                creado_en__year=hoy.year,
                creado_en__month=hoy.month
            )
        return queryset

    class Meta:
        model = Pago
        fields = {
            'estado': ['exact', 'in'],
            'monto': ['exact', 'gte', 'lte', 'gt', 'lt'],
            'creado_en': ['exact', 'date', 'date__gte', 'date__lte', 'year', 'month'],
            'fecha_completado': ['exact', 'date', 'date__gte', 'date__lte'],
            'monto_reembolsado': ['exact', 'gte', 'lte', 'gt'],
        }


# ==========================================================
# 📝 FILTRO: TRANSACCIÓN
# ==========================================================

class TransaccionFilter(django_filters.FilterSet):
    """
    Filtro para transacciones

    Uso:
    ?tipo=pago
    ?exitosa=true
    ?pago=5
    ?fecha_desde=2025-01-01
    ?fecha_hasta=2025-01-31
    ?monto_min=10
    """

    # ==========================================================
    # FILTROS BÁSICOS
    # ==========================================================

    tipo = django_filters.MultipleChoiceFilter(
        field_name='tipo',
        choices=TipoTransaccion.choices,
        help_text='Filtra por tipo de transacción'
    )

    exitosa = django_filters.BooleanFilter(
        field_name='exitosa',
        help_text='Filtra por estado exitoso (true/false/null)'
    )

    pago = django_filters.NumberFilter(
        field_name='pago__id',
        help_text='ID del pago'
    )

    pago_referencia = django_filters.CharFilter(
        field_name='pago__referencia',
        lookup_expr='icontains',
        help_text='Referencia del pago'
    )

    # ==========================================================
    # FILTROS POR MONTO
    # ==========================================================

    monto_min = django_filters.NumberFilter(
        field_name='monto',
        lookup_expr='gte',
        help_text='Monto mínimo'
    )

    monto_max = django_filters.NumberFilter(
        field_name='monto',
        lookup_expr='lte',
        help_text='Monto máximo'
    )

    # ==========================================================
    # FILTROS POR FECHA
    # ==========================================================

    fecha_desde = django_filters.DateTimeFilter(
        field_name='creado_en',
        lookup_expr='gte',
        help_text='Fecha desde (YYYY-MM-DD HH:MM:SS)'
    )

    fecha_hasta = django_filters.DateTimeFilter(
        field_name='creado_en',
        lookup_expr='lte',
        help_text='Fecha hasta (YYYY-MM-DD HH:MM:SS)'
    )

    fecha_dia = django_filters.DateFilter(
        field_name='creado_en',
        lookup_expr='date',
        help_text='Fecha exacta (YYYY-MM-DD)'
    )

    # ==========================================================
    # FILTROS ESPECIALES
    # ==========================================================

    codigo_respuesta = django_filters.CharFilter(
        field_name='codigo_respuesta',
        lookup_expr='icontains',
        help_text='Código de respuesta de la pasarela'
    )

    descripcion = django_filters.CharFilter(
        field_name='descripcion',
        lookup_expr='icontains',
        help_text='Búsqueda en descripción'
    )

    # ==========================================================
    # FILTROS DE ESTADO
    # ==========================================================

    solo_exitosas = django_filters.BooleanFilter(
        method='filter_solo_exitosas',
        help_text='Solo transacciones exitosas'
    )

    solo_fallidas = django_filters.BooleanFilter(
        method='filter_solo_fallidas',
        help_text='Solo transacciones fallidas'
    )

    en_proceso = django_filters.BooleanFilter(
        method='filter_en_proceso',
        help_text='Solo transacciones en proceso'
    )

    # ==========================================================
    # MÉTODOS DE FILTRADO PERSONALIZADO
    # ==========================================================

    def filter_solo_exitosas(self, queryset, name, value):
        """Filtra solo transacciones exitosas"""
        if value:
            return queryset.filter(exitosa=True)
        return queryset

    def filter_solo_fallidas(self, queryset, name, value):
        """Filtra solo transacciones fallidas"""
        if value:
            return queryset.filter(exitosa=False)
        return queryset

    def filter_en_proceso(self, queryset, name, value):
        """Filtra transacciones en proceso"""
        if value:
            return queryset.filter(exitosa__isnull=True)
        return queryset

    class Meta:
        model = Transaccion
        fields = {
            'tipo': ['exact', 'in'],
            'exitosa': ['exact'],
            'monto': ['exact', 'gte', 'lte'],
            'creado_en': ['exact', 'gte', 'lte', 'date'],
        }


# ==========================================================
# 💳 FILTRO: MÉTODO DE PAGO
# ==========================================================

class MetodoPagoFilter(django_filters.FilterSet):
    """
    Filtro para métodos de pago

    Uso:
    ?activo=true
    ?tipo=efectivo
    ?requiere_verificacion=true
    ?permite_reembolso=true
    """

    activo = django_filters.BooleanFilter(
        field_name='activo',
        help_text='Filtra por métodos activos'
    )

    tipo = django_filters.MultipleChoiceFilter(
        field_name='tipo',
        choices=TipoMetodoPago.choices,
        help_text='Filtra por tipo de método'
    )

    requiere_verificacion = django_filters.BooleanFilter(
        field_name='requiere_verificacion',
        help_text='Requiere verificación manual'
    )

    permite_reembolso = django_filters.BooleanFilter(
        field_name='permite_reembolso',
        help_text='Permite reembolsos'
    )

    tiene_pasarela = django_filters.BooleanFilter(
        method='filter_tiene_pasarela',
        help_text='Tiene pasarela externa configurada'
    )

    nombre = django_filters.CharFilter(
        field_name='nombre',
        lookup_expr='icontains',
        help_text='Búsqueda por nombre'
    )

    def filter_tiene_pasarela(self, queryset, name, value):
        """Filtra métodos con pasarela configurada"""
        if value:
            return queryset.exclude(pasarela_nombre='')
        return queryset.filter(pasarela_nombre='')

    class Meta:
        model = MetodoPago
        fields = {
            'tipo': ['exact', 'in'],
            'activo': ['exact'],
            'requiere_verificacion': ['exact'],
            'permite_reembolso': ['exact'],
        }


# ==========================================================
# 📊 EJEMPLOS DE USO
# ==========================================================
"""
EJEMPLOS DE FILTROS EN URL:

1. Pagos completados en efectivo del mes actual:
   /api/pagos/pagos/?estado=completado&metodo_pago_tipo=efectivo&este_mes=true

2. Pagos pendientes de verificación:
   /api/pagos/pagos/?requiere_verificacion=true

3. Pagos entre $50 y $100 de esta semana:
   /api/pagos/pagos/?monto_min=50&monto_max=100&esta_semana=true

4. Pagos reembolsados de un cliente específico:
   /api/pagos/pagos/?fue_reembolsado=true&cliente=5

5. Buscar pago por referencia parcial:
   /api/pagos/pagos/?referencia_parcial=abc123

6. Pagos con tarjeta del día de hoy:
   /api/pagos/pagos/?es_tarjeta=true&hoy=true

7. Transacciones exitosas de un pago:
   /api/pagos/transacciones/?pago=5&solo_exitosas=true

8. Transacciones fallidas de hoy:
   /api/pagos/transacciones/?solo_fallidas=true&fecha_dia=2025-01-15

9. Pagos completados en enero 2025:
   /api/pagos/pagos/?estado=completado&fecha_desde=2025-01-01&fecha_hasta=2025-01-31

10. Búsqueda general:
    /api/pagos/pagos/?buscar=juan@email.com

11. Métodos activos con pasarela:
    /api/pagos/metodos/?activo=true&tiene_pasarela=true

12. Transferencias verificadas hoy:
    /api/pagos/pagos/?es_transferencia=true&fue_verificado=true&hoy=true
"""
