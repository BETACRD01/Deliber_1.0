# middleware/log_api_requests.py
import logging
import time
import json
from django.conf import settings

logger = logging.getLogger('api_logger')

class LogAPIRequestsMiddleware:
    """
    Middleware avanzado que loguea peticiones a la API con información detallada:
    - Método, URL, query params
    - IP, User Agent, Usuario autenticado
    - Body del request (configurable)
    - Status code, tiempo de respuesta, tamaño
    - Colorización para mejor lectura en consola
    """

    # Códigos ANSI para colores en consola
    COLORS = {
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'RED': '\033[91m',
        'BLUE': '\033[94m',
        'CYAN': '\033[96m',
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
    }

    def __init__(self, get_response):
        self.get_response = get_response

        # Configuración (puedes moverla a settings.py)
        self.log_body = getattr(settings, 'API_LOG_BODY', False)
        self.body_max_length = getattr(settings, 'API_LOG_BODY_MAX_LENGTH', 1000)
        self.ignored_paths = getattr(settings, 'API_LOG_IGNORED_PATHS', [
            '/admin',
            '/static',
            '/media',
            '/favicon.ico',
            '/__debug__',
        ])

    def __call__(self, request):
        # Verificar si debemos ignorar esta petición
        if self._should_ignore(request):
            return self.get_response(request)

        # Capturar tiempo de inicio
        start_time = time.time()

        # Log request entrante
        self._log_request(request)

        # Procesar request
        response = self.get_response(request)

        # Calcular tiempo de procesamiento
        duration = time.time() - start_time

        # Log response saliente
        self._log_response(request, response, duration)

        return response

    def _should_ignore(self, request):
        """Determina si debemos ignorar el logging de esta petición"""
        return any(request.path.startswith(path) for path in self.ignored_paths)

    def _get_client_ip(self, request):
        """Obtiene la IP real del cliente considerando proxies y Docker"""
        # Prioridad: X-Forwarded-For (proxies/nginx) > X-Real-IP > REMOTE_ADDR
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Puede venir como: "client_ip, proxy1_ip, proxy2_ip"
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            x_real_ip = request.META.get('HTTP_X_REAL_IP')
            if x_real_ip:
                ip = x_real_ip
            else:
                ip = request.META.get('REMOTE_ADDR', 'unknown')

        # Filtrar IPs de Docker/localhost que no son útiles
        if ip in ['172.17.0.1', '172.18.0.1', '::1', '127.0.0.1']:
            return f'{ip} (Docker/Local)'

        return ip

    def _get_request_body(self, request):
        """Obtiene el body del request si está configurado"""
        if not self.log_body:
            return None

        # Solo loguear body en métodos que lo usan
        if request.method not in ['POST', 'PUT', 'PATCH']:
            return None

        try:
            body = request.body.decode('utf-8')

            # Truncar si es muy largo
            if len(body) > self.body_max_length:
                body = body[:self.body_max_length] + '... [truncado]'

            # Intentar parsear como JSON para mejor formato
            try:
                parsed = json.loads(body)
                # Ocultar campos sensibles
                parsed = self._mask_sensitive_data(parsed)
                return json.dumps(parsed, indent=2)
            except json.JSONDecodeError:
                return body

        except Exception as e:
            return f"[Error leyendo body: {str(e)}]"

    def _mask_sensitive_data(self, data):
        """Enmascara datos sensibles en el body"""
        sensitive_fields = ['password', 'token', 'secret', 'api_key', 'credit_card']

        if isinstance(data, dict):
            return {
                key: '***HIDDEN***' if any(s in key.lower() for s in sensitive_fields) else self._mask_sensitive_data(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        else:
            return data

    def _colorize(self, text, color_name):
        """Aplica color al texto para consola"""
        # En Docker los colores pueden causar problemas, verificar si stdout es un TTY
        import sys
        if not getattr(settings, 'API_LOG_COLORIZE', True):
            return text
        if not sys.stdout.isatty():
            return text  # Sin colores si no es un terminal interactivo
        color = self.COLORS.get(color_name, '')
        reset = self.COLORS['RESET']
        return f"{color}{text}{reset}"

    def _get_status_color(self, status_code):
        """Determina el color según el status code"""
        if 200 <= status_code < 300:
            return 'GREEN'
        elif 300 <= status_code < 400:
            return 'CYAN'
        elif 400 <= status_code < 500:
            return 'YELLOW'
        else:
            return 'RED'

    def _log_request(self, request):
        """Loguea información detallada del request entrante"""
        ip = self._get_client_ip(request)
        user = request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')[:100]

        # Construir mensaje
        method_colored = self._colorize(request.method, 'BOLD')
        path = request.get_full_path()

        logger.info(f"➡️  {method_colored} {path}")
        logger.info(f"    👤 Usuario: {user} | 🌐 IP: {ip}")
        logger.info(f"    🖥️  User-Agent: {user_agent}")

        # Content-Type si existe
        content_type = request.META.get('CONTENT_TYPE')
        if content_type:
            logger.info(f"    📄 Content-Type: {content_type}")

        # Body si está habilitado
        body = self._get_request_body(request)
        if body:
            logger.info(f"    📦 Body:\n{body}")

        logger.info("    " + "-" * 80)

    def _log_response(self, request, response, duration):
        """Loguea información detallada del response saliente"""
        status_color = self._get_status_color(response.status_code)
        status_colored = self._colorize(f"STATUS: {response.status_code}", status_color)

        # Calcular tamaño de respuesta
        response_size = len(response.content) if hasattr(response, 'content') else 0
        size_formatted = self._format_size(response_size)

        # Tiempo formateado
        duration_ms = duration * 1000

        # Determinar nivel de log según status
        log_level = logger.info
        if response.status_code >= 500:
            log_level = logger.error
        elif response.status_code >= 400:
            log_level = logger.warning

        method_colored = self._colorize(request.method, 'BOLD')
        path = request.get_full_path()

        log_level(f"⬅️  {method_colored} {path}")
        log_level(f"    {status_colored} | ⏱️  {duration_ms:.2f}ms | 📊 {size_formatted}")

        # Content-Type de respuesta
        content_type = response.get('Content-Type', 'unknown')
        log_level(f"    📄 Response Type: {content_type}")

        # Advertencia si es lento
        if duration_ms > 1000:
            logger.warning(f"    ⚠️  RESPUESTA LENTA: {duration_ms:.2f}ms")

        log_level("    " + "=" * 80 + "\n")

    def _format_size(self, size_bytes):
        """Formatea el tamaño en bytes a formato legible"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
