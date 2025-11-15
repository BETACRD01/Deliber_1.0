# -*- coding: utf-8 -*-
# usuarios/validators.py

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger('usuarios')


class ValidadorSolicitudCambioRol:
    """
    Validador centralizado para solicitudes de cambio de rol
    Maneja todas las validaciones de negocio antes de crear/procesar solicitudes
    """
    
    # ============================================
    # CONFIGURACIÓN
    # ============================================
    ROLES_PERMITIDOS = ['PROVEEDOR', 'REPARTIDOR']
    MOTIVO_MIN_LENGTH = 10
    MOTIVO_MAX_LENGTH = 500
    
    # ============================================
    # VALIDACIONES DE USUARIO
    # ============================================
    
    @staticmethod
    def validar_usuario_puede_solicitar(usuario):
        """
        Valida que el usuario pueda crear una nueva solicitud
        
        Reglas:
        - Usuario debe estar activo
        - No debe tener solicitudes pendientes
        
        Args:
            usuario: Instancia de User
            
        Raises:
            ValidationError: Si el usuario no cumple requisitos
        """
        # Verificar que el usuario esté activo
        if not usuario.is_active:
            logger.warning(f"⚠️ Usuario inactivo intentó solicitar: {usuario.email}")
            raise ValidationError({
                'usuario': _('Tu cuenta debe estar activa para solicitar cambio de rol')
            })
        
        # Verificar que no tenga solicitudes pendientes
        from .models import SolicitudCambioRol
        
        solicitudes_pendientes = SolicitudCambioRol.objects.filter(
            user=usuario,
            estado='PENDIENTE'
        ).count()
        
        if solicitudes_pendientes > 0:
            logger.warning(
                f"⚠️ Usuario con solicitud pendiente intentó crear otra: {usuario.email}"
            )
            raise ValidationError({
                'usuario': _(
                    'Ya tienes una solicitud pendiente. '
                    'Espera a que sea procesada antes de crear otra.'
                )
            })
        
        logger.info(f"✅ Usuario validado para solicitar: {usuario.email}")
    
    @staticmethod
    def validar_rol_solicitado(usuario, rol_solicitado):
        """
        Valida que el rol solicitado sea válido y permitido
        
        Reglas:
        - Rol debe estar en ROLES_PERMITIDOS
        - Usuario no debe tener ya ese rol
        
        Args:
            usuario: Instancia de User
            rol_solicitado: String con el rol (PROVEEDOR o REPARTIDOR)
            
        Raises:
            ValidationError: Si el rol no es válido
        """
        # Validar que el rol esté en la lista permitida
        if rol_solicitado not in ValidadorSolicitudCambioRol.ROLES_PERMITIDOS:
            logger.error(f"❌ Rol inválido solicitado: {rol_solicitado}")
            raise ValidationError({
                'rol_solicitado': _(
                    f'Rol no permitido. Opciones válidas: '
                    f'{", ".join(ValidadorSolicitudCambioRol.ROLES_PERMITIDOS)}'
                )
            })
        
        # Verificar que el usuario no tenga ya ese rol
        if usuario.tiene_rol(rol_solicitado):
            logger.warning(
                f"⚠️ Usuario ya tiene el rol solicitado: {usuario.email} - {rol_solicitado}"
            )
            raise ValidationError({
                'rol_solicitado': _(f'Ya tienes el rol {rol_solicitado}')
            })
        
        logger.info(f"✅ Rol validado: {usuario.email} → {rol_solicitado}")
    
    @staticmethod
    def validar_motivo(motivo):
        """
        Valida que el motivo sea apropiado
        
        Reglas:
        - Longitud entre MOTIVO_MIN_LENGTH y MOTIVO_MAX_LENGTH
        - No puede estar vacío
        
        Args:
            motivo: String con el motivo
            
        Raises:
            ValidationError: Si el motivo no cumple requisitos
        """
        if not motivo or not motivo.strip():
            raise ValidationError({
                'motivo': _('El motivo es obligatorio')
            })
        
        motivo_limpio = motivo.strip()
        longitud = len(motivo_limpio)
        
        if longitud < ValidadorSolicitudCambioRol.MOTIVO_MIN_LENGTH:
            raise ValidationError({
                'motivo': _(
                    f'El motivo debe tener al menos '
                    f'{ValidadorSolicitudCambioRol.MOTIVO_MIN_LENGTH} caracteres '
                    f'(actual: {longitud})'
                )
            })
        
        if longitud > ValidadorSolicitudCambioRol.MOTIVO_MAX_LENGTH:
            raise ValidationError({
                'motivo': _(
                    f'El motivo no puede exceder '
                    f'{ValidadorSolicitudCambioRol.MOTIVO_MAX_LENGTH} caracteres '
                    f'(actual: {longitud})'
                )
            })
        
        logger.info(f"✅ Motivo validado: {longitud} caracteres")
    
    # ============================================
    # VALIDACIÓN COMPLETA
    # ============================================
    
    @staticmethod
    def validar_solicitud_completa(usuario, rol_solicitado, motivo):
        """
        Ejecuta todas las validaciones en secuencia
        
        Args:
            usuario: Instancia de User
            rol_solicitado: String con el rol
            motivo: String con el motivo
            
        Raises:
            ValidationError: Si alguna validación falla
        """
        ValidadorSolicitudCambioRol.validar_usuario_puede_solicitar(usuario)
        ValidadorSolicitudCambioRol.validar_rol_solicitado(usuario, rol_solicitado)
        ValidadorSolicitudCambioRol.validar_motivo(motivo)
        
        logger.info(
            f"✅ Validación completa exitosa: {usuario.email} → {rol_solicitado}"
        )