# -*- coding: utf-8 -*-
# authentication/email_utils.py

import threading
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
import logging
from datetime import datetime

logger = logging.getLogger('authentication')

class EmailThread(threading.Thread):
    """
    Clase para enviar correos en segundo plano sin bloquear el servidor.
    Patrón: Fire and Forget.
    """
    def __init__(self, subject, body, from_email, recipient_list, html_content, extra_headers=None):
        self.subject = subject
        self.body = body
        self.from_email = from_email
        self.recipient_list = recipient_list
        self.html_content = html_content
        self.extra_headers = extra_headers
        threading.Thread.__init__(self)

    def run(self):
        try:
            msg = EmailMultiAlternatives(
                self.subject, 
                self.body, 
                self.from_email, 
                self.recipient_list
            )
            msg.attach_alternative(self.html_content, "text/html")
            
            if self.extra_headers:
                msg.extra_headers = self.extra_headers
            
            msg.send(fail_silently=False)
            # logger.debug(f"✅ [Background] Email enviado a {self.recipient_list}")
            
        except Exception as e:
            logger.error(f"⚠️ [Background] Fallo envío email (Red/SMTP): {e}")

class EmailService:
    
    @staticmethod
    def _get_base_url(user):
        """
        Determina inteligentemente la URL base:
        - Administradores/Staff -> Panel Web (http://...)
        - Usuarios/Repartidores -> App Móvil (jpexpress://...)
        """
        if user.is_staff or user.is_superuser or getattr(user, 'rol', '') == 'ADMINISTRADOR':
            return getattr(settings, 'FRONTEND_WEB_URL', 'http://localhost:5173')
        
        return getattr(settings, 'FRONTEND_MOBILE_URL', 'jpexpress://app')

    @staticmethod
    def _get_unsubscribe_url(user):
        try:
            token = default_token_generator.make_token(user)
            base_url = EmailService._get_base_url(user)
            # Ajusta esto si tu app móvil tiene pantalla de unsubscribe, sino usa web por defecto
            if "jpexpress://" in base_url:
                # Fallback a web para unsubscribe si es difícil en móvil
                base_url = getattr(settings, 'FRONTEND_WEB_URL', 'http://localhost:5173')
                
            return f"{base_url}/unsubscribe/{user.id}/{token}"
        except Exception:
            return "#"
    
    @staticmethod
    def _send_email(subject, to_email, html_content, text_content, user=None, include_unsubscribe=True):
        """
        Método ASÍNCRONO: Retorna True inmediatamente.
        """
        extra_headers = {}
        if include_unsubscribe and user:
            unsubscribe_url = EmailService._get_unsubscribe_url(user)
            extra_headers = {
                'List-Unsubscribe': f'<{unsubscribe_url}>',
                'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
            }
        
        # Iniciar hilo en background
        EmailThread(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_content=html_content,
            extra_headers=extra_headers
        ).start()
        
        return True
    
    @staticmethod
    def enviar_bienvenida(user):
        if not user.puede_recibir_emails(): return False
        
        base_url = EmailService._get_base_url(user)
        
        context = {
            'user': user,
            'nombre': user.first_name,
            'app_url': f"{base_url}/home", 
            'year': datetime.now().year,
        }
        
        try:
            html_content = render_to_string('authentication/emails/bienvenida.html', context)
            text_content = render_to_string('authentication/emails/bienvenida.txt', context)
        except Exception:
            html_content = f"<p>Bienvenido {user.first_name}</p>"
            text_content = f"Bienvenido {user.first_name}"
        
        return EmailService._send_email(f'¡Bienvenido, {user.first_name}!', user.email, html_content, text_content, user=user)

    @staticmethod
    def enviar_codigo_recuperacion(user, codigo):
        base_url = EmailService._get_base_url(user)
        
        context = {
            'user': user,
            'nombre': user.first_name,
            'codigo': codigo,
            'year': datetime.now().year,
            'expiracion_minutos': 15,
            # Genera link Web o Móvil según corresponda
            'reset_url': f"{base_url}/reset-password?code={codigo}&email={user.email}"
        }
        
        try:
            html_content = render_to_string('authentication/emails/codigo_recuperacion.html', context)
            text_content = render_to_string('authentication/emails/codigo_recuperacion.txt', context)
        except Exception:
            html_content = f"<p>Código: <strong>{codigo}</strong></p>"
            text_content = f"Código: {codigo}"
        
        return EmailService._send_email('Código de Recuperación', user.email, html_content, text_content, user=user, include_unsubscribe=False)

    # Shortcuts
    @staticmethod
    def enviar_confirmacion_cambio_password(user):
        return EmailService._send_email('✅ Contraseña Actualizada', user.email, "<p>Cambio exitoso</p>", "Cambio exitoso", user=user, include_unsubscribe=False)
    
    @staticmethod
    def enviar_confirmacion_baja(user):
        return EmailService._send_email('Baja confirmada', user.email, "<p>Baja confirmada</p>", "Baja confirmada", user=user, include_unsubscribe=False)

# Helper functions globales
def enviar_email_bienvenida(user): return EmailService.enviar_bienvenida(user)
def enviar_codigo_recuperacion_password(user, codigo): return EmailService.enviar_codigo_recuperacion(user, codigo)
def enviar_confirmacion_cambio_password(user): return EmailService.enviar_confirmacion_cambio_password(user)
def enviar_email_confirmacion_baja(user): return EmailService.enviar_confirmacion_baja(user)