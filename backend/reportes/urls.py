# reportes/urls.py
"""
URLs para el sistema de reportes
✅ Rutas separadas por rol (Admin, Proveedor, Repartidor)
✅ Endpoints documentados
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReporteAdminViewSet,
    ReporteProveedorViewSet,
    ReporteRepartidorViewSet,
)

app_name = 'reportes'

# ============================================
# ROUTERS
# ============================================

# Router para administradores
router_admin = DefaultRouter()
router_admin.register(r'admin', ReporteAdminViewSet, basename='reporte-admin')

# Router para proveedores
router_proveedor = DefaultRouter()
router_proveedor.register(r'proveedor', ReporteProveedorViewSet, basename='reporte-proveedor')

# Router para repartidores
router_repartidor = DefaultRouter()
router_repartidor.register(r'repartidor', ReporteRepartidorViewSet, basename='reporte-repartidor')

# ============================================
# URL PATTERNS
# ============================================

urlpatterns = [
    # ============================================
    # RUTAS PARA ADMINISTRADOR
    # ============================================
    # GET /api/reportes/admin/ - Listar todos los pedidos (con filtros)
    # GET /api/reportes/admin/{id}/ - Detalle de un pedido
    # GET /api/reportes/admin/estadisticas/ - Estadísticas globales
    # GET /api/reportes/admin/metricas-diarias/?dias=30 - Métricas por día
    # GET /api/reportes/admin/top-proveedores/?limit=10 - Top proveedores
    # GET /api/reportes/admin/top-repartidores/?limit=10 - Top repartidores
    # GET /api/reportes/admin/exportar/?formato=excel - Exportar Excel/CSV
    path('', include(router_admin.urls)),

    # ============================================
    # RUTAS PARA PROVEEDOR
    # ============================================
    # GET /api/reportes/proveedor/ - Listar sus pedidos (con filtros)
    # GET /api/reportes/proveedor/{id}/ - Detalle de su pedido
    # GET /api/reportes/proveedor/estadisticas/ - Sus estadísticas
    # GET /api/reportes/proveedor/exportar/?formato=excel - Exportar sus pedidos
    path('', include(router_proveedor.urls)),

    # ============================================
    # RUTAS PARA REPARTIDOR
    # ============================================
    # GET /api/reportes/repartidor/ - Listar sus entregas (con filtros)
    # GET /api/reportes/repartidor/{id}/ - Detalle de su entrega
    # GET /api/reportes/repartidor/estadisticas/ - Sus estadísticas
    # GET /api/reportes/repartidor/exportar/?formato=excel - Exportar sus entregas
    path('', include(router_repartidor.urls)),
]


# ============================================
# DOCUMENTACIÓN DE ENDPOINTS
# ============================================

"""
📊 ENDPOINTS DISPONIBLES:

┌─────────────────────────────────────────────────────────────────────┐
│ ADMINISTRADOR (requiere is_staff=True)                              │
├─────────────────────────────────────────────────────────────────────┤
│ GET  /api/reportes/admin/                                           │
│      → Lista todos los pedidos (paginados)                          │
│      Filtros: fecha_inicio, fecha_fin, estado, tipo, proveedor,    │
│               repartidor, cliente, buscar, ordenar_por              │
│                                                                      │
│ GET  /api/reportes/admin/{id}/                                      │
│      → Detalle completo de un pedido                                │
│                                                                      │
│ GET  /api/reportes/admin/estadisticas/                              │
│      → Estadísticas globales del sistema                            │
│      Response: total_pedidos, ingresos, tasas, promedios...         │
│                                                                      │
│ GET  /api/reportes/admin/metricas-diarias/?dias=30                  │
│      → Métricas agregadas por día (para gráficos)                   │
│      Response: array de {fecha, total_pedidos, ingresos...}         │
│                                                                      │
│ GET  /api/reportes/admin/top-proveedores/?limit=10                  │
│      → Top proveedores por ventas                                   │
│      Response: array de {proveedor, pedidos, ingresos}              │
│                                                                      │
│ GET  /api/reportes/admin/top-repartidores/?limit=10                 │
│      → Top repartidores por entregas                                │
│      Response: array de {repartidor, entregas, comisiones}          │
│                                                                      │
│ GET  /api/reportes/admin/exportar/?formato=excel                    │
│      → Exportar reporte a Excel o CSV                               │
│      Params: formato (excel|csv), + todos los filtros disponibles  │
│      Response: Archivo descargable                                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ PROVEEDOR (requiere user.es_proveedor()=True)                      │
├─────────────────────────────────────────────────────────────────────┤
│ GET  /api/reportes/proveedor/                                       │
│      → Lista solo sus pedidos (paginados)                           │
│      Filtros: fecha_inicio, fecha_fin, estado, periodo              │
│                                                                      │
│ GET  /api/reportes/proveedor/{id}/                                  │
│      → Detalle de su pedido                                         │
│                                                                      │
│ GET  /api/reportes/proveedor/estadisticas/                          │
│      → Sus estadísticas personales                                  │
│      Response: total_pedidos, ingresos, comisiones, tasas...        │
│                                                                      │
│ GET  /api/reportes/proveedor/exportar/?formato=excel                │
│      → Exportar sus pedidos a Excel o CSV                           │
│      Response: Archivo descargable                                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ REPARTIDOR (requiere user.es_repartidor()=True)                    │
├─────────────────────────────────────────────────────────────────────┤
│ GET  /api/reportes/repartidor/                                      │
│      → Lista solo sus entregas (paginados)                          │
│      Filtros: fecha_inicio, fecha_fin, estado, periodo              │
│                                                                      │
│ GET  /api/reportes/repartidor/{id}/                                 │
│      → Detalle de su entrega                                        │
│                                                                      │
│ GET  /api/reportes/repartidor/estadisticas/                         │
│      → Sus estadísticas personales                                  │
│      Response: entregas, comisiones, calificación...                │
│                                                                      │
│ GET  /api/reportes/repartidor/exportar/?formato=excel               │
│      → Exportar sus entregas a Excel o CSV                          │
│      Response: Archivo descargable                                  │
└─────────────────────────────────────────────────────────────────────┘

📖 EJEMPLOS DE USO:

1. Listar pedidos del día (Admin):
   GET /api/reportes/admin/?periodo=hoy

2. Filtrar por estado y fecha (Admin):
   GET /api/reportes/admin/?estado=entregado&fecha_inicio=2025-01-01&fecha_fin=2025-01-31

3. Buscar pedidos (Admin):
   GET /api/reportes/admin/?buscar=Juan

4. Estadísticas del mes actual (Proveedor):
   GET /api/reportes/proveedor/estadisticas/

5. Exportar pedidos de la última semana (Repartidor):
   GET /api/reportes/repartidor/exportar/?periodo=ultima_semana&formato=excel

6. Top 5 proveedores (Admin):
   GET /api/reportes/admin/top-proveedores/?limit=5

7. Métricas de los últimos 7 días (Admin):
   GET /api/reportes/admin/metricas-diarias/?dias=7

🔒 AUTENTICACIÓN:
- Todos los endpoints requieren autenticación (Token/JWT)
- Los permisos se validan automáticamente según el rol

📄 PAGINACIÓN:
- Todos los listados están paginados (default: 100 items por página)
- Params: page, page_size

🔍 FILTROS DISPONIBLES:

Admin:
  - fecha_inicio, fecha_fin (YYYY-MM-DD)
  - periodo (hoy, ayer, ultima_semana, ultimo_mes, este_mes)
  - estado (confirmado, en_preparacion, en_ruta, entregado, cancelado)
  - tipo (proveedor, directo)
  - cliente (ID), cliente_email
  - proveedor (ID), proveedor_nombre
  - repartidor (ID)
  - total_min, total_max
  - metodo_pago
  - con_repartidor (true/false)
  - solo_entregados, solo_cancelados, solo_activos (true/false)
  - buscar (búsqueda general)
  - ordenar_por (fecha, -fecha, total, -total, ganancia, -ganancia)

Proveedor/Repartidor:
  - fecha_inicio, fecha_fin
  - periodo (hoy, ultima_semana, este_mes)
  - estado
  - solo_entregados (true/false)
"""
