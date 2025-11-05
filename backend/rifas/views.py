# -*- coding: utf-8 -*-
# rifas/views.py
"""
Views/ViewSets para API REST de Rifas

✅ FUNCIONALIDADES:
- CRUD de rifas (solo admin)
- Consulta de rifa activa (usuarios)
- Verificar elegibilidad personal
- Realizar sorteo (admin)
- Historial de ganadores
- Estadísticas
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Rifa, Participacion, EstadoRifa
from .serializers import (
    RifaListSerializer,
    RifaDetailSerializer,
    RifaWriteSerializer,
    RifaActivaAppSerializer,
    ParticipacionSerializer,
    ParticipacionSimpleSerializer,
    ElegibilidadSerializer,
    RealizarSorteoSerializer,
    SorteoResultadoSerializer,
    HistorialGanadoresSerializer,
    EstadisticasRifasSerializer,
    ListaParticipantesSerializer,
    ParticipanteSerializer,
    UsuarioSimpleSerializer
)
from authentication.models import User
from pedidos.models import Pedido, EstadoPedido

import logging

logger = logging.getLogger('rifas')


# ============================================
# 🔐 PERMISOS PERSONALIZADOS
# ============================================

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permite lectura a todos, escritura solo a admin
    """

    def has_permission(self, request, view):
        # Lectura permitida para todos los autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Escritura solo para admin
        return request.user and request.user.is_staff


class IsAdmin(permissions.BasePermission):
    """
    Solo admin puede acceder
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_staff


# ============================================
# 🎲 VIEWSET: RIFAS
# ============================================

class RifaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Rifas

    ✅ ENDPOINTS:
    - GET    /api/rifas/              - Listar todas las rifas
    - GET    /api/rifas/{id}/         - Detalle de rifa
    - POST   /api/rifas/              - Crear rifa (admin)
    - PUT    /api/rifas/{id}/         - Actualizar rifa (admin)
    - DELETE /api/rifas/{id}/         - Eliminar rifa (admin)

    ✅ CUSTOM ACTIONS:
    - GET    /api/rifas/activa/                  - Rifa activa actual
    - GET    /api/rifas/{id}/elegibilidad/       - Mi elegibilidad
    - POST   /api/rifas/{id}/sortear/            - Realizar sorteo (admin)
    - GET    /api/rifas/{id}/participantes/      - Lista participantes (admin)
    - GET    /api/rifas/historial_ganadores/     - Historial
    - GET    /api/rifas/estadisticas/            - Estadísticas generales
    """

    queryset = Rifa.objects.all().select_related(
        'ganador',
        'creado_por'
    ).order_by('-fecha_inicio')

    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        """Seleccionar serializer según acción"""
        if self.action == 'list':
            return RifaListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RifaWriteSerializer
        elif self.action == 'activa':
            return RifaActivaAppSerializer
        elif self.action == 'sortear':
            return SorteoResultadoSerializer
        elif self.action == 'participantes':
            return ListaParticipantesSerializer
        elif self.action == 'historial_ganadores':
            return HistorialGanadoresSerializer
        elif self.action == 'estadisticas':
            return EstadisticasRifasSerializer
        else:
            return RifaDetailSerializer

    def get_permissions(self):
        """Permisos según acción"""
        if self.action in ['sortear', 'participantes', 'create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    # ============================================
    # 📋 CRUD ESTÁNDAR
    # ============================================

    def list(self, request, *args, **kwargs):
        """
        Lista todas las rifas

        Query params opcionales:
        - estado: filtrar por estado (activa/finalizada/cancelada)
        - mes: filtrar por mes (1-12)
        - anio: filtrar por año
        """
        queryset = self.get_queryset()

        # Filtros opcionales
        estado = request.query_params.get('estado')
        mes = request.query_params.get('mes')
        anio = request.query_params.get('anio')

        if estado:
            queryset = queryset.filter(estado=estado)

        if mes:
            queryset = queryset.filter(mes=int(mes))

        if anio:
            queryset = queryset.filter(anio=int(anio))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Detalle de una rifa específica"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Crear nueva rifa (solo admin)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Retornar detalle completo
        rifa = serializer.instance
        detail_serializer = RifaDetailSerializer(rifa, context={'request': request})

        logger.info(f"Rifa creada por {request.user.email}: {rifa.titulo}")

        return Response(
            detail_serializer.data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """Actualizar rifa (solo admin)"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Retornar detalle completo
        detail_serializer = RifaDetailSerializer(instance, context={'request': request})

        logger.info(f"Rifa actualizada por {request.user.email}: {instance.titulo}")

        return Response(detail_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Eliminar rifa (solo admin)
        Solo se pueden eliminar rifas canceladas
        """
        instance = self.get_object()

        if instance.estado != EstadoRifa.CANCELADA:
            return Response(
                {
                    'error': 'Solo se pueden eliminar rifas canceladas',
                    'detail': 'Primero cancela la rifa antes de eliminarla'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        titulo = instance.titulo
        self.perform_destroy(instance)

        logger.warning(f"Rifa eliminada por {request.user.email}: {titulo}")

        return Response(
            {'message': f'Rifa "{titulo}" eliminada correctamente'},
            status=status.HTTP_204_NO_CONTENT
        )

    # ============================================
    # 🎯 CUSTOM ACTIONS
    # ============================================

    @action(detail=False, methods=['get'], url_path='activa')
    def activa(self, request):
        """
        GET /api/rifas/activa/

        Obtiene la rifa activa actual
        Incluye elegibilidad del usuario autenticado
        """
        rifa = Rifa.obtener_rifa_activa()

        if not rifa:
            return Response(
                {
                    'message': 'No hay rifa activa en este momento',
                    'rifa': None
                },
                status=status.HTTP_200_OK
            )

        serializer = self.get_serializer(rifa)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='elegibilidad')
    def elegibilidad(self, request, pk=None):
        """
        GET /api/rifas/{id}/elegibilidad/

        Verifica si el usuario actual es elegible para participar
        """
        rifa = self.get_object()

        elegibilidad = rifa.usuario_es_elegible(request.user)
        serializer = ElegibilidadSerializer(elegibilidad)

        return Response({
            'rifa': {
                'id': str(rifa.id),
                'titulo': rifa.titulo,
                'pedidos_minimos': rifa.pedidos_minimos
            },
            'elegibilidad': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='sortear', permission_classes=[IsAdmin])
    @transaction.atomic
    def sortear(self, request, pk=None):
        """
        POST /api/rifas/{id}/sortear/

        Realiza el sorteo de la rifa (solo admin)

        Body: {"confirmar": true}
        """
        rifa = self.get_object()
        rifa = Rifa.objects.select_for_update().get(pk=pk)

        # Validar input
        input_serializer = RealizarSorteoSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        # Verificar estado
        if rifa.estado != EstadoRifa.ACTIVA:
            return Response(
                {
                    'success': False,
                    'error': f'No se puede sortear una rifa {rifa.get_estado_display().lower()}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if rifa.ganador:
            return Response(
                {
                    'success': False,
                    'error': 'Esta rifa ya tiene un ganador',
                    'ganador': UsuarioSimpleSerializer(rifa.ganador).data
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Realizar sorteo
        try:
            ganador = rifa.realizar_sorteo()

            if ganador:
                logger.info(
                    f"Sorteo realizado por {request.user.email} "
                    f"para rifa {rifa.titulo}. Ganador: {ganador.email}"
                )

                return Response({
                    'success': True,
                    'message': f'¡Sorteo realizado! Ganador: {ganador.get_full_name()}',
                    'ganador': UsuarioSimpleSerializer(ganador).data,
                    'rifa': RifaListSerializer(rifa, context={'request': request}).data,
                    'total_participantes': rifa.total_participantes,
                    'fecha_sorteo': rifa.fecha_sorteo
                })
            else:
                return Response({
                    'success': False,
                    'message': 'No hay participantes elegibles para sortear',
                    'ganador': None,
                    'rifa': RifaListSerializer(rifa, context={'request': request}).data,
                    'total_participantes': 0,
                    'fecha_sorteo': rifa.fecha_sorteo
                })

        except ValidationError as e:
            return Response(
                {
                    'success': False,
                    'error': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error al realizar sorteo: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': 'Error interno al realizar el sorteo'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='participantes', permission_classes=[IsAdmin])
    def participantes(self, request, pk=None):
        """
        GET /api/rifas/{id}/participantes/

        Lista todos los participantes elegibles (solo admin)
        """
        rifa = self.get_object()

        # Obtener participantes elegibles
        participantes_queryset = rifa.obtener_participantes_elegibles()

        # Construir lista con datos
        participantes_data = []
        for usuario in participantes_queryset:
            elegibilidad = rifa.usuario_es_elegible(usuario)
            participantes_data.append({
                'usuario': usuario,
                'pedidos_completados': elegibilidad['pedidos'],
                'elegible': elegibilidad['elegible']
            })

        return Response({
            'total': len(participantes_data),
            'participantes': ParticipanteSerializer(participantes_data, many=True).data
        })

    @action(detail=False, methods=['get'], url_path='historial-ganadores')
    def historial_ganadores(self, request):
        """
        GET /api/rifas/historial-ganadores/

        Obtiene historial de ganadores recientes

        Query params:
        - limit: cantidad de registros (default: 10)
        """
        limit = int(request.query_params.get('limit', 10))

        historial = Rifa.obtener_historial_ganadores(limit=limit)

        data = []
        for rifa in historial:
            data.append({
                'id': rifa.id,
                'titulo': rifa.titulo,
                'mes_nombre': rifa.mes_nombre,
                'anio': rifa.anio,
                'premio': rifa.premio,
                'valor_premio': rifa.valor_premio,
                'ganador': rifa.ganador,
                'fecha_sorteo': rifa.fecha_sorteo,
                'total_participantes': rifa.total_participantes
            })

        serializer = HistorialGanadoresSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='estadisticas')
    def estadisticas(self, request):
        """
        GET /api/rifas/estadisticas/

        Obtiene estadísticas generales del sistema de rifas
        """
        # Rifa activa
        rifa_activa = Rifa.obtener_rifa_activa()

        # Totales
        total_rifas = Rifa.objects.filter(estado=EstadoRifa.FINALIZADA).count()
        total_ganadores = Rifa.objects.filter(
            estado=EstadoRifa.FINALIZADA,
            ganador__isnull=False
        ).count()

        valor_total = Rifa.objects.filter(
            estado=EstadoRifa.FINALIZADA,
            ganador__isnull=False
        ).aggregate(
            total=Sum('valor_premio')
        )['total'] or 0

        # Últimos ganadores
        ultimos_ganadores = Rifa.obtener_historial_ganadores(limit=5)

        # Estadísticas personales del usuario
        mis_participaciones = Participacion.objects.filter(
            usuario=request.user
        ).count()

        mis_victorias = Participacion.objects.filter(
            usuario=request.user,
            ganador=True
        ).count()

        # Construir datos para serializer
        ultimos_ganadores_data = []
        for rifa in ultimos_ganadores:
            ultimos_ganadores_data.append({
                'id': rifa.id,
                'titulo': rifa.titulo,
                'mes_nombre': rifa.mes_nombre,
                'anio': rifa.anio,
                'premio': rifa.premio,
                'valor_premio': rifa.valor_premio,
                'ganador': rifa.ganador,
                'fecha_sorteo': rifa.fecha_sorteo,
                'total_participantes': rifa.total_participantes
            })

        data = {
            'rifa_activa': rifa_activa,
            'total_rifas_realizadas': total_rifas,
            'total_ganadores': total_ganadores,
            'valor_total_premios': valor_total,
            'ultimos_ganadores': ultimos_ganadores_data,
            'mi_participaciones': mis_participaciones,
            'mis_victorias': mis_victorias
        }

        serializer = EstadisticasRifasSerializer(data, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='cancelar', permission_classes=[IsAdmin])
    def cancelar(self, request, pk=None):
        """
        POST /api/rifas/{id}/cancelar/

        Cancela una rifa (solo admin)

        Body (opcional): {"motivo": "razón de cancelación"}
        """
        rifa = self.get_object()

        motivo = request.data.get('motivo', 'Sin motivo especificado')

        try:
            rifa.cancelar_rifa(motivo=motivo)

            logger.warning(
                f"Rifa cancelada por {request.user.email}: {rifa.titulo}. "
                f"Motivo: {motivo}"
            )

            return Response({
                'success': True,
                'message': f'Rifa "{rifa.titulo}" cancelada correctamente',
                'motivo': motivo,
                'rifa': RifaListSerializer(rifa, context={'request': request}).data
            })

        except ValidationError as e:
            return Response(
                {
                    'success': False,
                    'error': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


# ============================================
# 🎟️ VIEWSET: PARTICIPACIONES
# ============================================

class ParticipacionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para Participaciones

    ✅ ENDPOINTS:
    - GET /api/participaciones/              - Listar participaciones
    - GET /api/participaciones/{id}/         - Detalle de participación
    - GET /api/participaciones/mis-participaciones/  - Mis participaciones
    """

    queryset = Participacion.objects.all().select_related(
        'rifa',
        'usuario'
    ).order_by('-fecha_registro')

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Seleccionar serializer"""
        if self.action == 'list':
            return ParticipacionSimpleSerializer
        return ParticipacionSerializer

    def get_queryset(self):
        """
        Filtrar queryset según usuario:
        - Admin: ve todas
        - Usuario: solo sus participaciones
        """
        if self.request.user.is_staff:
            return super().get_queryset()

        return super().get_queryset().filter(usuario=self.request.user)

    @action(detail=False, methods=['get'], url_path='mis-participaciones')
    def mis_participaciones(self, request):
        """
        GET /api/participaciones/mis-participaciones/

        Obtiene todas las participaciones del usuario actual
        """
        participaciones = Participacion.objects.filter(
            usuario=request.user
        ).select_related('rifa').order_by('-fecha_registro')

        serializer = ParticipacionSerializer(
            participaciones,
            many=True,
            context={'request': request}
        )

        return Response({
            'total': participaciones.count(),
            'victorias': participaciones.filter(ganador=True).count(),
            'participaciones': serializer.data
        })
