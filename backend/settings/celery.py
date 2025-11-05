# settings/celery.py
"""
Configuración de Celery para el proyecto.

Este archivo configura Celery como la cola de tareas asíncronas
del proyecto Django, utilizando Redis como broker.

IMPORTANTE: Las tareas programadas se gestionan desde Django Admin
usando django-celery-beat (DatabaseScheduler).

Para ejecutar:
--------------
# Worker (procesa tareas)
celery -A settings worker -l info

# Beat (tareas programadas desde DB)
celery -A settings beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Ambos juntos
celery -A settings worker -B -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# En Docker (ya configurado en docker-compose.yml):
docker-compose up -d celery_worker celery_beat
"""
import os
from celery import Celery

# Establecer el módulo de configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')

# Crear la aplicación de Celery
app = Celery('deliber')

# Cargar configuración desde Django settings con namespace 'CELERY'
# Esto significa que todas las configuraciones de Celery en settings.py
# deben tener el prefijo CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodescubrir tareas en todas las apps instaladas
# Busca archivos tasks.py en cada app
app.autodiscover_tasks()

# Asegurar que la app esté finalizada
app.finalize()


# ==========================================================
# 📅 TAREAS PROGRAMADAS (DJANGO-CELERY-BEAT)
# ==========================================================
# NOTA: Las tareas programadas se gestionan desde Django Admin
# en la sección "Periodic Tasks" de django-celery-beat.
#
# Para crear tareas programadas:
# 1. Ir a Django Admin > Periodic Tasks
# 2. Crear un nuevo "Interval" o "Crontab" schedule
# 3. Crear una nueva "Periodic Task" asociándola al schedule
#
# Ventajas de usar DatabaseScheduler:
# - ✅ Gestión visual desde Django Admin
# - ✅ No requiere reiniciar servicios al cambiar horarios
# - ✅ Historial de ejecuciones
# - ✅ Habilitar/deshabilitar tareas sin código
# ==========================================================


# ==========================================================
# ⚙️ CONFIGURACIÓN ADICIONAL DE CELERY
# ==========================================================

# Configuración de tiempo de espera
app.conf.task_soft_time_limit = 60 * 5  # 5 minutos soft limit
app.conf.task_time_limit = 60 * 10      # 10 minutos hard limit

# Configuración de reintentos
app.conf.task_default_retry_delay = 60    # 1 minuto entre reintentos
app.conf.task_max_retries = 3             # Máximo 3 reintentos

# Configuración de resultados
app.conf.result_expires = 60 * 60 * 24   # Los resultados expiran en 24 horas

# Serialización
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

# Zona horaria
app.conf.timezone = 'America/Guayaquil'
app.conf.enable_utc = True

# Optimizaciones
app.conf.worker_prefetch_multiplier = 4
app.conf.worker_max_tasks_per_child = 1000

# Logging
app.conf.worker_hijack_root_logger = False
app.conf.worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
app.conf.worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s'


# ==========================================================
# 🔍 TAREA DE PRUEBA
# ==========================================================
@app.task(bind=True, name='debug_task')
def debug_task(self):
    """
    Tarea de prueba para verificar que Celery está funcionando.

    Uso en Django Shell:
    >>> from settings.celery import debug_task
    >>> result = debug_task.delay()
    >>> print(result.get())

    Uso en Docker:
    docker-compose exec backend python manage.py shell
    >>> from settings.celery import debug_task
    >>> debug_task.delay()
    """
    print(f'Request: {self.request!r}')
    return {
        'status': 'success',
        'message': 'Celery está funcionando correctamente',
        'worker_id': self.request.id,
        'timezone': app.conf.timezone,
    }


# ==========================================================
# 📊 SEÑALES DE CELERY (OPCIONAL)
# ==========================================================
import logging

logger = logging.getLogger('celery')

try:
    from celery.signals import task_prerun, task_postrun, task_failure

    @task_prerun.connect
    def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
        """Se ejecuta antes de cada tarea"""
        if task:
            logger.info(f'🚀 Iniciando tarea: {task.name} [ID: {task_id}]')


    @task_postrun.connect
    def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, **extra):
        """Se ejecuta después de cada tarea"""
        if task:
            logger.info(f'✅ Tarea completada: {task.name} [ID: {task_id}]')


    @task_failure.connect
    def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **extra):
        """Se ejecuta cuando una tarea falla"""
        if sender:
            logger.error(
                f'❌ Tarea fallida: {sender.name} [ID: {task_id}]\n'
                f'Error: {exception}\n'
                f'Traceback: {traceback}'
            )

except ImportError:
    logger.warning('⚠️ No se pudieron importar las señales de Celery')


# ==========================================================
# 📝 EJEMPLO DE TAREAS PERSONALIZADAS
# ==========================================================
# Crea estas tareas en tus apps (ej: pedidos/tasks.py)
#
# from celery import shared_task
#
# @shared_task(name='pedidos.verificar_pedidos_retrasados')
# def verificar_pedidos_retrasados():
#     """Verifica pedidos retrasados"""
#     # Tu lógica aquí
#     pass
#
# Luego créalas en Django Admin > Periodic Tasks
# ==========================================================


if __name__ == '__main__':
    app.start()
