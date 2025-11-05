from pathlib import Path
from datetime import timedelta
import os
import sys
import logging
from dotenv import load_dotenv

# ==========================================
# INICIALIZACION
# ==========================================
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

# Logger para configuracion
logger = logging.getLogger(__name__)

# ==========================================
# DETECCION DE RED (ANTES DE TODO)
# ==========================================
try:
    from utils.network_detector import NetworkDetector, obtener_config_red
    NETWORK_DETECTION_ENABLED = True
    CONFIG_RED = obtener_config_red()
except ImportError:
    NETWORK_DETECTION_ENABLED = False
    CONFIG_RED = None
    print("⚠️ network_detector no disponible, usando configuracion estatica del .env")

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_env_bool(key: str, default: bool = False) -> bool:
    """Convierte variable de entorno a boolean"""
    return os.getenv(key, str(default)).lower() in ('true', '1', 'yes')

def get_env_list(key: str, default: str = '') -> list:
    """Convierte variable de entorno separada por comas a lista"""
    value = os.getenv(key, default)
    return [item.strip() for item in value.split(',') if item.strip()]

def validate_required_env(*keys):
    """Valida que las variables de entorno requeridas existan"""
    missing = [key for key in keys if not os.getenv(key)]
    if missing:
        raise EnvironmentError(f"Variables de entorno faltantes: {', '.join(missing)}")

# ==========================================
# VALIDACION DE VARIABLES CRITICAS
# ==========================================
validate_required_env('SECRET_KEY', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD')

# ==========================================
# CONFIGURACION BASICA
# ==========================================
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = get_env_bool('DEBUG', True)

# ==========================================
# ALLOWED_HOSTS DINAMICO
# ==========================================
if NETWORK_DETECTION_ENABLED and CONFIG_RED:
    ALLOWED_HOSTS = NetworkDetector.obtener_allowed_hosts(CONFIG_RED)
    logger.info(f"✅ ALLOWED_HOSTS configurado automaticamente para red: {CONFIG_RED['nombre']}")
    logger.info(f"   Total hosts permitidos: {len(ALLOWED_HOSTS)}")
else:
    ALLOWED_HOSTS = get_env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1')
    ALLOWED_HOSTS.extend(['0.0.0.0', '10.0.2.2', '*.local', 'backend'])
    logger.warning("⚠️ Usando ALLOWED_HOSTS estatico desde .env")

# ==========================================
# FRONTEND_URL DINAMICO
# ==========================================
if NETWORK_DETECTION_ENABLED and CONFIG_RED:
    FRONTEND_URL = NetworkDetector.obtener_frontend_url(
        CONFIG_RED, 
        puerto=int(os.getenv('BACKEND_PORT', 8000))
    )
    logger.info(f"✅ FRONTEND_URL: {FRONTEND_URL}")
else:
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:8000')

# ==========================================
# APLICACIONES INSTALADAS
# ==========================================
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'django_celery_beat',
    'django_celery_results',
    'django_redis',
    'django_filters',
]

LOCAL_APPS = [
    'authentication.apps.AuthenticationConfig',
    'usuarios.apps.UsuariosConfig',
    'proveedores.apps.ProveedoresConfig',
    'repartidores.apps.RepartidoresConfig',
    'productos.apps.ProductosConfig',
    'pedidos.apps.PedidosConfig',
    'pagos.apps.PagosConfig',
    'rifas.apps.RifasConfig',
    'chat.apps.ChatConfig',
    'notificaciones.apps.NotificacionesConfig',
    'administradores.apps.AdministradoresConfig',
    'reportes.apps.ReportesConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ==========================================
# MIDDLEWARE
# ==========================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'middleware.api_key_auth.ApiKeyAuthenticationMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'middleware.log_api_requests.LogAPIRequestsMiddleware',
]

ROOT_URLCONF = 'settings.urls'

# ==========================================
# TEMPLATES
# ==========================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'settings.wsgi.application'

# ==========================================
# DATABASE
# ==========================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# ==========================================
# CACHE (REDIS)
# ==========================================
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/1')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': REDIS_PASSWORD,
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
        },
        'KEY_PREFIX': 'deliber',
        'TIMEOUT': 300,
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ==========================================
# CELERY CONFIGURATION
# ==========================================
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Guayaquil'
CELERY_ENABLE_UTC = True

CELERY_RESULT_EXPIRES = 86400
CELERY_RESULT_BACKEND_MAX_RETRIES = 10
CELERY_RESULT_BACKEND_ALWAYS_RETRY = True

CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 1800
CELERY_TASK_SOFT_TIME_LIMIT = 1500
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True

CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_DISABLE_RATE_LIMITS = False

CELERY_TASK_DEFAULT_RETRY_DELAY = 60
CELERY_TASK_MAX_RETRIES = 3

CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_WORKER_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
CELERY_WORKER_TASK_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s'

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10

CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_DEFAULT_EXCHANGE = 'default'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'default'

CELERY_SEND_TASK_SENT_EVENT = True
CELERY_SEND_EVENTS = True

# ==========================================
# AUTENTICACION Y SEGURIDAD
# ==========================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

AUTH_USER_MODEL = 'authentication.User'

# ==========================================
# INTERNACIONALIZACION
# ==========================================
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True

# ==========================================
# ARCHIVOS ESTATICOS Y MEDIA
# ==========================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

try:
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f'⚠️ No se pudo crear directorio media: {e}')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==========================================
# DJANGO ALLAUTH
# ==========================================
SITE_ID = 1

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_UNIQUE_EMAIL = True
SOCIALACCOUNT_AUTO_SIGNUP = True

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
            'key': ''
        }
    }
}

GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')

# ==========================================
# EMAIL CONFIGURATION
# ==========================================
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = get_env_bool('EMAIL_USE_TLS', True)
EMAIL_USE_SSL = get_env_bool('EMAIL_USE_SSL', False)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# ==========================================
# REST FRAMEWORK
# ==========================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
}

if not DEBUG:
    REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ]
    REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
        'user': '1000/hour',
        'anon': '100/hour',
        'login': '10/minute',
        'register': '5/hour',
        'upload': '50/hour',
        'fcm': '50/hour',
    }
else:
    REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
    REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}

# ==========================================
# JWT CONFIGURATION (MEJORADO)
# ==========================================
SIMPLE_JWT = {
    # ✅ CAMBIO PRINCIPAL: Aumentar tiempo de vida
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),  # 12 horas (antes 30 min)
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),   # 30 días (antes 7)
    
    # ✅ NUEVO: Configuración para refresh automático
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    # Configuración de seguridad
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    # ✅ NUEVO: Agregar claims personalizados útiles para el cliente
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    # ✅ NUEVO: Configuración de tokens
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    
    # ✅ NUEVO: Claims adicionales en el token
    'TOKEN_OBTAIN_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenObtainPairSerializer',
    'TOKEN_REFRESH_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenRefreshSerializer',
    'TOKEN_VERIFY_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenVerifySerializer',
    'TOKEN_BLACKLIST_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenBlacklistSerializer',
    
    # ✅ NUEVO: Sliding tokens (opcional, deshabilitado por ahora)
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(hours=12),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=30),
}

# ✅ NUEVO: Configuración para desarrollo
if DEBUG:
    # En desarrollo, tokens más largos para facilitar testing
    SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(hours=24)  # 24 horas
    logger.info("🔧 JWT: Modo DEBUG - Tokens de 24 horas")
else:
    # En producción, tokens más cortos por seguridad
    SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(hours=2)  # 2 horas
    logger.info("🔐 JWT: Modo PRODUCCIÓN - Tokens de 2 horas")

# ==========================================
# CORS CONFIGURATION
# ==========================================
CORS_ALLOW_ALL_ORIGINS = DEBUG

if not DEBUG:
    if NETWORK_DETECTION_ENABLED and CONFIG_RED:
        CORS_ALLOWED_ORIGINS = NetworkDetector.obtener_cors_origins(
            CONFIG_RED,
            puerto=int(os.getenv('BACKEND_PORT', 8000))
        )
        logger.info(f"✅ CORS_ALLOWED_ORIGINS: {len(CORS_ALLOWED_ORIGINS)} origenes en produccion")
    else:
        CORS_ALLOWED_ORIGINS = get_env_list(
            'CORS_ALLOWED_ORIGINS', 
            'https://api.jpexpress.com,https://jpexpress.com'
        )

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-api-key',
]

# ==========================================
# CSRF_TRUSTED_ORIGINS DINAMICO
# ==========================================
if NETWORK_DETECTION_ENABLED and CONFIG_RED:
    CSRF_TRUSTED_ORIGINS = NetworkDetector.obtener_cors_origins(
        CONFIG_RED, 
        puerto=int(os.getenv('BACKEND_PORT', 8000))
    )
    logger.info(f"✅ CSRF_TRUSTED_ORIGINS: {len(CSRF_TRUSTED_ORIGINS)} origenes configurados")
else:
    CSRF_TRUSTED_ORIGINS = get_env_list(
        'CSRF_TRUSTED_ORIGINS', 
        'http://localhost:8000,http://127.0.0.1:8000'
    )
    logger.warning("⚠️ Usando CSRF_TRUSTED_ORIGINS estatico desde .env")

# ==========================================
# API LOGGING MIDDLEWARE
# ==========================================
API_LOG_BODY = DEBUG
API_LOG_BODY_MAX_LENGTH = 1000
API_LOG_COLORIZE = True
API_LOG_IGNORED_PATHS = ['/admin', '/static', '/media', '/favicon.ico', '/__debug__', '/health', '/metrics']

# ==========================================
# LOGGING CONFIGURATION
# ==========================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'INFO',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'api_logger': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# ==========================================
# SECURITY SETTINGS (PRODUCCION)
# ==========================================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ==========================================
# RATE LIMITING
# ==========================================
ENABLE_LOGIN_BLOCKING = not DEBUG

if DEBUG:
    RATE_LIMIT_CONFIG = {
        'LOGIN_ATTEMPTS': 10,
        'LOGIN_WINDOW': 60,
        'BURST_REQUESTS': 30,
        'BURST_WINDOW': 10,
        'RESET_PASSWORD': 5,
        'RESET_PASSWORD_WINDOW': 3600,
    }
else:
    RATE_LIMIT_CONFIG = {
        'LOGIN_ATTEMPTS': 5,
        'LOGIN_WINDOW': 60,
        'BURST_REQUESTS': 10,
        'BURST_WINDOW': 10,
        'RESET_PASSWORD': 3,
        'RESET_PASSWORD_WINDOW': 3600,
    }

RATE_LIMIT_LOGIN_ATTEMPTS = RATE_LIMIT_CONFIG['LOGIN_ATTEMPTS']
RATE_LIMIT_LOGIN_WINDOW = RATE_LIMIT_CONFIG['LOGIN_WINDOW']
RATE_LIMIT_BURST_REQUESTS = RATE_LIMIT_CONFIG['BURST_REQUESTS']
RATE_LIMIT_BURST_WINDOW = RATE_LIMIT_CONFIG['BURST_WINDOW']
RATE_LIMIT_RESET_PASSWORD = RATE_LIMIT_CONFIG['RESET_PASSWORD']
RATE_LIMIT_RESET_PASSWORD_WINDOW = RATE_LIMIT_CONFIG['RESET_PASSWORD_WINDOW']

RATE_LIMIT_MESSAGES = {
    'login': 'Demasiados intentos de inicio de sesion. Por favor espera {tiempo} segundos.',
    'burst': 'Detectamos actividad sospechosa. Por favor espera un momento.',
    'reset_password': 'Has alcanzado el limite de solicitudes. Intenta mas tarde.',
}

# ==========================================
# FIREBASE (LAZY LOADING)
# ==========================================
FIREBASE_CREDENTIALS_PATH = BASE_DIR / 'firebase-credentials.json'

def initialize_firebase():
    """Inicializa Firebase solo cuando se necesita"""
    if not FIREBASE_CREDENTIALS_PATH.exists():
        print('⚠️ Firebase credentials no encontrado')
        return False
    
    try:
        from utils.firebase_service import FirebaseService
        if FirebaseService.initialize():
            print('✅ Firebase: Notificaciones Push ACTIVAS')
            return True
        else:
            print('⚠️ Firebase: Notificaciones Push DESACTIVADAS')
            return False
    except ImportError:
        print('⚠️ firebase_service no encontrado')
        return False
    except Exception as e:
        print(f'❌ Error al inicializar Firebase: {e}')
        return False

# ==========================================
# API KEYS VALIDATION
# ==========================================
API_KEY_WEB = os.getenv('API_KEY_WEB', '')
API_KEY_MOBILE = os.getenv('API_KEY_MOBILE', '')

# ==========================================
# STARTUP INFO
# ==========================================
def log_startup_info():
    """Muestra informacion de inicio solo una vez"""
    if not DEBUG:
        return
    
    print('=' * 70)
    print('DELIBER - Configuracion de Desarrollo')
    print('=' * 70)
    print(f'✅ DEBUG: {DEBUG}')
    
    if NETWORK_DETECTION_ENABLED and CONFIG_RED:
        print(f'✅ Red detectada: {CONFIG_RED["nombre"]} ({CONFIG_RED.get("modo", "AUTO")})')
        print(f'✅ IP Servidor: {CONFIG_RED["ip_servidor"]}')
        print(f'✅ ALLOWED_HOSTS: {len(ALLOWED_HOSTS)} hosts configurados')
    else:
        print('⚠️  Deteccion de red: Deshabilitada')
    
    print(f'✅ Database: {DATABASES["default"]["NAME"]}@{DATABASES["default"]["HOST"]}')
    print(f'✅ Redis: {REDIS_URL}')
    print(f'✅ Celery Broker: {CELERY_BROKER_URL}')
    print(f'✅ Frontend URL: {FRONTEND_URL}')
    
    if API_KEY_WEB and API_KEY_MOBILE:
        print('✅ API Keys: Configuradas')
    else:
        print('⚠️  API Keys: No configuradas')
    
    if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
        print('⚠️  Email: No configurado')
    else:
        print('✅ Email: Configurado')
    
    print('=' * 70)

# Ejecutar solo si no es un comando de Django
if 'runserver' in sys.argv or 'run_gunicorn' in sys.argv:
    log_startup_info()