# pagos/views.py
"""
Views y ViewSets para el módulo de Pagos (Django REST Framework).

✅ CARACTERÍSTICAS:
- ViewSets completos para API REST
- Endpoints para CRUD de pagos
- Acciones personalizadas (verificar, reembolsar)
- Filtros y búsqueda avanzada
- Permisos granulares
- Webhooks para pasarelas externas
- Estadísticas y reportes
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import (
    MetodoPago, Pago, Transaccion, EstadisticasPago,
    EstadoPago, TipoMetodoPago
)
from .serializers import (
    MetodoPagoSerializer, MetodoPagoListSerializer,
    PagoDetailSerializer, PagoListSerializer, PagoCreateSerializer,
    PagoUpdateEstadoSerializer, PagoReembolsoSerializer,
    TransaccionSerializer, TransaccionListSerializer,
    EstadisticasPagoSerializer, PagoResumenSerializer
)
from .filters import PagoFilter, TransaccionFilter
import logging
import json

logger = logging.getLogger('pagos')


# ==========================================================
# 🔒 PERMISOS PERSONALIZADOS
# ==========================================================

class IsOwnerOrAdmin(IsAuthenticated):
    """
    Permiso: El usuario es el dueño del pago o es admin
    """
    def has_object_permission(self, request, view, obj):
        # Admin tiene acceso total
        if request.user.is_staff:
            return True

        # El cliente del pedido puede ver su pago
        return obj.pedido.cliente.user == request.user


class CanVerifyPayments(IsAuthenticated):
    """
    Permiso: Puede verificar pagos (solo admin)
    """
    def has_permission(self, request, view):
        return request.user.is_staff


# ==========================================================
# 💳 VIEWSET: MÉTODO DE PAGO
# ==========================================================

class MetodoPagoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para métodos de pago (solo lectura para clientes)

    GET /api/pagos/metodos/ - Lista métodos activos
    GET /api/pagos/metodos/{id}/ - Detalle de método
    """
    queryset = MetodoPago.objects.filter(activo=True)
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Serializer según acción"""
        if self.action == 'list':
            return MetodoPagoListSerializer
        return MetodoPagoSerializer

    def get_queryset(self):
        """Queryset según usuario"""
        queryset = super().get_queryset()

        # Admin ve todos, clientes solo activos
        if not self.request.user.is_staff:
            queryset = queryset.filter(activo=True)

        return queryset

    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """
        GET /api/pagos/metodos/disponibles/

        Lista solo métodos disponibles actualmente
        """
        metodos = self.get_queryset().filter(activo=True)
        serializer = MetodoPagoListSerializer(metodos, many=True)

        return Response({
            'count': metodos.count(),
            'metodos': serializer.data
        })


# ==========================================================
# 💰 VIEWSET: PAGO
# ==========================================================

class PagoViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal para pagos

    GET /api/pagos/ - Lista pagos del usuario
    POST /api/pagos/ - Crear nuevo pago
    GET /api/pagos/{id}/ - Detalle de pago
    PATCH /api/pagos/{id}/actualizar_estado/ - Actualizar estado
    POST /api/pagos/{id}/reembolsar/ - Procesar reembolso
    POST /api/pagos/{id}/verificar/ - Verificar transferencia
    GET /api/pagos/{id}/transacciones/ - Historial de transacciones
    GET /api/pagos/mis_pagos/ - Pagos del usuario actual
    GET /api/pagos/pendientes_verificacion/ - Pagos pendientes (admin)
    GET /api/pagos/estadisticas/ - Estadísticas generales
    """
    queryset = Pago.objects.all()
    permission_classes = [IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PagoFilter
    search_fields = ['referencia', 'pedido__id', 'notas']
    ordering_fields = ['creado_en', 'monto', 'estado']
    ordering = ['-creado_en']

    def get_serializer_class(self):
        """Serializer según acción"""
        if self.action == 'list':
            return PagoListSerializer
        elif self.action == 'create':
            return PagoCreateSerializer
        elif self.action == 'actualizar_estado':
            return PagoUpdateEstadoSerializer
        elif self.action == 'reembolsar':
            return PagoReembolsoSerializer
        elif self.action == 'resumen':
            return PagoResumenSerializer
        return PagoDetailSerializer

    def get_queryset(self):
        """Queryset según usuario"""
        queryset = super().get_queryset()
        user = self.request.user

        # Admin ve todos
        if user.is_staff:
            return queryset

        # Cliente solo ve sus pagos
        return queryset.filter(pedido__cliente__user=user)

    def create(self, request, *args, **kwargs):
        """
        POST /api/pagos/

        Crea un nuevo pago para un pedido
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pago = serializer.save()

        # Retornar con serializer detallado
        output_serializer = PagoDetailSerializer(pago)

        logger.info(
            f"✅ Pago creado: {pago.referencia} "
            f"por usuario {request.user.email}"
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['patch'], permission_classes=[CanVerifyPayments])
    def actualizar_estado(self, request, pk=None):
        """
        PATCH /api/pagos/{id}/actualizar_estado/

        Actualiza el estado del pago (solo admin)

        Body:
        {
            "estado": "completado",
            "motivo": "Verificado manualmente",
            "pasarela_respuesta": {}
        }
        """
        pago = self.get_object()

        serializer = self.get_serializer(
            data=request.data,
            context={'pago': pago, 'request': request}
        )
        serializer.is_valid(raise_exception=True)

        pago_actualizado = serializer.save()

        output_serializer = PagoDetailSerializer(pago_actualizado)

        return Response({
            'message': 'Estado actualizado exitosamente',
            'pago': output_serializer.data
        })

    @action(detail=True, methods=['post'], permission_classes=[CanVerifyPayments])
    def reembolsar(self, request, pk=None):
        """
        POST /api/pagos/{id}/reembolsar/

        Procesa un reembolso total o parcial (solo admin)

        Body:
        {
            "monto": 50.00,  // Opcional, null = reembolso total
            "motivo": "Cliente insatisfecho"
        }
        """
        pago = self.get_object()

        serializer = self.get_serializer(
            data=request.data,
            context={'pago': pago}
        )
        serializer.is_valid(raise_exception=True)

        pago_actualizado = serializer.save()

        output_serializer = PagoDetailSerializer(pago_actualizado)

        return Response({
            'message': 'Reembolso procesado exitosamente',
            'pago': output_serializer.data
        })

    @action(detail=True, methods=['post'], permission_classes=[CanVerifyPayments])
    def verificar(self, request, pk=None):
        """
        POST /api/pagos/{id}/verificar/

        Verifica y completa una transferencia bancaria (solo admin)

        Body:
        {
            "notas": "Comprobante verificado - Banco Pichincha"
        }
        """
        pago = self.get_object()

        # Validar que sea transferencia
        if pago.metodo_pago.tipo != TipoMetodoPago.TRANSFERENCIA:
            return Response(
                {'error': 'Solo se pueden verificar transferencias bancarias'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar estado
        if pago.estado != EstadoPago.PENDIENTE:
            return Response(
                {'error': f'El pago no está pendiente (estado actual: {pago.get_estado_display()})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar notas si se proporcionaron
        notas = request.data.get('notas', '')
        if notas:
            pago.notas = f"{pago.notas}\n\n{notas}".strip()

        # Marcar como completado
        pago.marcar_completado(verificado_por=request.user)

        output_serializer = PagoDetailSerializer(pago)

        logger.info(
            f"✅ Transferencia verificada: {pago.referencia} "
            f"por {request.user.email}"
        )

        return Response({
            'message': 'Transferencia verificada y completada',
            'pago': output_serializer.data
        })

    @action(detail=True, methods=['get'])
    def transacciones(self, request, pk=None):
        """
        GET /api/pagos/{id}/transacciones/

        Obtiene el historial de transacciones del pago
        """
        pago = self.get_object()
        transacciones = pago.transacciones.all()

        serializer = TransaccionSerializer(transacciones, many=True)

        return Response({
            'count': transacciones.count(),
            'transacciones': serializer.data
        })

    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        """
        GET /api/pagos/{id}/resumen/

        Obtiene un resumen rápido del pago
        """
        pago = self.get_object()
        resumen = pago.obtener_resumen()

        serializer = PagoResumenSerializer(resumen)

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def mis_pagos(self, request):
        """
        GET /api/pagos/mis_pagos/

        Lista todos los pagos del usuario actual
        """
        pagos = Pago.objects.filter(
            pedido__cliente__user=request.user
        ).order_by('-creado_en')

        # Aplicar paginación
        page = self.paginate_queryset(pagos)
        if page is not None:
            serializer = PagoListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PagoListSerializer(pagos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pendientes_verificacion(self, request):
        """
        GET /api/pagos/pendientes_verificacion/

        Lista pagos pendientes de verificación manual (solo admin)
        """
        pagos = Pago.objects.requieren_verificacion()

        serializer = PagoListSerializer(pagos, many=True)

        return Response({
            'count': pagos.count(),
            'pagos': serializer.data
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def estadisticas(self, request):
        """
        GET /api/pagos/estadisticas/

        Estadísticas generales de pagos (solo admin)

        Query params:
        - fecha_inicio: YYYY-MM-DD
        - fecha_fin: YYYY-MM-DD
        """
        # Obtener filtros de fecha
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')

        queryset = Pago.objects.all()

        if fecha_inicio:
            queryset = queryset.filter(creado_en__date__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(creado_en__date__lte=fecha_fin)

        # Calcular estadísticas
        stats = queryset.aggregate(
            total_pagos=Count('id'),
            pagos_completados=Count('id', filter=Q(estado=EstadoPago.COMPLETADO)),
            pagos_pendientes=Count('id', filter=Q(estado=EstadoPago.PENDIENTE)),
            pagos_procesando=Count('id', filter=Q(estado=EstadoPago.PROCESANDO)),
            pagos_fallidos=Count('id', filter=Q(estado=EstadoPago.FALLIDO)),
            pagos_reembolsados=Count('id', filter=Q(estado=EstadoPago.REEMBOLSADO)),
            monto_total=Sum('monto', filter=Q(estado=EstadoPago.COMPLETADO)),
            monto_reembolsado_total=Sum('monto_reembolsado'),
            monto_efectivo=Sum('monto', filter=Q(
                estado=EstadoPago.COMPLETADO,
                metodo_pago__tipo=TipoMetodoPago.EFECTIVO
            )),
            monto_transferencias=Sum('monto', filter=Q(
                estado=EstadoPago.COMPLETADO,
                metodo_pago__tipo=TipoMetodoPago.TRANSFERENCIA
            )),
            monto_tarjetas=Sum('monto', filter=Q(
                estado=EstadoPago.COMPLETADO,
                metodo_pago__tipo__in=[
                    TipoMetodoPago.TARJETA_CREDITO,
                    TipoMetodoPago.TARJETA_DEBITO
                ]
            ))
        )

        # Calcular métricas adicionales
        if stats['total_pagos'] > 0:
            stats['tasa_exito'] = round(
                (stats['pagos_completados'] / stats['total_pagos']) * 100, 2
            )
            stats['tasa_fallo'] = round(
                (stats['pagos_fallidos'] / stats['total_pagos']) * 100, 2
            )
        else:
            stats['tasa_exito'] = 0
            stats['tasa_fallo'] = 0

        if stats['pagos_completados'] > 0 and stats['monto_total']:
            stats['ticket_promedio'] = round(
                float(stats['monto_total']) / stats['pagos_completados'], 2
            )
        else:
            stats['ticket_promedio'] = 0

        # Convertir Decimals a float para JSON
        for key in stats:
            if stats[key] is None:
                stats[key] = 0
            elif isinstance(stats[key], type(Sum('monto'))):
                stats[key] = float(stats[key]) if stats[key] else 0

        return Response({
            'periodo': {
                'fecha_inicio': fecha_inicio or 'Todos',
                'fecha_fin': fecha_fin or 'Todos'
            },
            'estadisticas': stats
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def del_dia(self, request):
        """
        GET /api/pagos/del_dia/

        Pagos del día actual (solo admin)
        """
        pagos_hoy = Pago.objects.del_dia()
        stats = Pago.objects.estadisticas_del_dia()

        serializer = PagoListSerializer(pagos_hoy, many=True)

        return Response({
            'fecha': timezone.now().date(),
            'estadisticas': stats,
            'pagos': serializer.data
        })


# ==========================================================
# 📃 VIEWSET: TRANSACCIÓN
# ==========================================================

class TransaccionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para transacciones (solo lectura)

    GET /api/pagos/transacciones/ - Lista transacciones
    GET /api/pagos/transacciones/{id}/ - Detalle de transacción
    """
    queryset = Transaccion.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = TransaccionFilter
    ordering_fields = ['creado_en', 'monto']
    ordering = ['-creado_en']

    def get_serializer_class(self):
        """Serializer según acción"""
        if self.action == 'list':
            return TransaccionListSerializer
        return TransaccionSerializer

    def get_queryset(self):
        """Queryset según usuario"""
        queryset = super().get_queryset()
        user = self.request.user

        # Admin ve todas
        if user.is_staff:
            return queryset

        # Cliente solo ve transacciones de sus pagos
        return queryset.filter(pago__pedido__cliente__user=user)


# ==========================================================
# 📊 VIEWSET: ESTADÍSTICAS
# ==========================================================

class EstadisticasPagoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para estadísticas de pagos (solo admin)

    GET /api/pagos/estadisticas-diarias/ - Lista estadísticas
    GET /api/pagos/estadisticas-diarias/{id}/ - Detalle
    GET /api/pagos/estadisticas-diarias/recalcular/ - Recalcula estadísticas
    """
    queryset = EstadisticasPago.objects.all()
    serializer_class = EstadisticasPagoSerializer
    permission_classes = [IsAdminUser]
    ordering = ['-fecha']

    @action(detail=False, methods=['post'])
    def recalcular(self, request):
        """
        POST /api/pagos/estadisticas-diarias/recalcular/

        Recalcula estadísticas del día

        Body (opcional):
        {
            "fecha": "2025-01-15"  // Si no se envía, calcula para hoy
        }
        """
        fecha_str = request.data.get('fecha')

        if fecha_str:
            from datetime import datetime
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            fecha = timezone.now().date()

        # Recalcular
        estadistica = EstadisticasPago.calcular_y_guardar(fecha)
        serializer = self.get_serializer(estadistica)

        return Response({
            'message': 'Estadísticas recalculadas exitosamente',
            'estadistica': serializer.data
        })


# ==========================================================
# 🔗 WEBHOOKS: PASARELAS EXTERNAS
# ==========================================================

@csrf_exempt
def stripe_webhook(request):
    """
    POST /api/pagos/webhook/stripe/

    Webhook de Stripe para notificaciones de pagos
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        payload = json.loads(request.body)
        event_type = payload.get('type')

        logger.info(f"📩 Webhook Stripe recibido: {event_type}")

        if event_type == 'payment_intent.succeeded':
            # Pago exitoso
            payment_intent = payload.get('data', {}).get('object', {})
            pasarela_id = payment_intent.get('id')

            # Buscar pago
            try:
                pago = Pago.objects.get(pasarela_id_transaccion=pasarela_id)
                pago.marcar_completado(pasarela_respuesta=payload)

                logger.info(f"✅ Pago completado via webhook: {pago.referencia}")

            except Pago.DoesNotExist:
                logger.warning(f"⚠️ Pago no encontrado: {pasarela_id}")

        elif event_type == 'payment_intent.payment_failed':
            # Pago fallido
            payment_intent = payload.get('data', {}).get('object', {})
            pasarela_id = payment_intent.get('id')
            error_message = payment_intent.get('last_payment_error', {}).get('message', 'Error desconocido')

            try:
                pago = Pago.objects.get(pasarela_id_transaccion=pasarela_id)
                pago.marcar_fallido(error_message, pasarela_respuesta=payload)

                logger.warning(f"❌ Pago fallido via webhook: {pago.referencia}")

            except Pago.DoesNotExist:
                logger.warning(f"⚠️ Pago no encontrado: {pasarela_id}")

        return JsonResponse({'status': 'success'})

    except Exception as e:
        logger.error(f"Error procesando webhook Stripe: {e}")
        return JsonResponse(
            {'status': 'error', 'message': str(e)},
            status=400
        )


@csrf_exempt
def kushki_webhook(request):
    """
    POST /api/pagos/webhook/kushki/

    Webhook de Kushki para notificaciones de pagos
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        payload = json.loads(request.body)

        logger.info(f"📩 Webhook Kushki recibido")

        # Implementar lógica específica de Kushki
        # Similar a Stripe pero con estructura de Kushki

        # Ejemplo básico:
        # transaction_id = payload.get('transaction_id')
        # status = payload.get('status')
        #
        # if status == 'success':
        #     pago = Pago.objects.get(pasarela_id_transaccion=transaction_id)
        #     pago.marcar_completado(pasarela_respuesta=payload)

        return JsonResponse({'status': 'success'})

    except Exception as e:
        logger.error(f"Error procesando webhook Kushki: {e}")
        return JsonResponse(
            {'status': 'error', 'message': str(e)},
            status=400
        )


@csrf_exempt
def paymentez_webhook(request):
    """
    POST /api/pagos/webhook/paymentez/

    Webhook de Paymentez para notificaciones de pagos
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        payload = json.loads(request.body)

        logger.info(f"📩 Webhook Paymentez recibido")

        # Implementar lógica específica de Paymentez

        # Ejemplo básico:
        # transaction_id = payload.get('transaction', {}).get('id')
        # status_code = payload.get('transaction', {}).get('status')
        #
        # if status_code == 'success':
        #     pago = Pago.objects.get(pasarela_id_transaccion=transaction_id)
        #     pago.marcar_completado(pasarela_respuesta=payload)

        return JsonResponse({'status': 'success'})

    except Exception as e:
        logger.error(f"Error procesando webhook Paymentez: {e}")
        return JsonResponse(
            {'status': 'error', 'message': str(e)},
            status=400
        )
