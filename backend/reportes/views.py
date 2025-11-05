# reportes/views.py
"""
Views para el sistema de reportes de pedidos
✅ Endpoints para Admin, Proveedor y Repartidor
✅ Estadísticas, métricas y exportación
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import HttpResponse
import logging

from pedidos.models import Pedido, EstadoPedido, TipoPedido
from .serializers import (
    PedidoReporteSerializer,
    PedidoReporteResumidoSerializer,
    EstadisticasGeneralesSerializer,
    EstadisticasProveedorSerializer,
    EstadisticasRepartidorSerializer,
    MetricasDiariasSerializer,
    TopProveedoresSerializer,
    TopRepartidoresSerializer,
    ExportarReporteSerializer,
)
from .filters import (
    PedidoReporteFilter,
    PedidoProveedorFilter,
    PedidoRepartidorFilter,
)
from .permissions import (
    EsAdministrador,
    EsProveedor,
    EsRepartidor,
    EsAdminOProveedor,
    EsAdminORepartidor,
    validar_acceso_proveedor,
    validar_acceso_repartidor,
)
from .utils import exportar_pedidos_excel, exportar_pedidos_csv

logger = logging.getLogger('reportes')


# ============================================
# VIEWSET: REPORTES PARA ADMINISTRADOR
# ============================================

class ReporteAdminViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para reportes del administrador
    ✅ Acceso completo a todos los pedidos
    ✅ Estadísticas globales
    ✅ Exportación
    """
    permission_classes = [IsAuthenticated, EsAdministrador]
    serializer_class = PedidoReporteSerializer
    filterset_class = PedidoReporteFilter

    def get_queryset(self):
        """
        Queryset optimizado con select_related
        """
        return Pedido.objects.select_related(
            'cliente__user',
            'proveedor',
            'repartidor__user'
        ).all()

    def get_serializer_class(self):
        """
        Usa serializer resumido para listados grandes
        """
        if self.action == 'list':
            return PedidoReporteResumidoSerializer
        return PedidoReporteSerializer

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        GET /api/reportes/admin/estadisticas/

        Estadísticas globales del sistema
        """
        hoy = timezone.now().date()
        primer_dia_mes = hoy.replace(day=1)

        # Totales generales
        total_pedidos = Pedido.objects.count()
        pedidos_hoy = Pedido.objects.filter(creado_en__date=hoy).count()
        pedidos_mes = Pedido.objects.filter(creado_en__date__gte=primer_dia_mes).count()

        # Por estado
        pedidos_confirmados = Pedido.objects.filter(estado=EstadoPedido.CONFIRMADO).count()
        pedidos_en_preparacion = Pedido.objects.filter(estado=EstadoPedido.EN_PREPARACION).count()
        pedidos_en_ruta = Pedido.objects.filter(estado=EstadoPedido.EN_RUTA).count()
        pedidos_entregados = Pedido.objects.filter(estado=EstadoPedido.ENTREGADO).count()
        pedidos_cancelados = Pedido.objects.filter(estado=EstadoPedido.CANCELADO).count()

        # Por tipo
        pedidos_proveedor = Pedido.objects.filter(tipo=TipoPedido.PROVEEDOR).count()
        pedidos_directos = Pedido.objects.filter(tipo=TipoPedido.DIRECTO).count()

        # Financiero - Totales
        ingresos_data = Pedido.objects.filter(estado=EstadoPedido.ENTREGADO).aggregate(
            total=Sum('total'),
            ganancia=Sum('ganancia_app')
        )

        # Financiero - Hoy
        ingresos_hoy_data = Pedido.objects.filter(
            estado=EstadoPedido.ENTREGADO,
            creado_en__date=hoy
        ).aggregate(
            total=Sum('total'),
            ganancia=Sum('ganancia_app')
        )

        # Financiero - Mes
        ingresos_mes_data = Pedido.objects.filter(
            estado=EstadoPedido.ENTREGADO,
            creado_en__date__gte=primer_dia_mes
        ).aggregate(
            total=Sum('total'),
            ganancia=Sum('ganancia_app')
        )

        # Promedios
        ticket_promedio = ingresos_data['total'] / pedidos_entregados if pedidos_entregados > 0 else 0

        comision_promedio = Pedido.objects.filter(
            estado=EstadoPedido.ENTREGADO
        ).aggregate(
            promedio=Avg('comision_repartidor')
        )['promedio'] or 0

        # Tasas
        tasa_entrega = (pedidos_entregados / total_pedidos * 100) if total_pedidos > 0 else 0
        tasa_cancelacion = (pedidos_cancelados / total_pedidos * 100) if total_pedidos > 0 else 0

        data = {
            'total_pedidos': total_pedidos,
            'pedidos_hoy': pedidos_hoy,
            'pedidos_mes_actual': pedidos_mes,
            'pedidos_confirmados': pedidos_confirmados,
            'pedidos_en_preparacion': pedidos_en_preparacion,
            'pedidos_en_ruta': pedidos_en_ruta,
            'pedidos_entregados': pedidos_entregados,
            'pedidos_cancelados': pedidos_cancelados,
            'pedidos_proveedor': pedidos_proveedor,
            'pedidos_directos': pedidos_directos,
            'ingresos_totales': ingresos_data['total'] or 0,
            'ingresos_hoy': ingresos_hoy_data['total'] or 0,
            'ingresos_mes_actual': ingresos_mes_data['total'] or 0,
            'ganancia_app_total': ingresos_data['ganancia'] or 0,
            'ganancia_app_hoy': ingresos_hoy_data['ganancia'] or 0,
            'ganancia_app_mes': ingresos_mes_data['ganancia'] or 0,
            'ticket_promedio': round(ticket_promedio, 2),
            'comision_promedio_repartidor': round(comision_promedio, 2),
            'tasa_entrega': round(tasa_entrega, 2),
            'tasa_cancelacion': round(tasa_cancelacion, 2),
        }

        serializer = EstadisticasGeneralesSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def metricas_diarias(self, request):
        """
        GET /api/reportes/admin/metricas-diarias/?dias=30

        Métricas agregadas por día (para gráficos)
        """
        dias = int(request.query_params.get('dias', 30))
        fecha_inicio = timezone.now().date() - timedelta(days=dias)

        # Agrupar por fecha
        metricas = []
        fecha_actual = fecha_inicio
        hoy = timezone.now().date()

        while fecha_actual <= hoy:
            pedidos_dia = Pedido.objects.filter(creado_en__date=fecha_actual)

            stats = pedidos_dia.aggregate(
                total=Count('id'),
                entregados=Count('id', filter=Q(estado=EstadoPedido.ENTREGADO)),
                cancelados=Count('id', filter=Q(estado=EstadoPedido.CANCELADO)),
                ingresos=Sum('total', filter=Q(estado=EstadoPedido.ENTREGADO)),
                ganancia=Sum('ganancia_app', filter=Q(estado=EstadoPedido.ENTREGADO))
            )

            ticket_prom = (stats['ingresos'] / stats['entregados']) if stats['entregados'] and stats['ingresos'] else 0

            metricas.append({
                'fecha': fecha_actual,
                'total_pedidos': stats['total'] or 0,
                'pedidos_entregados': stats['entregados'] or 0,
                'pedidos_cancelados': stats['cancelados'] or 0,
                'ingresos': stats['ingresos'] or 0,
                'ganancia_app': stats['ganancia'] or 0,
                'ticket_promedio': round(ticket_prom, 2),
            })

            fecha_actual += timedelta(days=1)

        serializer = MetricasDiariasSerializer(metricas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def top_proveedores(self, request):
        """
        GET /api/reportes/admin/top-proveedores/?limit=10

        Top proveedores por ventas
        """
        limit = int(request.query_params.get('limit', 10))

        proveedores = Pedido.objects.filter(
            proveedor__isnull=False,
            estado=EstadoPedido.ENTREGADO
        ).values(
            'proveedor__id',
            'proveedor__nombre',
            'proveedor__tipo_proveedor'
        ).annotate(
            total_pedidos=Count('id'),
            ingresos_totales=Sum('total')
        ).order_by('-ingresos_totales')[:limit]

        data = [{
            'proveedor_id': p['proveedor__id'],
            'proveedor_nombre': p['proveedor__nombre'],
            'proveedor_tipo': p['proveedor__tipo_proveedor'],
            'total_pedidos': p['total_pedidos'],
            'ingresos_totales': p['ingresos_totales'],
        } for p in proveedores]

        serializer = TopProveedoresSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def top_repartidores(self, request):
        """
        GET /api/reportes/admin/top-repartidores/?limit=10

        Top repartidores por entregas
        """
        limit = int(request.query_params.get('limit', 10))

        repartidores = Pedido.objects.filter(
            repartidor__isnull=False,
            estado=EstadoPedido.ENTREGADO
        ).values(
            'repartidor__id',
            'repartidor__user__first_name',
            'repartidor__user__last_name'
        ).annotate(
            total_entregas=Count('id'),
            comisiones_totales=Sum('comision_repartidor'),
            calificacion_promedio=Avg('repartidor__calificacion_promedio')
        ).order_by('-total_entregas')[:limit]

        data = [{
            'repartidor_id': r['repartidor__id'],
            'repartidor_nombre': f"{r['repartidor__user__first_name']} {r['repartidor__user__last_name']}",
            'total_entregas': r['total_entregas'],
            'comisiones_totales': r['comisiones_totales'],
            'calificacion_promedio': round(r['calificacion_promedio'] or 0, 2),
        } for r in repartidores]

        serializer = TopRepartidoresSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def exportar(self, request):
        """
        GET /api/reportes/admin/exportar/?formato=excel

        Exporta reportes a Excel o CSV
        """
        serializer = ExportarReporteSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        formato = serializer.validated_data.get('formato', 'excel')

        # Aplicar filtros
        queryset = self.filter_queryset(self.get_queryset())

        if formato == 'excel':
            response = exportar_pedidos_excel(queryset)
        else:
            response = exportar_pedidos_csv(queryset)

        logger.info(f"✅ Reporte exportado por admin: {request.user.email} - {formato}")
        return response


# ============================================
# VIEWSET: REPORTES PARA PROVEEDOR
# ============================================

class ReporteProveedorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para reportes del proveedor
    ✅ Solo ve sus propios pedidos
    """
    permission_classes = [IsAuthenticated, EsProveedor]
    serializer_class = PedidoReporteSerializer
    filterset_class = PedidoProveedorFilter

    def get_queryset(self):
        """
        Solo pedidos del proveedor autenticado
        """
        try:
            proveedor = self.request.user.proveedor
            return Pedido.objects.filter(
                proveedor=proveedor
            ).select_related(
                'cliente__user',
                'repartidor__user'
            )
        except Exception as e:
            logger.error(f"❌ Error obteniendo pedidos del proveedor: {e}")
            return Pedido.objects.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return PedidoReporteResumidoSerializer
        return PedidoReporteSerializer

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        GET /api/reportes/proveedor/estadisticas/

        Estadísticas del proveedor
        """
        try:
            proveedor = request.user.proveedor

            queryset = Pedido.objects.filter(proveedor=proveedor)

            total_pedidos = queryset.count()
            pedidos_entregados = queryset.filter(estado=EstadoPedido.ENTREGADO).count()
            pedidos_cancelados = queryset.filter(estado=EstadoPedido.CANCELADO).count()
            pedidos_activos = queryset.filter(
                estado__in=[EstadoPedido.CONFIRMADO, EstadoPedido.EN_PREPARACION, EstadoPedido.EN_RUTA]
            ).count()

            financiero = queryset.filter(estado=EstadoPedido.ENTREGADO).aggregate(
                ingresos=Sum('total'),
                comisiones=Sum('comision_proveedor')
            )

            ticket_promedio = (financiero['ingresos'] / pedidos_entregados) if pedidos_entregados > 0 else 0
            tasa_entrega = (pedidos_entregados / total_pedidos * 100) if total_pedidos > 0 else 0

            data = {
                'proveedor_id': proveedor.id,
                'proveedor_nombre': proveedor.nombre,
                'total_pedidos': total_pedidos,
                'pedidos_entregados': pedidos_entregados,
                'pedidos_cancelados': pedidos_cancelados,
                'pedidos_activos': pedidos_activos,
                'ingresos_totales': financiero['ingresos'] or 0,
                'comisiones_totales': financiero['comisiones'] or 0,
                'ticket_promedio': round(ticket_promedio, 2),
                'tasa_entrega': round(tasa_entrega, 2),
            }

            serializer = EstadisticasProveedorSerializer(data)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"❌ Error calculando estadísticas del proveedor: {e}")
            return Response(
                {'error': 'Error al calcular estadísticas'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def exportar(self, request):
        """
        GET /api/reportes/proveedor/exportar/?formato=excel

        Exporta sus pedidos
        """
        queryset = self.filter_queryset(self.get_queryset())
        formato = request.query_params.get('formato', 'excel')

        if formato == 'excel':
            response = exportar_pedidos_excel(queryset)
        else:
            response = exportar_pedidos_csv(queryset)

        logger.info(f"✅ Reporte exportado por proveedor: {request.user.email}")
        return response


# ============================================
# VIEWSET: REPORTES PARA REPARTIDOR
# ============================================

class ReporteRepartidorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para reportes del repartidor
    ✅ Solo ve sus propias entregas
    """
    permission_classes = [IsAuthenticated, EsRepartidor]
    serializer_class = PedidoReporteSerializer
    filterset_class = PedidoRepartidorFilter

    def get_queryset(self):
        """
        Solo entregas del repartidor autenticado
        """
        try:
            repartidor = self.request.user.repartidor
            return Pedido.objects.filter(
                repartidor=repartidor
            ).select_related(
                'cliente__user',
                'proveedor'
            )
        except Exception as e:
            logger.error(f"❌ Error obteniendo entregas del repartidor: {e}")
            return Pedido.objects.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return PedidoReporteResumidoSerializer
        return PedidoReporteSerializer

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        GET /api/reportes/repartidor/estadisticas/

        Estadísticas del repartidor
        """
        try:
            repartidor = request.user.repartidor
            hoy = timezone.now().date()
            primer_dia_mes = hoy.replace(day=1)

            queryset = Pedido.objects.filter(repartidor=repartidor)

            total_entregas = queryset.filter(estado=EstadoPedido.ENTREGADO).count()
            entregas_hoy = queryset.filter(estado=EstadoPedido.ENTREGADO, creado_en__date=hoy).count()
            entregas_mes = queryset.filter(estado=EstadoPedido.ENTREGADO, creado_en__date__gte=primer_dia_mes).count()

            comisiones = queryset.filter(estado=EstadoPedido.ENTREGADO).aggregate(
                total=Sum('comision_repartidor'),
                hoy=Sum('comision_repartidor', filter=Q(creado_en__date=hoy)),
                mes=Sum('comision_repartidor', filter=Q(creado_en__date__gte=primer_dia_mes))
            )

            ticket_promedio = queryset.filter(estado=EstadoPedido.ENTREGADO).aggregate(
                promedio=Avg('total')
            )['promedio'] or 0

            data = {
                'repartidor_id': repartidor.id,
                'repartidor_nombre': repartidor.user.get_full_name(),
                'total_entregas': total_entregas,
                'entregas_hoy': entregas_hoy,
                'entregas_mes': entregas_mes,
                'comisiones_totales': comisiones['total'] or 0,
                'comisiones_hoy': comisiones['hoy'] or 0,
                'comisiones_mes': comisiones['mes'] or 0,
                'calificacion_promedio': repartidor.calificacion_promedio,
                'ticket_promedio': round(ticket_promedio, 2),
            }

            serializer = EstadisticasRepartidorSerializer(data)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"❌ Error calculando estadísticas del repartidor: {e}")
            return Response(
                {'error': 'Error al calcular estadísticas'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def exportar(self, request):
        """
        GET /api/reportes/repartidor/exportar/?formato=excel

        Exporta sus entregas
        """
        queryset = self.filter_queryset(self.get_queryset())
        formato = request.query_params.get('formato', 'excel')

        if formato == 'excel':
            response = exportar_pedidos_excel(queryset)
        else:
            response = exportar_pedidos_csv(queryset)

        logger.info(f"✅ Reporte exportado por repartidor: {request.user.email}")
        return response
