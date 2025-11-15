# -*- coding: utf-8 -*-
# authentication/throttles.py

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger('authentication')


# ==========================================
# THROTTLES PERSONALIZADOS POR ENDPOINT
# ==========================================

class LoginRateThrottle(AnonRateThrottle):
    """
    Rate limiting específico para login
    Protege contra ataques de fuerza bruta
    """
    scope = 'login'
    
    def get_rate(self):
        """Obtiene rate desde settings"""
        if settings.DEBUG:
            return '20/minute'  # Desarrollo: 20 intentos por minuto
        return '5/minute'  # Producción: 5 intentos por minuto
    
    def get_cache_key(self, request, view):
        """Cache key por IP"""
        ident = self.get_ident(request)
        return f'throttle_login_{ident}'
    
    def throttle_failure(self):
        """Registra cuando se excede el límite"""
        logger.warning(f"❌ Rate limit excedido para login desde IP: {self.get_ident(self.request)}")
        return super().throttle_failure()


class RegisterRateThrottle(AnonRateThrottle):
    """
    Rate limiting para registro
    Más permisivo que login pero con protección
    """
    scope = 'register'
    
    def get_rate(self):
        """Registros por hora por IP"""
        if settings.DEBUG:
            return '20/hour'  # Desarrollo: más permisivo
        return '5/hour'  # Producción: más restrictivo
    
    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f'throttle_register_{ident}'
    
    def throttle_failure(self):
        """Registra cuando se excede el límite"""
        logger.warning(f"❌ Rate limit excedido para registro desde IP: {self.get_ident(self.request)}")
        return super().throttle_failure()


class PasswordResetRateThrottle(AnonRateThrottle):
    """
    Rate limiting para reset de password
    Muy restrictivo para evitar spam y ataques
    """
    scope = 'password_reset'
    
    def get_rate(self):
        if settings.DEBUG:
            return '10/hour'  # Desarrollo: 10 intentos por hora
        return '3/hour'  # Producción: 3 intentos por hora
    
    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f'throttle_password_reset_{ident}'
    
    def throttle_failure(self):
        """Registra cuando se excede el límite"""
        logger.warning(f"❌ Rate limit excedido para reset password desde IP: {self.get_ident(self.request)}")
        return super().throttle_failure()


class CodeVerificationThrottle(AnonRateThrottle):
    """
    Rate limiting para verificación de código de recuperación
    Protege contra ataques de fuerza bruta en códigos de 6 dígitos
    """
    scope = 'code_verification'
    
    def get_rate(self):
        if settings.DEBUG:
            return '30/hour'  # Desarrollo: 30 intentos por hora
        return '10/hour'  # Producción: 10 intentos por hora
    
    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f'throttle_code_verification_{ident}'
    
    def throttle_failure(self):
        """Registra cuando se excede el límite"""
        logger.warning(f"❌ Rate limit excedido en verificación de código desde IP: {self.get_ident(self.request)}")
        return super().throttle_failure()


class AuthenticatedUserThrottle(UserRateThrottle):
    """
    Rate limiting para usuarios autenticados
    Más permisivo que anónimos
    """
    scope = 'user'
    rate = '1000/hour'  # 1000 peticiones por hora
    
    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return f'throttle_user_{ident}'


class BurstRateThrottle(AnonRateThrottle):
    """
    Detecta ráfagas de peticiones (posible ataque)
    """
    scope = 'burst'
    
    def get_rate(self):
        if settings.DEBUG:
            return '100/minute'  # Desarrollo: más permisivo
        return '30/minute'  # Producción: 30 peticiones por minuto
    
    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f'throttle_burst_{ident}'
    
    def throttle_failure(self):
        """Registra cuando se excede el límite"""
        logger.warning(f"❌ Ráfaga de peticiones detectada desde IP: {self.get_ident(self.request)}")
        return super().throttle_failure()


# ==========================================
# FUNCIONES HELPER
# ==========================================

def get_throttle_message(throttle_scope):
    """
    Retorna mensaje personalizado según el tipo de throttle
    """
    messages = {
        'login': 'Demasiados intentos de inicio de sesión. Espera un momento e intenta nuevamente.',
        'register': 'Demasiados intentos de registro. Por favor espera antes de intentar nuevamente.',
        'password_reset': 'Has alcanzado el límite de solicitudes de recuperación de contraseña.',
        'code_verification': 'Demasiados intentos de verificación de código. Espera antes de intentar nuevamente.',
        'burst': 'Detectamos actividad sospechosa. Tu acceso ha sido temporalmente limitado.',
        'user': 'Has excedido el límite de peticiones. Espera un momento.',
    }
    return messages.get(throttle_scope, 'Demasiadas peticiones. Intenta más tarde.')


def check_custom_rate_limit(request, key_prefix, max_attempts, window_seconds):
    """
    Sistema de rate limiting manual usando Redis
    Útil para casos muy específicos
    
    Args:
        request: Request de Django
        key_prefix: Prefijo para la key de cache
        max_attempts: Número máximo de intentos
        window_seconds: Ventana de tiempo en segundos
    
    Returns:
        dict: {
            'permitido': bool,
            'intentos_restantes': int,
            'tiempo_espera': int (segundos),
            'bloqueado': bool
        }
    """
    # Obtener IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    cache_key = f'{key_prefix}_{ip}'
    
    try:
        # Obtener datos del cache
        data = cache.get(cache_key, {
            'intentos': 0,
            'primer_intento': timezone.now().timestamp()
        })
        
        intentos = data.get('intentos', 0)
        primer_intento = data.get('primer_intento', timezone.now().timestamp())
        tiempo_transcurrido = timezone.now().timestamp() - primer_intento
        
        # Si pasó la ventana, resetear
        if tiempo_transcurrido > window_seconds:
            intentos = 0
            primer_intento = timezone.now().timestamp()
        
        # Verificar si excedió el límite
        if intentos >= max_attempts:
            tiempo_restante = int(window_seconds - tiempo_transcurrido)
            logger.warning(f"❌ Rate limit excedido: {cache_key} ({intentos}/{max_attempts})")
            return {
                'permitido': False,
                'intentos_restantes': 0,
                'tiempo_espera': max(tiempo_restante, 0),
                'bloqueado': True
            }
        
        # Incrementar contador
        intentos += 1
        cache.set(cache_key, {
            'intentos': intentos,
            'primer_intento': primer_intento
        }, window_seconds)
        
        intentos_restantes = max_attempts - intentos
        return {
            'permitido': True,
            'intentos_restantes': intentos_restantes,
            'tiempo_espera': 0,
            'bloqueado': False
        }
        
    except Exception as e:
        logger.error(f"❌ Error en check_custom_rate_limit: {e}")
        # En caso de error, permitir la petición
        return {
            'permitido': True,
            'intentos_restantes': 999,
            'tiempo_espera': 0,
            'bloqueado': False
        }


def reset_rate_limit(request, key_prefix):
    """
    Resetea el rate limit para una IP específica
    Útil después de login exitoso
    
    Args:
        request: Request de Django
        key_prefix: Prefijo de la cache key a resetear
    
    Returns:
        bool: True si se reseteó exitosamente
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    cache_key = f'{key_prefix}_{ip}'
    
    try:
        cache.delete(cache_key)
        logger.debug(f"✅ Rate limit reseteado para IP {ip} en key {key_prefix}")
        return True
    except Exception as e:
        logger.error(f"❌ Error reseteando rate limit: {e}")
        return False


def get_rate_limit_info(request, key_prefix):
    """
    Obtiene información sobre el estado actual del rate limit
    Útil para debugging y mostrar info al usuario
    
    Args:
        request: Request de Django
        key_prefix: Prefijo de la cache key
    
    Returns:
        dict: Información del rate limit o None si no existe
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    cache_key = f'{key_prefix}_{ip}'
    
    try:
        data = cache.get(cache_key)
        if not data:
            return None
        
        intentos = data.get('intentos', 0)
        primer_intento = data.get('primer_intento', timezone.now().timestamp())
        tiempo_transcurrido = int(timezone.now().timestamp() - primer_intento)
        
        return {
            'ip': ip,
            'cache_key': cache_key,
            'intentos': intentos,
            'tiempo_transcurrido_segundos': tiempo_transcurrido,
            'primer_intento_timestamp': primer_intento
        }
    except Exception as e:
        logger.error(f"❌ Error obteniendo info de rate limit: {e}")
        return None