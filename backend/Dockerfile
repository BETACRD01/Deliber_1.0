# ==========================================
# DOCKERFILE: Backend Django + Celery
# ==========================================

FROM python:3.11-slim AS base

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

# Limpiar caché y actualizar índices
RUN apt-get clean && rm -rf /var/lib/apt/lists/* && apt-get update --fix-missing

# Instalar dependencias del sistema necesarias
RUN apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq-dev \
    gcc \
    g++ \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff-dev \
    bash \
    curl \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

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
RUN groupadd -g 1000 appuser && \
    useradd -d /app -s /sbin/nologin -c "App user" -u 1000 -g 1000 appuser

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