# 🚀 DELIBER - Sistema de Delivery

Sistema completo de delivery con Django REST Framework, Celery y PostgreSQL.

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Comandos Disponibles](#-comandos-disponibles)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [URLs Importantes](#-urls-importantes)
- [Troubleshooting](#-troubleshooting)
- [Producción](#-producción)

---

## ✨ Características

- 🔐 **Autenticación JWT** con doble sistema (Web + Mobile)
- 👥 **Multi-rol**: Usuarios, Proveedores, Repartidores, Administradores
- 📦 **Gestión de Pedidos** en tiempo real
- 💳 **Sistema de Pagos** integrado
- 🎟️ **Sistema de Rifas**
- 💬 **Chat en tiempo real**
- 📊 **Reportes completos** para todos los roles
- 🔔 **Notificaciones Push** con Firebase
- 📧 **Envío de emails** con Gmail SMTP
- 🔄 **Tareas asíncronas** con Celery
- 🗄️ **PostgreSQL** como base de datos
- ⚡ **Redis** para caché y Celery
- 🐳 **Dockerizado** completamente

---

## 📦 Requisitos Previos

- **Docker** >= 20.10
- **Docker Compose** >= 2.0
- **Make** (opcional, para comandos útiles)
- **Git**

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <tu-repositorio>
cd deliber
```

### 2. Configurar variables de entorno

```bash
cp backend/.env.example backend/.env
```

Edita `backend/.env` con tus configuraciones.

### 3. Copiar credenciales de Firebase

```bash
# Copia tu archivo de credenciales de Firebase
cp path/to/your/firebase-credentials.json backend/firebase-credentials.json
```

### 4. Construir e iniciar servicios

```bash
# Usando Make (recomendado)
make build
make up

# O usando Docker Compose directamente
docker-compose build
docker-compose up -d
```

---

## ⚙️ Configuración

### Variables de Entorno Principales

```bash
# Django
SECRET_KEY=tu_secret_key_aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.4

# Base de Datos
POSTGRES_DB=deliber_db
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
DB_HOST=postgres
DB_PORT=5432

# Redis
REDIS_PASSWORD=redis123
REDIS_URL=redis://:redis123@redis:6379/0

# Email
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password

# API Keys
API_KEY_WEB=tu_api_key_web
API_KEY_MOBILE=tu_api_key_mobile
```

### Redes Permitidas

```bash
RED_CASA_RANGE=192.168.1.*
RED_INSTITUCIONAL_RANGE=172.16.*.*
RED_HOTSPOT_RANGE=192.168.137.*
```

---

## 🎯 Uso

### Iniciar servicios básicos

```bash
make up
```

### Iniciar con Adminer (gestión de BD)

```bash
make up-dev
```

### Iniciar con Flower (monitoreo de Celery)

```bash
make up-monitor
```

### Iniciar todo (desarrollo completo)

```bash
make up-full
```

### Ver logs

```bash
# Todos los servicios
make logs

# Backend específico
make logs-backend

# Celery worker
make logs-celery
```

### Acceder al shell

```bash
# Bash en backend
make shell

# Django shell
make shell-django

# PostgreSQL shell
make shell-db
```

---

## 🛠️ Comandos Disponibles

### Docker

| Comando | Descripción |
|---------|-------------|
| `make build` | Construir imágenes |
| `make up` | Iniciar servicios |
| `make up-dev` | Iniciar con Adminer |
| `make up-monitor` | Iniciar con Flower |
| `make up-full` | Iniciar todo |
| `make down` | Detener servicios |
| `make restart` | Reiniciar servicios |
| `make status` | Ver estado |

### Desarrollo

| Comando | Descripción |
|---------|-------------|
| `make shell` | Bash en backend |
| `make shell-django` | Django shell |
| `make shell-db` | PostgreSQL shell |
| `make migrate` | Ejecutar migraciones |
| `make makemigrations` | Crear migraciones |
| `make createsuperuser` | Crear superusuario |
| `make collectstatic` | Recolectar estáticos |

### Testing

| Comando | Descripción |
|---------|-------------|
| `make test` | Ejecutar tests |
| `make test-coverage` | Tests con cobertura |

### Celery

| Comando | Descripción |
|---------|-------------|
| `make celery-restart` | Reiniciar Celery |
| `make celery-purge` | Limpiar cola |
| `make celery-inspect` | Inspeccionar tareas |

### Limpieza

| Comando | Descripción |
|---------|-------------|
| `make clean` | Limpiar todo |
| `make clean-containers` | Eliminar contenedores |
| `make clean-volumes` | Eliminar volúmenes |
| `make clean-cache` | Limpiar caché Python |

### Utilidades

| Comando | Descripción |
|---------|-------------|
| `make backup-db` | Backup de BD |
| `make restore-db FILE=backup.sql` | Restaurar BD |
| `make info` | Información del proyecto |
| `make help` | Ver todos los comandos |

---

## 📁 Estructura del Proyecto

```
deliber/
├── backend/
│   ├── settings/                # Configuración Django
│   │   ├── __init__.py
│   │   ├── settings.py          # Settings optimizado
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── authentication/          # Autenticación
│   ├── usuarios/                # Gestión de usuarios
│   ├── proveedores/             # Gestión de proveedores
│   ├── repartidores/            # Gestión de repartidores
│   ├── productos/               # Gestión de productos
│   ├── pedidos/                 # Gestión de pedidos
│   ├── pagos/                   # Sistema de pagos
│   ├── rifas/                   # Sistema de rifas
│   ├── chat/                    # Chat en tiempo real
│   ├── notificaciones/          # Notificaciones push
│   ├── administradores/         # Panel admin
│   ├── reportes/                # Reportes
│   ├── middleware/              # Middlewares custom
│   ├── utils/                   # Utilidades
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── firebase-credentials.json
│   └── .env
├── docker-compose.yml
├── Makefile
├── .dockerignore
└── README.md
```

---

## 🌐 URLs Importantes

### Desarrollo

- **Backend**: http://localhost:8000
- **Admin Django**: http://localhost:8000/admin
- **API Docs**: http://localhost:8000/api/docs (si está configurado)
- **Adminer**: http://localhost:8080 (con profile `dev`)
  - Sistema: PostgreSQL
  - Servidor: postgres
  - Usuario: admin
  - Contraseña: admin123
  - Base de datos: deliber_db
- **Flower**: http://localhost:5555 (con profile `monitoring`)
  - Usuario: admin
  - Contraseña: admin123

### Superusuario por defecto (desarrollo)

- **Email**: admin@deliber.com
- **Contraseña**: admin123

---

## 🐛 Troubleshooting

### El backend no inicia

```bash
# Ver logs
make logs-backend

# Verificar que postgres y redis estén listos
make status

# Reiniciar servicios
make restart
```

### Error de migraciones

```bash
# Entrar al contenedor
make shell

# Ejecutar migraciones manualmente
python manage.py migrate
```

### Celery no procesa tareas

```bash
# Ver logs de Celery
make logs-celery

# Reiniciar Celery
make celery-restart

# Limpiar cola si es necesario
make celery-purge
```

### Error de permisos en media/

```bash
# Desde el host
sudo chown -R 1000:1000 backend/media
sudo chown -R 1000:1000 backend/staticfiles
```

### Limpiar y empezar de cero

```bash
# ADVERTENCIA: Esto eliminará TODOS los datos
make clean
make build
make up
```

### Base de datos corrupta

```bash
# Hacer backup primero (si es posible)
make backup-db

# Eliminar volumen de PostgreSQL
docker volume rm deliber_postgres_data

# Reiniciar
make up
```

---

## 🚀 Producción

### Cambios necesarios para producción

1. **Variables de entorno**:
```bash
DEBUG=False
SECRET_KEY=<genera_uno_nuevo_seguro>
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
```

2. **Passwords**:
- Cambia TODOS los passwords (DB, Redis, API Keys)
- Usa contraseñas fuertes y únicas

3. **Docker Compose**:
- Cambia comando de `runserver` a `gunicorn`
- Configura volúmenes externos
- Usa secrets para credenciales

4. **CORS**:
```bash
CORS_ALLOWED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com
```

5. **SSL/TLS**:
- Configura certificados SSL
- Usa HTTPS en todas las URLs

6. **Backups**:
```bash
# Configurar backups automáticos
crontab -e
0 2 * * * cd /path/to/deliber && make backup-db
```

### Comando de producción

```bash
# Usar gunicorn en lugar de runserver
docker-compose exec backend bash
/app/entrypoint.sh gunicorn
```

---

## 📝 Licencia

[Tu licencia aquí]

---

## 👥 Contribución

[Instrucciones de contribución]

---

## 📞 Contacto

[Tu información de contacto]

---

**¡Gracias por usar DELIBER!** 🎉
