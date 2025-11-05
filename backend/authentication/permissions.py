from rest_framework import permissions

# ==========================================
# PERMISOS INDIVIDUALES POR ROL
# ==========================================

class EsAdministrador(permissions.BasePermission):
    """
    Permiso personalizado para verificar si es administrador
    """
    message = 'Solo los administradores pueden realizar esta acción'
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.es_administrador()


class EsRepartidor(permissions.BasePermission):
    """
    Permiso personalizado para verificar si es repartidor
    """
    message = 'Solo los repartidores pueden realizar esta acción'
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.es_repartidor()


class EsProveedor(permissions.BasePermission):
    """
    Permiso personalizado para verificar si es proveedor
    """
    message = 'Solo los proveedores pueden realizar esta acción'
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.es_proveedor()


class EsUsuario(permissions.BasePermission):
    """
    Permiso personalizado para verificar si es usuario regular
    """
    message = 'Solo los usuarios regulares pueden realizar esta acción'
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.es_usuario()


class EsProveedorVerificado(permissions.BasePermission):
    """
    Permiso para verificar que el proveedor esté verificado
    """
    message = 'Tu cuenta de proveedor debe estar verificada para realizar esta acción'
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                request.user.es_proveedor() and 
                request.user.verificado)


class PuedeCrearRifas(permissions.BasePermission):
    """
    Solo administradores pueden crear rifas
    """
    message = 'Solo los administradores pueden crear rifas'
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.puede_crear_rifas()


# ==========================================
# PERMISOS COMBINADOS
# ==========================================

class EsAdministradorORepartidor(permissions.BasePermission):
    """
    Permite acceso a administradores o repartidores
    """
    message = 'Solo los administradores o repartidores pueden realizar esta acción'
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                (request.user.es_administrador() or request.user.es_repartidor()))


class EsAdministradorOProveedor(permissions.BasePermission):
    """
    Permite acceso a administradores o proveedores
    """
    message = 'Solo los administradores o proveedores pueden realizar esta acción'
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                (request.user.es_administrador() or request.user.es_proveedor()))


class NoEsUsuarioRegular(permissions.BasePermission):
    """
    Permite acceso a todos menos usuarios regulares (admin, proveedor, repartidor)
    """
    message = 'Esta acción no está disponible para usuarios regulares'
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                not request.user.es_usuario())


# ==========================================
# PERMISOS A NIVEL DE OBJETO
# ==========================================

class EsPropietarioOAdministrador(permissions.BasePermission):
    """
    Permite editar solo si es el propietario del objeto o es administrador
    """
    message = 'No tienes permiso para modificar este recurso'
    
    def has_object_permission(self, request, view, obj):
        # Los administradores pueden todo
        if request.user.es_administrador():
            return True
        
        # Verificar si el objeto tiene un campo 'user' o 'usuario'
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        
        # Si el objeto es el mismo usuario
        if obj == request.user:
            return True
        
        return False


class SoloLecturaSiNoEsPropietario(permissions.BasePermission):
    """
    Permite lectura a todos, pero escritura solo al propietario o admin
    """
    message = 'Solo puedes modificar tus propios recursos'
    
    def has_object_permission(self, request, view, obj):
        # Permitir métodos seguros (GET, HEAD, OPTIONS) a todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Los administradores pueden modificar todo
        if request.user.es_administrador():
            return True
        
        # Verificar propiedad del objeto
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        elif obj == request.user:
            return True
        
        return False


class CuentaActiva(permissions.BasePermission):
    """
    Verifica que la cuenta del usuario esté activa y no desactivada
    """
    message = 'Tu cuenta está desactivada. Contacta con soporte.'
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                request.user.is_active and
                not request.user.cuenta_desactivada)