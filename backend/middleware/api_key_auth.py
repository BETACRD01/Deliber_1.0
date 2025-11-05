# middleware/api_key_auth.py

import os
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import logging

logger = logging.getLogger('api_logger')


class ApiKeyAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware para validar API Key antes de JWT (mejorado)

    Flujo de seguridad:
    1. Verifica si el endpoint requiere API Key
    2. Si está en modo DEBUG, permite JWT sin API Key
    3. Valida el API Key en el header X-API-KEY
    4. Identifica el tipo de cliente (web/mobile)
    5. Permite que JWT se valide después

    MEJORAS:
    - ✅ Modo flexible en desarrollo (DEBUG=True)
    - ✅ Mejor logging de errores
    - ✅ Endpoints de refresh token incluidos
    - ✅ Validación más robusta
    """

    # Endpoints que NO requieren API Key (públicos)
    PUBLIC_ENDPOINTS = [
        '/admin/',
        '/api/auth/login/',
        '/api/auth/registro/',
        '/api/auth/google-login/',
        '/api/auth/token/refresh/',  # ✅ Agregado
        '/api/auth/token/verify/',    # ✅ Agregado
        '/api/auth/solicitar-codigo-recuperacion/',
        '/api/auth/verificar-codigo/',
        '/api/auth/reset-password-con-codigo/',
        '/api/auth/solicitar-reset-password/',
        '/api/auth/reset-password/',
        '/accounts/',
        '/static/',
        '/media/',
        '/',
    ]

    # API Keys válidas (desde .env)
    VALID_API_KEYS = {
        'web': os.getenv('API_KEY_WEB', ''),
        'mobile': os.getenv('API_KEY_MOBILE', ''),
    }

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

        # Validar que las API Keys estén configuradas
        if not self.VALID_API_KEYS['web'] or not self.VALID_API_KEYS['mobile']:
            logger.warning('⚠️ API Keys no configuradas en .env')

        # Modo de operación
        self.debug_mode = getattr(settings, 'DEBUG', False)
        if self.debug_mode:
            logger.info('🔓 API Key Middleware en modo DEBUG (flexible)')

    def process_request(self, request):
        """Procesa cada petición antes de llegar a las vistas"""

        # 1. Verificar si el endpoint es público
        if self._is_public_endpoint(request.path):
            logger.debug(f'✅ Endpoint público: {request.path}')
            return None

        # 2. Obtener API Key del header
        api_key = request.META.get('HTTP_X_API_KEY', '')

        # 🔍 DIAGNÓSTICO: Ver qué headers llegan
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        logger.info(f'🔍 DIAGNÓSTICO {request.method} {request.path}:')
        logger.info(f'   - API Key presente: {bool(api_key)}')
        logger.info(f'   - Authorization header: {auth_header[:50] if auth_header else "VACÍO"}...')
        logger.info(f'   - DEBUG mode: {self.debug_mode}')

        # 3. MODO DESARROLLO: Permitir JWT sin API Key
        if self.debug_mode and not api_key:
            # Verificar si tiene Authorization header (JWT)

            if auth_header.startswith('Bearer '):
                logger.warning(
                    f'⚠️ Request sin API Key pero con JWT (permitido en DEBUG): '
                    f'{request.method} {request.path}'
                )
                request.client_type = 'unknown'
                request.api_key_validated = False
                return None  # Permitir que JWT se valide

            # Si no tiene ni API Key ni JWT, rechazar
            logger.error(f'❌ Request sin API Key ni JWT: {request.method} {request.path}')
            return self._error_response(
                'API Key requerida. Incluye el header X-API-KEY',
                status=403
            )

        # 4. MODO PRODUCCIÓN: API Key obligatoria
        if not api_key:
            logger.error(f'❌ API Key faltante: {request.method} {request.path}')
            return self._error_response(
                'API Key requerida. Incluye el header X-API-KEY',
                status=403
            )

        # 5. Validar API Key y determinar tipo de cliente
        client_type = self._validate_api_key(api_key)

        if not client_type:
            logger.error(
                f'❌ API Key inválida: {request.method} {request.path} '
                f'Key: {api_key[:10]}...'
            )
            return self._error_response(
                'API Key inválida',
                status=403
            )

        # 6. Agregar información del cliente al request
        request.client_type = client_type
        request.api_key_validated = True

        logger.debug(f'✅ API Key válida ({client_type}): {request.method} {request.path}')

        # 7. Continuar con JWT Authentication
        return None

    def _is_public_endpoint(self, path):
        """Verifica si el endpoint es público"""
        return any(path.startswith(endpoint) for endpoint in self.PUBLIC_ENDPOINTS)

    def _validate_api_key(self, api_key):
        """
        Valida el API Key y retorna el tipo de cliente

        Returns:
            str: 'web' o 'mobile' si es válido, None si es inválido
        """
        for client_type, valid_key in self.VALID_API_KEYS.items():
            if valid_key and api_key == valid_key:
                return client_type
        return None

    def _error_response(self, message, status=403):
        """Respuesta de error estandarizada"""
        return JsonResponse({
            'error': message,
            'status': 'unauthorized',
            'code': status,
            'hint': 'Incluye el header X-API-KEY en tu petición' if status == 403 else None
        }, status=status)


class ClientTypePermissionMiddleware(MiddlewareMixin):
    """
    Middleware opcional para restricciones adicionales por tipo de cliente

    Ejemplo: Ciertos endpoints solo para web admin
    """

    # Endpoints exclusivos para admin web
    ADMIN_ONLY_ENDPOINTS = [
        '/api/admin/repartidores/estado/',
        '/api/admin/estadisticas/',
    ]

    def process_request(self, request):
        """Valida permisos según tipo de cliente"""

        # Solo aplica si ya se validó API Key
        if not hasattr(request, 'api_key_validated'):
            return None

        # Si no se validó API Key (modo DEBUG), permitir
        if not request.api_key_validated:
            return None

        # Verificar si el endpoint es solo para admin web
        if any(request.path.startswith(endpoint) for endpoint in self.ADMIN_ONLY_ENDPOINTS):
            if request.client_type != 'web':
                logger.warning(
                    f'⚠️ Acceso denegado a endpoint admin: '
                    f'{request.method} {request.path} (client: {request.client_type})'
                )
                return JsonResponse({
                    'error': 'Este endpoint solo está disponible para el panel de administración',
                    'status': 'forbidden',
                    'code': 403
                }, status=403)

        return None
