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

# Funciones de logging
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
# ESPERAR A POSTGRESQL (OPTIMIZADO)
# ==========================================
log "Esperando a PostgreSQL..."

RETRIES=30
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
    RETRIES=$((RETRIES - 1))
    if [ $RETRIES -eq 0 ]; then
        warning "PostgreSQL no responde después de 30 intentos"
        break
    fi
    warning "PostgreSQL no disponible - reintentando... ($RETRIES intentos restantes)"
    sleep 1
done

log "✓ PostgreSQL check completado!"

# ==========================================
# ESPERAR A REDIS (OPTIMIZADO - REDUCIDO)
# ==========================================
log "Esperando a Redis..."

RETRIES=20
until redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q PONG; do
    RETRIES=$((RETRIES - 1))
    if [ $RETRIES -eq 0 ]; then
        warning "Redis no responde, pero continuando de todas formas..."
        break
    fi
    warning "Redis no disponible - reintentando... ($RETRIES intentos restantes)"
    sleep 1
done

log "✓ Redis check completado!"

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
        python manage.py collectstatic --noinput --clear 2>&1 | grep -E "(Deleted|copied)" | tail -5 || true
        
        # Crear superusuario si no existe
        if [ "$DEBUG" = "True" ]; then
            info "Verificando superusuario..."
            python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()

try:
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@deliber.com',
            password='admin123'
        )
        print('✓ Superusuario creado')
    else:
        print('✓ Superusuario ya existe')
except Exception as e:
    print(f'⚠ Error al crear superusuario: {str(e)}')
EOF
        fi
        
        # Mostrar información de configuración
        echo ""
        echo "============================================================"
        echo "DELIBER - Configuración de Desarrollo"
        echo "============================================================"
        echo "✓ DEBUG: $DEBUG"
        echo "✓ Database: $POSTGRES_DB@$DB_HOST"
        echo "✓ Redis: $REDIS_HOST:$REDIS_PORT"
        echo "✓ Celery Broker: redis://$REDIS_HOST:$REDIS_PORT/0"
        echo "✓ Backend: http://0.0.0.0:8000"
        echo "============================================================"
        echo ""
        
        log "✓ Iniciando servidor Django en 0.0.0.0:8000"
        exec python manage.py runserver 0.0.0.0:8000
        ;;
        
    celery_worker)
        log "Iniciando Celery Worker..."
        exec celery -A settings worker \
            --loglevel=info \
            --concurrency=2 \
            --max-tasks-per-child=1000 \
            --time-limit=1800 \
            --soft-time-limit=1500
        ;;
        
    celery_beat)
        log "Iniciando Celery Beat..."
        
        # Limpiar archivos de schedule anteriores (soporta tanto archivos como directorios)
        if [ -e /app/celerybeat-schedule ]; then
            rm -rf /app/celerybeat-schedule
            info "✓ Limpiado schedule anterior"
        fi
        
        # Crear directorio para datos de celery beat si no existe
        mkdir -p /app/celerybeat-data
        
        exec celery -A settings beat \
            --loglevel=info \
            --schedule=/app/celerybeat-data/celerybeat-schedule.db \
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
        
        info "Ejecutando migraciones..."
        python manage.py migrate --noinput
        
        info "Recolectando archivos estáticos..."
        python manage.py collectstatic --noinput --clear 2>&1 | tail -2 || true
        
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