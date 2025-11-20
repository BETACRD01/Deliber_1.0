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
logger = logging.getLogger(__name__)

# ==========================================
# DETECCION DE RED
# ==========================================
try:
    from utils.network_detector import NetworkDetector, obtener_config_red
    NETWORK_DETECTION_ENABLED = True
    CONFIG_RED = obtener_config_red()
except ImportError:
    NETWORK_DETECTION_ENABLED = False
    CONFIG_RED = None
    print("⚠️ network_detector no disponible")

def get_env_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ("true", "1", "yes")

def get_env_list(key: str, default: str = "") -> list:
    value = os.getenv(key, default)
    return [item.strip() for item in value.split(",") if item.strip()]

# ==========================================
# CONFIGURACION BASICA
# ==========================================
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = get_env_bool("DEBUG", True)

if NETWORK_DETECTION_ENABLED and CONFIG_RED:
    ALLOWED_HOSTS = NetworkDetector.obtener_allowed_hosts(CONFIG_RED)
else:
    ALLOWED_HOSTS = get_env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
    ALLOWED_HOSTS.extend(["0.0.0.0", "10.0.2.2", "*.local", "backend"])

# ==========================================
# FRONTEND URLS (ESTRATEGIA DUAL: WEB + MÓVIL)
# ==========================================

# 1. URL WEB (Para Administradores)
env_web = os.getenv("FRONTEND_WEB_URL", "")
if env_web:
    FRONTEND_WEB_URL = env_web
elif NETWORK_DETECTION_ENABLED and CONFIG_RED:
    FRONTEND_WEB_URL = NetworkDetector.obtener_frontend_url(
        CONFIG_RED, puerto=5173
    )
else:
    FRONTEND_WEB_URL = "http://localhost:5173"

# 2. URL MÓVIL (Para Usuarios App)
# Deep Link por defecto
FRONTEND_MOBILE_URL = os.getenv("FRONTEND_MOBILE_URL", "jpexpress://app")

# 3. URL FALLBACK (Por defecto usamos Web)
FRONTEND_URL = FRONTEND_WEB_URL

# ==========================================
# APLICACIONES
# ==========================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "django_celery_beat",
    "django_celery_results",
    "django_redis",
    "django_filters",
    'phonenumber_field',
    # Apps Locales
    "authentication.apps.AuthenticationConfig",
    "usuarios.apps.UsuariosConfig",
    "proveedores.apps.ProveedoresConfig",
    "repartidores.apps.RepartidoresConfig",
    "productos.apps.ProductosConfig",
    "pedidos.apps.PedidosConfig",
    "pagos.apps.PagosConfig",
    "rifas.apps.RifasConfig",
    "chat.apps.ChatConfig",
    "notificaciones.apps.NotificacionesConfig",
    "administradores.apps.AdministradoresConfig",
    "reportes.apps.ReportesConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "middleware.api_key_auth.ApiKeyAuthenticationMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "middleware.log_api_requests.LogAPIRequestsMiddleware",
]

ROOT_URLCONF = "settings.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "settings.wsgi.application"

# ==========================================
# DATABASE & CACHE
# ==========================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 600, # Persistencia
    }
}

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "deliber",
    }
}

# ==========================================
# CELERY
# ==========================================
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Guayaquil"

# ==========================================
# AUTH & SEGURIDAD
# ==========================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

if DEBUG:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
else:
    PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.Argon2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]

AUTH_USER_MODEL = "authentication.User"
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Guayaquil"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==========================================
# ALLAUTH & EMAIL
# ==========================================
SITE_ID = 1
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_UNIQUE_EMAIL = True

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = get_env_bool("EMAIL_USE_TLS", True)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

# ==========================================
# DRF & JWT
# ==========================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
}

if not DEBUG:
    REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ]
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
        "user": "5000/hour",
        "anon": "100/hour",
        "login": "10/minute",
        "register": "5/hour",
    }

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24 if DEBUG else 2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": "Bearer",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ==========================================
# CORS & CSRF
# ==========================================
CORS_ALLOW_ALL_ORIGINS = DEBUG
if not DEBUG:
    if NETWORK_DETECTION_ENABLED and CONFIG_RED:
        CORS_ALLOWED_ORIGINS = NetworkDetector.obtener_cors_origins(CONFIG_RED, 8000)
    else:
        CORS_ALLOWED_ORIGINS = get_env_list("CORS_ALLOWED_ORIGINS", "https://jpexpress.com")

    if NETWORK_DETECTION_ENABLED and CONFIG_RED:
        CSRF_TRUSTED_ORIGINS = NetworkDetector.obtener_cors_origins(CONFIG_RED, 8000)
    else:
        CSRF_TRUSTED_ORIGINS = get_env_list("CSRF_TRUSTED_ORIGINS", "https://jpexpress.com")
else:
    # Orígenes de desarrollo
    CORS_ALLOWED_ORIGINS = get_env_list(
        "CORS_ALLOWED_ORIGINS", 
        "http://localhost:5173,http://127.0.0.1:5173,http://192.168.1.22:5173"
    )
    CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

CORS_ALLOW_CREDENTIALS = True

# ==========================================
# LOGGING
# ==========================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
        },
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "authentication": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# ==========================================
# STARTUP LOG
# ==========================================
if "runserver" in sys.argv or "run_gunicorn" in sys.argv:
    if not DEBUG:
        print(f"✅ WEB ADMIN: {FRONTEND_WEB_URL}")
        print(f"📱 MOBILE APP: {FRONTEND_MOBILE_URL}")