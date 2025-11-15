# -*- coding: utf-8 -*-
# authentication/email_utils.py

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
import logging
from datetime import datetime

logger = logging.getLogger('authentication')


class EmailService:
    """
    Servicio centralizado para el envío de emails
    """
    
    @staticmethod
    def _get_unsubscribe_url(user):
        """Genera URL para darse de baja de notificaciones"""
        token = default_token_generator.make_token(user)
        unsubscribe_path = reverse('unsubscribe_emails', kwargs={
            'user_id': user.id,
            'token': token
        })
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return f"{frontend_url}{unsubscribe_path}"
    
    @staticmethod
    def _send_email(subject, to_email, html_content, text_content, user=None, 
                    include_unsubscribe=True):
        """
        Método interno para enviar emails con versión HTML y texto plano
        """
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email]
            )
            
            email.attach_alternative(html_content, "text/html")
            
            # Agregar headers de unsubscribe (RFC 8058)
            if include_unsubscribe and user:
                unsubscribe_url = EmailService._get_unsubscribe_url(user)
                email.extra_headers = {
                    'List-Unsubscribe': f'<{unsubscribe_url}>',
                    'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
                }
            
            email.send(fail_silently=False)
            logger.info(f"✅ Email '{subject}' enviado exitosamente a {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando email a {to_email}: {e}")
            return False
    
    @staticmethod
    def enviar_bienvenida(user):
        """
        Envía email de bienvenida al registrarse
        """
        if not user.puede_recibir_emails():
            logger.info(f"ℹ️ Usuario {user.email} no puede recibir emails")
            return False
        
        context = {
            'user': user,
            'nombre': user.first_name,
            'apellido': user.last_name,
            'app_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
            'year': datetime.now().year,
            'unsubscribe_url': EmailService._get_unsubscribe_url(user)
        }
        
        try:
            # Renderizar templates
            html_content = render_to_string(
                'authentication/emails/bienvenida.html',
                context
            )
            text_content = render_to_string(
                'authentication/emails/bienvenida.txt',
                context
            )
        except Exception as e:
            logger.error(f"❌ Error renderizando templates de bienvenida: {e}")
            # Crear contenido por defecto si los templates no existen
            html_content = f"<p>¡Bienvenido a nuestra plataforma, {user.first_name}!</p>"
            text_content = f"¡Bienvenido a nuestra plataforma, {user.first_name}!"
        
        subject = f'¡Bienvenido a JP Express, {user.first_name}!'
        
        return EmailService._send_email(
            subject=subject,
            to_email=user.email,
            html_content=html_content,
            text_content=text_content,
            user=user,
            include_unsubscribe=True
        )
    
    @staticmethod
    def enviar_codigo_recuperacion(user, codigo):
        """
        Envía email con código de 6 dígitos para recuperación de contraseña
        
        Args:
            user: Usuario que solicitó el código
            codigo: Código de 6 dígitos (string)
        
        Returns:
            bool: True si se envió exitosamente
        """
        if not user.puede_recibir_emails():
            logger.info(f"ℹ️ Usuario {user.email} no puede recibir emails")
            return False
        
        context = {
            'user': user,
            'nombre': user.first_name,
            'codigo': codigo,
            'year': datetime.now().year,
            'expiracion_minutos': 15,
        }
        
        try:
            html_content = render_to_string(
                'authentication/emails/codigo_recuperacion.html',
                context
            )
            text_content = render_to_string(
                'authentication/emails/codigo_recuperacion.txt',
                context
            )
        except Exception as e:
            logger.error(f"❌ Error renderizando templates de código: {e}")
            # Contenido por defecto
            html_content = f"""
            <p>Hola {user.first_name},</p>
            <p>Recibimos una solicitud para restablecer tu contraseña.</p>
            <p>Tu código de verificación es: <strong>{codigo}</strong></p>
            <p>Este código expira en 15 minutos.</p>
            <p>Si no solicitaste este cambio, ignora este correo.</p>
            """
            text_content = f"Tu código de verificación es: {codigo}\nExpira en 15 minutos."
        
        subject = 'Código de Recuperación - JP Express'
        
        return EmailService._send_email(
            subject=subject,
            to_email=user.email,
            html_content=html_content,
            text_content=text_content,
            user=user,
            include_unsubscribe=False
        )
    
    @staticmethod
    def enviar_confirmacion_cambio_password(user):
        """
        Envía confirmación de que la contraseña fue cambiada exitosamente
        """
        if not user.puede_recibir_emails():
            logger.info(f"ℹ️ Usuario {user.email} no puede recibir emails")
            return False
        
        context = {
            'user': user,
            'nombre': user.first_name,
            'year': datetime.now().year,
        }
        
        try:
            html_content = render_to_string(
                'authentication/emails/cambio_password_exitoso.html',
                context
            )
            text_content = render_to_string(
                'authentication/emails/cambio_password_exitoso.txt',
                context
            )
        except Exception as e:
            logger.error(f"❌ Error renderizando templates de confirmación: {e}")
            # Contenido por defecto
            html_content = f"""
            <p>Hola {user.first_name},</p>
            <p>Tu contraseña ha sido actualizada exitosamente.</p>
            <p>Si no realizaste este cambio, contacta con soporte inmediatamente.</p>
            """
            text_content = "Tu contraseña ha sido actualizada exitosamente."
        
        subject = '✅ Contraseña Actualizada - JP Express'
        
        return EmailService._send_email(
            subject=subject,
            to_email=user.email,
            html_content=html_content,
            text_content=text_content,
            user=user,
            include_unsubscribe=False
        )
    
    @staticmethod
    def enviar_confirmacion_baja(user):
        """
        Envía confirmación de baja de notificaciones
        """
        context = {
            'user': user,
            'nombre': user.first_name,
            'year': datetime.now().year,
            'resubscribe_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/preferencias"
        }
        
        try:
            html_content = render_to_string(
                'authentication/emails/confirmacion_baja.html',
                context
            )
            text_content = render_to_string(
                'authentication/emails/confirmacion_baja.txt',
                context
            )
        except Exception as e:
            logger.error(f"❌ Error renderizando templates de baja: {e}")
            # Contenido por defecto
            html_content = f"""
            <p>Hola {user.first_name},</p>
            <p>Has sido dado de baja exitosamente de nuestras notificaciones.</p>
            <p>Puedes reactivarlas en cualquier momento en tu perfil.</p>
            """
            text_content = "Has sido dado de baja de nuestras notificaciones."
        
        subject = 'Has sido dado de baja de nuestras notificaciones - JP Express'
        
        return EmailService._send_email(
            subject=subject,
            to_email=user.email,
            html_content=html_content,
            text_content=text_content,
            user=user,
            include_unsubscribe=False
        )


# ==========================================
# FUNCIONES HELPER (SHORTCUTS)
# ==========================================

def enviar_email_bienvenida(user):
    """Shortcut para enviar email de bienvenida"""
    return EmailService.enviar_bienvenida(user)


def enviar_codigo_recuperacion_password(user, codigo):
    """Shortcut para enviar código de recuperación"""
    return EmailService.enviar_codigo_recuperacion(user, codigo)


def enviar_confirmacion_cambio_password(user):
    """Shortcut para enviar confirmación de cambio"""
    return EmailService.enviar_confirmacion_cambio_password(user)


def enviar_email_confirmacion_baja(user):
    """Shortcut para enviar confirmación de baja"""
    return EmailService.enviar_confirmacion_baja(user)