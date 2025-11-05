# ==========================================
# DOCKERFILE: Backend Django + Celery
# ==========================================

FROM python:3.11-alpine AS base

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Directorio de trabajo
WORKDIR /app

# ==========================================
# STAGE 1: Dependencias del sistema
# ==========================================
FROM base AS dependencies

# Instalar dependencias del sistema necesarias
RUN apk add --no-cache \
    # PostgreSQL
    postgresql-dev \
    postgresql-client \
    # Compiladores
    gcc \
    g++ \
    python3-dev \
    musl-dev \
    linux-headers \
    libffi-dev \
    # Pillow (imágenes)
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev \
    # Utilidades
    bash \
    curl \
    redis \
    git

# ==========================================
# STAGE 2: Instalación de Python packages
# ==========================================
FROM dependencies AS builder

# Copiar solo requirements para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ==========================================
# STAGE 3: Imagen final
# ==========================================
FROM dependencies AS final

# Copiar dependencias instaladas desde builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Crear usuario no-root para seguridad
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

# Crear directorios necesarios
RUN mkdir -p /app/media /app/staticfiles /app/logs && \
    chown -R appuser:appuser /app

# Copiar el código del proyecto
COPY --chown=appuser:appuser . .

# Copiar entrypoint
COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Cambiar a usuario no-root
USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/admin/login/', timeout=5)" || exit 1

# Exponer puerto
EXPOSE 8000

# Entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Comando por defecto (puede ser sobreescrito)
CMD ["runserver"]