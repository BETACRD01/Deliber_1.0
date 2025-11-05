# -*- coding: utf-8 -*-
# authentication/email_utils.py

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
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
        from django.contrib.auth.tokens import default_token_generator
        token = default_token_generator.make_token(user)
        unsubscribe_path = reverse('unsubscribe_emails', kwargs={
            'user_id': user.id,
            'token': token
        })
        return f"{settings.FRONTEND_URL}{unsubscribe_path}"
    
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
            logger.info(f"Usuario {user.email} no puede recibir emails")
            return False
        
        context = {
            'user': user,
            'app_url': settings.FRONTEND_URL,
            'year': datetime.now().year,
            'unsubscribe_url': EmailService._get_unsubscribe_url(user)
        }
        
        # Renderizar templates
        html_content = render_to_string(
            'authentication/emails/bienvenida.html',
            context
        )
        text_content = render_to_string(
            'authentication/emails/bienvenida.txt',
            context
        )
        
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
    def enviar_reset_password(user, reset_url):
        """
        Envía email de recuperación de contraseña con URL (MÉTODO ANTIGUO)
        """
        if not user.puede_recibir_emails():
            logger.info(f"Usuario {user.email} no puede recibir emails")
            return False
        
        context = {
            'user': user,
            'reset_url': reset_url,
            'year': datetime.now().year,
            'unsubscribe_url': EmailService._get_unsubscribe_url(user)
        }
        
        html_content = render_to_string(
            'authentication/emails/reset_password.html',
            context
        )
        text_content = render_to_string(
            'authentication/emails/reset_password.txt',
            context
        )
        
        subject = 'Recuperación de contraseña - JP Express'
        
        return EmailService._send_email(
            subject=subject,
            to_email=user.email,
            html_content=html_content,
            text_content=text_content,
            user=user,
            include_unsubscribe=False
        )
    
    @staticmethod
    def enviar_codigo_recuperacion(user, codigo):
        """
        ✅ NUEVO: Envía email con código de 6 dígitos para recuperación de contraseña
        
        Args:
            user: Usuario que solicitó el código
            codigo: Código de 6 dígitos (string)
        
        Returns:
            bool: True si se envió exitosamente
        """
        if not user.puede_recibir_emails():
            logger.info(f"Usuario {user.email} no puede recibir emails")
            return False
        
        context = {
            'user': user,
            'codigo': codigo,
            'year': datetime.now().year,
            'expiracion_minutos': 15,
        }
        
        # ✅ Usar los templates existentes reset_password.html y reset_password.txt
        html_content = render_to_string(
            'authentication/emails/reset_password.html',
            context
        )
        text_content = render_to_string(
            'authentication/emails/reset_password.txt',
            context
        )
        
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
        ✅ NUEVO: Envía confirmación de que la contraseña fue cambiada exitosamente
        """
        if not user.puede_recibir_emails():
            return False
        
        context = {
            'user': user,
            'year': datetime.now().year,
        }
        
        # Usar los templates existentes (crearás cambio_password_exitoso.html y .txt)
        html_content = render_to_string(
            'authentication/emails/cambio_password_exitoso.html',
            context
        )
        text_content = render_to_string(
            'authentication/emails/cambio_password_exitoso.txt',
            context
        )
        
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
            'year': datetime.now().year,
            'resubscribe_url': f"{settings.FRONTEND_URL}/preferencias"
        }
        
        html_content = render_to_string(
            'authentication/emails/confirmacion_baja.html',
            context
        )
        text_content = render_to_string(
            'authentication/emails/confirmacion_baja.txt',
            context
        )
        
        subject = 'Has sido dado de baja de nuestras notificaciones - JP Express'
        
        return EmailService._send_email(
            subject=subject,
            to_email=user.email,
            html_content=html_content,
            text_content=text_content,
            user=user,
            include_unsubscribe=False
        )
    
    @staticmethod
    def enviar_notificacion_pedido(user, pedido):
        """
        Envía notificación sobre cambio de estado de pedido
        """
        if not user.puede_recibir_emails() or not user.notificaciones_pedidos:
            return False
        
        context = {
            'user': user,
            'pedido': pedido,
            'year': datetime.now().year,
            'unsubscribe_url': EmailService._get_unsubscribe_url(user)
        }
        
        html_content = render_to_string(
            'authentication/emails/notificacion_pedido.html',
            context
        )
        text_content = render_to_string(
            'authentication/emails/notificacion_pedido.txt',
            context
        )
        
        subject = f'Actualización de tu pedido #{pedido.id} - JP Express'
        
        return EmailService._send_email(
            subject=subject,
            to_email=user.email,
            html_content=html_content,
            text_content=text_content,
            user=user,
            include_unsubscribe=True
        )
    
    @staticmethod
    def enviar_marketing(user, titulo, contenido):
        """
        Envía email de marketing/promociones
        """
        if not user.puede_recibir_marketing():
            return False
        
        context = {
            'user': user,
            'titulo': titulo,
            'contenido': contenido,
            'year': datetime.now().year,
            'unsubscribe_url': EmailService._get_unsubscribe_url(user)
        }
        
        html_content = render_to_string(
            'authentication/emails/marketing.html',
            context
        )
        text_content = render_to_string(
            'authentication/emails/marketing.txt',
            context
        )
        
        subject = f'{titulo} - JP Express'
        
        return EmailService._send_email(
            subject=subject,
            to_email=user.email,
            html_content=html_content,
            text_content=text_content,
            user=user,
            include_unsubscribe=True
        )


# ==========================================
# FUNCIONES HELPER (SHORTCUTS)
# ==========================================

def enviar_email_bienvenida(user):
    """Shortcut para enviar email de bienvenida"""
    return EmailService.enviar_bienvenida(user)


def enviar_email_reset_password(user, reset_url):
    """Shortcut para enviar email de reset password (método antiguo)"""
    return EmailService.enviar_reset_password(user, reset_url)


def enviar_codigo_recuperacion_password(user, codigo):
    """✅ NUEVO: Shortcut para enviar código de recuperación"""
    return EmailService.enviar_codigo_recuperacion(user, codigo)


def enviar_confirmacion_cambio_password(user):
    """✅ NUEVO: Shortcut para enviar confirmación de cambio"""
    return EmailService.enviar_confirmacion_cambio_password(user)


def enviar_email_confirmacion_baja(user):
    """Shortcut para enviar confirmación de baja"""
    return EmailService.enviar_confirmacion_baja(user)


def enviar_notificacion_pedido(user, pedido):
    """Shortcut para enviar notificación de pedido"""
    return EmailService.enviar_notificacion_pedido(user, pedido)


def enviar_email_marketing(user, titulo, contenido):
    """Shortcut para enviar email de marketing"""
    return EmailService.enviar_marketing(user, titulo, contenido)