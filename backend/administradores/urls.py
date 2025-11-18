# administradores/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# ============================================
# ROUTER PARA VIEWSETS
# ============================================
router = DefaultRouter()

# Gestión de usuarios
router.register(r"usuarios", views.GestionUsuariosViewSet, basename="admin-usuarios")

# Gestión de proveedores
router.register(
    r"proveedores", views.GestionProveedoresViewSet, basename="admin-proveedores"
)

# Gestión de repartidores
router.register(
    r"repartidores", views.GestionRepartidoresViewSet, basename="admin-repartidores"
)

# Logs de acciones
router.register(
    r"acciones", views.AccionesAdministrativasViewSet, basename="admin-acciones"
)

# Administradores
router.register(
    r"administradores", views.AdministradoresViewSet, basename="admin-administradores"
)

# Dashboard
router.register(r"dashboard", views.DashboardAdminViewSet, basename="admin-dashboard")

# ✅ Solicitudes de Cambio de Rol
router.register(
    r"solicitudes-cambio-rol",
    views.GestionSolicitudesCambioRolViewSet,
    basename="admin-solicitudes-cambio-rol",
)

# ============================================
# URL PATTERNS
# ============================================
urlpatterns = [
    # Router principal (todos los viewsets)
    path("", include(router.urls)),
    # Configuración del sistema
    path(
        "configuracion/",
        views.ConfiguracionSistemaViewSet.as_view({"get": "list", "put": "update"}),
        name="admin-configuracion",
    ),
]
