# authentication/utils.py

from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger('authentication')


class RateLimiter:
    """
    Sistema de rate limiting inteligente usando Redis
    """
    
    @staticmethod
    def get_client_ip(request):
        """Obtiene la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        logger.debug(f"IP detectada: {ip}")
        return ip
    
    @staticmethod
    def check_rate_limit(request, action='login'):
        """
        Verifica si se excedió el rate limit
        
        Args:
            request: Request de Django
            action: Acción a limitar ('login', 'reset_password', etc)
        
        Returns:
            dict: {
                'permitido': bool,
                'intentos_restantes': int,
                'tiempo_espera': int (segundos),
                'bloqueado': bool
            }
        """
        ip = RateLimiter.get_client_ip(request)
        
        # Obtener configuración según la acción
        if action == 'login':
            limit = settings.RATE_LIMIT_LOGIN_ATTEMPTS
            window = settings.RATE_LIMIT_LOGIN_WINDOW
        elif action == 'reset_password':
            limit = settings.RATE_LIMIT_RESET_PASSWORD
            window = settings.RATE_LIMIT_RESET_PASSWORD_WINDOW
        else:
            limit = 10
            window = 60
        
        cache_key = f'rate_limit:{action}:{ip}'
        
        try:
            # Obtener intentos actuales desde Redis
            data = cache.get(cache_key, {'intentos': 0, 'primer_intento': timezone.now().timestamp()})
            
            intentos = data.get('intentos', 0)
            primer_intento = data.get('primer_intento', timezone.now().timestamp())
            tiempo_transcurrido = timezone.now().timestamp() - primer_intento
            
            # Si pasó la ventana de tiempo, resetear contador
            if tiempo_transcurrido > window:
                intentos = 0
                primer_intento = timezone.now().timestamp()
            
            # Verificar si está bloqueado
            if intentos >= limit:
                tiempo_restante = int(window - tiempo_transcurrido)
                logger.warning(f"Rate limit excedido para IP {ip} en acción '{action}'")
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
            }, window)
            
            intentos_restantes = limit - intentos
            
            logger.debug(f"Rate limit OK para IP {ip}: {intentos}/{limit} intentos")
            
            return {
                'permitido': True,
                'intentos_restantes': intentos_restantes,
                'tiempo_espera': 0,
                'bloqueado': False
            }
            
        except Exception as e:
            logger.error(f"Error en rate limiting: {e}")
            # En caso de error con Redis, permitir la petición
            return {
                'permitido': True,
                'intentos_restantes': 999,
                'tiempo_espera': 0,
                'bloqueado': False
            }
    
    @staticmethod
    def reset_rate_limit(request, action='login'):
        """
        Resetea el rate limit (llamar después de login exitoso)
        """
        ip = RateLimiter.get_client_ip(request)
        cache_key = f'rate_limit:{action}:{ip}'
        
        try:
            cache.delete(cache_key)
            logger.debug(f"Rate limit reseteado para IP {ip} en acción '{action}'")
        except Exception as e:
            logger.error(f"Error al resetear rate limit: {e}")
    
    @staticmethod
    def check_burst(request):
        """
        Detecta ráfagas de peticiones (posible ataque de fuerza bruta)
        
        Returns:
            dict: {
                'es_rafaga': bool,
                'tiempo_espera': int
            }
        """
        # En desarrollo, desactivar detección de ráfagas
        if settings.DEBUG:
            return {'es_rafaga': False, 'tiempo_espera': 0}
        
        ip = RateLimiter.get_client_ip(request)
        cache_key = f'burst_detect:{ip}'
        
        max_requests = settings.RATE_LIMIT_BURST_REQUESTS
        window = settings.RATE_LIMIT_BURST_WINDOW
        
        try:
            # Obtener timestamps de peticiones recientes
            timestamps = cache.get(cache_key, [])
            now = timezone.now().timestamp()
            
            # Filtrar solo las peticiones dentro de la ventana
            timestamps = [t for t in timestamps if now - t < window]
            
            # Si hay demasiadas peticiones, es una ráfaga
            if len(timestamps) >= max_requests:
                logger.warning(f"Ráfaga de peticiones detectada desde IP {ip}: {len(timestamps)} peticiones en {window}s")
                return {
                    'es_rafaga': True,
                    'tiempo_espera': window
                }
            
            # Agregar timestamp actual
            timestamps.append(now)
            cache.set(cache_key, timestamps, window * 2)
            
            return {'es_rafaga': False, 'tiempo_espera': 0}
            
        except Exception as e:
            logger.error(f"Error en detección de ráfagas: {e}")
            return {'es_rafaga': False, 'tiempo_espera': 0}
    
    @staticmethod
    def get_attempts_info(request, action='login'):
        """
        Obtiene información sobre los intentos actuales
        (útil para debugging)
        """
        ip = RateLimiter.get_client_ip(request)
        cache_key = f'rate_limit:{action}:{ip}'
        
        try:
            data = cache.get(cache_key, {'intentos': 0})
            return {
                'ip': ip,
                'intentos': data.get('intentos', 0),
                'cache_key': cache_key
            }
        except Exception as e:
            logger.error(f"Error obteniendo info de intentos: {e}")
            return None