# pedidos/views.py (CORREGIDO Y SINCRONIZADO)
"""
Views para la gestión de pedidos.

✅ CORRECCIONES APLICADAS:
- Estructura correcta de relaciones User → Perfil → Proveedor/Repartidor
- Validaciones robustas de permisos
- Manejo consistente de errores
- Logging mejorado
- Try-except en accesos a modelos relacionados
"""
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.pagination import PageNumberPagination
import logging

from .models import Pedido, EstadoPedido, TipoPedido
from .serializers import (
    PedidoCreateSerializer,
    PedidoListSerializer,
    PedidoDetailSerializer,
    PedidoAceptarRepartidorSerializer,
    PedidoConfirmarProveedorSerializer,
    PedidoCancelacionSerializer,
    PedidoEstadoUpdateSerializer,
    PedidoGananciasSerializer,
)

logger = logging.getLogger("pedidos")


# ==========================================================
# 🔧 CONFIGURACIÓN GLOBAL
# ==========================================================
class PedidoThrottle(UserRateThrottle):
    """Límite de 60 peticiones por hora por usuario"""
    rate = "60/hour"


class StandardPagination(PageNumberPagination):
    """Paginación estándar para listados"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


# ==========================================================
# 🔐 FUNCIONES AUXILIARES DE PERMISOS (CORREGIDAS)
# ==========================================================
def verificar_permiso_cliente(user):
    """Verifica que el usuario sea cliente"""
    return (
        hasattr(user, 'perfil') and
        user.perfil.rol.upper() == 'CLIENTE'
    )


def verificar_permiso_proveedor(user, pedido=None):
    """
    ✅ CORREGIDO: Verifica que el usuario sea proveedor
    La relación correcta es: User → proveedor (OneToOne)
    """
    if not hasattr(user, 'proveedor'):
        return False

    # Si se proporciona pedido, verificar que sea el proveedor asignado
    if pedido:
        return pedido.proveedor_id == user.proveedor.id

    return True


def verificar_permiso_repartidor(user, pedido=None):
    """
    ✅ CORREGIDO: Verifica que el usuario sea repartidor
    La relación correcta es: User → Perfil → repartidor
    """
    if not hasattr(user, 'perfil'):
        return False

    if user.perfil.rol.upper() != 'REPARTIDOR':
        return False

    if not hasattr(user.perfil, 'repartidor'):
        return False

    # Si se proporciona pedido, verificar que sea el repartidor asignado
    if pedido and pedido.repartidor:
        return pedido.repartidor_id == user.perfil.repartidor.id

    return True


def verificar_permiso_admin(user):
    """Verifica que el usuario sea administrador"""
    return user.is_staff or user.is_superuser


# ==========================================================
# 📦 CREAR Y LISTAR PEDIDOS (CORREGIDO)
# ==========================================================
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([PedidoThrottle])
def pedidos_view(request):
    """
    ✅ CORREGIDO: Manejo correcto de perfiles y relaciones

    - GET: Lista pedidos según el rol del usuario
    - POST: Crea un nuevo pedido (solo cliente)
    """
    user = request.user

    # -----------------------------
    # Crear pedido (cliente)
    # -----------------------------
    if request.method == "POST":
        if not verificar_permiso_cliente(user):
            logger.warning(
                f"Usuario {user.email} intentó crear pedido sin ser cliente. "
                f"Rol: {getattr(user.perfil, 'rol', 'sin_perfil') if hasattr(user, 'perfil') else 'sin_perfil'}"
            )
            return Response(
                {"error": "Solo los clientes pueden crear pedidos."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            serializer = PedidoCreateSerializer(
                data=request.data,
                context={'request': request}
            )

            if not serializer.is_valid():
                logger.warning(
                    f"Validación fallida al crear pedido: {serializer.errors}"
                )
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                pedido = serializer.save()

            logger.info(
                f"✅ Pedido #{pedido.id} creado por {user.email} - "
                f"Tipo: {pedido.tipo} - Total: ${pedido.total}"
            )

            return Response(
                {
                    "mensaje": "Pedido creado correctamente.",
                    "pedido": PedidoDetailSerializer(pedido).data
                },
                status=status.HTTP_201_CREATED
            )

        except DjangoValidationError as e:
            logger.error(f"Error de validación al crear pedido: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                f"Error inesperado al crear pedido: {e}",
                exc_info=True
            )
            return Response(
                {"error": "Error interno al crear el pedido."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # -----------------------------
    # Listar pedidos (CORREGIDO)
    # -----------------------------
    try:
        # ✅ Iniciar queryset base
        pedidos = Pedido.objects.select_related(
            'cliente__user',
            'proveedor',
            'repartidor__user'
        )

        # ✅ CORRECCIÓN: Filtrar según rol con manejo robusto
        if verificar_permiso_admin(user):
            # Admin ve todos los pedidos
            logger.debug(f"Admin {user.email} consultando todos los pedidos")
            pass

        elif hasattr(user, 'perfil'):
            rol = user.perfil.rol.upper()

            if rol == 'CLIENTE':
                # Cliente ve solo sus pedidos
                pedidos = pedidos.filter(cliente=user.perfil)
                logger.debug(f"Cliente {user.email} consultando sus pedidos")

            elif rol == 'PROVEEDOR':
                # ✅ CORREGIDO: Proveedor accede mediante user.proveedor
                if not hasattr(user, 'proveedor'):
                    logger.error(
                        f"Usuario {user.email} tiene rol PROVEEDOR pero no tiene "
                        "instancia de Proveedor vinculada"
                    )
                    return Response(
                        {
                            "error": "Usuario no tiene proveedor asociado.",
                            "detalle": "Contacte con soporte para resolver este problema."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                pedidos = pedidos.filter(proveedor=user.proveedor)
                logger.debug(
                    f"Proveedor {user.email} ({user.proveedor.nombre}) "
                    f"consultando sus pedidos"
                )

            elif rol == 'REPARTIDOR':
                # ✅ CORREGIDO: Repartidor accede mediante user.perfil.repartidor
                if not hasattr(user.perfil, 'repartidor'):
                    logger.error(
                        f"Usuario {user.email} tiene rol REPARTIDOR pero no tiene "
                        "instancia de Repartidor vinculada"
                    )
                    return Response(
                        {
                            "error": "Perfil de repartidor no encontrado.",
                            "detalle": "Contacte con soporte para resolver este problema."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                repartidor = user.perfil.repartidor

                # Repartidor ve: sus pedidos asignados + pedidos disponibles
                pedidos = pedidos.filter(
                    repartidor=repartidor
                ) | pedidos.filter(
                    repartidor__isnull=True,
                    estado=EstadoPedido.CONFIRMADO
                )

                logger.debug(
                    f"Repartidor {user.email} consultando pedidos "
                    "(asignados + disponibles)"
                )

            else:
                logger.warning(
                    f"Usuario {user.email} tiene rol no reconocido: {rol}"
                )
                return Response(
                    {
                        "error": "Rol de usuario no reconocido.",
                        "rol": rol
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        else:
            # Usuario sin perfil y no es admin
            logger.warning(
                f"Usuario {user.email} no tiene perfil y no es admin"
            )
            return Response(
                {"error": "Usuario sin perfil asociado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Filtros opcionales por query params
        estado = request.GET.get('estado')
        if estado and estado in dict(EstadoPedido.choices):
            pedidos = pedidos.filter(estado=estado)
            logger.debug(f"Filtrando por estado: {estado}")

        tipo = request.GET.get('tipo')
        if tipo and tipo in dict(TipoPedido.choices):
            pedidos = pedidos.filter(tipo=tipo)
            logger.debug(f"Filtrando por tipo: {tipo}")

        # ✅ Paginación
        paginator = StandardPagination()
        page = paginator.paginate_queryset(
            pedidos.order_by('-creado_en'),
            request
        )

        serializer = PedidoListSerializer(page, many=True)

        logger.info(
            f"✅ Usuario {user.email} consultó {pedidos.count()} pedidos"
        )

        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        logger.error(
            f"Error inesperado al listar pedidos: {e}",
            exc_info=True
        )
        return Response(
            {"error": "Error interno al obtener pedidos."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==========================================================
# 🔍 DETALLE DE PEDIDO (CORREGIDO)
# ==========================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pedido_detalle(request, pedido_id):
    """
    ✅ CORREGIDO: Validación robusta de permisos

    Muestra los detalles completos de un pedido.
    Solo accesible por: cliente dueño, proveedor, repartidor asignado o admin.
    """
    try:
        pedido = get_object_or_404(
            Pedido.objects.select_related(
                'cliente__user',
                'proveedor',
                'repartidor__user'
            ),
            id=pedido_id
        )

        user = request.user

        # ✅ Verificar permisos con funciones corregidas
        tiene_permiso = False
        motivo_permiso = ""

        if verificar_permiso_admin(user):
            tiene_permiso = True
            motivo_permiso = "admin"

        elif hasattr(user, 'perfil'):
            # Cliente dueño del pedido
            if (user.perfil.rol.upper() == 'CLIENTE' and
                pedido.cliente_id == user.perfil.id):
                tiene_permiso = True
                motivo_permiso = "cliente_dueño"

            # Proveedor del pedido
            elif verificar_permiso_proveedor(user, pedido):
                tiene_permiso = True
                motivo_permiso = "proveedor_asignado"

            # Repartidor asignado
            elif verificar_permiso_repartidor(user, pedido):
                tiene_permiso = True
                motivo_permiso = "repartidor_asignado"

        if not tiene_permiso:
            logger.warning(
                f"❌ Usuario {user.email} intentó acceder al pedido #{pedido_id} "
                f"sin permiso"
            )
            return Response(
                {"error": "No tiene permiso para ver este pedido."},
                status=status.HTTP_403_FORBIDDEN
            )

        logger.debug(
            f"✅ Usuario {user.email} accedió al pedido #{pedido_id} "
            f"como {motivo_permiso}"
        )

        serializer = PedidoDetailSerializer(pedido)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(
            f"Error al obtener detalle del pedido #{pedido_id}: {e}",
            exc_info=True
        )
        return Response(
            {"error": "Error interno al obtener detalle del pedido."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==========================================================
# 🛵 ACEPTAR PEDIDO (REPARTIDOR) - CORREGIDO
# ==========================================================
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def aceptar_pedido_repartidor(request, pedido_id):
    """
    ✅ CORREGIDO: Validación correcta del repartidor

    Un repartidor acepta un pedido disponible o encargo directo.
    """
    try:
        user = request.user

        # ✅ Verificar que sea repartidor con función corregida
        if not verificar_permiso_repartidor(user):
            logger.warning(
                f"❌ Usuario {user.email} intentó aceptar pedido sin ser repartidor. "
                f"Rol: {getattr(user.perfil, 'rol', 'sin_perfil') if hasattr(user, 'perfil') else 'sin_perfil'}"
            )
            return Response(
                {"error": "Solo los repartidores pueden aceptar pedidos."},
                status=status.HTTP_403_FORBIDDEN
            )

        pedido = get_object_or_404(Pedido, id=pedido_id)

        # ✅ Obtener repartidor de la relación correcta
        try:
            repartidor = user.perfil.repartidor
        except AttributeError:
            logger.error(
                f"❌ Usuario {user.email} no tiene repartidor vinculado"
            )
            return Response(
                {
                    "error": "No se encontró el perfil de repartidor.",
                    "detalle": "Contacte con soporte."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        data = {'repartidor_id': repartidor.id}

        serializer = PedidoAceptarRepartidorSerializer(
            data=data,
            context={'pedido': pedido}
        )

        if not serializer.is_valid():
            logger.warning(
                f"Validación fallida al aceptar pedido #{pedido_id}: "
                f"{serializer.errors}"
            )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            serializer.save()

        logger.info(
            f"✅ Pedido #{pedido.id} aceptado por repartidor {user.email} "
            f"(ID: {repartidor.id})"
        )

        return Response({
            "mensaje": "Pedido aceptado correctamente.",
            "pedido": PedidoDetailSerializer(pedido).data
        }, status=status.HTTP_200_OK)

    except DjangoValidationError as e:
        logger.error(f"Error de validación al aceptar pedido: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(
            f"Error inesperado al aceptar pedido #{pedido_id}: {e}",
            exc_info=True
        )
        return Response(
            {"error": "Error interno al aceptar pedido."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==========================================================
# 🍳 CONFIRMAR PEDIDO (PROVEEDOR) - CORREGIDO
# ==========================================================
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def confirmar_pedido_proveedor(request, pedido_id):
    """
    ✅ CORREGIDO: Validación correcta del proveedor

    El proveedor confirma que ha comenzado la preparación del pedido.
    """
    try:
        user = request.user
        pedido = get_object_or_404(Pedido, id=pedido_id)

        # ✅ Verificar que sea el proveedor del pedido
        if not verificar_permiso_proveedor(user, pedido):
            logger.warning(
                f"❌ Usuario {user.email} intentó confirmar pedido #{pedido_id} "
                f"sin ser el proveedor asignado"
            )
            return Response(
                {"error": "Solo el proveedor asignado puede confirmar este pedido."},
                status=status.HTTP_403_FORBIDDEN
            )

        # ✅ Obtener proveedor de la relación correcta
        try:
            proveedor = user.proveedor
        except AttributeError:
            logger.error(
                f"❌ Usuario {user.email} no tiene proveedor vinculado"
            )
            return Response(
                {
                    "error": "No se encontró el perfil de proveedor.",
                    "detalle": "Contacte con soporte."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        data = {'proveedor_id': proveedor.id}

        serializer = PedidoConfirmarProveedorSerializer(
            data=data,
            context={'pedido': pedido}
        )

        if not serializer.is_valid():
            logger.warning(
                f"Validación fallida al confirmar pedido #{pedido_id}: "
                f"{serializer.errors}"
            )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            serializer.save()

        logger.info(
            f"✅ Pedido #{pedido.id} confirmado por proveedor {user.email} "
            f"({proveedor.nombre})"
        )

        return Response({
            "mensaje": "Pedido confirmado por el proveedor.",
            "pedido": PedidoDetailSerializer(pedido).data
        }, status=status.HTTP_200_OK)

    except DjangoValidationError as e:
        logger.error(f"Error de validación al confirmar pedido: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(
            f"Error inesperado al confirmar pedido #{pedido_id}: {e}",
            exc_info=True
        )
        return Response(
            {"error": "Error interno al confirmar pedido."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==========================================================
# 🚚 CAMBIO DE ESTADO (GENERAL) - CORREGIDO
# ==========================================================
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def cambiar_estado_pedido(request, pedido_id):
    """
    ✅ CORREGIDO: Validación robusta de permisos

    Permite a proveedor, repartidor o admin cambiar el estado de un pedido.
    """
    try:
        user = request.user
        pedido = get_object_or_404(Pedido, id=pedido_id)

        # ✅ Verificar permisos con funciones corregidas
        tiene_permiso = False
        rol_actor = ""

        if verificar_permiso_admin(user):
            tiene_permiso = True
            rol_actor = "admin"
        elif verificar_permiso_proveedor(user, pedido):
            tiene_permiso = True
            rol_actor = "proveedor"
        elif verificar_permiso_repartidor(user, pedido):
            tiene_permiso = True
            rol_actor = "repartidor"

        if not tiene_permiso:
            logger.warning(
                f"❌ Usuario {user.email} intentó cambiar estado del "
                f"pedido #{pedido_id} sin permiso"
            )
            return Response(
                {"error": "No tiene permiso para cambiar el estado de este pedido."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PedidoEstadoUpdateSerializer(
            data=request.data,
            context={'pedido': pedido}
        )

        if not serializer.is_valid():
            logger.warning(
                f"Validación fallida al cambiar estado del pedido #{pedido_id}: "
                f"{serializer.errors}"
            )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            serializer.update(pedido, serializer.validated_data)

        logger.info(
            f"✅ Estado del pedido #{pedido.id} cambiado a {pedido.estado} "
            f"por {user.email} (rol: {rol_actor})"
        )

        return Response({
            "mensaje": "Estado actualizado correctamente.",
            "pedido": PedidoDetailSerializer(pedido).data
        }, status=status.HTTP_200_OK)

    except DjangoValidationError as e:
        logger.error(f"Error de validación al cambiar estado: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(
            f"Error inesperado al cambiar estado del pedido #{pedido_id}: {e}",
            exc_info=True
        )
        return Response(
            {"error": "Error interno al cambiar estado."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==========================================================
# 🚫 CANCELACIÓN DEL PEDIDO (CORREGIDO)
# ==========================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancelar_pedido(request, pedido_id):
    """
    ✅ CORREGIDO: Validación robusta de permisos

    Permite cancelar un pedido con motivo.
    Puede cancelar: cliente dueño, proveedor, repartidor asignado o admin.
    """
    try:
        user = request.user
        pedido = get_object_or_404(Pedido, id=pedido_id)

        # ✅ Verificar permisos con funciones corregidas
        tiene_permiso = False
        rol_actor = ""

        if verificar_permiso_admin(user):
            tiene_permiso = True
            rol_actor = "admin"

        elif hasattr(user, 'perfil'):
            # Cliente dueño
            if (user.perfil.rol.upper() == 'CLIENTE' and
                pedido.cliente_id == user.perfil.id):
                tiene_permiso = True
                rol_actor = "cliente"

            # Proveedor del pedido
            elif verificar_permiso_proveedor(user, pedido):
                tiene_permiso = True
                rol_actor = "proveedor"

            # Repartidor asignado
            elif verificar_permiso_repartidor(user, pedido):
                tiene_permiso = True
                rol_actor = "repartidor"

        if not tiene_permiso:
            logger.warning(
                f"❌ Usuario {user.email} intentó cancelar pedido #{pedido_id} "
                f"sin permiso"
            )
            return Response(
                {"error": "No tiene permiso para cancelar este pedido."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PedidoCancelacionSerializer(
            data=request.data,
            context={'pedido': pedido, 'request': request}
        )

        if not serializer.is_valid():
            logger.warning(
                f"Validación fallida al cancelar pedido #{pedido_id}: "
                f"{serializer.errors}"
            )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            serializer.save()

        logger.info(
            f"✅ Pedido #{pedido.id} cancelado por {user.email} (rol: {rol_actor}). "
            f"Motivo: {request.data.get('motivo', 'No especificado')}"
        )

        return Response({
            "mensaje": "Pedido cancelado correctamente.",
            "pedido": PedidoDetailSerializer(pedido).data
        }, status=status.HTTP_200_OK)

    except DjangoValidationError as e:
        logger.error(f"Error de validación al cancelar pedido: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(
            f"Error inesperado al cancelar pedido #{pedido_id}: {e}",
            exc_info=True
        )
        return Response(
            {"error": "Error interno al cancelar pedido."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==========================================================
# 💰 VER DISTRIBUCIÓN DE GANANCIAS (CORREGIDO)
# ==========================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ver_ganancias_pedido(request, pedido_id):
    """
    ✅ CORREGIDO: Validación robusta de permisos

    Muestra las comisiones del pedido (repartidor, proveedor, app).
    Solo accesible por: admin, proveedor o repartidor del pedido.
    """
    try:
        user = request.user
        pedido = get_object_or_404(Pedido, id=pedido_id)

        # ✅ Verificar permisos con funciones corregidas
        tiene_permiso = False

        if verificar_permiso_admin(user):
            tiene_permiso = True
        elif verificar_permiso_proveedor(user, pedido):
            tiene_permiso = True
        elif verificar_permiso_repartidor(user, pedido):
            tiene_permiso = True

        if not tiene_permiso:
            logger.warning(
                f"❌ Usuario {user.email} intentó ver ganancias del "
                f"pedido #{pedido_id} sin permiso"
            )
            return Response(
                {"error": "No tiene permiso para ver las ganancias de este pedido."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PedidoGananciasSerializer(pedido)

        logger.debug(
            f"✅ Usuario {user.email} consultó ganancias del pedido #{pedido_id}"
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(
            f"Error al obtener ganancias del pedido #{pedido_id}: {e}",
            exc_info=True
        )
        return Response(
            {"error": "Error interno al obtener ganancias."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
