# repartidores/permissions.py
from rest_framework.permissions import BasePermission

class IsRepartidor(BasePermission):
    """
    Permiso personalizado: solo usuarios con perfil de repartidor pueden acceder.
    """
    message = "Solo repartidores pueden acceder a este recurso."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'repartidor')
        )


class IsRepartidorActivo(BasePermission):
    """
    Permiso extendido: el repartidor debe estar activo y verificado.
    """
    message = "Tu cuenta de repartidor no está activa o verificada."

    def has_permission(self, request, view):
        if not hasattr(request.user, 'repartidor'):
            return False

        repartidor = request.user.repartidor
        return repartidor.activo and repartidor.verificado
