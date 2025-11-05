# -*- coding: utf-8 -*-
# administradores/views.py
"""
ViewSets para gestión de usuarios por administradores
✅ Gestión completa de usuarios regulares
✅ Gestión de proveedores (verificar, desactivar)
✅ Gestión de repartidores (verificar, desactivar)
✅ Logs de acciones administrativas
✅ Configuración del sistema
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
import logging

from authentication.models import User
from usuarios.models import Perfil
from proveedores.models import Proveedor
from repartidores.models import Repartidor
from pedidos.models import Pedido, EstadoPedido
from .models import Administrador, AccionAdministrativa, ConfiguracionSistema
from .serializers import (
    AdministradorSerializer,
    UsuarioListSerializer,
    UsuarioDetalleSerializer,
    UsuarioEditarSerializer,
    CambiarRolSerializer,
    DesactivarUsuarioSerializer,
    ResetearPasswordSerializer,
    ProveedorListSerializer,
    ProveedorDetalleSerializer,
    VerificarProveedorSerializer,
    RepartidorListSerializer,
    RepartidorDetalleSerializer,
    VerificarRepartidorSerializer,
    AccionAdministrativaSerializer,
    ConfiguracionSistemaSerializer,
)
from .permissions import (
    EsAdministrador,
    PuedeGestionarUsuarios,
    PuedeGestionarProveedores,
    PuedeGestionarRepartidores,
    PuedeConfigurarSistema,
    AdministradorActivo,
    validar_no_es_superusuario,
    validar_no_auto_modificacion_critica,
    obtener_perfil_admin,
)

logger = logging.getLogger('administradores')


# ============================================
# HELPER: REGISTRAR ACCIÓN
# ============================================

def registrar_accion_admin(request, tipo_accion, descripcion, **kwargs):
    """
    Helper para registrar acciones administrativas
    """
    try:
        admin = obtener_perfil_admin(request.user)
        if not admin:
            logger.warning(f"Usuario sin perfil admin intentó registrar acción: {request.user.email}")
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


# ============================================
# VIEWSET: GESTIÓN DE USUARIOS
# ============================================

class GestionUsuariosViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión completa de usuarios

    Endpoints:
    - GET /api/admin/usuarios/ - Listar usuarios
    - GET /api/admin/usuarios/{id}/ - Detalle de usuario
    - PUT/PATCH /api/admin/usuarios/{id}/ - Editar usuario
    - POST /api/admin/usuarios/{id}/cambiar_rol/ - Cambiar rol
    - POST /api/admin/usuarios/{id}/desactivar/ - Desactivar usuario
    - POST /api/admin/usuarios/{id}/activar/ - Activar usuario
    - POST /api/admin/usuarios/{id}/resetear_password/ - Resetear contraseña
    - GET /api/admin/usuarios/{id}/historial_pedidos/ - Ver pedidos del usuario
    - GET /api/admin/usuarios/estadisticas/ - Estadísticas de usuarios
    """
    permission_classes = [IsAuthenticated, EsAdministrador, AdministradorActivo, PuedeGestionarUsuarios]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['rol', 'is_active', 'cuenta_desactivada', 'verificado']
    search_fields = ['email', 'first_name', 'last_name', 'celular', 'username']
    ordering_fields = ['created_at', 'email', 'first_name']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Queryset de usuarios excluyendo administradores (se gestionan aparte)
        """
        return User.objects.exclude(
            rol=User.RolChoices.ADMINISTRADOR
        ).select_related('perfil_usuario')

    def get_serializer_class(self):
        """
        Serializer según la acción
        """
        if self.action == 'list':
            return UsuarioListSerializer
        elif self.action in ['update', 'partial_update']:
            return UsuarioEditarSerializer
        elif self.action == 'cambiar_rol':
            return CambiarRolSerializer
        elif self.action == 'desactivar':
            return DesactivarUsuarioSerializer
        elif self.action == 'resetear_password':
            return ResetearPasswordSerializer
        return UsuarioDetalleSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        GET /api/admin/usuarios/{id}/

        Detalle completo de un usuario
        """
        usuario = self.get_object()
        serializer = self.get_serializer(usuario)

        logger.info(f"👁️ Admin {request.user.email} viendo detalle de usuario {usuario.email}")

        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        PUT/PATCH /api/admin/usuarios/{id}/

        Editar información de un usuario
        """
        partial = kwargs.pop('partial', False)
        usuario = self.get_object()

        # Validar que no sea superusuario
        validar_no_es_superusuario(usuario)

        serializer = self.get_serializer(usuario, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Guardar cambios
        self.perform_update(serializer)

        # Registrar acción
        registrar_accion_admin(
            request,
            'editar_usuario',
            f"Usuario editado: {usuario.email}",
            modelo_afectado='User',
            objeto_id=str(usuario.id),
            datos_nuevos=serializer.data
        )

        logger.info(f"✅ Usuario editado por admin: {usuario.email}")

        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cambiar_rol(self, request, pk=None):
        """
        POST /api/admin/usuarios/{id}/cambiar_rol/

        Cambia el rol de un usuario

        Body:
        {
            "nuevo_rol": "REPARTIDOR",
            "motivo": "Solicitud aprobada"
        }
        """
        usuario = self.get_object()

        # Validaciones
        validar_no_es_superusuario(usuario)
        validar_no_auto_modificacion_critica(request.user, usuario, 'cambiar_rol')

        serializer = CambiarRolSerializer(
            data=request.data,
            context={'usuario': usuario}
        )
        serializer.is_valid(raise_exception=True)

        rol_anterior = usuario.rol
        nuevo_rol = serializer.validated_data['nuevo_rol']
        motivo = serializer.validated_data.get('motivo', '')

        # Cambiar rol
        usuario.rol = nuevo_rol
        usuario.save(update_fields=['rol', 'updated_at'])

        # Registrar acción
        registrar_accion_admin(
            request,
            'cambiar_rol',
            f"Rol cambiado de {rol_anterior} a {nuevo_rol} para {usuario.email}. Motivo: {motivo}",
            modelo_afectado='User',
            objeto_id=str(usuario.id),
            datos_anteriores={'rol': rol_anterior},
            datos_nuevos={'rol': nuevo_rol}
        )

        logger.info(
            f"✅ Rol cambiado: {usuario.email} - {rol_anterior} → {nuevo_rol} "
            f"por {request.user.email}"
        )

        return Response({
            'message': f'Rol cambiado exitosamente de {rol_anterior} a {nuevo_rol}',
            'usuario': UsuarioDetalleSerializer(usuario).data
        })

    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        """
        POST /api/admin/usuarios/{id}/desactivar/

        Desactiva un usuario

        Body:
        {
            "razon": "Violación de términos",
            "permanente": false
        }
        """
        usuario = self.get_object()

        # Validaciones
        validar_no_es_superusuario(usuario)
        validar_no_auto_modificacion_critica(request.user, usuario, 'desactivar')

        serializer = DesactivarUsuarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        razon = serializer.validated_data['razon']
        permanente = serializer.validated_data['permanente']

        # Desactivar usuario
        usuario.desactivar_cuenta(razon=razon)

        if permanente:
            usuario.is_active = False
            usuario.save(update_fields=['is_active'])

        # Registrar acción
        registrar_accion_admin(
            request,
            'desactivar_usuario',
            f"Usuario desactivado: {usuario.email}. Razón: {razon}. Permanente: {permanente}",
            modelo_afectado='User',
            objeto_id=str(usuario.id)
        )

        logger.warning(
            f"⚠️ Usuario desactivado: {usuario.email} por {request.user.email}. "
            f"Razón: {razon}"
        )

        return Response({
            'message': 'Usuario desactivado exitosamente',
            'permanente': permanente
        })

    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """
        POST /api/admin/usuarios/{id}/activar/

        Activa un usuario desactivado
        """
        usuario = self.get_object()

        # Validar que no sea superusuario
        validar_no_es_superusuario(usuario)

        if not usuario.cuenta_desactivada and usuario.is_active:
            return Response(
                {'error': 'El usuario ya está activo'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Reactivar usuario
        usuario.reactivar_cuenta()
        usuario.is_active = True
        usuario.save(update_fields=['is_active'])

        # Registrar acción
        registrar_accion_admin(
            request,
            'activar_usuario',
            f"Usuario activado: {usuario.email}",
            modelo_afectado='User',
            objeto_id=str(usuario.id)
        )

        logger.info(f"✅ Usuario reactivado: {usuario.email} por {request.user.email}")

        return Response({
            'message': 'Usuario activado exitosamente',
            'usuario': UsuarioDetalleSerializer(usuario).data
        })

    @action(detail=True, methods=['post'])
    def resetear_password(self, request, pk=None):
        """
        POST /api/admin/usuarios/{id}/resetear_password/

        Resetea la contraseña de un usuario

        Body:
        {
            "nueva_password": "nuevapassword123",
            "confirmar_password": "nuevapassword123"
        }
        """
        usuario = self.get_object()

        # Validaciones
        validar_no_es_superusuario(usuario)

        serializer = ResetearPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        nueva_password = serializer.validated_data['nueva_password']

        # Cambiar contraseña
        usuario.set_password(nueva_password)
        usuario.save(update_fields=['password'])

        # Limpiar intentos fallidos
        usuario.intentos_login_fallidos = 0
        usuario.cuenta_bloqueada_hasta = None
        usuario.save(update_fields=['intentos_login_fallidos', 'cuenta_bloqueada_hasta'])

        # Registrar acción
        registrar_accion_admin(
            request,
            'resetear_password',
            f"Contraseña reseteada para: {usuario.email}",
            modelo_afectado='User',
            objeto_id=str(usuario.id)
        )

        logger.info(f"🔑 Contraseña reseteada: {usuario.email} por {request.user.email}")

        return Response({
            'message': 'Contraseña reseteada exitosamente'
        })

    @action(detail=True, methods=['get'])
    def historial_pedidos(self, request, pk=None):
        """
        GET /api/admin/usuarios/{id}/historial_pedidos/

        Ver historial de pedidos del usuario
        """
        usuario = self.get_object()

        if usuario.rol != User.RolChoices.USUARIO:
            return Response(
                {'error': 'Solo usuarios regulares tienen historial de pedidos'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            perfil = usuario.perfil_usuario
            pedidos = perfil.pedidos.all().order_by('-creado_en')[:50]  # Últimos 50

            from pedidos.serializers import PedidoSerializer
            serializer = PedidoSerializer(pedidos, many=True)

            return Response({
                'total_pedidos': perfil.total_pedidos,
                'pedidos_mes_actual': perfil.pedidos_mes_actual,
                'pedidos': serializer.data
            })

        except Exception as e:
            logger.error(f"❌ Error obteniendo historial de pedidos: {e}")
            return Response(
                {'error': 'Error al obtener historial'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        GET /api/admin/usuarios/estadisticas/

        Estadísticas generales de usuarios
        """
        total_usuarios = User.objects.count()
        usuarios_activos = User.objects.filter(is_active=True, cuenta_desactivada=False).count()
        usuarios_desactivados = User.objects.filter(Q(is_active=False) | Q(cuenta_desactivada=True)).count()

        # Por rol
        por_rol = User.objects.values('rol').annotate(total=Count('id'))

        # Usuarios nuevos (último mes)
        hace_un_mes = timezone.now() - timezone.timedelta(days=30)
        usuarios_nuevos = User.objects.filter(created_at__gte=hace_un_mes).count()

        return Response({
            'total_usuarios': total_usuarios,
            'usuarios_activos': usuarios_activos,
            'usuarios_desactivados': usuarios_desactivados,
            'usuarios_nuevos_mes': usuarios_nuevos,
            'por_rol': list(por_rol),
        })


# ============================================
# VIEWSET: GESTIÓN DE PROVEEDORES
# ============================================

class GestionProveedoresViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestión de proveedores

    Endpoints:
    - GET /api/admin/proveedores/ - Listar proveedores
    - GET /api/admin/proveedores/{id}/ - Detalle de proveedor
    - POST /api/admin/proveedores/{id}/verificar/ - Verificar proveedor
    - POST /api/admin/proveedores/{id}/desactivar/ - Desactivar proveedor
    - POST /api/admin/proveedores/{id}/activar/ - Activar proveedor
    - GET /api/admin/proveedores/pendientes/ - Proveedores pendientes de verificación
    """
    permission_classes = [IsAuthenticated, EsAdministrador, AdministradorActivo, PuedeGestionarProveedores]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['verificado', 'activo', 'tipo_proveedor']
    search_fields = ['nombre', 'user__email', 'telefono']
    ordering_fields = ['creado_en', 'nombre', 'calificacion_promedio']
    ordering = ['-creado_en']

    def get_queryset(self):
        """
        Queryset de proveedores
        """
        return Proveedor.objects.select_related('user').all()

    def get_serializer_class(self):
        """
        Serializer según la acción
        """
        if self.action == 'list':
            return ProveedorListSerializer
        return ProveedorDetalleSerializer

    @action(detail=True, methods=['post'])
    def verificar(self, request, pk=None):
        """
        POST /api/admin/proveedores/{id}/verificar/

        Verifica o rechaza un proveedor

        Body:
        {
            "verificado": true,
            "motivo": "Documentación completa"
        }
        """
        proveedor = self.get_object()

        serializer = VerificarProveedorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verificado = serializer.validated_data['verificado']
        motivo = serializer.validated_data.get('motivo', '')

        # Cambiar estado
        proveedor.verificado = verificado
        proveedor.save(update_fields=['verificado', 'actualizado_en'])

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
        proveedor.save(update_fields=['activo', 'actualizado_en'])

        # Registrar acción
        registrar_accion_admin(
            request,
            'desactivar_proveedor',
            f"Proveedor desactivado: {proveedor.nombre}",
            modelo_afectado='Proveedor',
            objeto_id=str(proveedor.id)
        )

        logger.warning(f"⚠️ Proveedor desactivado: {proveedor.nombre} por {request.user.email}")

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
        proveedor.save(update_fields=['activo', 'actualizado_en'])

        # Registrar acción
        registrar_accion_admin(
            request,
            'activar_proveedor',
            f"Proveedor activado: {proveedor.nombre}",
            modelo_afectado='Proveedor',
            objeto_id=str(proveedor.id)
        )

        logger.info(f"✅ Proveedor activado: {proveedor.nombre} por {request.user.email}")

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


# ============================================
# VIEWSET: GESTIÓN DE REPARTIDORES
# ============================================

class GestionRepartidoresViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestión de repartidores

    Endpoints:
    - GET /api/admin/repartidores/ - Listar repartidores
    - GET /api/admin/repartidores/{id}/ - Detalle de repartidor
    - POST /api/admin/repartidores/{id}/verificar/ - Verificar repartidor
    - POST /api/admin/repartidores/{id}/desactivar/ - Desactivar repartidor
    - POST /api/admin/repartidores/{id}/activar/ - Activar repartidor
    - GET /api/admin/repartidores/pendientes/ - Repartidores pendientes de verificación
    """
    permission_classes = [IsAuthenticated, EsAdministrador, AdministradorActivo, PuedeGestionarRepartidores]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['verificado', 'activo', 'estado']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'cedula', 'telefono']
    ordering_fields = ['creado_en', 'entregas_completadas', 'calificacion_promedio']
    ordering = ['-creado_en']

    def get_queryset(self):
        """
        Queryset de repartidores
        """
        return Repartidor.objects.select_related('user').all()

    def get_serializer_class(self):
        """
        Serializer según la acción
        """
        if self.action == 'list':
            return RepartidorListSerializer
        return RepartidorDetalleSerializer

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

        # Cambiar estado
        repartidor.verificado = verificado
        repartidor.save(update_fields=['verificado', 'actualizado_en'])

        # Si se rechaza, desactivar
        if not verificado:
            repartidor.activo = False
            repartidor.save(update_fields=['activo'])

        # Registrar acción
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
        repartidor.save(update_fields=['activo', 'actualizado_en'])

        # Registrar acción
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
        repartidor.save(update_fields=['activo', 'actualizado_en'])

        # Registrar acción
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


# ============================================
# VIEWSET: LOGS DE ACCIONES
# ============================================

class AccionesAdministrativasViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para ver logs de acciones administrativas

    Endpoints:
    - GET /api/admin/acciones/ - Listar acciones
    - GET /api/admin/acciones/{id}/ - Detalle de acción
    - GET /api/admin/acciones/mis_acciones/ - Mis acciones
    """
    permission_classes = [IsAuthenticated, EsAdministrador, AdministradorActivo]
    serializer_class = AccionAdministrativaSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tipo_accion', 'exitosa', 'administrador']
    ordering_fields = ['fecha_accion']
    ordering = ['-fecha_accion']

    def get_queryset(self):
        """
        Queryset de acciones
        """
        return AccionAdministrativa.objects.select_related('administrador__user').all()

    @action(detail=False, methods=['get'])
    def mis_acciones(self, request):
        """
        GET /api/admin/acciones/mis_acciones/

        Ver mis propias acciones
        """
        try:
            admin = obtener_perfil_admin(request.user)
            if not admin:
                return Response(
                    {'error': 'No tienes perfil de administrador'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            acciones = self.get_queryset().filter(administrador=admin)[:100]  # Últimas 100
            serializer = self.get_serializer(acciones, many=True)

            return Response({
                'total': admin.total_acciones,
                'acciones': serializer.data
            })

        except Exception as e:
            logger.error(f"❌ Error obteniendo acciones: {e}")
            return Response(
                {'error': 'Error al obtener acciones'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================
# VIEWSET: CONFIGURACIÓN DEL SISTEMA
# ============================================

class ConfiguracionSistemaViewSet(viewsets.ViewSet):
    """
    ViewSet para configuración del sistema

    Endpoints:
    - GET /api/admin/configuracion/ - Ver configuración
    - PUT /api/admin/configuracion/ - Actualizar configuración
    """
    permission_classes = [IsAuthenticated, EsAdministrador, AdministradorActivo, PuedeConfigurarSistema]

    def list(self, request):
        """
        GET /api/admin/configuracion/

        Ver configuración actual del sistema
        """
        config = ConfiguracionSistema.obtener()
        serializer = ConfiguracionSistemaSerializer(config)

        logger.info(f"👁️ Admin {request.user.email} viendo configuración del sistema")

        return Response(serializer.data)

    def update(self, request):
        """
        PUT /api/admin/configuracion/

        Actualizar configuración del sistema
        """
        config = ConfiguracionSistema.obtener()
        serializer = ConfiguracionSistemaSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Guardar cambios
        admin = obtener_perfil_admin(request.user)
        config.modificado_por = admin
        serializer.save()

        # Registrar acción
        registrar_accion_admin(
            request,
            'configurar_sistema',
            f"Configuración del sistema actualizada",
            modelo_afectado='ConfiguracionSistema',
            objeto_id='1',
            datos_nuevos=serializer.data
        )

        logger.warning(
            f"⚙️ Configuración del sistema actualizada por: {request.user.email}"
        )

        return Response({
            'message': 'Configuración actualizada exitosamente',
            'configuracion': serializer.data
        })


# ============================================
# VIEWSET: ADMINISTRADORES
# ============================================

class AdministradoresViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestionar administradores

    Endpoints:
    - GET /api/admin/administradores/ - Listar administradores
    - GET /api/admin/administradores/{id}/ - Detalle de administrador
    - GET /api/admin/administradores/mi_perfil/ - Mi perfil de admin
    """
    permission_classes = [IsAuthenticated, EsAdministrador, AdministradorActivo]
    serializer_class = AdministradorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'cargo']
    ordering_fields = ['creado_en', 'user__email']
    ordering = ['-creado_en']

    def get_queryset(self):
        """
        Queryset de administradores
        """
        return Administrador.objects.select_related('user').filter(activo=True)

    @action(detail=False, methods=['get'])
    def mi_perfil(self, request):
        """
        GET /api/admin/administradores/mi_perfil/

        Ver mi perfil de administrador
        """
        try:
            admin = obtener_perfil_admin(request.user)
            if not admin:
                return Response(
                    {'error': 'No tienes perfil de administrador'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = self.get_serializer(admin)

            return Response(serializer.data)

        except Exception as e:
            logger.error(f"❌ Error obteniendo perfil de admin: {e}")
            return Response(
                {'error': 'Error al obtener perfil'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================
# VIEWSET: DASHBOARD ADMINISTRATIVO
# ============================================

class DashboardAdminViewSet(viewsets.ViewSet):
    """
    ViewSet para el dashboard administrativo

    Endpoints:
    - GET /api/admin/dashboard/ - Estadísticas generales
    - GET /api/admin/dashboard/resumen_dia/ - Resumen del día
    - GET /api/admin/dashboard/alertas/ - Alertas del sistema
    """
    permission_classes = [IsAuthenticated, EsAdministrador, AdministradorActivo]

    def list(self, request):
        """
        GET /api/admin/dashboard/

        Estadísticas generales del sistema
        """
        hoy = timezone.now().date()

        # Usuarios
        total_usuarios = User.objects.count()
        usuarios_activos = User.objects.filter(is_active=True, cuenta_desactivada=False).count()
        usuarios_nuevos_hoy = User.objects.filter(created_at__date=hoy).count()

        # Proveedores
        total_proveedores = Proveedor.objects.count()
        proveedores_verificados = Proveedor.objects.filter(verificado=True).count()
        proveedores_pendientes = Proveedor.objects.filter(verificado=False, activo=True).count()

        # Repartidores
        total_repartidores = Repartidor.objects.count()
        repartidores_verificados = Repartidor.objects.filter(verificado=True).count()
        repartidores_disponibles = Repartidor.objects.filter(
            estado='disponible',
            activo=True,
            verificado=True
        ).count()
        repartidores_pendientes = Repartidor.objects.filter(verificado=False, activo=True).count()

        # Pedidos
        total_pedidos = Pedido.objects.count()
        pedidos_hoy = Pedido.objects.filter(creado_en__date=hoy).count()
        pedidos_activos = Pedido.objects.filter(
            estado__in=[EstadoPedido.CONFIRMADO, EstadoPedido.EN_PREPARACION, EstadoPedido.EN_RUTA]
        ).count()
        pedidos_entregados = Pedido.objects.filter(estado=EstadoPedido.ENTREGADO).count()

        # Financiero (solo pedidos entregados)
        financiero = Pedido.objects.filter(estado=EstadoPedido.ENTREGADO).aggregate(
            ingresos_totales=Sum('total'),
            ganancia_app_total=Sum('ganancia_app')
        )

        financiero_hoy = Pedido.objects.filter(
            estado=EstadoPedido.ENTREGADO,
            creado_en__date=hoy
        ).aggregate(
            ingresos_hoy=Sum('total'),
            ganancia_app_hoy=Sum('ganancia_app')
        )

        return Response({
            'usuarios': {
                'total': total_usuarios,
                'activos': usuarios_activos,
                'nuevos_hoy': usuarios_nuevos_hoy,
            },
            'proveedores': {
                'total': total_proveedores,
                'verificados': proveedores_verificados,
                'pendientes': proveedores_pendientes,
            },
            'repartidores': {
                'total': total_repartidores,
                'verificados': repartidores_verificados,
                'disponibles': repartidores_disponibles,
                'pendientes': repartidores_pendientes,
            },
            'pedidos': {
                'total': total_pedidos,
                'hoy': pedidos_hoy,
                'activos': pedidos_activos,
                'entregados': pedidos_entregados,
            },
            'financiero': {
                'ingresos_totales': financiero['ingresos_totales'] or 0,
                'ganancia_app_total': financiero['ganancia_app_total'] or 0,
                'ingresos_hoy': financiero_hoy['ingresos_hoy'] or 0,
                'ganancia_app_hoy': financiero_hoy['ganancia_app_hoy'] or 0,
            }
        })

    @action(detail=False, methods=['get'])
    def resumen_dia(self, request):
        """
        GET /api/admin/dashboard/resumen_dia/

        Resumen detallado del día actual
        """
        hoy = timezone.now().date()

        # Pedidos del día por estado
        pedidos_hoy = Pedido.objects.filter(creado_en__date=hoy)

        por_estado = pedidos_hoy.values('estado').annotate(
            total=Count('id')
        )

        # Nuevos registros hoy
        nuevos_usuarios = User.objects.filter(created_at__date=hoy).count()
        nuevos_proveedores = Proveedor.objects.filter(creado_en__date=hoy).count()
        nuevos_repartidores = Repartidor.objects.filter(creado_en__date=hoy).count()

        # Acciones administrativas hoy
        acciones_hoy = AccionAdministrativa.objects.filter(
            fecha_accion__date=hoy
        ).count()

        return Response({
            'fecha': hoy,
            'pedidos': {
                'total': pedidos_hoy.count(),
                'por_estado': list(por_estado),
            },
            'nuevos_registros': {
                'usuarios': nuevos_usuarios,
                'proveedores': nuevos_proveedores,
                'repartidores': nuevos_repartidores,
            },
            'acciones_administrativas': acciones_hoy,
        })

    @action(detail=False, methods=['get'])
    def alertas(self, request):
        """
        GET /api/admin/dashboard/alertas/

        Alertas y notificaciones importantes del sistema
        """
        alertas = []

        # Proveedores pendientes de verificación
        proveedores_pendientes = Proveedor.objects.filter(
            verificado=False,
            activo=True
        ).count()

        if proveedores_pendientes > 0:
            alertas.append({
                'tipo': 'proveedores_pendientes',
                'nivel': 'warning',
                'mensaje': f'{proveedores_pendientes} proveedor(es) pendiente(s) de verificación',
                'cantidad': proveedores_pendientes
            })

        # Repartidores pendientes de verificación
        repartidores_pendientes = Repartidor.objects.filter(
            verificado=False,
            activo=True
        ).count()

        if repartidores_pendientes > 0:
            alertas.append({
                'tipo': 'repartidores_pendientes',
                'nivel': 'warning',
                'mensaje': f'{repartidores_pendientes} repartidor(es) pendiente(s) de verificación',
                'cantidad': repartidores_pendientes
            })

        # Pedidos sin repartidor (confirmados hace más de 10 minutos)
        hace_10_min = timezone.now() - timezone.timedelta(minutes=10)
        pedidos_sin_repartidor = Pedido.objects.filter(
            estado=EstadoPedido.CONFIRMADO,
            repartidor__isnull=True,
            creado_en__lt=hace_10_min
        ).count()

        if pedidos_sin_repartidor > 0:
            alertas.append({
                'tipo': 'pedidos_sin_repartidor',
                'nivel': 'danger',
                'mensaje': f'{pedidos_sin_repartidor} pedido(s) sin repartidor asignado',
                'cantidad': pedidos_sin_repartidor
            })

        # Pedidos con retraso (en ruta hace más de 60 minutos)
        hace_60_min = timezone.now() - timezone.timedelta(minutes=60)
        pedidos_retrasados = Pedido.objects.filter(
            estado=EstadoPedido.EN_RUTA,
            actualizado_en__lt=hace_60_min
        ).count()

        if pedidos_retrasados > 0:
            alertas.append({
                'tipo': 'pedidos_retrasados',
                'nivel': 'danger',
                'mensaje': f'{pedidos_retrasados} pedido(s) con posible retraso',
                'cantidad': pedidos_retrasados
            })

        # Usuarios con cuenta bloqueada
        usuarios_bloqueados = User.objects.filter(
            cuenta_bloqueada_hasta__isnull=False,
            cuenta_bloqueada_hasta__gt=timezone.now()
        ).count()

        if usuarios_bloqueados > 0:
            alertas.append({
                'tipo': 'usuarios_bloqueados',
                'nivel': 'info',
                'mensaje': f'{usuarios_bloqueados} usuario(s) con cuenta bloqueada temporalmente',
                'cantidad': usuarios_bloqueados
            })

        return Response({
            'total_alertas': len(alertas),
            'alertas': alertas
        })
