# notificaciones/urls.py
"""
URLs de la API de notificaciones
✅ Router con ViewSet
✅ Endpoints REST estándar
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from notificaciones.views import NotificacionViewSet

# Crear router
router = DefaultRouter()
router.register(r'notificaciones', NotificacionViewSet, basename='notificacion')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]

# Endpoints generados automáticamente:
# GET    /api/notificaciones/                      - Listar notificaciones
# GET    /api/notificaciones/{id}/                 - Detalle de notificación
# POST   /api/notificaciones/{id}/marcar_leida/    - Marcar como leída
# POST   /api/notificaciones/{id}/marcar_no_leida/ - Marcar como no leída
# POST   /api/notificaciones/marcar_varias_leidas/ - Marcar varias como leídas
# GET    /api/notificaciones/no_leidas/            - Solo no leídas
# GET    /api/notificaciones/estadisticas/         - Estadísticas
# DELETE /api/notificaciones/eliminar_antiguas/    - Eliminar antiguas
# POST   /api/notificaciones/test_notificacion/    - Test (solo desarrollo)
