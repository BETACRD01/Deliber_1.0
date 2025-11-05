# notificaciones/views.py
"""
ViewSets y API endpoints para notificaciones
✅ CRUD de notificaciones
✅ Marcar como leída
✅ Estadísticas
✅ Filtros y búsqueda
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django.utils import timezone

from notificaciones.models import Notificacion
from notificaciones.serializers import (
    NotificacionSerializer,
    NotificacionListSerializer,
    MarcarLeidaSerializer,
    EstadisticasNotificacionesSerializer
)

logger = logging.getLogger('notificaciones')


class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ✅ ViewSet para gestión de notificaciones

    Endpoints:
    - GET /api/notificaciones/ - Listar notificaciones del usuario
    - GET /api/notificaciones/{id}/ - Detalle de notificación
    - POST /api/notificaciones/marcar_leida/ - Marcar como leída
    - POST /api/notificaciones/marcar_no_leida/ - Marcar como no leída
    - POST /api/notificaciones/marcar_todas_leidas/ - Marcar todas como leídas
    - GET /api/notificaciones/estadisticas/ - Obtener estadísticas
    - GET /api/notificaciones/no_leidas/ - Solo no leídas
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        ✅ Retorna solo las notificaciones del usuario autenticado
        """
        user = self.request.user

        # Queryset base optimizado
        queryset = Notificacion.objects.filter(
            usuario=user
        ).select_related('pedido').order_by('-creada_en')

        # Filtro por tipo
        tipo = self.request.query_params.get('tipo', None)
        if tipo:
            queryset = queryset.filter(tipo=tipo)

        # Filtro por estado (leída/no leída)
        leida = self.request.query_params.get('leida', None)
        if leida is not None:
            leida_bool = leida.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(leida=leida_bool)

        # Filtro por pedido
        pedido_id = self.request.query_params.get('pedido', None)
        if pedido_id:
            queryset = queryset.filter(pedido_id=pedido_id)

        return queryset

    def get_serializer_class(self):
        """
        ✅ Usa serializer optimizado para listado
        """
        if self.action == 'list':
            return NotificacionListSerializer
        return NotificacionSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        ✅ Al obtener detalle, marcar automáticamente como leída
        """
        instance = self.get_object()

        # Marcar como leída si no lo está
        if not instance.leida:
            instance.marcar_como_leida()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def marcar_leida(self, request, pk=None):
        """
        ✅ Marca una notificación como leída

        POST /api/notificaciones/{id}/marcar_leida/
        """
        notificacion = self.get_object()

        if notificacion.leida:
            return Response(
                {'detail': 'La notificación ya estaba marcada como leída'},
                status=status.HTTP_200_OK
            )

        notificacion.marcar_como_leida()

        serializer = self.get_serializer(notificacion)
        return Response(
            {
                'detail': 'Notificación marcada como leída',
                'notificacion': serializer.data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def marcar_no_leida(self, request, pk=None):
        """
        ✅ Marca una notificación como no leída

        POST /api/notificaciones/{id}/marcar_no_leida/
        """
        notificacion = self.get_object()

        if not notificacion.leida:
            return Response(
                {'detail': 'La notificación ya estaba marcada como no leída'},
                status=status.HTTP_200_OK
            )

        notificacion.marcar_como_no_leida()

        serializer = self.get_serializer(notificacion)
        return Response(
            {
                'detail': 'Notificación marcada como no leída',
                'notificacion': serializer.data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'])
    def marcar_varias_leidas(self, request):
        """
        ✅ Marca varias notificaciones como leídas

        POST /api/notificaciones/marcar_varias_leidas/
        Body: {
            "notificacion_ids": ["uuid1", "uuid2", ...],
            "marcar_todas": false
        }
        """
        serializer = MarcarLeidaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        if serializer.validated_data.get('marcar_todas'):
            # Marcar todas las notificaciones como leídas
            count = Notificacion.marcar_todas_leidas(user)

            return Response(
                {
                    'detail': f'{count} notificaciones marcadas como leídas',
                    'count': count
                },
                status=status.HTTP_200_OK
            )

        # Marcar notificaciones específicas
        notificacion_ids = serializer.validated_data.get('notificacion_ids', [])

        notificaciones = Notificacion.objects.filter(
            id__in=notificacion_ids,
            usuario=user,
            leida=False
        )

        count = notificaciones.update(
            leida=True,
            leida_en=timezone.now()
        )

        return Response(
            {
                'detail': f'{count} notificaciones marcadas como leídas',
                'count': count
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def no_leidas(self, request):
        """
        ✅ Obtiene solo notificaciones no leídas

        GET /api/notificaciones/no_leidas/
        """
        notificaciones = Notificacion.obtener_no_leidas(request.user)

        # Paginación manual si es necesario
        page = self.paginate_queryset(notificaciones)
        if page is not None:
            serializer = NotificacionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = NotificacionListSerializer(notificaciones, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        ✅ Obtiene estadísticas de notificaciones del usuario

        GET /api/notificaciones/estadisticas/

        Retorna:
        - total_notificaciones
        - no_leidas
        - leidas
        - por_tipo (desglose por tipo)
        - ultima_notificacion
        """
        user = request.user

        # Contar totales
        total = Notificacion.objects.filter(usuario=user).count()
        no_leidas = Notificacion.contar_no_leidas(user)
        leidas = total - no_leidas

        # Contar por tipo
        por_tipo = {}
        tipos = Notificacion.objects.filter(
            usuario=user
        ).values('tipo').annotate(
            count=Count('id')
        )

        for item in tipos:
            tipo_display = dict(Notificacion._meta.get_field('tipo').choices).get(
                item['tipo'],
                item['tipo']
            )
            por_tipo[tipo_display] = item['count']

        # Última notificación
        ultima = Notificacion.objects.filter(
            usuario=user
        ).order_by('-creada_en').first()

        ultima_fecha = ultima.creada_en if ultima else None

        data = {
            'total_notificaciones': total,
            'no_leidas': no_leidas,
            'leidas': leidas,
            'por_tipo': por_tipo,
            'ultima_notificacion': ultima_fecha
        }

        serializer = EstadisticasNotificacionesSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'])
    def eliminar_antiguas(self, request):
        """
        ✅ Elimina notificaciones leídas antiguas

        DELETE /api/notificaciones/eliminar_antiguas/?dias=30

        Query params:
        - dias: Número de días de antigüedad (default: 30)
        """
        dias = int(request.query_params.get('dias', 30))

        if dias < 7:
            return Response(
                {'detail': 'El mínimo es 7 días'},
                status=status.HTTP_400_BAD_REQUEST
            )

        count = Notificacion.eliminar_antiguas(dias)

        return Response(
            {
                'detail': f'{count} notificaciones eliminadas',
                'count': count,
                'dias': dias
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'])
    def test_notificacion(self, request):
        """
        ✅ ENDPOINT DE PRUEBA: Envía una notificación de prueba

        POST /api/notificaciones/test_notificacion/

        Solo para desarrollo/testing
        """
        from notificaciones.services import crear_y_enviar_notificacion

        user = request.user

        exito = crear_y_enviar_notificacion(
            usuario=user,
            titulo="🧪 Notificación de prueba",
            mensaje="Esta es una notificación de prueba del sistema. Si la recibes, ¡todo funciona correctamente!",
            tipo='sistema',
            datos_extra={
                'tipo': 'test',
                'timestamp': str(timezone.now())
            }
        )

        if exito:
            return Response(
                {'detail': 'Notificación de prueba enviada correctamente'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'detail': 'Error al enviar notificación de prueba'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
