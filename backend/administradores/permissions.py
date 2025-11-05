# -*- coding: utf-8 -*-
# administradores/permissions.py
"""
Permisos personalizados para el módulo de administradores
✅ Control de acceso granular por tipo de acción
✅ Validación de permisos específicos del administrador
✅ Protección contra acciones no autorizadas
"""

from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
import logging

logger = logging.getLogger('administradores')


# ============================================
# PERMISO BASE: ES ADMINISTRADOR
# ============================================

class EsAdministrador(permissions.BasePermission):
    """
    Permiso base: solo usuarios con rol ADMINISTRADOR o superusuarios
    """
    message = "Solo los administradores pueden acceder a esta funcionalidad."

    def has_permission(self, request, view):
        """
        Verifica que el usuario sea administrador
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Verificar si es administrador o superusuario
        es_admin = (
            request.user.is_superuser or
            request.user.is_staff or
            request.user.es_administrador()
        )

        if not es_admin:
            logger.warning(
                f"⚠️ Acceso denegado a funcionalidad administrativa: "
                f"{request.user.email} no es administrador"
            )

        return es_admin


# ============================================
# PERMISO: PUEDE GESTIONAR USUARIOS
# ============================================

class PuedeGestionarUsuarios(permissions.BasePermission):
    """
    Permiso para gestionar usuarios (listar, editar, desactivar, etc.)
    """
    message = "No tienes permiso para gestionar usuarios."

    def has_permission(self, request, view):
        """
        Verifica que el administrador tenga permiso para gestionar usuarios
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusuarios siempre pueden
        if request.user.is_superuser:
            return True

        # Verificar permiso específico
        try:
            admin = request.user.perfil_admin

            if not admin.activo:
                logger.warning(
                    f"⚠️ Administrador inactivo intentó gestionar usuarios: "
                    f"{request.user.email}"
                )
                return False

            tiene_permiso = admin.puede_gestionar_usuarios

            if not tiene_permiso:
                logger.warning(
                    f"⚠️ Administrador sin permiso intentó gestionar usuarios: "
                    f"{request.user.email}"
                )

            return tiene_permiso

        except Exception as e:
            logger.error(f"❌ Error verificando permisos de usuario: {e}")
            return False


# ============================================
# PERMISO: PUEDE GESTIONAR PROVEEDORES
# ============================================

class PuedeGestionarProveedores(permissions.BasePermission):
    """
    Permiso para gestionar proveedores (verificar, desactivar, etc.)
    """
    message = "No tienes permiso para gestionar proveedores."

    def has_permission(self, request, view):
        """
        Verifica que el administrador tenga permiso para gestionar proveedores
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusuarios siempre pueden
        if request.user.is_superuser:
            return True

        # Verificar permiso específico
        try:
            admin = request.user.perfil_admin

            if not admin.activo:
                return False

            tiene_permiso = admin.puede_gestionar_proveedores

            if not tiene_permiso:
                logger.warning(
                    f"⚠️ Administrador sin permiso intentó gestionar proveedores: "
                    f"{request.user.email}"
                )

            return tiene_permiso

        except Exception as e:
            logger.error(f"❌ Error verificando permisos de proveedor: {e}")
            return False


# ============================================
# PERMISO: PUEDE GESTIONAR REPARTIDORES
# ============================================

class PuedeGestionarRepartidores(permissions.BasePermission):
    """
    Permiso para gestionar repartidores (verificar, desactivar, etc.)
    """
    message = "No tienes permiso para gestionar repartidores."

    def has_permission(self, request, view):
        """
        Verifica que el administrador tenga permiso para gestionar repartidores
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusuarios siempre pueden
        if request.user.is_superuser:
            return True

        # Verificar permiso específico
        try:
            admin = request.user.perfil_admin

            if not admin.activo:
                return False

            tiene_permiso = admin.puede_gestionar_repartidores

            if not tiene_permiso:
                logger.warning(
                    f"⚠️ Administrador sin permiso intentó gestionar repartidores: "
                    f"{request.user.email}"
                )

            return tiene_permiso

        except Exception as e:
            logger.error(f"❌ Error verificando permisos de repartidor: {e}")
            return False


# ============================================
# PERMISO: PUEDE GESTIONAR PEDIDOS
# ============================================

class PuedeGestionarPedidos(permissions.BasePermission):
    """
    Permiso para gestionar pedidos (cancelar, reasignar, etc.)
    """
    message = "No tienes permiso para gestionar pedidos."

    def has_permission(self, request, view):
        """
        Verifica que el administrador tenga permiso para gestionar pedidos
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusuarios siempre pueden
        if request.user.is_superuser:
            return True

        # Verificar permiso específico
        try:
            admin = request.user.perfil_admin

            if not admin.activo:
                return False

            tiene_permiso = admin.puede_gestionar_pedidos

            if not tiene_permiso:
                logger.warning(
                    f"⚠️ Administrador sin permiso intentó gestionar pedidos: "
                    f"{request.user.email}"
                )

            return tiene_permiso

        except Exception as e:
            logger.error(f"❌ Error verificando permisos de pedidos: {e}")
            return False


# ============================================
# PERMISO: PUEDE GESTIONAR RIFAS
# ============================================

class PuedeGestionarRifas(permissions.BasePermission):
    """
    Permiso para gestionar rifas (crear, sortear, cancelar)
    """
    message = "No tienes permiso para gestionar rifas."

    def has_permission(self, request, view):
        """
        Verifica que el administrador tenga permiso para gestionar rifas
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusuarios siempre pueden
        if request.user.is_superuser:
            return True

        # Verificar permiso específico
        try:
            admin = request.user.perfil_admin

            if not admin.activo:
                return False

            tiene_permiso = admin.puede_gestionar_rifas

            if not tiene_permiso:
                logger.warning(
                    f"⚠️ Administrador sin permiso intentó gestionar rifas: "
                    f"{request.user.email}"
                )

            return tiene_permiso

        except Exception as e:
            logger.error(f"❌ Error verificando permisos de rifas: {e}")
            return False


# ============================================
# PERMISO: PUEDE VER REPORTES
# ============================================

class PuedeVerReportes(permissions.BasePermission):
    """
    Permiso para acceder a reportes y estadísticas
    """
    message = "No tienes permiso para ver reportes."

    def has_permission(self, request, view):
        """
        Verifica que el administrador tenga permiso para ver reportes
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusuarios siempre pueden
        if request.user.is_superuser:
            return True

        # Verificar permiso específico
        try:
            admin = request.user.perfil_admin

            if not admin.activo:
                return False

            tiene_permiso = admin.puede_ver_reportes

            if not tiene_permiso:
                logger.warning(
                    f"⚠️ Administrador sin permiso intentó ver reportes: "
                    f"{request.user.email}"
                )

            return tiene_permiso

        except Exception as e:
            logger.error(f"❌ Error verificando permisos de reportes: {e}")
            return False


# ============================================
# PERMISO: PUEDE CONFIGURAR SISTEMA
# ============================================

class PuedeConfigurarSistema(permissions.BasePermission):
    """
    Permiso para modificar configuraciones globales del sistema
    Solo super administradores
    """
    message = "Solo los super administradores pueden configurar el sistema."

    def has_permission(self, request, view):
        """
        Verifica que sea super administrador
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Solo superusuarios o admins con permiso especial
        if request.user.is_superuser:
            return True

        # Verificar permiso específico
        try:
            admin = request.user.perfil_admin

            if not admin.activo:
                return False

            tiene_permiso = admin.puede_configurar_sistema

            if not tiene_permiso:
                logger.warning(
                    f"⚠️ Administrador sin permiso intentó configurar sistema: "
                    f"{request.user.email}"
                )

            return tiene_permiso

        except Exception as e:
            logger.error(f"❌ Error verificando permisos de configuración: {e}")
            return False


# ============================================
# PERMISO: SOLO LECTURA
# ============================================

class SoloLecturaAdmin(permissions.BasePermission):
    """
    Permite solo operaciones de lectura (GET, HEAD, OPTIONS)
    Útil para administradores con permisos limitados
    """
    message = "Solo tienes permisos de lectura."

    def has_permission(self, request, view):
        """
        Permite solo métodos seguros
        """
        return request.method in permissions.SAFE_METHODS


# ============================================
# PERMISO COMPUESTO: ADMINISTRADOR ACTIVO
# ============================================

class AdministradorActivo(permissions.BasePermission):
    """
    Verifica que el administrador esté activo
    """
    message = "Tu cuenta de administrador está inactiva."

    def has_permission(self, request, view):
        """
        Verifica que el administrador esté activo
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusuarios siempre están activos
        if request.user.is_superuser:
            return True

        # Verificar estado del administrador
        try:
            admin = request.user.perfil_admin

            if not admin.activo:
                logger.warning(
                    f"⚠️ Administrador inactivo intentó acceder: "
                    f"{request.user.email}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"❌ Error verificando estado del administrador: {e}")
            return False


# ============================================
# VALIDADOR: NO MODIFICAR SUPERUSUARIOS
# ============================================

def validar_no_es_superusuario(usuario_objetivo):
    """
    Valida que no se intente modificar un superusuario

    Args:
        usuario_objetivo: Usuario que se quiere modificar

    Raises:
        PermissionDenied: Si es superusuario
    """
    if usuario_objetivo.is_superuser:
        logger.warning(
            f"⚠️ Intento de modificar superusuario: {usuario_objetivo.email}"
        )
        raise PermissionDenied(
            "No se puede modificar un superusuario desde esta interfaz."
        )


# ============================================
# VALIDADOR: NO AUTO-MODIFICACIÓN CRÍTICA
# ============================================

def validar_no_auto_modificacion_critica(usuario_actual, usuario_objetivo, accion):
    """
    Valida que un admin no se desactive a sí mismo o cambie sus propios permisos

    Args:
        usuario_actual: Usuario que realiza la acción
        usuario_objetivo: Usuario que será modificado
        accion: Tipo de acción (desactivar, cambiar_permisos, etc.)

    Raises:
        PermissionDenied: Si intenta modificarse a sí mismo
    """
    if usuario_actual.id == usuario_objetivo.id:
        acciones_criticas = ['desactivar', 'cambiar_rol', 'eliminar']

        if accion in acciones_criticas:
            logger.warning(
                f"⚠️ Administrador intentó {accion} su propia cuenta: "
                f"{usuario_actual.email}"
            )
            raise PermissionDenied(
                f"No puedes {accion} tu propia cuenta. "
                f"Contacta a otro administrador."
            )


# ============================================
# HELPER: OBTENER PERFIL ADMIN
# ============================================

def obtener_perfil_admin(user):
    """
    Obtiene el perfil de administrador de forma segura

    Args:
        user: Usuario

    Returns:
        Administrador o None
    """
    try:
        return user.perfil_admin
    except Exception:
        return None


# ============================================
# HELPER: VERIFICAR PERMISO ESPECÍFICO
# ============================================

def tiene_permiso_especifico(user, permiso):
    """
    Verifica si un usuario tiene un permiso específico

    Args:
        user: Usuario
        permiso: Nombre del permiso

    Returns:
        bool: True si tiene el permiso
    """
    # Superusuarios siempre tienen todos los permisos
    if user.is_superuser:
        return True

    # Obtener perfil de administrador
    admin = obtener_perfil_admin(user)

    if not admin or not admin.activo:
        return False

    # Verificar permiso específico
    return admin.tiene_permiso(permiso)


# ============================================
# DECORATOR: REQUIERE PERMISO
# ============================================

def requiere_permiso(permiso):
    """
    Decorator para validar permisos en vistas

    Uso:
        @requiere_permiso('gestionar_usuarios')
        def mi_vista(request):
            ...
    """
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            if not tiene_permiso_especifico(request.user, permiso):
                logger.warning(
                    f"⚠️ Permiso denegado: {request.user.email} "
                    f"no tiene permiso '{permiso}'"
                )
                raise PermissionDenied(
                    f"No tienes permiso para realizar esta acción."
                )
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


# ============================================
# CLASE: PERMISO DINÁMICO
# ============================================

class PermisoDinamico(permissions.BasePermission):
    """
    Permiso que se configura dinámicamente

    Uso:
        permission_classes = [PermisoDinamico]
        permiso_requerido = 'gestionar_usuarios'
    """

    def has_permission(self, request, view):
        """
        Verifica el permiso especificado en el view
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Obtener el permiso requerido desde el view
        permiso_requerido = getattr(view, 'permiso_requerido', None)

        if not permiso_requerido:
            logger.error("❌ View no especifica permiso_requerido")
            return False

        return tiene_permiso_especifico(request.user, permiso_requerido)


# ============================================
# VALIDADOR: MÚLTIPLES PERMISOS (AND)
# ============================================

class RequiereMultiplesPermisos(permissions.BasePermission):
    """
    Requiere que el usuario tenga TODOS los permisos especificados

    Uso:
        permission_classes = [RequiereMultiplesPermisos]
        permisos_requeridos = ['gestionar_usuarios', 'ver_reportes']
    """

    def has_permission(self, request, view):
        """
        Verifica todos los permisos
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Obtener lista de permisos requeridos
        permisos = getattr(view, 'permisos_requeridos', [])

        if not permisos:
            return True

        # Verificar todos los permisos
        for permiso in permisos:
            if not tiene_permiso_especifico(request.user, permiso):
                logger.warning(
                    f"⚠️ Permiso denegado: {request.user.email} "
                    f"no tiene permiso '{permiso}'"
                )
                return False

        return True


# ============================================
# VALIDADOR: MÚLTIPLES PERMISOS (OR)
# ============================================

class RequiereCualquierPermiso(permissions.BasePermission):
    """
    Requiere que el usuario tenga AL MENOS UNO de los permisos especificados

    Uso:
        permission_classes = [RequiereCualquierPermiso]
        permisos_opcionales = ['gestionar_usuarios', 'gestionar_proveedores']
    """

    def has_permission(self, request, view):
        """
        Verifica si tiene al menos un permiso
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Obtener lista de permisos opcionales
        permisos = getattr(view, 'permisos_opcionales', [])

        if not permisos:
            return True

        # Verificar si tiene al menos uno
        for permiso in permisos:
            if tiene_permiso_especifico(request.user, permiso):
                return True

        logger.warning(
            f"⚠️ Permiso denegado: {request.user.email} "
            f"no tiene ninguno de los permisos requeridos"
        )

        return False
