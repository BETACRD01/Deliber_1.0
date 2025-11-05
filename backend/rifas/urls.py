# -*- coding: utf-8 -*-
# rifas/urls.py
"""
URLs para API REST de Rifas

✅ ENDPOINTS DISPONIBLES:

RIFAS:
- GET    /api/rifas/                        - Listar todas las rifas
- GET    /api/rifas/{id}/                   - Detalle de rifa específica
- POST   /api/rifas/                        - Crear rifa (solo admin)
- PUT    /api/rifas/{id}/                   - Actualizar rifa (solo admin)
- PATCH  /api/rifas/{id}/                   - Actualizar parcial (solo admin)
- DELETE /api/rifas/{id}/                   - Eliminar rifa (solo admin)

RIFAS - ACCIONES CUSTOM:
- GET    /api/rifas/activa/                 - Obtener rifa activa actual
- GET    /api/rifas/historial-ganadores/    - Historial de ganadores
- GET    /api/rifas/estadisticas/           - Estadísticas generales
- GET    /api/rifas/{id}/elegibilidad/      - Verificar mi elegibilidad
- GET    /api/rifas/{id}/participantes/     - Lista participantes (admin)
- POST   /api/rifas/{id}/sortear/           - Realizar sorteo (admin)
- POST   /api/rifas/{id}/cancelar/          - Cancelar rifa (admin)

PARTICIPACIONES:
- GET    /api/participaciones/              - Listar participaciones
- GET    /api/participaciones/{id}/         - Detalle de participación
- GET    /api/participaciones/mis-participaciones/  - Mis participaciones
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RifaViewSet, ParticipacionViewSet

# ============================================
# 🔧 ROUTER PRINCIPAL
# ============================================

router = DefaultRouter()

# Registrar ViewSets
router.register(
    r'rifas',
    RifaViewSet,
    basename='rifa'
)

router.register(
    r'participaciones',
    ParticipacionViewSet,
    basename='participacion'
)

# ============================================
# 📍 URL PATTERNS
# ============================================

app_name = 'rifas'

urlpatterns = [
    # Incluir todas las rutas del router
    path('', include(router.urls)),
]

