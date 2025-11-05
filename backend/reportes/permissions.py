# reportes/permissions.py
"""
Permisos personalizados para el sistema de reportes
✅ Control de acceso por rol (Admin, Proveedor, Repartidor)
✅ Validaciones de seguridad
"""
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
import logging

logger = logging.getLogger('reportes')


# ============================================
# PERMISO: SOLO ADMINISTRADORES
# ============================================

class EsAdministrador(permissions.BasePermission):
    """
    Permiso para acceder a reportes globales
    Solo staff/superusuarios pueden ver todos los reportes
    """
    message = "Solo los administradores pueden acceder a los reportes globales."

    def has_permission(self, request, view):
        """
        Verifica si el usuario es administrador
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Verificar si es staff o superuser
        es_admin = request.user.is_staff or request.user.is_superuser

        if not es_admin:
            logger.warning(
                f"⚠️ Acceso denegado a reportes: {request.user.email} "
                f"no es administrador"
            )

        return es_admin


# ============================================
# PERMISO: SOLO PROVEEDORES
# ============================================

class EsProveedor(permissions.BasePermission):
    """
    Permiso para proveedores
    Pueden ver solo sus propios reportes
    """
    message = "Solo los proveedores pueden acceder a este reporte."

    def has_permission(self, request, view):
        """
        Verifica si el usuario es un proveedor
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Verificar si es proveedor
        es_proveedor = request.user.es_proveedor()

        if not es_proveedor:
            logger.warning(
                f"⚠️ Acceso denegado a reportes de proveedor: "
                f"{request.user.email} no es proveedor"
            )

        return es_proveedor

    def has_object_permission(self, request, view, obj):
        """
        Verifica que el proveedor solo acceda a sus propios datos
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Si es admin, puede ver todo
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Verificar que el pedido pertenezca al proveedor
        try:
            proveedor = request.user.proveedor

            # Si el objeto es un pedido
            if hasattr(obj, 'proveedor'):
                return obj.proveedor == proveedor

            return False

        except Exception as e:
            logger.error(f"❌ Error verificando permisos de proveedor: {e}")
            return False


# ============================================
# PERMISO: SOLO REPARTIDORES
# ============================================

class EsRepartidor(permissions.BasePermission):
    """
    Permiso para repartidores
    Pueden ver solo sus propias entregas
    """
    message = "Solo los repartidores pueden acceder a este reporte."

    def has_permission(self, request, view):
        """
        Verifica si el usuario es un repartidor
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Verificar si es repartidor
        es_repartidor = request.user.es_repartidor()

        if not es_repartidor:
            logger.warning(
                f"⚠️ Acceso denegado a reportes de repartidor: "
                f"{request.user.email} no es repartidor"
            )

        return es_repartidor

    def has_object_permission(self, request, view, obj):
        """
        Verifica que el repartidor solo acceda a sus propios datos
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Si es admin, puede ver todo
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Verificar que el pedido pertenezca al repartidor
        try:
            repartidor = request.user.repartidor

            # Si el objeto es un pedido
            if hasattr(obj, 'repartidor'):
                return obj.repartidor == repartidor

            return False

        except Exception as e:
            logger.error(f"❌ Error verificando permisos de repartidor: {e}")
            return False


# ============================================
# PERMISO: ADMIN O PROVEEDOR (HÍBRIDO)
# ============================================

class EsAdminOProveedor(permissions.BasePermission):
    """
    Permiso híbrido para endpoints compartidos
    Admin puede ver todo, Proveedor solo lo suyo
    """
    message = "Solo administradores o proveedores pueden acceder."

    def has_permission(self, request, view):
        """
        Permite acceso a admins y proveedores
        """
        if not request.user or not request.user.is_authenticated:
            return False

        es_admin = request.user.is_staff or request.user.is_superuser
        es_proveedor = request.user.es_proveedor()

        return es_admin or es_proveedor

    def has_object_permission(self, request, view, obj):
        """
        Admin ve todo, Proveedor solo lo suyo
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin puede ver todo
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Proveedor solo ve lo suyo
        if request.user.es_proveedor():
            try:
                proveedor = request.user.proveedor
                if hasattr(obj, 'proveedor'):
                    return obj.proveedor == proveedor
            except Exception:
                pass

        return False


# ============================================
# PERMISO: ADMIN O REPARTIDOR (HÍBRIDO)
# ============================================

class EsAdminORepartidor(permissions.BasePermission):
    """
    Permiso híbrido para endpoints compartidos
    Admin puede ver todo, Repartidor solo lo suyo
    """
    message = "Solo administradores o repartidores pueden acceder."

    def has_permission(self, request, view):
        """
        Permite acceso a admins y repartidores
        """
        if not request.user or not request.user.is_authenticated:
            return False

        es_admin = request.user.is_staff or request.user.is_superuser
        es_repartidor = request.user.es_repartidor()

        return es_admin or es_repartidor

    def has_object_permission(self, request, view, obj):
        """
        Admin ve todo, Repartidor solo lo suyo
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin puede ver todo
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Repartidor solo ve lo suyo
        if request.user.es_repartidor():
            try:
                repartidor = request.user.repartidor
                if hasattr(obj, 'repartidor'):
                    return obj.repartidor == repartidor
            except Exception:
                pass

        return False


# ============================================
# PERMISO: SOLO LECTURA PARA REPORTES
# ============================================

class SoloLecturaReportes(permissions.BasePermission):
    """
    Permite solo operaciones de lectura (GET, HEAD, OPTIONS)
    Los reportes no deben ser modificables via API
    """
    message = "Los reportes son de solo lectura."

    def has_permission(self, request, view):
        """
        Solo permite métodos seguros (lectura)
        """
        return request.method in permissions.SAFE_METHODS


# ============================================
# PERMISO COMPUESTO: ADMIN COMPLETO, OTROS RESTRINGIDOS
# ============================================

class PermisoReporte(permissions.BasePermission):
    """
    Permiso compuesto para reportes:
    - Admin: acceso completo
    - Proveedor: solo sus datos
    - Repartidor: solo sus datos
    - Cliente: denegado
    """

    def has_permission(self, request, view):
        """
        Valida el acceso inicial
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin siempre puede
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Proveedor y Repartidor pueden acceder
        if request.user.es_proveedor() or request.user.es_repartidor():
            return True

        # Clientes no pueden acceder a reportes
        logger.warning(
            f"⚠️ Cliente intentó acceder a reportes: {request.user.email}"
        )
        return False

    def has_object_permission(self, request, view, obj):
        """
        Valida el acceso a objetos específicos
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin puede ver todo
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Proveedor solo ve sus pedidos
        if request.user.es_proveedor():
            try:
                proveedor = request.user.proveedor
                if hasattr(obj, 'proveedor'):
                    if obj.proveedor != proveedor:
                        logger.warning(
                            f"⚠️ Proveedor {proveedor.id} intentó acceder a "
                            f"pedido de otro proveedor"
                        )
                        return False
                    return True
            except Exception as e:
                logger.error(f"❌ Error validando proveedor: {e}")
                return False

        # Repartidor solo ve sus entregas
        if request.user.es_repartidor():
            try:
                repartidor = request.user.repartidor
                if hasattr(obj, 'repartidor'):
                    if obj.repartidor != repartidor:
                        logger.warning(
                            f"⚠️ Repartidor {repartidor.id} intentó acceder a "
                            f"pedido de otro repartidor"
                        )
                        return False
                    return True
            except Exception as e:
                logger.error(f"❌ Error validando repartidor: {e}")
                return False

        return False


# ============================================
# HELPERS PARA VALIDACIÓN
# ============================================

def validar_acceso_proveedor(user, proveedor_id):
    """
    Valida que un usuario proveedor solo acceda a sus propios datos

    Args:
        user: Usuario autenticado
        proveedor_id: ID del proveedor a validar

    Returns:
        bool: True si tiene acceso, False si no

    Raises:
        PermissionDenied: Si no tiene acceso
    """
    # Admin siempre puede
    if user.is_staff or user.is_superuser:
        return True

    # Validar que sea proveedor
    if not user.es_proveedor():
        raise PermissionDenied("No eres un proveedor.")

    # Validar que sea su propio ID
    try:
        if user.proveedor.id != proveedor_id:
            logger.warning(
                f"⚠️ Proveedor {user.proveedor.id} intentó acceder a "
                f"datos del proveedor {proveedor_id}"
            )
            raise PermissionDenied(
                "No tienes permiso para acceder a datos de otro proveedor."
            )
        return True
    except Exception as e:
        logger.error(f"❌ Error validando acceso de proveedor: {e}")
        raise PermissionDenied("Error al validar permisos.")


def validar_acceso_repartidor(user, repartidor_id):
    """
    Valida que un usuario repartidor solo acceda a sus propios datos

    Args:
        user: Usuario autenticado
        repartidor_id: ID del repartidor a validar

    Returns:
        bool: True si tiene acceso, False si no

    Raises:
        PermissionDenied: Si no tiene acceso
    """
    # Admin siempre puede
    if user.is_staff or user.is_superuser:
        return True

    # Validar que sea repartidor
    if not user.es_repartidor():
        raise PermissionDenied("No eres un repartidor.")

    # Validar que sea su propio ID
    try:
        if user.repartidor.id != repartidor_id:
            logger.warning(
                f"⚠️ Repartidor {user.repartidor.id} intentó acceder a "
                f"datos del repartidor {repartidor_id}"
            )
            raise PermissionDenied(
                "No tienes permiso para acceder a datos de otro repartidor."
            )
        return True
    except Exception as e:
        logger.error(f"❌ Error validando acceso de repartidor: {e}")
        raise PermissionDenied("Error al validar permisos.")
