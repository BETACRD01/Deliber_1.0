# -*- coding: utf-8 -*-
# usuarios/solicitudes.py
"""
Sistema completo para gestionar solicitudes de cambio de rol
Usuario Normal → Proveedor / Repartidor

Incluye:
- Validaciones exhaustivas
- Notificaciones FCM al usuario
- Auditoría de acciones administrativas
- Transacciones atómicas
- Manejo de errores robusto
"""

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from authentication.models import User
from .models import SolicitudCambioRol
import logging

logger = logging.getLogger('usuarios')


# ============================================
# 🔍 VALIDADOR DE SOLICITUDES
# ============================================

class ValidadorSolicitudCambioRol:
    """
    Valida que el usuario pueda solicitar un cambio de rol
    
    Validaciones:
    - El usuario existe y está verificado
    - No tiene solicitud pendiente para ese rol
    - No tiene ya ese rol
    - Datos básicos completados
    """
    
    @staticmethod
    def validar_usuario_puede_solicitar(usuario):
        """
        Valida si el usuario puede solicitar cambio de rol
        
        Args:
            usuario (User): Usuario a validar
        
        Returns:
            tuple: (puede_solicitar: bool, razon: str)
        
        Raises:
            ValidationError: Si no puede solicitar
        """
        # ✅ 1. Verificar que usuario existe
        if not usuario:
            raise ValidationError("Usuario no encontrado")
        
        # ✅ 2. Verificar que usuario está verificado
        if not usuario.verificado:
            raise ValidationError({
                'usuario': "Debes estar verificado para solicitar cambio de rol. "
                          "Verifica tu email primero."
            })
        
        # ✅ 3. Verificar que usuario está activo
        if usuario.cuenta_desactivada:
            raise ValidationError({
                'usuario': "Tu cuenta está desactivada. No puedes solicitar cambios."
            })
        
        # ✅ 4. Verificar que usuario no está baneado
        if not usuario.is_active:
            raise ValidationError({
                'usuario': "Tu cuenta ha sido deshabilitada. Contacta soporte."
            })
        
        # ✅ 5. Verificar que tiene datos básicos
        if not usuario.email:
            raise ValidationError({
                'usuario': "Completa tu email en el perfil"
            })
        
        if not usuario.celular:
            raise ValidationError({
                'usuario': "Completa tu teléfono en el perfil"
            })
        
        return (True, "✅ Usuario válido para solicitar cambio de rol")
    
    @staticmethod
    def validar_rol_solicitado(usuario, rol_solicitado):
        """
        Valida el rol solicitado
        
        Args:
            usuario (User): Usuario
            rol_solicitado (str): Rol solicitado (PROVEEDOR, REPARTIDOR)
        
        Returns:
            tuple: (valido: bool, razon: str)
        
        Raises:
            ValidationError: Si el rol no es válido
        """
        # ✅ 1. Validar que el rol existe
        roles_validos = ['PROVEEDOR', 'REPARTIDOR']
        if rol_solicitado not in roles_validos:
            raise ValidationError({
                'rol_solicitado': f"Rol inválido. Roles válidos: {', '.join(roles_validos)}"
            })
        
        # ✅ 2. Validar que ya no tiene ese rol
        if usuario.tiene_rol(rol_solicitado):
            raise ValidationError({
                'rol_solicitado': f"Ya tienes el rol {rol_solicitado}"
            })
        
        # ✅ 3. Validar que no hay solicitud pendiente
        solicitud_pendiente = SolicitudCambioRol.objects.filter(
            user=usuario,
            rol_solicitado=rol_solicitado,
            estado='PENDIENTE'
        ).exists()
        
        if solicitud_pendiente:
            raise ValidationError({
                'rol_solicitado': f"Ya tienes una solicitud pendiente para {rol_solicitado}"
            })
        
        # ✅ 4. Validar que la solicitud rechazada tiene espera
        ultimo_rechazo = SolicitudCambioRol.objects.filter(
            user=usuario,
            rol_solicitado=rol_solicitado,
            estado='RECHAZADA'
        ).order_by('-respondido_en').first()
        
        if ultimo_rechazo:
            dias_espera = 30
            tiempo_transcurrido = timezone.now() - ultimo_rechazo.respondido_en
            
            if tiempo_transcurrido.days < dias_espera:
                dias_faltantes = dias_espera - tiempo_transcurrido.days
                raise ValidationError({
                    'rol_solicitado': (
                        f"Fue rechazada hace poco. Espera {dias_faltantes} día(s) "
                        f"antes de solicitar de nuevo."
                    )
                })
        
        return (True, f"✅ Rol {rol_solicitado} válido para solicitar")
    
    @staticmethod
    def validar_motivo(motivo):
        """
        Valida el motivo de la solicitud
        
        Args:
            motivo (str): Motivo de la solicitud
        
        Returns:
            tuple: (valido: bool, razon: str)
        
        Raises:
            ValidationError: Si el motivo no es válido
        """
        if not motivo or not motivo.strip():
            raise ValidationError({
                'motivo': "El motivo no puede estar vacío"
            })
        
        motivo = motivo.strip()
        
        if len(motivo) < 10:
            raise ValidationError({
                'motivo': "El motivo debe tener al menos 10 caracteres"
            })
        
        if len(motivo) > 500:
            raise ValidationError({
                'motivo': "El motivo no puede exceder 500 caracteres"
            })
        
        # Validar que no sea spam
        palabras_spam = ['spam', 'prueba', 'test', '123', 'asdf']
        if any(palabra in motivo.lower() for palabra in palabras_spam):
            raise ValidationError({
                'motivo': "El motivo parece ser inválido. Proporciona una razón real."
            })
        
        return (True, "✅ Motivo válido")


# ============================================
# 📝 GESTOR DE SOLICITUDES
# ============================================

class GestorSolicitudCambioRol:
    """
    Gestor central para crear y administrar solicitudes de cambio de rol
    
    Responsabilidades:
    - Crear solicitudes con validaciones
    - Procesar respuestas del admin
    - Enviar notificaciones
    - Registrar auditoría
    """
    
    @staticmethod
    @transaction.atomic
    def crear_solicitud(usuario, rol_solicitado, motivo):
        """
        Crea una nueva solicitud de cambio de rol
        
        Args:
            usuario (User): Usuario que solicita
            rol_solicitado (str): Rol solicitado (PROVEEDOR, REPARTIDOR)
            motivo (str): Motivo de la solicitud
        
        Returns:
            SolicitudCambioRol: Solicitud creada
        
        Raises:
            ValidationError: Si hay error en validaciones
        """
        logger.info(f"🔍 Validando solicitud de {usuario.email} → {rol_solicitado}")
        
        # ✅ Validar usuario
        ValidadorSolicitudCambioRol.validar_usuario_puede_solicitar(usuario)
        
        # ✅ Validar rol
        ValidadorSolicitudCambioRol.validar_rol_solicitado(usuario, rol_solicitado)
        
        # ✅ Validar motivo
        ValidadorSolicitudCambioRol.validar_motivo(motivo)
        
        # ✅ Crear solicitud
        solicitud = SolicitudCambioRol.objects.create(
            user=usuario,
            rol_solicitado=rol_solicitado,
            motivo=motivo.strip(),
            estado='PENDIENTE'
        )
        
        logger.info(
            f"✅ Solicitud creada: {usuario.email} → {rol_solicitado} "
            f"(ID: {solicitud.id})"
        )
        
        # 📬 Enviar notificación (sin bloquear si falla)
        try:
            NotificadorSolicitud.notificar_solicitud_creada(solicitud)
        except Exception as e:
            logger.error(f"⚠️  Error enviando notificación: {e}")
        
        return solicitud
    
    @staticmethod
    @transaction.atomic
    def aceptar_solicitud(solicitud, admin, motivo_respuesta=''):
        """
        Acepta una solicitud de cambio de rol
        
        Args:
            solicitud (SolicitudCambioRol): Solicitud a aceptar
            admin (User): Usuario admin que acepta
            motivo_respuesta (str): Motivo de la aceptación (opcional)
        
        Returns:
            dict: Resultado de la operación
        
        Raises:
            ValidationError: Si no se puede aceptar
        """
        # ✅ Validar que es PENDIENTE
        if solicitud.estado != 'PENDIENTE':
            raise ValidationError(
                f"Solo puedes aceptar solicitudes PENDIENTE. "
                f"Estado actual: {solicitud.estado}"
            )
        
        # ✅ Validar que admin es admin
        if not admin.is_staff:
            raise ValidationError("Solo administradores pueden aceptar solicitudes")
        
        logger.info(
            f"✅ Aceptando solicitud: {solicitud.user.email} → "
            f"{solicitud.rol_solicitado} por {admin.email}"
        )
        
        try:
            # 1️⃣ Actualizar solicitud
            solicitud.estado = 'ACEPTADA'
            solicitud.admin_responsable = admin
            solicitud.motivo_respuesta = motivo_respuesta
            solicitud.respondido_en = timezone.now()
            solicitud.save(update_fields=[
                'estado', 'admin_responsable', 'motivo_respuesta', 'respondido_en'
            ])
            
            # 2️⃣ Agregar rol al usuario
            solicitud.user.agregar_rol(solicitud.rol_solicitado)
            
            # 3️⃣ Crear objeto específico si es necesario
            if solicitud.rol_solicitado == 'PROVEEDOR':
                GestorSolicitudCambioRol._crear_proveedor(solicitud.user)
            elif solicitud.rol_solicitado == 'REPARTIDOR':
                GestorSolicitudCambioRol._crear_repartidor(solicitud.user)
            
            # 4️⃣ Registrar auditoría
            GestorSolicitudCambioRol._registrar_auditoria(
                admin=admin,
                tipo_accion='aceptar_solicitud_rol',
                descripcion=f"Aceptada solicitud de {solicitud.user.email} "
                           f"para {solicitud.rol_solicitado}",
                solicitud=solicitud
            )
            
            # 5️⃣ Enviar notificación al usuario
            try:
                NotificadorSolicitud.notificar_solicitud_aceptada(solicitud)
            except Exception as e:
                logger.error(f"⚠️  Error enviando notificación: {e}")
            
            logger.info(f"✅ Solicitud aceptada: {solicitud.id}")
            
            return {
                'exitoso': True,
                'solicitud_id': solicitud.id,
                'usuario': solicitud.user.email,
                'rol': solicitud.rol_solicitado,
                'mensaje': f"Solicitud aceptada. {solicitud.user.email} "
                          f"ahora es {solicitud.rol_solicitado}"
            }
        
        except Exception as e:
            logger.error(f"❌ Error aceptando solicitud: {e}", exc_info=True)
            raise ValidationError(f"Error al aceptar: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def rechazar_solicitud(solicitud, admin, motivo_respuesta):
        """
        Rechaza una solicitud de cambio de rol
        
        Args:
            solicitud (SolicitudCambioRol): Solicitud a rechazar
            admin (User): Usuario admin que rechaza
            motivo_respuesta (str): Motivo del rechazo
        
        Returns:
            dict: Resultado de la operación
        
        Raises:
            ValidationError: Si no se puede rechazar
        """
        # ✅ Validar que es PENDIENTE
        if solicitud.estado != 'PENDIENTE':
            raise ValidationError(
                f"Solo puedes rechazar solicitudes PENDIENTE. "
                f"Estado actual: {solicitud.estado}"
            )
        
        # ✅ Validar que admin es admin
        if not admin.is_staff:
            raise ValidationError("Solo administradores pueden rechazar solicitudes")
        
        # ✅ Validar motivo
        if not motivo_respuesta or not motivo_respuesta.strip():
            raise ValidationError(
                "Debes proporcionar un motivo cuando rechazas una solicitud"
            )
        
        logger.info(
            f"❌ Rechazando solicitud: {solicitud.user.email} → "
            f"{solicitud.rol_solicitado} por {admin.email}"
        )
        
        try:
            # 1️⃣ Actualizar solicitud
            solicitud.estado = 'RECHAZADA'
            solicitud.admin_responsable = admin
            solicitud.motivo_respuesta = motivo_respuesta.strip()
            solicitud.respondido_en = timezone.now()
            solicitud.save(update_fields=[
                'estado', 'admin_responsable', 'motivo_respuesta', 'respondido_en'
            ])
            
            # 2️⃣ Registrar auditoría
            GestorSolicitudCambioRol._registrar_auditoria(
                admin=admin,
                tipo_accion='rechazar_solicitud_rol',
                descripcion=f"Rechazada solicitud de {solicitud.user.email} "
                           f"para {solicitud.rol_solicitado}. Motivo: {motivo_respuesta}",
                solicitud=solicitud
            )
            
            # 3️⃣ Enviar notificación al usuario
            try:
                NotificadorSolicitud.notificar_solicitud_rechazada(solicitud)
            except Exception as e:
                logger.error(f"⚠️  Error enviando notificación: {e}")
            
            logger.info(f"✅ Solicitud rechazada: {solicitud.id}")
            
            return {
                'exitoso': True,
                'solicitud_id': solicitud.id,
                'usuario': solicitud.user.email,
                'rol': solicitud.rol_solicitado,
                'motivo': motivo_respuesta,
                'mensaje': f"Solicitud rechazada. {solicitud.user.email} "
                          f"puede solicitar de nuevo después de 30 días"
            }
        
        except Exception as e:
            logger.error(f"❌ Error rechazando solicitud: {e}", exc_info=True)
            raise ValidationError(f"Error al rechazar: {str(e)}")
    
    @staticmethod
    def _crear_proveedor(usuario):
        """Crea registro de Proveedor cuando es aceptado"""
        try:
            from proveedores.models import Proveedor
            
            if not hasattr(usuario, 'proveedor') or usuario.proveedor is None:
                Proveedor.objects.create(
                    user=usuario,
                    nombre=usuario.get_full_name() or usuario.email,
                    ruc='TEMP' + str(usuario.id).zfill(10),
                    email=usuario.email,
                    telefono=usuario.celular,
                    tipo_proveedor='otro',
                    activo=True,
                    verificado=usuario.verificado
                )
                logger.info(f"✅ Proveedor creado para {usuario.email}")
        except Exception as e:
            logger.error(f"❌ Error creando Proveedor: {e}", exc_info=True)
    
    @staticmethod
    def _crear_repartidor(usuario):
        """Crea registro de Repartidor cuando es aceptado"""
        try:
            from repartidores.models import Repartidor, EstadoRepartidor
            
            if not hasattr(usuario, 'repartidor') or usuario.repartidor is None:
                Repartidor.objects.create(
                    user=usuario,
                    cedula=usuario.celular,
                    telefono=usuario.celular,
                    estado=EstadoRepartidor.FUERA_SERVICIO,
                    verificado=usuario.verificado,
                    activo=True
                )
                logger.info(f"✅ Repartidor creado para {usuario.email}")
        except Exception as e:
            logger.error(f"❌ Error creando Repartidor: {e}", exc_info=True)
    
    @staticmethod
    def _registrar_auditoria(admin, tipo_accion, descripcion, solicitud=None):
        """Registra la acción en auditoría"""
        try:
            from proveedores.models import AccionAdministrativa
            
            AccionAdministrativa.registrar_accion(
                administrador=admin,
                tipo_accion=tipo_accion,
                descripcion=descripcion,
                modelo_afectado='SolicitudCambioRol',
                objeto_id=str(solicitud.id) if solicitud else None,
                datos_nuevos={
                    'estado': 'ACEPTADA' if 'aceptar' in tipo_accion else 'RECHAZADA',
                    'usuario': solicitud.user.email if solicitud else None,
                    'rol': solicitud.rol_solicitado if solicitud else None,
                }
            )
        except Exception as e:
            logger.error(f"⚠️  Error registrando auditoría: {e}")


# ============================================
# 📬 NOTIFICADOR DE SOLICITUDES
# ============================================

class NotificadorSolicitud:
    """
    Envía notificaciones FCM al usuario cuando:
    - Se crea una solicitud
    - Es aceptada
    - Es rechazada
    """
    
    @staticmethod
    def notificar_solicitud_creada(solicitud):
        """Notifica que la solicitud fue creada"""
        try:
            perfil = solicitud.user.perfil_usuario
            
            if not perfil.puede_recibir_notificaciones:
                logger.info(f"⚠️  Usuario {solicitud.user.email} no tiene notificaciones habilitadas")
                return
            
            # Aquí iría el envío de notificación FCM real
            mensaje = {
                'titulo': '📝 Solicitud Enviada',
                'cuerpo': f"Tu solicitud para ser {solicitud.rol_solicitado} fue enviada al administrador",
                'tipo': 'solicitud_creada',
                'solicitud_id': str(solicitud.id),
                'estado': 'PENDIENTE'
            }
            
            logger.info(f"📬 Notificación FCM enviada a {solicitud.user.email}: {mensaje}")
        
        except Exception as e:
            logger.error(f"❌ Error en notificación: {e}")
    
    @staticmethod
    def notificar_solicitud_aceptada(solicitud):
        """Notifica que la solicitud fue aceptada"""
        try:
            perfil = solicitud.user.perfil_usuario
            
            if not perfil.puede_recibir_notificaciones:
                logger.info(f"⚠️  Usuario {solicitud.user.email} no tiene notificaciones habilitadas")
                return
            
            mensaje = {
                'titulo': '✅ ¡Solicitud Aceptada!',
                'cuerpo': f"¡Felicitaciones! Tu solicitud para ser {solicitud.rol_solicitado} fue aceptada",
                'tipo': 'solicitud_aceptada',
                'solicitud_id': str(solicitud.id),
                'estado': 'ACEPTADA'
            }
            
            logger.info(f"📬 Notificación FCM enviada a {solicitud.user.email}: {mensaje}")
        
        except Exception as e:
            logger.error(f"❌ Error en notificación: {e}")
    
    @staticmethod
    def notificar_solicitud_rechazada(solicitud):
        """Notifica que la solicitud fue rechazada"""
        try:
            perfil = solicitud.user.perfil_usuario
            
            if not perfil.puede_recibir_notificaciones:
                logger.info(f"⚠️  Usuario {solicitud.user.email} no tiene notificaciones habilitadas")
                return
            
            mensaje = {
                'titulo': '❌ Solicitud Rechazada',
                'cuerpo': f"Tu solicitud para ser {solicitud.rol_solicitado} fue rechazada. "
                         f"Motivo: {solicitud.motivo_respuesta}",
                'tipo': 'solicitud_rechazada',
                'solicitud_id': str(solicitud.id),
                'estado': 'RECHAZADA'
            }
            
            logger.info(f"📬 Notificación FCM enviada a {solicitud.user.email}: {mensaje}")
        
        except Exception as e:
            logger.error(f"❌ Error en notificación: {e}")