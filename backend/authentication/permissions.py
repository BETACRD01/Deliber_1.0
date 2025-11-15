# -*- coding: utf-8 -*-
# authentication/permissions.py

from rest_framework import permissions


# ==========================================
# PERMISOS BÁSICOS
# ==========================================

class EsAdministrador(permissions.BasePermission):
    """
    Permiso personalizado para verificar si es administrador
    """
    message = 'Solo los administradores pueden realizar esta acción'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff
        )


class CuentaActiva(permissions.BasePermission):
    """
    Verifica que la cuenta del usuario esté activa y no desactivada
    """
    message = 'Tu cuenta está desactivada. Contacta con soporte.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_active and
            not request.user.cuenta_desactivada
        )


class NoEstasBloqueado(permissions.BasePermission):
    """
    Verifica que la cuenta no esté temporalmente bloqueada
    """
    message = 'Tu cuenta está temporalmente bloqueada. Intenta más tarde.'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return True
        
        return not request.user.esta_bloqueado()


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
        if request.user.is_staff:
            return True
        
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
        if request.user.is_staff:
            return True
        
        # Si el objeto es el mismo usuario
        if obj == request.user:
            return True
        
        return False


# ==========================================
# COMBINACIONES DE PERMISOS
# ==========================================

class PuedeModificarPropioUsuario(permissions.BasePermission):
    """
    Permite que un usuario solo modifique sus propios datos
    """
    message = 'Solo puedes modificar tu propia información'
    
    def has_object_permission(self, request, view, obj):
        # Métodos seguros para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admin puede modificar todo
        if request.user.is_staff:
            return True
        
        # Cada usuario solo su propia información
        return obj == request.user