# ==========================================
# MAKEFILE: Comandos útiles para Deliber
# ==========================================

.PHONY: help build up down restart logs shell migrate test clean

# Colores
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
BLUE=\033[0;34m
NC=\033[0m # No Color

help: ## Mostrar ayuda
	@echo "$(GREEN)╔════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║     DELIBER - Comandos disponibles    ║$(NC)"
	@echo "$(GREEN)╚════════════════════════════════════════╝$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ==========================================
# COMANDOS DOCKER
# ==========================================

build: ## Construir imágenes Docker
	@echo "$(GREEN)🔨 Construyendo imágenes...$(NC)"
	docker-compose build --no-cache

up: ## Iniciar todos los servicios
	@echo "$(GREEN)🚀 Iniciando servicios...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Servicios iniciados$(NC)"
	@echo "  $(BLUE)Backend:$(NC)  http://localhost:8000"
	@echo "  $(BLUE)Admin:$(NC)    http://localhost:8000/admin"
	@echo ""
	@echo "$(YELLOW)💡 Tip: Usa 'make logs' para ver los logs$(NC)"

up-dev: ## Iniciar servicios con Adminer (desarrollo)
	@echo "$(GREEN)🚀 Iniciando servicios (modo desarrollo)...$(NC)"
	docker-compose --profile dev up -d
	@echo "$(GREEN)✓ Servicios iniciados$(NC)"
	@echo "  $(BLUE)Backend:$(NC)  http://localhost:8000"
	@echo "  $(BLUE)Admin:$(NC)    http://localhost:8000/admin"
	@echo "  $(BLUE)Adminer:$(NC)  http://localhost:8080"
	@echo "    Usuario: admin | DB: deliber_db"

up-monitor: ## Iniciar servicios con Flower (monitoreo)
	@echo "$(GREEN)🚀 Iniciando servicios con monitoreo...$(NC)"
	docker-compose --profile monitoring up -d
	@echo "$(GREEN)✓ Servicios iniciados$(NC)"
	@echo "  $(BLUE)Backend:$(NC)  http://localhost:8000"
	@echo "  $(BLUE)Admin:$(NC)    http://localhost:8000/admin"
	@echo "  $(BLUE)Flower:$(NC)   http://localhost:5555"
	@echo "    Usuario: admin | Password: admin123"

up-full: ## Iniciar todos los servicios (dev + monitoring)
	@echo "$(GREEN)🚀 Iniciando todos los servicios...$(NC)"
	docker-compose --profile dev --profile monitoring up -d
	@echo "$(GREEN)✓ Todos los servicios iniciados$(NC)"
	@echo "  $(BLUE)Backend:$(NC)  http://localhost:8000"
	@echo "  $(BLUE)Admin:$(NC)    http://localhost:8000/admin"
	@echo "  $(BLUE)Adminer:$(NC)  http://localhost:8080"
	@echo "  $(BLUE)Flower:$(NC)   http://localhost:5555"

down: ## Detener todos los servicios
	@echo "$(YELLOW)⏹️  Deteniendo servicios...$(NC)"
	docker-compose --profile dev --profile monitoring down

restart: ## Reiniciar todos los servicios
	@echo "$(YELLOW)🔄 Reiniciando servicios...$(NC)"
	docker-compose restart
	@echo "$(GREEN)✓ Servicios reiniciados$(NC)"

stop: ## Detener servicios sin eliminar contenedores
	@echo "$(YELLOW)⏸️  Deteniendo servicios...$(NC)"
	docker-compose stop

# ==========================================
# LOGS Y MONITOREO
# ==========================================

logs: ## Ver logs de todos los servicios
	docker-compose logs -f

logs-backend: ## Ver logs del backend
	docker-compose logs -f backend

logs-celery: ## Ver logs de Celery worker
	docker-compose logs -f celery_worker

logs-beat: ## Ver logs de Celery beat
	docker-compose logs -f celery_beat

logs-db: ## Ver logs de PostgreSQL
	docker-compose logs -f postgres

logs-redis: ## Ver logs de Redis
	docker-compose logs -f redis

status: ## Ver estado de todos los servicios
	@echo "$(BLUE)📊 Estado de los servicios:$(NC)"
	@docker-compose ps

# ==========================================
# DESARROLLO
# ==========================================

shell: ## Abrir shell en el contenedor backend
	@echo "$(BLUE)🐚 Abriendo shell en backend...$(NC)"
	docker-compose exec backend bash

shell-django: ## Abrir Django shell
	@echo "$(BLUE)🐍 Abriendo Django shell...$(NC)"
	docker-compose exec backend python manage.py shell

shell-db: ## Abrir shell de PostgreSQL
	@echo "$(BLUE)🗄️  Abriendo PostgreSQL shell...$(NC)"
	docker-compose exec postgres psql -U admin -d deliber_db

migrate: ## Ejecutar migraciones
	@echo "$(GREEN)📦 Ejecutando migraciones...$(NC)"
	docker-compose exec backend python manage.py migrate

makemigrations: ## Crear nuevas migraciones
	@echo "$(GREEN)📝 Creando migraciones...$(NC)"
	docker-compose exec backend python manage.py makemigrations

createsuperuser: ## Crear superusuario
	@echo "$(BLUE)👤 Creando superusuario...$(NC)"
	docker-compose exec backend python manage.py createsuperuser

collectstatic: ## Recolectar archivos estáticos
	@echo "$(GREEN)📁 Recolectando archivos estáticos...$(NC)"
	docker-compose exec backend python manage.py collectstatic --noinput

# ==========================================
# TESTING
# ==========================================

test: ## Ejecutar tests
	@echo "$(BLUE)🧪 Ejecutando tests...$(NC)"
	docker-compose exec backend python manage.py test

test-coverage: ## Ejecutar tests con cobertura
	@echo "$(BLUE)🧪 Ejecutando tests con cobertura...$(NC)"
	docker-compose exec backend coverage run --source='.' manage.py test
	docker-compose exec backend coverage report
	docker-compose exec backend coverage html
	@echo "$(GREEN)✓ Reporte de cobertura generado en htmlcov/index.html$(NC)"

# ==========================================
# CELERY
# ==========================================

celery-restart: ## Reiniciar Celery worker y beat
	@echo "$(YELLOW)🔄 Reiniciando Celery...$(NC)"
	docker-compose restart celery_worker celery_beat
	@echo "$(GREEN)✓ Celery reiniciado$(NC)"

celery-purge: ## Limpiar cola de Celery
	@echo "$(RED)🗑️  Limpiando cola de Celery...$(NC)"
	docker-compose exec backend celery -A settings purge -f
	@echo "$(GREEN)✓ Cola limpiada$(NC)"

celery-inspect: ## Inspeccionar tareas activas
	@echo "$(BLUE)🔍 Inspeccionando tareas de Celery...$(NC)"
	docker-compose exec backend celery -A settings inspect active

# ==========================================
# LIMPIEZA
# ==========================================

clean: ## Limpiar contenedores, volúmenes y cache
	@echo "$(RED)🧹 Limpiando contenedores y volúmenes...$(NC)"
	docker-compose down -v
	@echo "$(GREEN)✓ Limpieza completa$(NC)"

clean-containers: ## Eliminar solo contenedores
	@echo "$(RED)🗑️  Eliminando contenedores...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Contenedores eliminados$(NC)"

clean-volumes: ## Eliminar volúmenes de datos
	@echo "$(RED)⚠️  ADVERTENCIA: Esto eliminará TODOS los datos$(NC)"
	@read -p "¿Estás seguro? [y/N]: " confirm && [ "$$confirm" = "y" ] || exit 1
	docker volume rm deliber_postgres_data deliber_redis_data deliber_media_data deliber_static_data 2>/dev/null || true
	@echo "$(GREEN)✓ Volúmenes eliminados$(NC)"

clean-cache: ## Limpiar caché de Python
	@echo "$(YELLOW)🧹 Limpiando caché de Python...$(NC)"
	find ./backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find ./backend -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Caché limpiado$(NC)"

# ==========================================
# UTILIDADES
# ==========================================

ps: ## Listar contenedores activos
	docker-compose ps

rebuild: ## Reconstruir y reiniciar servicios
	@echo "$(YELLOW)🔨 Reconstruyendo servicios...$(NC)"
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "$(GREEN)✓ Servicios reconstruidos$(NC)"

backup-db: ## Backup de la base de datos
	@echo "$(BLUE)💾 Creando backup de la base de datos...$(NC)"
	@mkdir -p backups
	docker-compose exec -T postgres pg_dump -U admin deliber_db > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Backup creado en backups/$(NC)"

restore-db: ## Restaurar base de datos (uso: make restore-db FILE=backup.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Error: Especifica el archivo con FILE=backup.sql$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)⚠️  Restaurando base de datos desde $(FILE)...$(NC)"
	docker-compose exec -T postgres psql -U admin -d deliber_db < $(FILE)
	@echo "$(GREEN)✓ Base de datos restaurada$(NC)"

# ==========================================
# INFORMACIÓN
# ==========================================

info: ## Mostrar información del proyecto
	@echo "$(BLUE)╔════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║        DELIBER - Información          ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Servicios disponibles:$(NC)"
	@echo "  • Backend Django (Puerto 8000)"
	@echo "  • PostgreSQL (Puerto 5432)"
	@echo "  • Redis (Puerto 6379)"
	@echo "  • Celery Worker + Beat"
	@echo "  • Flower - Monitoreo (Puerto 5555) [profile: monitoring]"
	@echo "  • Adminer - Admin DB (Puerto 8080) [profile: dev]"
	@echo ""
	@echo "$(YELLOW)Comandos útiles:$(NC)"
	@echo "  make up          - Iniciar servicios básicos"
	@echo "  make up-dev      - Iniciar con Adminer"
	@echo "  make up-monitor  - Iniciar con Flower"
	@echo "  make up-full     - Iniciar todo"
	@echo "  make logs        - Ver logs"
	@echo "  make shell       - Bash en backend"
	@echo ""