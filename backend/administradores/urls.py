# -*- coding: utf-8 -*-
# administradores/urls.py
"""
URLs para el módulo de administradores
✅ Rutas organizadas por funcionalidad
✅ Endpoints RESTful
✅ Documentación completa
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GestionUsuariosViewSet,
    GestionProveedoresViewSet,
    GestionRepartidoresViewSet,
    AccionesAdministrativasViewSet,
    ConfiguracionSistemaViewSet,
    AdministradoresViewSet,
    DashboardAdminViewSet,
)

app_name = 'administradores'

# ============================================
# ROUTERS
# ============================================

router = DefaultRouter()

# Gestión de usuarios
router.register(r'usuarios', GestionUsuariosViewSet, basename='usuarios')

# Gestión de proveedores
router.register(r'proveedores', GestionProveedoresViewSet, basename='proveedores')

# Gestión de repartidores
router.register(r'repartidores', GestionRepartidoresViewSet, basename='repartidores')

# Logs de acciones
router.register(r'acciones', AccionesAdministrativasViewSet, basename='acciones')

# Administradores
router.register(r'administradores', AdministradoresViewSet, basename='administradores')

# Dashboard
router.register(r'dashboard', DashboardAdminViewSet, basename='dashboard')

# ============================================
# URL PATTERNS
# ============================================

urlpatterns = [
    # Rutas del router
    path('', include(router.urls)),

    # Configuración del sistema (ViewSet sin router)
    path('configuracion/', ConfiguracionSistemaViewSet.as_view({
        'get': 'list',
        'put': 'update',
    }), name='configuracion'),
]


# ============================================
# DOCUMENTACIÓN DE ENDPOINTS
# ============================================

"""
📋 ENDPOINTS DISPONIBLES:

┌─────────────────────────────────────────────────────────────────────────────┐
│ GESTIÓN DE USUARIOS (requiere: puede_gestionar_usuarios)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ GET    /api/admin/usuarios/                                                 │
│        → Listar usuarios con filtros                                        │
│        Filtros: rol, is_active, cuenta_desactivada, verificado             │
│        Search: email, first_name, last_name, celular, username             │
│                                                                              │
│ GET    /api/admin/usuarios/{id}/                                            │
│        → Detalle completo de un usuario                                     │
│                                                                              │
│ PUT    /api/admin/usuarios/{id}/                                            │
│        → Editar información del usuario                                     │
│        Body: first_name, last_name, celular, fecha_nacimiento, etc.        │
│                                                                              │
│ PATCH  /api/admin/usuarios/{id}/                                            │
│        → Edición parcial                                                    │
│                                                                              │
│ POST   /api/admin/usuarios/{id}/cambiar_rol/                               │
│        → Cambiar rol del usuario                                            │
│        Body: {"nuevo_rol": "REPARTIDOR", "motivo": "..."}                  │
│                                                                              │
│ POST   /api/admin/usuarios/{id}/desactivar/                                │
│        → Desactivar usuario                                                 │
│        Body: {"razon": "...", "permanente": false}                         │
│                                                                              │
│ POST   /api/admin/usuarios/{id}/activar/                                   │
│        → Reactivar usuario desactivado                                      │
│                                                                              │
│ POST   /api/admin/usuarios/{id}/resetear_password/                         │
│        → Resetear contraseña del usuario                                    │
│        Body: {"nueva_password": "...", "confirmar_password": "..."}        │
│                                                                              │
│ GET    /api/admin/usuarios/{id}/historial_pedidos/                         │
│        → Ver historial de pedidos del usuario                               │
│        Response: {total_pedidos, pedidos_mes_actual, pedidos: [...]}       │
│                                                                              │
│ GET    /api/admin/usuarios/estadisticas/                                   │
│        → Estadísticas generales de usuarios                                 │
│        Response: total, activos, desactivados, nuevos, por_rol             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ GESTIÓN DE PROVEEDORES (requiere: puede_gestionar_proveedores)             │
├─────────────────────────────────────────────────────────────────────────────┤
│ GET    /api/admin/proveedores/                                              │
│        → Listar proveedores                                                 │
│        Filtros: verificado, activo, tipo_proveedor                         │
│        Search: nombre, user__email, telefono                               │
│                                                                              │
│ GET    /api/admin/proveedores/{id}/                                         │
│        → Detalle completo de un proveedor                                   │
│                                                                              │
│ POST   /api/admin/proveedores/{id}/verificar/                              │
│        → Verificar o rechazar proveedor                                     │
│        Body: {"verificado": true, "motivo": "..."}                         │
│                                                                              │
│ POST   /api/admin/proveedores/{id}/desactivar/                             │
│        → Desactivar proveedor                                               │
│                                                                              │
│ POST   /api/admin/proveedores/{id}/activar/                                │
│        → Activar proveedor                                                  │
│                                                                              │
│ GET    /api/admin/proveedores/pendientes/                                  │
│        → Lista proveedores pendientes de verificación                       │
│        Response: {total, proveedores: [...]}                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ GESTIÓN DE REPARTIDORES (requiere: puede_gestionar_repartidores)           │
├─────────────────────────────────────────────────────────────────────────────┤
│ GET    /api/admin/repartidores/                                             │
│        → Listar repartidores                                                │
│        Filtros: verificado, activo, estado                                 │
│        Search: user__email, first_name, last_name, cedula, telefono        │
│                                                                              │
│ GET    /api/admin/repartidores/{id}/                                        │
│        → Detalle completo de un repartidor                                  │
│                                                                              │
│ POST   /api/admin/repartidores/{id}/verificar/                             │
│        → Verificar o rechazar repartidor                                    │
│        Body: {"verificado": true, "motivo": "..."}                         │
│                                                                              │
│ POST   /api/admin/repartidores/{id}/desactivar/                            │
│        → Desactivar repartidor                                              │
│                                                                              │
│ POST   /api/admin/repartidores/{id}/activar/                               │
│        → Activar repartidor                                                 │
│                                                                              │
│ GET    /api/admin/repartidores/pendientes/                                 │
│        → Lista repartidores pendientes de verificación                      │
│        Response: {total, repartidores: [...]}                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ LOGS DE ACCIONES (todos los admins activos)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ GET    /api/admin/acciones/                                                 │
│        → Listar todas las acciones administrativas                          │
│        Filtros: tipo_accion, exitosa, administrador                        │
│        Ordenar: fecha_accion                                                │
│                                                                              │
│ GET    /api/admin/acciones/{id}/                                            │
│        → Detalle de una acción específica                                   │
│                                                                              │
│ GET    /api/admin/acciones/mis_acciones/                                   │
│        → Ver mis propias acciones (últimas 100)                             │
│        Response: {total, acciones: [...]}                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ CONFIGURACIÓN DEL SISTEMA (requiere: puede_configurar_sistema)             │
├─────────────────────────────────────────────────────────────────────────────┤
│ GET    /api/admin/configuracion/                                            │
│        → Ver configuración actual del sistema                               │
│        Response: comisiones, límites, contacto, mantenimiento              │
│                                                                              │
│ PUT    /api/admin/configuracion/                                            │
│        → Actualizar configuración del sistema                               │
│        Body: comisiones, pedidos_minimos_rifa, limites, etc.               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ ADMINISTRADORES (todos los admins activos)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ GET    /api/admin/administradores/                                          │
│        → Listar administradores activos                                     │
│        Search: user__email, first_name, last_name, cargo                   │
│                                                                              │
│ GET    /api/admin/administradores/{id}/                                     │
│        → Detalle de un administrador                                        │
│                                                                              │
│ GET    /api/admin/administradores/mi_perfil/                               │
│        → Ver mi perfil de administrador                                     │
│        Response: permisos, cargo, estadísticas                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ DASHBOARD (todos los admins activos)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ GET    /api/admin/dashboard/                                                │
│        → Estadísticas generales del sistema                                 │
│        Response: usuarios, proveedores, repartidores, pedidos, financiero  │
│                                                                              │
│ GET    /api/admin/dashboard/resumen_dia/                                   │
│        → Resumen detallado del día actual                                   │
│        Response: pedidos_hoy, nuevos_registros, acciones                   │
│                                                                              │
│ GET    /api/admin/dashboard/alertas/                                       │
│        → Alertas importantes del sistema                                    │
│        Response: {total_alertas, alertas: [{tipo, nivel, mensaje}]}       │
└─────────────────────────────────────────────────────────────────────────────┘

🔐 AUTENTICACIÓN:
- Todos los endpoints requieren autenticación (JWT Token)
- Header: Authorization: Bearer <token>
- Los permisos se validan según el perfil de administrador

📄 PAGINACIÓN:
- Todos los listados están paginados (default: 100 items)
- Params: ?page=1&page_size=50

🔍 FILTROS COMUNES:
- Usuarios: ?rol=USUARIO&is_active=true&search=juan
- Proveedores: ?verificado=false&tipo_proveedor=restaurante
- Repartidores: ?estado=disponible&verificado=true
- Acciones: ?tipo_accion=editar_usuario&exitosa=true

📊 ORDENAMIENTO:
- Usar: ?ordering=-created_at (descendente) o ?ordering=email (ascendente)
- Campos disponibles según el endpoint

🔔 ALERTAS DEL SISTEMA:
Niveles:
- info: Informativo
- warning: Advertencia (requiere atención)
- danger: Crítico (requiere acción inmediata)

Tipos:
- proveedores_pendientes
- repartidores_pendientes
- pedidos_sin_repartidor
- pedidos_retrasados
- usuarios_bloqueados

📝 EJEMPLOS DE USO:

1. Listar usuarios activos:
   GET /api/admin/usuarios/?is_active=true

2. Buscar usuario por email:
   GET /api/admin/usuarios/?search=juan@example.com

3. Cambiar rol de usuario:
   POST /api/admin/usuarios/123/cambiar_rol/
   Body: {"nuevo_rol": "REPARTIDOR", "motivo": "Solicitud aprobada"}

4. Verificar proveedor:
   POST /api/admin/proveedores/456/verificar/
   Body: {"verificado": true, "motivo": "Documentación completa"}

5. Ver alertas del sistema:
   GET /api/admin/dashboard/alertas/

6. Ver mi historial de acciones:
   GET /api/admin/acciones/mis_acciones/

7. Actualizar comisiones:
   PUT /api/admin/configuracion/
   Body: {"comision_app_proveedor": 12.00}

8. Ver proveedores pendientes:
   GET /api/admin/proveedores/pendientes/

9. Resetear contraseña de usuario:
   POST /api/admin/usuarios/789/resetear_password/
   Body: {"nueva_password": "NuevaPass123", "confirmar_password": "NuevaPass123"}

10. Ver estadísticas del dashboard:
    GET /api/admin/dashboard/

⚠️ NOTAS IMPORTANTES:
- No se puede modificar superusuarios desde estos endpoints
- No puedes desactivar tu propia cuenta de administrador
- Todas las acciones quedan registradas en el log de auditoría
- Los cambios en configuración afectan todo el sistema
- Las verificaciones de proveedores/repartidores son irreversibles
"""
