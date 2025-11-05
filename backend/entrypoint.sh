#!/bin/bash
# ==========================================
# ENTRYPOINT: Backend Django + Celery
# ==========================================

set -e  # Exit on error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# ==========================================
# ESPERAR A QUE POSTGRES ESTÉ LISTO
# ==========================================
log "Esperando a PostgreSQL..."

RETRIES=30
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
    >&2 warning "PostgreSQL no disponible - reintentando... ($RETRIES intentos restantes)"
    RETRIES=$((RETRIES - 1))
    if [ $RETRIES -eq 0 ]; then
        error "PostgreSQL no disponible después de 30 intentos"
        exit 1
    fi
    sleep 1
done

log "✓ PostgreSQL está listo!"

# ==========================================
# ESPERAR A QUE REDIS ESTÉ LISTO
# ==========================================
log "Esperando a Redis..."

RETRIES=30
until redis-cli -h redis -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q PONG; do
    >&2 warning "Redis no disponible - reintentando... ($RETRIES intentos restantes)"
    RETRIES=$((RETRIES - 1))
    if [ $RETRIES -eq 0 ]; then
        error "Redis no disponible después de 30 intentos"
        exit 1
    fi
    sleep 1
done

log "✓ Redis está listo!"

# ==========================================
# EJECUTAR SEGÚN EL COMANDO
# ==========================================
case "$1" in
    runserver)
        log "Iniciando Django en modo desarrollo..."
        
        # Ejecutar migraciones
        info "Ejecutando migraciones..."
        python manage.py migrate --noinput
        
        # Recolectar archivos estáticos
        info "Recolectando archivos estáticos..."
        python manage.py collectstatic --noinput --clear
        
        # Crear superusuario si no existe (solo en desarrollo)
        if [ "$DEBUG" = "True" ]; then
            info "Verificando superusuario..."
            python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()

try:
    if not User.objects.filter(email='admin@deliber.com').exists():
        # Intentar crear con username (modelo estándar o personalizado con username)
        try:
            User.objects.create_superuser(
                username='admin',
                email='admin@deliber.com',
                password='admin123',
                first_name='Admin',
                last_name='Deliber'
            )
            print('✓ Superusuario creado: admin@deliber.com / admin123')
        except TypeError:
            # Si falla, intentar sin username (modelo solo con email)
            User.objects.create_superuser(
                email='admin@deliber.com',
                password='admin123',
                first_name='Admin',
                last_name='Deliber'
            )
            print('✓ Superusuario creado (sin username): admin@deliber.com / admin123')
    else:
        print('✓ Superusuario ya existe')
except Exception as e:
    print(f'⚠ Error al crear superusuario: {str(e)}')
    print('Puedes crearlo manualmente con: python manage.py createsuperuser')
EOF
        fi
        
        # Mostrar información de configuración
        echo ""
        echo "=================================================="
        echo "DELIBER - Configuración de Desarrollo"
        echo "=================================================="
        echo "✓ DEBUG: $DEBUG"
        echo "✓ Database: $POSTGRES_DB@$DB_HOST"
        echo "✓ Redis: $REDIS_URL"
        echo "✓ Celery Broker: $CELERY_BROKER_URL"
        echo "✓ API Keys: Configuradas"
        echo "✓ Email: Configurado"
        echo "=================================================="
        echo ""
        
        log "✓ Iniciando servidor Django en 0.0.0.0:8000"
        exec python manage.py runserver 0.0.0.0:8000
        ;;
        
    celery_worker)
        log "Iniciando Celery Worker..."
        exec celery -A settings worker \
            --loglevel=info \
            --concurrency=4 \
            --max-tasks-per-child=1000 \
            --time-limit=1800 \
            --soft-time-limit=1500
        ;;
        
    celery_beat)
        log "Iniciando Celery Beat..."
        
        # Limpiar archivo de schedule antiguo
        rm -f /app/celerybeat-schedule
        
        exec celery -A settings beat \
            --loglevel=info \
            --scheduler django_celery_beat.schedulers:DatabaseScheduler
        ;;
        
    flower)
        log "Iniciando Flower..."
        exec celery -A settings flower \
            --port=5555 \
            --basic_auth="${FLOWER_USER:-admin}:${FLOWER_PASSWORD:-admin123}"
        ;;
        
    gunicorn)
        log "Iniciando Gunicorn (producción)..."
        
        # Ejecutar migraciones
        info "Ejecutando migraciones..."
        python manage.py migrate --noinput
        
        # Recolectar archivos estáticos
        info "Recolectando archivos estáticos..."
        python manage.py collectstatic --noinput --clear
        
        exec gunicorn settings.wsgi:application \
            --bind 0.0.0.0:8000 \
            --workers 4 \
            --threads 2 \
            --worker-class gthread \
            --worker-tmp-dir /dev/shm \
            --max-requests 1000 \
            --max-requests-jitter 50 \
            --timeout 60 \
            --graceful-timeout 30 \
            --access-logfile - \
            --error-logfile - \
            --log-level info
        ;;
        
    test)
        log "Ejecutando tests..."
        exec python manage.py test "${@:2}"
        ;;
        
    shell)
        log "Iniciando Django shell..."
        exec python manage.py shell
        ;;
        
    bash)
        log "Iniciando bash..."
        exec /bin/bash
        ;;
        
    *)
        error "Comando no reconocido: $1"
        echo ""
        echo "Comandos disponibles:"
        echo "  runserver      - Iniciar Django development server"
        echo "  celery_worker  - Iniciar Celery worker"
        echo "  celery_beat    - Iniciar Celery beat"
        echo "  flower         - Iniciar Flower (monitor de Celery)"
        echo "  gunicorn       - Iniciar Gunicorn (producción)"
        echo "  test           - Ejecutar tests"
        echo "  shell          - Django shell"
        echo "  bash           - Bash shell"
        exit 1
        ;;
esac