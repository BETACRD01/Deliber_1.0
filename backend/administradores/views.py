# -*- coding: utf-8 -*-
# administradores/views.py
"""
ViewSets para gestión de usuarios por administradores
✅ Gestión completa de usuarios regulares
✅ Gestión de proveedores (verificar, desactivar)
✅ Gestión de repartidores (verificar, desactivar)
✅ Logs de acciones administrativas
✅ Configuración del sistema
✅ Gestión de solicitudes de cambio de rol
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models, transaction
from django.conf import settings
import logging

# Modelos
from authentication.models import User
from usuarios.models import Perfil, SolicitudCambioRol
from usuarios.solicitudes import GestorSolicitudCambioRol
from proveedores.models import Proveedor
from repartidores.models import Repartidor
from pedidos.models import Pedido, EstadoPedido
from .models import Administrador, AccionAdministrativa, ConfiguracionSistema

# Serializers
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

# Permissions
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

logger = logging.getLogger("administradores")


# ============================================
# HELPERS
# ============================================


def registrar_accion_admin(request, tipo_accion, descripcion, **kwargs):
    """Helper para registrar acciones administrativas"""
    try:
        admin = obtener_perfil_admin(request.user)
        if not admin:
            logger.warning(
                f"Usuario sin perfil admin intentó registrar acción: {request.user.email}"
            )
            return None

        ip_address = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        AccionAdministrativa.registrar_accion(
            administrador=admin,
            tipo_accion=tipo_accion,
            descripcion=descripcion,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs,
        )
    except Exception as e:
        logger.error(f"❌ Error registrando acción: {e}")


def obtener_ip_cliente(request):
    """Obtiene la IP del cliente desde request"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")


# ============================================
# VIEWSET: GESTIÓN DE USUARIOS
# ============================================


class GestionUsuariosViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión completa de usuarios"""

    permission_classes = [
        IsAuthenticated,
        EsAdministrador,
        AdministradorActivo,
        PuedeGestionarUsuarios,
    ]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["rol", "is_active", "cuenta_desactivada", "verificado"]
    search_fields = ["email", "first_name", "last_name", "celular", "username"]
    ordering_fields = ["created_at", "email", "first_name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Queryset de usuarios excluyendo administradores"""
        return User.objects.exclude(rol=User.RolChoices.ADMINISTRADOR).select_related(
            "perfil_usuario"
        )

    def get_serializer_class(self):
        """Serializer según la acción"""
        if self.action == "list":
            return UsuarioListSerializer
        elif self.action in ["update", "partial_update"]:
            return UsuarioEditarSerializer
        elif self.action == "cambiar_rol":
            return CambiarRolSerializer
        elif self.action == "desactivar":
            return DesactivarUsuarioSerializer
        elif self.action == "resetear_password":
            return ResetearPasswordSerializer
        return UsuarioDetalleSerializer

    def retrieve(self, request, *args, **kwargs):
        """GET /api/admin/usuarios/{id}/ - Detalle de usuario"""
        usuario = self.get_object()
        serializer = self.get_serializer(usuario)
        logger.info(
            f"👁️ Admin {request.user.email} viendo detalle de usuario {usuario.email}"
        )
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """PUT/PATCH /api/admin/usuarios/{id}/ - Editar usuario"""
        partial = kwargs.pop("partial", False)
        usuario = self.get_object()

        validar_no_es_superusuario(usuario)

        serializer = self.get_serializer(usuario, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        registrar_accion_admin(
            request,
            "editar_usuario",
            f"Usuario editado: {usuario.email}",
            modelo_afectado="User",
            objeto_id=str(usuario.id),
            datos_nuevos=serializer.data,
        )

        logger.info(f"✅ Usuario editado por admin: {usuario.email}")
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def cambiar_rol(self, request, pk=None):
        """POST /api/admin/usuarios/{id}/cambiar_rol/ - Cambiar rol"""
        usuario = self.get_object()
        validar_no_es_superusuario(usuario)
        validar_no_auto_modificacion_critica(request.user, usuario, "cambiar_rol")

        serializer = CambiarRolSerializer(
            data=request.data, context={"usuario": usuario}
        )
        serializer.is_valid(raise_exception=True)

        rol_anterior = usuario.rol
        nuevo_rol = serializer.validated_data["nuevo_rol"]
        motivo = serializer.validated_data.get("motivo", "")

        usuario.rol = nuevo_rol
        usuario.save(update_fields=["rol", "updated_at"])

        registrar_accion_admin(
            request,
            "cambiar_rol",
            f"Rol cambiado de {rol_anterior} a {nuevo_rol} para {usuario.email}. Motivo: {motivo}",
            modelo_afectado="User",
            objeto_id=str(usuario.id),
            datos_anteriores={"rol": rol_anterior},
            datos_nuevos={"rol": nuevo_rol},
        )

        logger.info(
            f"✅ Rol cambiado: {usuario.email} - {rol_anterior} → {nuevo_rol} "
            f"por {request.user.email}"
        )

        return Response(
            {
                "message": f"Rol cambiado exitosamente de {rol_anterior} a {nuevo_rol}",
                "usuario": UsuarioDetalleSerializer(usuario).data,
            }
        )

    @action(detail=True, methods=["post"])
    def desactivar(self, request, pk=None):
        """POST /api/admin/usuarios/{id}/desactivar/ - Desactivar usuario"""
        usuario = self.get_object()
        validar_no_es_superusuario(usuario)
        validar_no_auto_modificacion_critica(request.user, usuario, "desactivar")

        serializer = DesactivarUsuarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        razon = serializer.validated_data["razon"]
        permanente = serializer.validated_data["permanente"]

        usuario.desactivar_cuenta(razon=razon)

        if permanente:
            usuario.is_active = False
            usuario.save(update_fields=["is_active"])

        registrar_accion_admin(
            request,
            "desactivar_usuario",
            f"Usuario desactivado: {usuario.email}. Razón: {razon}. Permanente: {permanente}",
            modelo_afectado="User",
            objeto_id=str(usuario.id),
        )

        logger.warning(
            f"⚠️ Usuario desactivado: {usuario.email} por {request.user.email}. Razón: {razon}"
        )

        return Response(
            {"message": "Usuario desactivado exitosamente", "permanente": permanente}
        )

    @action(detail=True, methods=["post"])
    def activar(self, request, pk=None):
        """POST /api/admin/usuarios/{id}/activar/ - Activar usuario"""
        usuario = self.get_object()
        validar_no_es_superusuario(usuario)

        if not usuario.cuenta_desactivada and usuario.is_active:
            return Response(
                {"error": "El usuario ya está activo"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario.reactivar_cuenta()
        usuario.is_active = True
        usuario.save(update_fields=["is_active"])

        registrar_accion_admin(
            request,
            "activar_usuario",
            f"Usuario activado: {usuario.email}",
            modelo_afectado="User",
            objeto_id=str(usuario.id),
        )

        logger.info(f"✅ Usuario reactivado: {usuario.email} por {request.user.email}")

        return Response(
            {
                "message": "Usuario activado exitosamente",
                "usuario": UsuarioDetalleSerializer(usuario).data,
            }
        )

    @action(detail=True, methods=["post"])
    def resetear_password(self, request, pk=None):
        """POST /api/admin/usuarios/{id}/resetear_password/ - Resetear contraseña"""
        usuario = self.get_object()
        validar_no_es_superusuario(usuario)

        serializer = ResetearPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        nueva_password = serializer.validated_data["nueva_password"]

        usuario.set_password(nueva_password)
        usuario.intentos_login_fallidos = 0
        usuario.cuenta_bloqueada_hasta = None
        usuario.save(
            update_fields=[
                "password",
                "intentos_login_fallidos",
                "cuenta_bloqueada_hasta",
            ]
        )

        registrar_accion_admin(
            request,
            "resetear_password",
            f"Contraseña reseteada para: {usuario.email}",
            modelo_afectado="User",
            objeto_id=str(usuario.id),
        )

        logger.info(
            f"🔐 Contraseña reseteada: {usuario.email} por {request.user.email}"
        )

        return Response({"message": "Contraseña reseteada exitosamente"})

    @action(detail=True, methods=["get"])
    def historial_pedidos(self, request, pk=None):
        """GET /api/admin/usuarios/{id}/historial_pedidos/ - Historial de pedidos"""
        usuario = self.get_object()

        if usuario.rol != User.RolChoices.USUARIO:
            return Response(
                {"error": "Solo usuarios regulares tienen historial de pedidos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            perfil = usuario.perfil_usuario
            pedidos = perfil.pedidos.all().order_by("-creado_en")[:50]

            from pedidos.serializers import PedidoSerializer

            serializer = PedidoSerializer(pedidos, many=True)

            return Response(
                {
                    "total_pedidos": perfil.total_pedidos,
                    "pedidos_mes_actual": perfil.pedidos_mes_actual,
                    "pedidos": serializer.data,
                }
            )

        except Exception as e:
            logger.error(f"❌ Error obteniendo historial de pedidos: {e}")
            return Response(
                {"error": "Error al obtener historial"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        """GET /api/admin/usuarios/estadisticas/ - Estadísticas de usuarios"""
        total_usuarios = User.objects.count()
        usuarios_activos = User.objects.filter(
            is_active=True, cuenta_desactivada=False
        ).count()
        usuarios_desactivados = User.objects.filter(
            Q(is_active=False) | Q(cuenta_desactivada=True)
        ).count()

        por_rol = User.objects.values("rol").annotate(total=Count("id"))

        hace_un_mes = timezone.now() - timezone.timedelta(days=30)
        usuarios_nuevos = User.objects.filter(created_at__gte=hace_un_mes).count()

        return Response(
            {
                "total_usuarios": total_usuarios,
                "usuarios_activos": usuarios_activos,
                "usuarios_desactivados": usuarios_desactivados,
                "usuarios_nuevos_mes": usuarios_nuevos,
                "por_rol": list(por_rol),
            }
        )


# ============================================
# VIEWSET: GESTIÓN DE PROVEEDORES
# ============================================


class GestionProveedoresViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para gestión de proveedores"""

    permission_classes = [
        IsAuthenticated,
        EsAdministrador,
        AdministradorActivo,
        PuedeGestionarProveedores,
    ]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["verificado", "activo", "tipo_proveedor"]
    search_fields = ["nombre", "user__email", "telefono"]
    ordering_fields = ["creado_en", "nombre", "calificacion_promedio"]
    ordering = ["-creado_en"]

    def get_queryset(self):
        return Proveedor.objects.select_related("user").all()

    def get_serializer_class(self):
        if self.action == "list":
            return ProveedorListSerializer
        return ProveedorDetalleSerializer

    @action(detail=True, methods=["post"])
    def verificar(self, request, pk=None):
        """POST /api/admin/proveedores/{id}/verificar/ - Verificar proveedor"""
        proveedor = self.get_object()

        serializer = VerificarProveedorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verificado = serializer.validated_data["verificado"]
        motivo = serializer.validated_data.get("motivo", "")

        proveedor.verificado = verificado
        proveedor.save(update_fields=["verificado", "actualizado_en"])

        if not verificado:
            proveedor.activo = False
            proveedor.save(update_fields=["activo"])

        accion = "verificar_proveedor" if verificado else "rechazar_proveedor"
        registrar_accion_admin(
            request,
            accion,
            f"Proveedor {'verificado' if verificado else 'rechazado'}: {proveedor.nombre}. Motivo: {motivo}",
            modelo_afectado="Proveedor",
            objeto_id=str(proveedor.id),
        )

        logger.info(
            f"✅ Proveedor {'verificado' if verificado else 'rechazado'}: "
            f"{proveedor.nombre} por {request.user.email}"
        )

        return Response(
            {
                "message": f"Proveedor {'verificado' if verificado else 'rechazado'} exitosamente",
                "proveedor": ProveedorDetalleSerializer(proveedor).data,
            }
        )

    @action(detail=True, methods=["post"])
    def desactivar(self, request, pk=None):
        """POST /api/admin/proveedores/{id}/desactivar/ - Desactivar proveedor"""
        proveedor = self.get_object()

        if not proveedor.activo:
            return Response(
                {"error": "El proveedor ya está desactivado"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        proveedor.activo = False
        proveedor.save(update_fields=["activo", "actualizado_en"])

        registrar_accion_admin(
            request,
            "desactivar_proveedor",
            f"Proveedor desactivado: {proveedor.nombre}",
            modelo_afectado="Proveedor",
            objeto_id=str(proveedor.id),
        )

        logger.warning(
            f"⚠️ Proveedor desactivado: {proveedor.nombre} por {request.user.email}"
        )

        return Response({"message": "Proveedor desactivado exitosamente"})

    @action(detail=True, methods=["post"])
    def activar(self, request, pk=None):
        """POST /api/admin/proveedores/{id}/activar/ - Activar proveedor"""
        proveedor = self.get_object()

        if proveedor.activo:
            return Response(
                {"error": "El proveedor ya está activo"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        proveedor.activo = True
        proveedor.save(update_fields=["activo", "actualizado_en"])

        registrar_accion_admin(
            request,
            "activar_proveedor",
            f"Proveedor activado: {proveedor.nombre}",
            modelo_afectado="Proveedor",
            objeto_id=str(proveedor.id),
        )

        logger.info(
            f"✅ Proveedor activado: {proveedor.nombre} por {request.user.email}"
        )

        return Response({"message": "Proveedor activado exitosamente"})

    @action(detail=False, methods=["get"])
    def pendientes(self, request):
        """GET /api/admin/proveedores/pendientes/ - Proveedores pendientes"""
        pendientes = self.get_queryset().filter(verificado=False, activo=True)
        serializer = self.get_serializer(pendientes, many=True)
        return Response({"total": pendientes.count(), "proveedores": serializer.data})


# ============================================
# VIEWSET: GESTIÓN DE REPARTIDORES
# ============================================


class GestionRepartidoresViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para gestión de repartidores"""

    permission_classes = [
        IsAuthenticated,
        EsAdministrador,
        AdministradorActivo,
        PuedeGestionarRepartidores,
    ]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["verificado", "activo", "estado"]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "cedula",
        "telefono",
    ]
    ordering_fields = ["creado_en", "entregas_completadas", "calificacion_promedio"]
    ordering = ["-creado_en"]

    def get_queryset(self):
        return Repartidor.objects.select_related("user").all()

    def get_serializer_class(self):
        if self.action == "list":
            return RepartidorListSerializer
        return RepartidorDetalleSerializer

    @action(detail=True, methods=["post"])
    def verificar(self, request, pk=None):
        """POST /api/admin/repartidores/{id}/verificar/ - Verificar repartidor"""
        repartidor = self.get_object()

        serializer = VerificarRepartidorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verificado = serializer.validated_data["verificado"]
        motivo = serializer.validated_data.get("motivo", "")

        repartidor.verificado = verificado
        repartidor.save(update_fields=["verificado", "actualizado_en"])

        if not verificado:
            repartidor.activo = False
            repartidor.save(update_fields=["activo"])

        accion = "verificar_repartidor" if verificado else "rechazar_repartidor"
        registrar_accion_admin(
            request,
            accion,
            f"Repartidor {'verificado' if verificado else 'rechazado'}: {repartidor.user.get_full_name()}. Motivo: {motivo}",
            modelo_afectado="Repartidor",
            objeto_id=str(repartidor.id),
        )

        logger.info(
            f"✅ Repartidor {'verificado' if verificado else 'rechazado'}: "
            f"{repartidor.user.get_full_name()} por {request.user.email}"
        )

        return Response(
            {
                "message": f"Repartidor {'verificado' if verificado else 'rechazado'} exitosamente",
                "repartidor": RepartidorDetalleSerializer(repartidor).data,
            }
        )

    @action(detail=True, methods=["post"])
    def desactivar(self, request, pk=None):
        """POST /api/admin/repartidores/{id}/desactivar/ - Desactivar repartidor"""
        repartidor = self.get_object()

        if not repartidor.activo:
            return Response(
                {"error": "El repartidor ya está desactivado"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        repartidor.activo = False
        repartidor.save(update_fields=["activo", "actualizado_en"])

        registrar_accion_admin(
            request,
            "desactivar_repartidor",
            f"Repartidor desactivado: {repartidor.user.get_full_name()}",
            modelo_afectado="Repartidor",
            objeto_id=str(repartidor.id),
        )

        logger.warning(
            f"⚠️ Repartidor desactivado: {repartidor.user.get_full_name()} "
            f"por {request.user.email}"
        )

        return Response({"message": "Repartidor desactivado exitosamente"})

    @action(detail=True, methods=["post"])
    def activar(self, request, pk=None):
        """POST /api/admin/repartidores/{id}/activar/ - Activar repartidor"""
        repartidor = self.get_object()

        if repartidor.activo:
            return Response(
                {"error": "El repartidor ya está activo"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        repartidor.activo = True
        repartidor.save(update_fields=["activo", "actualizado_en"])

        registrar_accion_admin(
            request,
            "activar_repartidor",
            f"Repartidor activado: {repartidor.user.get_full_name()}",
            modelo_afectado="Repartidor",
            objeto_id=str(repartidor.id),
        )

        logger.info(
            f"✅ Repartidor activado: {repartidor.user.get_full_name()} "
            f"por {request.user.email}"
        )

        return Response({"message": "Repartidor activado exitosamente"})

    @action(detail=False, methods=["get"])
    def pendientes(self, request):
        """GET /api/admin/repartidores/pendientes/ - Repartidores pendientes"""
        pendientes = self.get_queryset().filter(verificado=False, activo=True)
        serializer = self.get_serializer(pendientes, many=True)
        return Response({"total": pendientes.count(), "repartidores": serializer.data})


# ============================================
# VIEWSET: LOGS DE ACCIONES
# ============================================


class AccionesAdministrativasViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para ver logs de acciones administrativas"""

    permission_classes = [IsAuthenticated, EsAdministrador, AdministradorActivo]
    serializer_class = AccionAdministrativaSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["tipo_accion", "exitosa", "administrador"]
    ordering_fields = ["fecha_accion"]
    ordering = ["-fecha_accion"]

    def get_queryset(self):
        return AccionAdministrativa.objects.select_related("administrador__user").all()

    @action(detail=False, methods=["get"])
    def mis_acciones(self, request):
        """GET /api/admin/acciones/mis_acciones/ - Mis acciones"""
        try:
            admin = obtener_perfil_admin(request.user)
            if not admin:
                return Response(
                    {"error": "No tienes perfil de administrador"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            acciones = self.get_queryset().filter(administrador=admin)[:100]
            serializer = self.get_serializer(acciones, many=True)

            return Response(
                {"total": admin.total_acciones, "acciones": serializer.data}
            )

        except Exception as e:
            logger.error(f"❌ Error obteniendo acciones: {e}")
            return Response(
                {"error": "Error al obtener acciones"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================
# VIEWSET: CONFIGURACIÓN DEL SISTEMA
# ============================================


class ConfiguracionSistemaViewSet(viewsets.ViewSet):
    """ViewSet para configuración del sistema"""

    permission_classes = [
        IsAuthenticated,
        EsAdministrador,
        AdministradorActivo,
        PuedeConfigurarSistema,
    ]

    def list(self, request):
        """GET /api/admin/configuracion/ - Ver configuración"""
        config = ConfiguracionSistema.obtener()
        serializer = ConfiguracionSistemaSerializer(config)
        logger.info(f"👁️ Admin {request.user.email} viendo configuración del sistema")
        return Response(serializer.data)

    def update(self, request):
        """PUT /api/admin/configuracion/ - Actualizar configuración"""
        config = ConfiguracionSistema.obtener()
        serializer = ConfiguracionSistemaSerializer(
            config, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        admin = obtener_perfil_admin(request.user)
        config.modificado_por = admin
        serializer.save()

        registrar_accion_admin(
            request,
            "configurar_sistema",
            "Configuración del sistema actualizada",
            modelo_afectado="ConfiguracionSistema",
            objeto_id="1",
            datos_nuevos=serializer.data,
        )

        logger.warning(
            f"⚙️ Configuración del sistema actualizada por: {request.user.email}"
        )

        return Response(
            {
                "message": "Configuración actualizada exitosamente",
                "configuracion": serializer.data,
            }
        )


# ============================================
# VIEWSET: ADMINISTRADORES
# ============================================


class AdministradoresViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para gestionar administradores"""

    permission_classes = [IsAuthenticated, EsAdministrador, AdministradorActivo]
    serializer_class = AdministradorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["user__email", "user__first_name", "user__last_name", "cargo"]
    ordering_fields = ["creado_en", "user__email"]
    ordering = ["-creado_en"]

    def get_queryset(self):
        return Administrador.objects.select_related("user").filter(activo=True)

    @action(detail=False, methods=["get"])
    def mi_perfil(self, request):
        """GET /api/admin/administradores/mi_perfil/ - Mi perfil"""
        try:
            admin = obtener_perfil_admin(request.user)
            if not admin:
                return Response(
                    {"error": "No tienes perfil de administrador"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = self.get_serializer(admin)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"❌ Error obteniendo perfil de admin: {e}")
            return Response(
                {"error": "Error al obtener perfil"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================
# VIEWSET: DASHBOARD ADMINISTRATIVO
# ============================================


class DashboardAdminViewSet(viewsets.ViewSet):
    """ViewSet para el dashboard administrativo"""

    permission_classes = [IsAuthenticated, EsAdministrador, AdministradorActivo]

    def list(self, request):
        """GET /api/admin/dashboard/ - Estadísticas generales"""
        hoy = timezone.now().date()

        # Usuarios
        total_usuarios = User.objects.count()
        usuarios_activos = User.objects.filter(
            is_active=True, cuenta_desactivada=False
        ).count()
        usuarios_nuevos_hoy = User.objects.filter(created_at__date=hoy).count()

        # Proveedores
        total_proveedores = Proveedor.objects.count()
        proveedores_verificados = Proveedor.objects.filter(verificado=True).count()
        proveedores_pendientes = Proveedor.objects.filter(
            verificado=False, activo=True
        ).count()

        # Repartidores
        total_repartidores = Repartidor.objects.count()
        repartidores_verificados = Repartidor.objects.filter(verificado=True).count()
        repartidores_disponibles = Repartidor.objects.filter(
            estado="disponible", activo=True, verificado=True
        ).count()
        repartidores_pendientes = Repartidor.objects.filter(
            verificado=False, activo=True
        ).count()

        # Pedidos
        total_pedidos = Pedido.objects.count()
        pedidos_hoy = Pedido.objects.filter(creado_en__date=hoy).count()
        pedidos_activos = Pedido.objects.filter(
            estado__in=[
                EstadoPedido.CONFIRMADO,
                EstadoPedido.EN_PREPARACION,
                EstadoPedido.EN_RUTA,
            ]
        ).count()
        pedidos_entregados = Pedido.objects.filter(
            estado=EstadoPedido.ENTREGADO
        ).count()

        # Financiero
        financiero = Pedido.objects.filter(estado=EstadoPedido.ENTREGADO).aggregate(
            ingresos_totales=Sum("total"), ganancia_app_total=Sum("ganancia_app")
        )

        financiero_hoy = Pedido.objects.filter(
            estado=EstadoPedido.ENTREGADO, creado_en__date=hoy
        ).aggregate(ingresos_hoy=Sum("total"), ganancia_app_hoy=Sum("ganancia_app"))

        return Response(
            {
                "usuarios": {
                    "total": total_usuarios,
                    "activos": usuarios_activos,
                    "nuevos_hoy": usuarios_nuevos_hoy,
                },
                "proveedores": {
                    "total": total_proveedores,
                    "verificados": proveedores_verificados,
                    "pendientes": proveedores_pendientes,
                },
                "repartidores": {
                    "total": total_repartidores,
                    "verificados": repartidores_verificados,
                    "disponibles": repartidores_disponibles,
                    "pendientes": repartidores_pendientes,
                },
                "pedidos": {
                    "total": total_pedidos,
                    "hoy": pedidos_hoy,
                    "activos": pedidos_activos,
                    "entregados": pedidos_entregados,
                },
                "financiero": {
                    "ingresos_totales": financiero["ingresos_totales"] or 0,
                    "ganancia_app_total": financiero["ganancia_app_total"] or 0,
                    "ingresos_hoy": financiero_hoy["ingresos_hoy"] or 0,
                    "ganancia_app_hoy": financiero_hoy["ganancia_app_hoy"] or 0,
                },
            }
        )

    @action(detail=False, methods=["get"])
    def resumen_dia(self, request):
        """GET /api/admin/dashboard/resumen_dia/ - Resumen del día"""
        hoy = timezone.now().date()

        pedidos_hoy = Pedido.objects.filter(creado_en__date=hoy)
        por_estado = pedidos_hoy.values("estado").annotate(total=Count("id"))

        nuevos_usuarios = User.objects.filter(created_at__date=hoy).count()
        nuevos_proveedores = Proveedor.objects.filter(creado_en__date=hoy).count()
        nuevos_repartidores = Repartidor.objects.filter(creado_en__date=hoy).count()

        acciones_hoy = AccionAdministrativa.objects.filter(
            fecha_accion__date=hoy
        ).count()

        return Response(
            {
                "fecha": hoy,
                "pedidos": {
                    "total": pedidos_hoy.count(),
                    "por_estado": list(por_estado),
                },
                "nuevos_registros": {
                    "usuarios": nuevos_usuarios,
                    "proveedores": nuevos_proveedores,
                    "repartidores": nuevos_repartidores,
                },
                "acciones_administrativas": acciones_hoy,
            }
        )

    @action(detail=False, methods=["get"])
    def alertas(self, request):
        """GET /api/admin/dashboard/alertas/ - Alertas del sistema"""
        alertas = []

        proveedores_pendientes = Proveedor.objects.filter(
            verificado=False, activo=True
        ).count()

        if proveedores_pendientes > 0:
            alertas.append(
                {
                    "tipo": "proveedores_pendientes",
                    "nivel": "warning",
                    "mensaje": f"{proveedores_pendientes} proveedor(es) pendiente(s)",
                    "cantidad": proveedores_pendientes,
                }
            )

        repartidores_pendientes = Repartidor.objects.filter(
            verificado=False, activo=True
        ).count()

        if repartidores_pendientes > 0:
            alertas.append(
                {
                    "tipo": "repartidores_pendientes",
                    "nivel": "warning",
                    "mensaje": f"{repartidores_pendientes} repartidor(es) pendiente(s)",
                    "cantidad": repartidores_pendientes,
                }
            )

        hace_10_min = timezone.now() - timezone.timedelta(minutes=10)
        pedidos_sin_repartidor = Pedido.objects.filter(
            estado=EstadoPedido.CONFIRMADO,
            repartidor__isnull=True,
            creado_en__lt=hace_10_min,
        ).count()

        if pedidos_sin_repartidor > 0:
            alertas.append(
                {
                    "tipo": "pedidos_sin_repartidor",
                    "nivel": "danger",
                    "mensaje": f"{pedidos_sin_repartidor} pedido(s) sin repartidor",
                    "cantidad": pedidos_sin_repartidor,
                }
            )

        hace_60_min = timezone.now() - timezone.timedelta(minutes=60)
        pedidos_retrasados = Pedido.objects.filter(
            estado=EstadoPedido.EN_RUTA, actualizado_en__lt=hace_60_min
        ).count()

        if pedidos_retrasados > 0:
            alertas.append(
                {
                    "tipo": "pedidos_retrasados",
                    "nivel": "danger",
                    "mensaje": f"{pedidos_retrasados} pedido(s) con posible retraso",
                    "cantidad": pedidos_retrasados,
                }
            )

        usuarios_bloqueados = User.objects.filter(
            cuenta_bloqueada_hasta__isnull=False,
            cuenta_bloqueada_hasta__gt=timezone.now(),
        ).count()

        if usuarios_bloqueados > 0:
            alertas.append(
                {
                    "tipo": "usuarios_bloqueados",
                    "nivel": "info",
                    "mensaje": f"{usuarios_bloqueados} usuario(s) bloqueado(s)",
                    "cantidad": usuarios_bloqueados,
                }
            )

        return Response({"total_alertas": len(alertas), "alertas": alertas})


# ============================================
# VIEWSET: GESTIÓN DE SOLICITUDES DE CAMBIO ROL
# ============================================


class GestionSolicitudesCambioRolViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para gestión de solicitudes de cambio de rol"""

    permission_classes = [IsAuthenticated, EsAdministrador, AdministradorActivo]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["estado", "rol_solicitado"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    ordering_fields = ["creado_en", "respondido_en"]
    ordering = ["estado", "-creado_en"]

    def get_queryset(self):
        """Queryset de solicitudes"""
        return SolicitudCambioRol.objects.select_related(
            "user", "admin_responsable"
        ).all()

    def get_serializer_class(self):
        """Serializer según la acción"""
        from usuarios.serializers import (
            SolicitudCambioRolDetalleSerializer,
            ResponderSolicitudCambioRolSerializer,
        )

        if self.action in ["aceptar", "rechazar"]:
            return ResponderSolicitudCambioRolSerializer
        return SolicitudCambioRolDetalleSerializer

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def aceptar(self, request, pk=None):
        """POST /api/admin/solicitudes-cambio-rol/{id}/aceptar/ - Aceptar solicitud"""
        try:
            solicitud = self.get_object()

            if solicitud.estado != "PENDIENTE":
                return Response(
                    {
                        "error": f"La solicitud ya fue {solicitud.get_estado_display().lower()}"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            motivo = serializer.validated_data.get("motivo_respuesta", "")

            logger.info(
                f"✅ Aceptando solicitud: {solicitud.user.email} → "
                f"{solicitud.rol_solicitado} por {request.user.email}"
            )

            # Usar gestor centralizado
            resultado = GestorSolicitudCambioRol.aceptar_solicitud(
                solicitud=solicitud, admin=request.user, motivo_respuesta=motivo
            )

            registrar_accion_admin(
                request,
                "cambiar_rol",
                f"Solicitud aceptada: {solicitud.user.email} → {solicitud.rol_solicitado}",
                modelo_afectado="SolicitudCambioRol",
                objeto_id=str(solicitud.id),
            )

            solicitud.refresh_from_db()

            logger.info(
                f"✅ Solicitud aceptada: {solicitud.user.email} "
                f"por {request.user.email}"
            )

            return Response(
                {
                    "mensaje": "Solicitud aceptada exitosamente",
                    "solicitud": self.get_serializer(solicitud).data,
                },
                status=status.HTTP_200_OK,
            )

        except SolicitudCambioRol.DoesNotExist:
            logger.warning(f"⚠️ Solicitud no encontrada: {pk}")
            return Response(
                {"error": "Solicitud no encontrada"}, status=status.HTTP_404_NOT_FOUND
            )

        except DjangoValidationError as e:
            logger.warning(f"⚠️ Error de validación: {e}")
            return Response(
                {"error": "Error de validación", "detalles": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.error(f"❌ Error aceptando solicitud: {e}", exc_info=True)
            return Response(
                {
                    "error": "Error al aceptar solicitud",
                    "detalle": str(e) if settings.DEBUG else "Intenta nuevamente",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def rechazar(self, request, pk=None):
        """POST /api/admin/solicitudes-cambio-rol/{id}/rechazar/ - Rechazar solicitud"""
        try:
            solicitud = self.get_object()

            if solicitud.estado != "PENDIENTE":
                return Response(
                    {
                        "error": f"La solicitud ya fue {solicitud.get_estado_display().lower()}"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            motivo = serializer.validated_data.get(
                "motivo_respuesta", "Sin especificar"
            )

            logger.info(
                f"❌ Rechazando solicitud: {solicitud.user.email} → "
                f"{solicitud.rol_solicitado} por {request.user.email}"
            )

            # Usar gestor centralizado
            resultado = GestorSolicitudCambioRol.rechazar_solicitud(
                solicitud=solicitud, admin=request.user, motivo_respuesta=motivo
            )

            registrar_accion_admin(
                request,
                "cambiar_rol",
                f"Solicitud rechazada: {solicitud.user.email}. Motivo: {motivo}",
                modelo_afectado="SolicitudCambioRol",
                objeto_id=str(solicitud.id),
            )

            solicitud.refresh_from_db()

            logger.warning(
                f"❌ Solicitud rechazada: {solicitud.user.email} "
                f"por {request.user.email}. Motivo: {motivo}"
            )

            return Response(
                {
                    "mensaje": "Solicitud rechazada exitosamente",
                    "solicitud": self.get_serializer(solicitud).data,
                },
                status=status.HTTP_200_OK,
            )

        except SolicitudCambioRol.DoesNotExist:
            logger.warning(f"⚠️ Solicitud no encontrada: {pk}")
            return Response(
                {"error": "Solicitud no encontrada"}, status=status.HTTP_404_NOT_FOUND
            )

        except DjangoValidationError as e:
            logger.warning(f"⚠️ Error de validación: {e}")
            return Response(
                {"error": "Error de validación", "detalles": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.error(f"❌ Error rechazando solicitud: {e}", exc_info=True)
            return Response(
                {
                    "error": "Error al rechazar solicitud",
                    "detalle": str(e) if settings.DEBUG else "Intenta nuevamente",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def pendientes(self, request):
        """GET /api/admin/solicitudes-cambio-rol/pendientes/ - Solicitudes pendientes"""
        pendientes = self.get_queryset().filter(estado="PENDIENTE")

        from usuarios.serializers import SolicitudCambioRolDetalleSerializer

        serializer = SolicitudCambioRolDetalleSerializer(pendientes, many=True)

        logger.info(f"📋 Solicitudes pendientes consultadas: {pendientes.count()}")

        return Response(
            {"total": pendientes.count(), "solicitudes": serializer.data},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        """GET /api/admin/solicitudes-cambio-rol/estadisticas/ - Estadísticas"""
        total = self.get_queryset().count()
        pendientes = self.get_queryset().filter(estado="PENDIENTE").count()
        aceptadas = self.get_queryset().filter(estado="ACEPTADA").count()
        rechazadas = self.get_queryset().filter(estado="RECHAZADA").count()

        por_rol = (
            self.get_queryset()
            .values("rol_solicitado")
            .annotate(
                total=Count("id"),
                pendientes=Count("id", filter=models.Q(estado="PENDIENTE")),
                aceptadas=Count("id", filter=models.Q(estado="ACEPTADA")),
                rechazadas=Count("id", filter=models.Q(estado="RECHAZADA")),
            )
        )

        logger.info("📊 Estadísticas de solicitudes consultadas")

        return Response(
            {
                "totales": {
                    "total": total,
                    "pendientes": pendientes,
                    "aceptadas": aceptadas,
                    "rechazadas": rechazadas,
                },
                "por_rol": list(por_rol),
            },
            status=status.HTTP_200_OK,
        )
