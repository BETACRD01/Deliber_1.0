# -*- coding: utf-8 -*-
# Proveedores/views.py - VIEWSETS PARA PROVEEDORES Y REPARTIDORES
"""
ViewSets actualizados para permitir edición completa de Proveedores y Repartidores

✅ Métodos update() y partial_update() implementados
✅ Acciones custom para editar contacto
✅ Validaciones robustas
✅ Logs de acciones administrativas
✅ Documentación completa en bloques
✅ Manejo de errores específicos
✅ Optimización de queries (select_related)

CAMBIOS PRINCIPALES:
- ReadOnlyModelViewSet → ModelViewSet (permite POST, PUT, PATCH, DELETE)
- Nuevos serializers para edición
- Métodos update() con validaciones y logs
- Acciones custom editar_contacto()
"""

from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers 
import logging

from authentication.models import User
from proveedores.models import Proveedor
from repartidores.models import Repartidor
from .models import AccionAdministrativa
from .serializers import (
    # Proveedores
    ProveedorListSerializer,
    ProveedorDetalleSerializer,
    ProveedorEditarSerializer,
    ProveedorEditarContactoSerializer,
    VerificarProveedorSerializer,
    # Repartidores
    RepartidorListSerializer,
    RepartidorDetalleSerializer,
    RepartidorEditarSerializer,
    RepartidorEditarContactoSerializer,
    VerificarRepartidorSerializer,
)
from .permissions import (
    EsAdministrador,
    PuedeGestionarProveedores,
    PuedeGestionarRepartidores,
    AdministradorActivo,
    obtener_perfil_admin,
)

logger = logging.getLogger('administradores')


# ════════════════════════════════════════════════════════════════════════════
# BLOQUE 0: VIEWSET PÚBLICO PARA CONSULTAR PROVEEDORES
# ════════════════════════════════════════════════════════════════════════════

class ProveedorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet PÚBLICO para consultar proveedores
    
    Solo permite: GET (lista y detalle)
    No permite: POST, PUT, PATCH, DELETE
    
    Endpoints:
    - GET /api/proveedores/
        Listar todos los proveedores verificados y activos
        Query params: tipo_proveedor=restaurante, ciudad=Quito, search=nombre
    
    - GET /api/proveedores/{id}/
        Obtener detalle de un proveedor
    
    - GET /api/proveedores/activos/
        Listar solo proveedores activos
    
    - GET /api/proveedores/abiertos/
        Listar solo proveedores abiertos ahora
    
    - GET /api/proveedores/por_tipo/
        Listar por tipo de proveedor
    
    - GET /api/proveedores/pendientes/
        Listar pendientes de verificación
    """
    
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo_proveedor', 'ciudad', 'activo', 'verificado']
    search_fields = ['nombre', 'descripcion', 'ciudad']
    ordering_fields = ['nombre', 'created_at']
    ordering = ['nombre']
    
    def get_queryset(self):
        """
        Retorna solo proveedores activos y verificados (público)
        """
        return Proveedor.objects.filter(
            activo=True,
            verificado=True,
            deleted_at__isnull=True
        ).select_related('user')
    
    def get_serializer_class(self):
        """Selecciona serializer según acción"""
        if self.action == 'list':
            return ProveedorListSerializer
        return ProveedorDetalleSerializer
    
    def list(self, request, *args, **kwargs):
        """GET /api/proveedores/ - Listar proveedores"""
        logger.info(f"📥 Listando proveedores - IP: {request.META.get('REMOTE_ADDR')}")
        return super().list(request, *args, **kwargs)
    
    def retrieve(self, request, *args, **kwargs):
        """GET /api/proveedores/{id}/ - Detalle de proveedor"""
        proveedor = self.get_object()
        logger.info(f"📥 Detalle de proveedor: {proveedor.nombre} - IP: {request.META.get('REMOTE_ADDR')}")
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def activos(self, request):
        """GET /api/proveedores/activos/ - Solo proveedores activos"""
        proveedores = self.get_queryset().filter(activo=True)
        serializer = self.get_serializer(proveedores, many=True)
        
        logger.info(f"📥 Listando {proveedores.count()} proveedores activos")
        
        return Response({
            'total': proveedores.count(),
            'proveedores': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def abiertos(self, request):
        """GET /api/proveedores/abiertos/ - Proveedores abiertos ahora"""
        from datetime import datetime
        
        proveedores = self.get_queryset()
        abiertos = []
        
        for proveedor in proveedores:
            if proveedor.esta_abierto():
                abiertos.append(proveedor)
        
        serializer = self.get_serializer(abiertos, many=True)
        
        logger.info(f"📥 Listando {len(abiertos)} proveedores abiertos")
        
        return Response({
            'total': len(abiertos),
            'proveedores': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """GET /api/proveedores/por_tipo/?tipo=restaurante"""
        tipo = request.query_params.get('tipo')
        
        if not tipo:
            return Response({
                'error': 'Debes proporcionar el parámetro tipo',
                'tipos_validos': [
                    'restaurante',
                    'farmacia',
                    'supermercado',
                    'tienda',
                    'otro'
                ]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        proveedores = self.get_queryset().filter(tipo_proveedor=tipo)
        serializer = self.get_serializer(proveedores, many=True)
        
        logger.info(f"📥 Listando {proveedores.count()} proveedores tipo {tipo}")
        
        return Response({
            'total': proveedores.count(),
            'tipo': tipo,
            'proveedores': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """GET /api/proveedores/pendientes/ - Pendientes de verificación"""
        # Para usuarios autenticados que sean admin
        if not request.user.is_authenticated or request.user.rol != 'ADMINISTRADOR':
            return Response({
                'error': 'No tienes permiso para ver proveedores pendientes'
            }, status=status.HTTP_403_FORBIDDEN)
        
        pendientes = Proveedor.objects.filter(
            verificado=False,
            activo=True,
            deleted_at__isnull=True
        ).select_related('user')
        
        serializer = ProveedorListSerializer(pendientes, many=True)
        
        logger.info(f"🛡️ Admin {request.user.email} listando {pendientes.count()} proveedores pendientes")
        
        return Response({
            'total': pendientes.count(),
            'proveedores': serializer.data
        })


# ════════════════════════════════════════════════════════════════════════════
# BLOQUE 1: HELPER - REGISTRAR ACCIONES
# ════════════════════════════════════════════════════════════════════════════

def registrar_accion_admin(request, tipo_accion, descripcion, **kwargs):
    """
    Helper para registrar acciones administrativas
    
    Args:
        request: Objeto request de Django
        tipo_accion (str): Tipo de acción (editar_proveedor, etc)
        descripcion (str): Descripción detallada de la acción
        **kwargs: Datos adicionales (modelo_afectado, objeto_id, datos_nuevos, etc)
    
    Returns:
        AccionAdministrativa: Instancia creada o None si hay error
    """
    try:
        admin = obtener_perfil_admin(request.user)
        if not admin:
            logger.warning(
                f"Usuario sin perfil admin intentó registrar acción: {request.user.email}"
            )
            return None

        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        AccionAdministrativa.registrar_accion(
            administrador=admin,
            tipo_accion=tipo_accion,
            descripcion=descripcion,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs
        )
    except Exception as e:
        logger.error(f"❌ Error registrando acción: {e}")
        return None


# ════════════════════════════════════════════════════════════════════════════
# BLOQUE 2: VIEWSET GESTIÓN DE PROVEEDORES
# ════════════════════════════════════════════════════════════════════════════

class GestionProveedoresViewSet(viewsets.ModelViewSet):
    """
    ViewSet para GESTIÓN COMPLETA de Proveedores
    
    Ahora permite: GET, POST, PUT, PATCH, DELETE (además de acciones custom)
    Cambio: ReadOnlyModelViewSet → ModelViewSet
    
    Endpoints:
    
    LISTADO Y DETALLE (GET):
    - GET /api/admin/proveedores/
        Listar todos los proveedores con filtros
        Query params: verificado=true/false, activo=true/false, tipo_proveedor=RESTAURANT
    
    - GET /api/admin/proveedores/{id}/
        Obtener detalle completo de un proveedor
    
    EDICIÓN (PUT/PATCH):
    - PUT /api/admin/proveedores/{id}/
        Editar toda la información del proveedor
        Body: todos los campos de ProveedorEditarSerializer
    
    - PATCH /api/admin/proveedores/{id}/
        Editar parcialmente (solo los campos enviados)
        Body: campos que quieras actualizar
    
    ACCIONES CUSTOM (POST):
    - POST /api/admin/proveedores/{id}/verificar/
        Verificar o rechazar un proveedor (ya existe)
    
    - POST /api/admin/proveedores/{id}/desactivar/
        Desactivar un proveedor (ya existe)
    
    - POST /api/admin/proveedores/{id}/activar/
        Activar un proveedor (ya existe)
    
    - PATCH /api/admin/proveedores/{id}/editar_contacto/
        Editar email y datos de contacto
    
    - GET /api/admin/proveedores/pendientes/
        Listar solo los pendientes de verificación (ya existe)
    """
    
    permission_classes = [
        IsAuthenticated,
        EsAdministrador,
        AdministradorActivo,
        PuedeGestionarProveedores
    ]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['verificado', 'activo', 'tipo_proveedor']
    search_fields = ['nombre', 'user__email', 'telefono']
    ordering_fields = ['created_at', 'nombre']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Obtiene queryset optimizado de proveedores
        Usa select_related para evitar N+1 queries
        """
        return Proveedor.objects.select_related('user').all()

    def get_serializer_class(self):
        """
        Selecciona el serializer según la acción
        - list: ProveedorListSerializer (datos básicos)
        - retrieve: ProveedorDetalleSerializer (completo)
        - update/partial_update: ProveedorEditarSerializer (edición)
        - editar_contacto: ProveedorEditarContactoSerializer (contacto)
        """
        if self.action == 'list':
            return ProveedorListSerializer
        elif self.action in ['update', 'partial_update']:
            return ProveedorEditarSerializer
        elif self.action == 'editar_contacto':
            return ProveedorEditarContactoSerializer
        return ProveedorDetalleSerializer

    # -------- MÉTODOS ESTÁNDAR --------

    def retrieve(self, request, *args, **kwargs):
        """
        GET /api/admin/proveedores/{id}/
        
        Obtiene detalle completo de un proveedor
        
        Response:
        {
            "id": 1,
            "nombre": "Mi Restaurante",
            "email": "contacto@mirestaurante.com",
            "telefono": "0987654321",
            "tipo_proveedor": "restaurante",
            "ruc": "1234567890123",
            "verificado": true,
            "activo": true
        }
        """
        proveedor = self.get_object()
        serializer = self.get_serializer(proveedor)

        logger.info(
            f"👁️ Admin {request.user.email} viendo detalle de proveedor: {proveedor.nombre}"
        )

        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        PUT /api/admin/proveedores/{id}/
        
        Edita TODA la información de un proveedor
        Requiere todos los campos de edición
        """
        partial = False  # PUT requiere todos los campos
        proveedor = self.get_object()

        serializer = self.get_serializer(
            proveedor,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)

        # Guardar cambios
        self.perform_update(serializer)

        # Registrar acción administrativa
        registrar_accion_admin(
            request,
            'editar_proveedor',
            f"Proveedor editado: {proveedor.nombre}",
            modelo_afectado='Proveedor',
            objeto_id=str(proveedor.id),
            datos_nuevos=serializer.data
        )

        logger.info(
            f"✅ Proveedor editado por admin: {proveedor.nombre} "
            f"por {request.user.email}"
        )

        return Response({
            'message': 'Proveedor editado exitosamente',
            'proveedor': ProveedorDetalleSerializer(proveedor).data
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /api/admin/proveedores/{id}/
        
        Edita PARCIALMENTE un proveedor
        Solo actualiza los campos enviados, el resto se mantiene igual
        """
        partial = True  # PATCH permite campos parciales
        proveedor = self.get_object()

        serializer = self.get_serializer(
            proveedor,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)

        # Guardar cambios
        self.perform_update(serializer)

        # Registrar acción administrativa
        registrar_accion_admin(
            request,
            'editar_proveedor',
            f"Información de proveedor actualizada: {proveedor.nombre}",
            modelo_afectado='Proveedor',
            objeto_id=str(proveedor.id),
            datos_nuevos=serializer.data
        )

        logger.info(
            f"✅ Proveedor actualizado por admin: {proveedor.nombre} "
            f"por {request.user.email}"
        )

        return Response({
            'message': 'Proveedor actualizado exitosamente',
            'proveedor': ProveedorDetalleSerializer(proveedor).data
        }, status=status.HTTP_200_OK)

    # -------- ACCIONES CUSTOM --------

    @action(detail=True, methods=['patch'])
    def editar_contacto(self, request, pk=None):
        """
        PATCH /api/admin/proveedores/{id}/editar_contacto/
        
        Edita los datos de CONTACTO del proveedor
        Modifica: email, nombre, apellido del usuario asociado
        """
        proveedor = self.get_object()
        usuario = proveedor.user

        serializer = self.get_serializer(
            data=request.data,
            context={'usuario': usuario}
        )
        serializer.is_valid(raise_exception=True)

        # Obtener datos validados
        email = serializer.validated_data.get('email')
        first_name = serializer.validated_data.get('first_name')
        last_name = serializer.validated_data.get('last_name')

        # Guardar cambios en el usuario
        if email:
            usuario.email = email
        if first_name:
            usuario.first_name = first_name
        if last_name:
            usuario.last_name = last_name

        usuario.save()

        # Registrar acción administrativa
        registrar_accion_admin(
            request,
            'editar_proveedor_contacto',
            f"Contacto del proveedor editado: {proveedor.nombre}",
            modelo_afectado='User',
            objeto_id=str(usuario.id),
            datos_nuevos={
                'email': usuario.email,
                'nombre_completo': usuario.get_full_name()
            }
        )

        logger.info(
            f"✅ Contacto del proveedor editado: {proveedor.nombre} "
            f"por {request.user.email}"
        )

        return Response({
            'message': 'Contacto editado exitosamente',
            'proveedor': ProveedorDetalleSerializer(proveedor).data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def verificar(self, request, pk=None):
        """
        POST /api/admin/proveedores/{id}/verificar/
        
        Verifica o rechaza un proveedor
        """
        proveedor = self.get_object()

        serializer = VerificarProveedorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verificado = serializer.validated_data['verificado']
        motivo = serializer.validated_data.get('motivo', '')

        # Cambiar estado
        proveedor.verificado = verificado
        proveedor.save(update_fields=['verificado', 'updated_at'])

        # Si se rechaza, desactivar
        if not verificado:
            proveedor.activo = False
            proveedor.save(update_fields=['activo'])

        # Registrar acción
        accion = 'verificar_proveedor' if verificado else 'rechazar_proveedor'
        registrar_accion_admin(
            request,
            accion,
            f"Proveedor {'verificado' if verificado else 'rechazado'}: {proveedor.nombre}. Motivo: {motivo}",
            modelo_afectado='Proveedor',
            objeto_id=str(proveedor.id)
        )

        logger.info(
            f"✅ Proveedor {'verificado' if verificado else 'rechazado'}: "
            f"{proveedor.nombre} por {request.user.email}"
        )

        return Response({
            'message': f"Proveedor {'verificado' if verificado else 'rechazado'} exitosamente",
            'proveedor': ProveedorDetalleSerializer(proveedor).data
        })

    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        """
        POST /api/admin/proveedores/{id}/desactivar/
        
        Desactiva un proveedor
        """
        proveedor = self.get_object()

        if not proveedor.activo:
            return Response(
                {'error': 'El proveedor ya está desactivado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        proveedor.activo = False
        proveedor.save(update_fields=['activo', 'updated_at'])

        # Registrar acción
        registrar_accion_admin(
            request,
            'desactivar_proveedor',
            f"Proveedor desactivado: {proveedor.nombre}",
            modelo_afectado='Proveedor',
            objeto_id=str(proveedor.id)
        )

        logger.warning(
            f"⚠️ Proveedor desactivado: {proveedor.nombre} por {request.user.email}"
        )

        return Response({
            'message': 'Proveedor desactivado exitosamente'
        })

    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """
        POST /api/admin/proveedores/{id}/activar/
        
        Activa un proveedor
        """
        proveedor = self.get_object()

        if proveedor.activo:
            return Response(
                {'error': 'El proveedor ya está activo'},
                status=status.HTTP_400_BAD_REQUEST
            )

        proveedor.activo = True
        proveedor.save(update_fields=['activo', 'updated_at'])

        # Registrar acción
        registrar_accion_admin(
            request,
            'activar_proveedor',
            f"Proveedor activado: {proveedor.nombre}",
            modelo_afectado='Proveedor',
            objeto_id=str(proveedor.id)
        )

        logger.info(
            f"✅ Proveedor activado: {proveedor.nombre} por {request.user.email}"
        )

        return Response({
            'message': 'Proveedor activado exitosamente'
        })

    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """
        GET /api/admin/proveedores/pendientes/
        
        Lista proveedores pendientes de verificación
        """
        pendientes = self.get_queryset().filter(verificado=False, activo=True)
        serializer = self.get_serializer(pendientes, many=True)

        return Response({
            'total': pendientes.count(),
            'proveedores': serializer.data
        })


# ════════════════════════════════════════════════════════════════════════════
# BLOQUE 3: VIEWSET GESTIÓN DE REPARTIDORES
# ════════════════════════════════════════════════════════════════════════════

class GestionRepartidoresViewSet(viewsets.ModelViewSet):
    """
    ViewSet para GESTIÓN COMPLETA de Repartidores
    
    Ahora permite: GET, POST, PUT, PATCH, DELETE (además de acciones custom)
    """
    
    permission_classes = [
        IsAuthenticated,
        EsAdministrador,
        AdministradorActivo,
        PuedeGestionarRepartidores
    ]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['verificado', 'activo', 'estado']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'cedula', 'telefono']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Obtiene queryset optimizado de repartidores
        Usa select_related para evitar N+1 queries
        """
        return Repartidor.objects.select_related('user').all()

    def get_serializer_class(self):
        """
        Selecciona el serializer según la acción
        """
        if self.action == 'list':
            return RepartidorListSerializer
        elif self.action in ['update', 'partial_update']:
            return RepartidorEditarSerializer
        elif self.action == 'editar_contacto':
            return RepartidorEditarContactoSerializer
        return RepartidorDetalleSerializer

    # -------- MÉTODOS ESTÁNDAR --------

    def retrieve(self, request, *args, **kwargs):
        """
        GET /api/admin/repartidores/{id}/
        
        Obtiene detalle completo de un repartidor
        """
        repartidor = self.get_object()
        serializer = self.get_serializer(repartidor)

        logger.info(
            f"👁️ Admin {request.user.email} viendo detalle de repartidor: {repartidor.user.get_full_name()}"
        )

        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        PUT /api/admin/repartidores/{id}/
        
        Edita TODA la información de un repartidor
        """
        partial = False
        repartidor = self.get_object()

        serializer = self.get_serializer(
            repartidor,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)

        registrar_accion_admin(
            request,
            'editar_repartidor',
            f"Repartidor editado: {repartidor.user.get_full_name()}",
            modelo_afectado='Repartidor',
            objeto_id=str(repartidor.id),
            datos_nuevos=serializer.data
        )

        logger.info(
            f"✅ Repartidor editado por admin: {repartidor.user.get_full_name()} "
            f"por {request.user.email}"
        )

        return Response({
            'message': 'Repartidor editado exitosamente',
            'repartidor': RepartidorDetalleSerializer(repartidor).data
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /api/admin/repartidores/{id}/
        
        Edita PARCIALMENTE un repartidor
        """
        partial = True
        repartidor = self.get_object()

        serializer = self.get_serializer(
            repartidor,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)

        registrar_accion_admin(
            request,
            'editar_repartidor',
            f"Información de repartidor actualizada: {repartidor.user.get_full_name()}",
            modelo_afectado='Repartidor',
            objeto_id=str(repartidor.id),
            datos_nuevos=serializer.data
        )

        logger.info(
            f"✅ Repartidor actualizado por admin: {repartidor.user.get_full_name()} "
            f"por {request.user.email}"
        )

        return Response({
            'message': 'Repartidor actualizado exitosamente',
            'repartidor': RepartidorDetalleSerializer(repartidor).data
        }, status=status.HTTP_200_OK)

    # -------- ACCIONES CUSTOM --------

    @action(detail=True, methods=['patch'])
    def editar_contacto(self, request, pk=None):
        """
        PATCH /api/admin/repartidores/{id}/editar_contacto/
        
        Edita los datos de CONTACTO del repartidor
        """
        repartidor = self.get_object()
        usuario = repartidor.user

        serializer = self.get_serializer(
            data=request.data,
            context={'usuario': usuario}
        )
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        first_name = serializer.validated_data.get('first_name')
        last_name = serializer.validated_data.get('last_name')

        if email:
            usuario.email = email
        if first_name:
            usuario.first_name = first_name
        if last_name:
            usuario.last_name = last_name

        usuario.save()

        registrar_accion_admin(
            request,
            'editar_repartidor_contacto',
            f"Contacto del repartidor editado: {repartidor.user.get_full_name()}",
            modelo_afectado='User',
            objeto_id=str(usuario.id),
            datos_nuevos={
                'email': usuario.email,
                'nombre_completo': usuario.get_full_name()
            }
        )

        logger.info(
            f"✅ Contacto del repartidor editado: {repartidor.user.get_full_name()} "
            f"por {request.user.email}"
        )

        return Response({
            'message': 'Contacto editado exitosamente',
            'repartidor': RepartidorDetalleSerializer(repartidor).data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def verificar(self, request, pk=None):
        """
        POST /api/admin/repartidores/{id}/verificar/
        
        Verifica o rechaza un repartidor
        """
        repartidor = self.get_object()

        serializer = VerificarRepartidorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verificado = serializer.validated_data['verificado']
        motivo = serializer.validated_data.get('motivo', '')

        repartidor.verificado = verificado
        repartidor.save(update_fields=['verificado', 'updated_at'])

        if not verificado:
            repartidor.activo = False
            repartidor.save(update_fields=['activo'])

        accion = 'verificar_repartidor' if verificado else 'rechazar_repartidor'
        registrar_accion_admin(
            request,
            accion,
            f"Repartidor {'verificado' if verificado else 'rechazado'}: {repartidor.user.get_full_name()}. Motivo: {motivo}",
            modelo_afectado='Repartidor',
            objeto_id=str(repartidor.id)
        )

        logger.info(
            f"✅ Repartidor {'verificado' if verificado else 'rechazado'}: "
            f"{repartidor.user.get_full_name()} por {request.user.email}"
        )

        return Response({
            'message': f"Repartidor {'verificado' if verificado else 'rechazado'} exitosamente",
            'repartidor': RepartidorDetalleSerializer(repartidor).data
        })

    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        """
        POST /api/admin/repartidores/{id}/desactivar/
        
        Desactiva un repartidor
        """
        repartidor = self.get_object()

        if not repartidor.activo:
            return Response(
                {'error': 'El repartidor ya está desactivado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        repartidor.activo = False
        repartidor.save(update_fields=['activo', 'updated_at'])

        registrar_accion_admin(
            request,
            'desactivar_repartidor',
            f"Repartidor desactivado: {repartidor.user.get_full_name()}",
            modelo_afectado='Repartidor',
            objeto_id=str(repartidor.id)
        )

        logger.warning(
            f"⚠️ Repartidor desactivado: {repartidor.user.get_full_name()} "
            f"por {request.user.email}"
        )

        return Response({
            'message': 'Repartidor desactivado exitosamente'
        })

    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """
        POST /api/admin/repartidores/{id}/activar/
        
        Activa un repartidor
        """
        repartidor = self.get_object()

        if repartidor.activo:
            return Response(
                {'error': 'El repartidor ya está activo'},
                status=status.HTTP_400_BAD_REQUEST
            )

        repartidor.activo = True
        repartidor.save(update_fields=['activo', 'updated_at'])

        registrar_accion_admin(
            request,
            'activar_repartidor',
            f"Repartidor activado: {repartidor.user.get_full_name()}",
            modelo_afectado='Repartidor',
            objeto_id=str(repartidor.id)
        )

        logger.info(
            f"✅ Repartidor activado: {repartidor.user.get_full_name()} "
            f"por {request.user.email}"
        )

        return Response({
            'message': 'Repartidor activado exitosamente'
        })

    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """
        GET /api/admin/repartidores/pendientes/
        
        Lista repartidores pendientes de verificación
        """
        pendientes = self.get_queryset().filter(verificado=False, activo=True)
        serializer = self.get_serializer(pendientes, many=True)

        return Response({
            'total': pendientes.count(),
            'repartidores': serializer.data
        })