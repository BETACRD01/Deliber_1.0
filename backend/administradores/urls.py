# -*- coding: utf-8 -*-
# administradores/urls.py
"""
URLs para el módulo de administradores

✅ Rutas organizadas por funcionalidad
✅ Endpoints RESTful completos
✅ Documentación de todos los endpoints
✅ Nuevos métodos PUT/PATCH para Proveedores y Repartidores
✅ Acciones custom para editar contacto
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
from .views import GestionSolicitudesCambioRolViewSet

app_name = 'administradores'

# ============================================
# BLOQUE 1: CONFIGURACIÓN DEL ROUTER
# ============================================

router = DefaultRouter()

# Gestión de usuarios
router.register(r'usuarios', GestionUsuariosViewSet, basename='usuarios')

# Gestión de proveedores (ahora con PUT, PATCH, editar_contacto)
router.register(r'proveedores', GestionProveedoresViewSet, basename='proveedores')

# Gestión de repartidores (ahora con PUT, PATCH, editar_contacto)
router.register(r'repartidores', GestionRepartidoresViewSet, basename='repartidores')

# Logs de acciones administrativas
router.register(r'acciones', AccionesAdministrativasViewSet, basename='acciones')

# Administradores
router.register(r'administradores', AdministradoresViewSet, basename='administradores')

# Dashboard administrativo
router.register(r'dashboard', DashboardAdminViewSet, basename='dashboard')

# ============================================
# BLOQUE 2: URL PATTERNS
# ============================================

urlpatterns = [
    # Rutas del router
    path('', include(router.urls)),

    # Configuración del sistema (ViewSet sin router - singleton)
    path('configuracion/', ConfiguracionSistemaViewSet.as_view({
        'get': 'list',
        'put': 'update',
    }), name='configuracion'),
]
router.register(
    r'solicitudes-cambio-rol',
    GestionSolicitudesCambioRolViewSet,
    basename='solicitudes-cambio-rol'
)

# ============================================
# BLOQUE 3: DOCUMENTACIÓN DE ENDPOINTS
# ============================================

"""
╔════════════════════════════════════════════════════════════════════════════════╗
║ 📋 ENDPOINTS DISPONIBLES - MÓDULO ADMINISTRADORES                            ║
╚════════════════════════════════════════════════════════════════════════════════╝

┌────────────────────────────────────────────────────────────────────────────────┐
│ 👥 GESTIÓN DE USUARIOS (requiere: puede_gestionar_usuarios)                   │
├────────────────────────────────────────────────────────────────────────────────┤
│
│ ✅ LISTADO Y DETALLE:
│ GET    /api/admin/usuarios/
│        → Listar todos los usuarios con filtros y búsqueda
│        Filtros: ?rol=USUARIO&is_active=true&cuenta_desactivada=false
│        Búsqueda: ?search=juan
│        Ordenamiento: ?ordering=-created_at
│
│ GET    /api/admin/usuarios/{id}/
│        → Obtener detalle completo de un usuario
│        Response: {id, email, nombre_completo, rol, estadisticas, ...}
│
│ ✅ EDICIÓN:
│ PUT    /api/admin/usuarios/{id}/
│        → Editar información del usuario (todos los campos)
│        Body: {first_name, last_name, celular, fecha_nacimiento, ...}
│
│ PATCH  /api/admin/usuarios/{id}/
│        → Editar parcialmente (solo campos enviados)
│        Body: {first_name, celular}
│
│ ✅ ACCIONES CUSTOM:
│ POST   /api/admin/usuarios/{id}/cambiar_rol/
│        → Cambiar rol del usuario
│        Body: {"nuevo_rol": "REPARTIDOR", "motivo": "Solicitud aprobada"}
│
│ POST   /api/admin/usuarios/{id}/desactivar/
│        → Desactivar usuario
│        Body: {"razon": "Violación de términos", "permanente": false}
│
│ POST   /api/admin/usuarios/{id}/activar/
│        → Reactivar usuario desactivado
│
│ POST   /api/admin/usuarios/{id}/resetear_password/
│        → Resetear contraseña
│        Body: {"nueva_password": "Pass123!", "confirmar_password": "Pass123!"}
│
│ GET    /api/admin/usuarios/{id}/historial_pedidos/
│        → Ver historial de pedidos del usuario
│        Response: {total_pedidos, pedidos_mes_actual, pedidos: [...]}
│
│ GET    /api/admin/usuarios/estadisticas/
│        → Estadísticas generales de usuarios
│        Response: {total_usuarios, activos, desactivados, por_rol, ...}
│
└────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────┐
│ 🏪 GESTIÓN DE PROVEEDORES (requiere: puede_gestionar_proveedores)             │
├────────────────────────────────────────────────────────────────────────────────┤
│
│ ✅ LISTADO Y DETALLE:
│ GET    /api/admin/proveedores/
│        → Listar todos los proveedores
│        Filtros: ?verificado=true&activo=true&tipo_proveedor=RESTAURANT
│        Búsqueda: ?search=nombre
│        Ordenamiento: ?ordering=-creado_en
│
│ GET    /api/admin/proveedores/{id}/
│        → Obtener detalle completo
│        Response: {id, nombre, ruc, email, telefono, tipo, ubicación, ...}
│
│ ✅ EDICIÓN DE INFORMACIÓN (NUEVO ✨):
│ PUT    /api/admin/proveedores/{id}/
│        → Editar toda la información del proveedor
│        Body: {
│            "nombre": "Mi Restaurante",
│            "tipo_proveedor": "RESTAURANT",
│            "ruc": "1234567890123",
│            "telefono": "0987654321",
│            "direccion": "Av. Principal 123",
│            "latitud": -0.2123,
│            "longitud": -78.4567,
│            "descripcion": "El mejor restaurante",
│            "horario_atencion": "08:00-20:00",
│            "tiempo_preparacion_promedio": 30
│        }
│
│ PATCH  /api/admin/proveedores/{id}/
│        → Editar parcialmente (solo campos enviados)
│        Body: {nombre: "Nuevo Nombre", telefono: "0987654321"}
│
│ ✅ EDICIÓN DE CONTACTO (NUEVO ✨):
│ PATCH  /api/admin/proveedores/{id}/editar_contacto/
│        → Editar email y datos de contacto del usuario
│        Body: {
│            "email": "contacto@email.com",
│            "first_name": "Juan",
│            "last_name": "Pérez"
│        }
│
│ ✅ ACCIONES CUSTOM:
│ POST   /api/admin/proveedores/{id}/verificar/
│        → Verificar o rechazar proveedor
│        Body: {"verificado": true, "motivo": "Documentación completa"}
│
│ POST   /api/admin/proveedores/{id}/desactivar/
│        → Desactivar proveedor
│
│ POST   /api/admin/proveedores/{id}/activar/
│        → Activar proveedor
│
│ GET    /api/admin/proveedores/pendientes/
│        → Listar proveedores pendientes de verificación
│        Response: {total, proveedores: [...]}
│
└────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────┐
│ 🚚 GESTIÓN DE REPARTIDORES (requiere: puede_gestionar_repartidores)           │
├────────────────────────────────────────────────────────────────────────────────┤
│
│ ✅ LISTADO Y DETALLE:
│ GET    /api/admin/repartidores/
│        → Listar todos los repartidores
│        Filtros: ?verificado=true&activo=true&estado=disponible
│        Búsqueda: ?search=nombre
│        Ordenamiento: ?ordering=-creado_en
│
│ GET    /api/admin/repartidores/{id}/
│        → Obtener detalle completo
│        Response: {id, nombre, cedula, telefono, estado, ubicación, ...}
│
│ ✅ EDICIÓN DE INFORMACIÓN (NUEVO ✨):
│ PUT    /api/admin/repartidores/{id}/
│        → Editar toda la información del repartidor
│        Body: {
│            "cedula": "1234567890",
│            "telefono": "0987654321",
│            "latitud": -0.2123,
│            "longitud": -78.4567
│        }
│
│ PATCH  /api/admin/repartidores/{id}/
│        → Editar parcialmente (solo campos enviados)
│        Body: {telefono: "0987654321", latitud: -0.2123, longitud: -78.4567}
│
│ ✅ EDICIÓN DE CONTACTO (NUEVO ✨):
│ PATCH  /api/admin/repartidores/{id}/editar_contacto/
│        → Editar email y datos de contacto del usuario
│        Body: {
│            "email": "repartidor@email.com",
│            "first_name": "Carlos",
│            "last_name": "González"
│        }
│
│ ✅ ACCIONES CUSTOM:
│ POST   /api/admin/repartidores/{id}/verificar/
│        → Verificar o rechazar repartidor
│        Body: {"verificado": true, "motivo": "Antecedentes verificados"}
│
│ POST   /api/admin/repartidores/{id}/desactivar/
│        → Desactivar repartidor
│
│ POST   /api/admin/repartidores/{id}/activar/
│        → Activar repartidor
│
│ GET    /api/admin/repartidores/pendientes/
│        → Listar repartidores pendientes de verificación
│        Response: {total, repartidores: [...]}
│
└────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────┐
│ 📝 LOGS DE ACCIONES ADMINISTRATIVAS (requiere: es_administrador)              │
├────────────────────────────────────────────────────────────────────────────────┤
│
│ GET    /api/admin/acciones/
│        → Listar todas las acciones realizadas
│        Filtros: ?tipo_accion=editar_usuario&exitosa=true
│        Ordenar: ?ordering=-fecha_accion
│
│ GET    /api/admin/acciones/{id}/
│        → Detalle de una acción específica
│
│ GET    /api/admin/acciones/mis_acciones/
│        → Ver mis propias acciones (últimas 100)
│        Response: {total, acciones: [...]}
│
│ 📊 TIPOS DE ACCIONES REGISTRADAS:
│ - crear_usuario, editar_usuario, desactivar_usuario, cambiar_rol
│ - verificar_proveedor, rechazar_proveedor, editar_proveedor, editar_proveedor_contacto
│ - verificar_repartidor, rechazar_repartidor, editar_repartidor, editar_repartidor_contacto
│ - cancelar_pedido, reasignar_pedido, editar_pedido
│ - crear_rifa, realizar_sorteo, cancelar_rifa
│ - configurar_sistema, notificacion_masiva, exportar_datos
│
└────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────┐
│ ⚙️  CONFIGURACIÓN DEL SISTEMA (requiere: puede_configurar_sistema)             │
├────────────────────────────────────────────────────────────────────────────────┤
│
│ GET    /api/admin/configuracion/
│        → Ver configuración actual del sistema
│        Response: comisiones, límites, contacto, mantenimiento, ...
│
│ PUT    /api/admin/configuracion/
│        → Actualizar configuración del sistema
│        Body: {
│            "comision_app_proveedor": 10.0,
│            "comision_app_directo": 15.0,
│            "comision_repartidor_proveedor": 25.0,
│            "comision_repartidor_directo": 85.0,
│            "pedidos_minimos_rifa": 3,
│            "pedido_maximo": 1000.00,
│            "pedido_minimo": 5.00,
│            "tiempo_maximo_entrega": 60,
│            "telefono_soporte": "0987654321",
│            "email_soporte": "soporte@app.com",
│            "mantenimiento": false,
│            "mensaje_mantenimiento": ""
│        }
│
└────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────┐
│ 👨‍💼 ADMINISTRADORES (requiere: es_administrador)                                │
├────────────────────────────────────────────────────────────────────────────────┤
│
│ GET    /api/admin/administradores/
│        → Listar administradores activos
│        Búsqueda: ?search=juan
│
│ GET    /api/admin/administradores/{id}/
│        → Detalle de un administrador
│
│ GET    /api/admin/administradores/mi_perfil/
│        → Ver mi perfil de administrador
│        Response: permisos, cargo, estadísticas, total_acciones
│
└────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────┐
│ 📊 DASHBOARD ADMINISTRATIVO (requiere: es_administrador)                      │
├────────────────────────────────────────────────────────────────────────────────┤
│
│ GET    /api/admin/dashboard/
│        → Estadísticas generales del sistema
│        Response: {
│            usuarios: {total, activos, nuevos_hoy},
│            proveedores: {total, verificados, pendientes},
│            repartidores: {total, verificados, disponibles, pendientes},
│            pedidos: {total, hoy, activos, entregados},
│            financiero: {ingresos_totales, ganancia_app, ingresos_hoy, ganancia_hoy}
│        }
│
│ GET    /api/admin/dashboard/resumen_dia/
│        → Resumen detallado del día actual
│        Response: {fecha, pedidos, nuevos_registros, acciones_administrativas}
│
│ GET    /api/admin/dashboard/alertas/
│        → Alertas importantes del sistema
│        Response: {
│            total_alertas,
│            alertas: [
│                {
│                    tipo: "proveedores_pendientes",
│                    nivel: "warning",
│                    mensaje: "...",
│                    cantidad: 5
│                }
│            ]
│        }
│
│ 🔔 TIPOS DE ALERTAS:
│ - proveedores_pendientes (warning)
│ - repartidores_pendientes (warning)
│ - pedidos_sin_repartidor (danger)
│ - pedidos_retrasados (danger)
│ - usuarios_bloqueados (info)
│
└────────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════

🔐 AUTENTICACIÓN:
✅ Todos los endpoints requieren autenticación (JWT Token)
   Header: Authorization: Bearer <tu_token_jwt>
✅ Los permisos se validan según el perfil de administrador

📄 PAGINACIÓN:
✅ Todos los listados están paginados (default: 100 items)
   ?page=1&page_size=50

🔎 BÚSQUEDA Y FILTROS:
✅ Búsqueda global: ?search=termino
✅ Filtros específicos: ?rol=USUARIO&is_active=true
✅ Ordenamiento: ?ordering=-created_at (desc) o ?ordering=email (asc)

📋 VALIDACIONES:
✅ RUC: 10 o 13 dígitos, único en el sistema
✅ Cédula: 10 dígitos, única en el sistema
✅ Teléfono: formato 09XXXXXXXXX (10 dígitos)
✅ Email: formato válido, único en el sistema
✅ Coordenadas: latitud (-90 a 90), longitud (-180 a 180)
✅ Horario: formato HH:MM-HH:MM

⚡ CÓDIGOS DE RESPUESTA:
✅ 200 OK - Operación exitosa
✅ 201 Created - Recurso creado
✅ 204 No Content - Eliminación exitosa
✅ 400 Bad Request - Validación fallida
✅ 401 Unauthorized - Sin autenticación
✅ 403 Forbidden - Sin permisos
✅ 404 Not Found - Recurso no existe
✅ 500 Internal Server Error - Error del servidor

═══════════════════════════════════════════════════════════════════════════════════

📌 EJEMPLOS DE USO:

1️⃣ EDITAR INFORMACIÓN DE PROVEEDOR (COMPLETO):
PUT /api/admin/proveedores/1/
Headers: Authorization: Bearer <token>
Content-Type: application/json
Body: {
    "nombre": "Nuevo Nombre",
    "tipo_proveedor": "RESTAURANT",
    "ruc": "1234567890123",
    "telefono": "0987654321",
    "direccion": "Av. Principal 123",
    "latitud": -0.2123,
    "longitud": -78.4567,
    "descripcion": "El mejor restaurante",
    "horario_atencion": "08:00-20:00",
    "tiempo_preparacion_promedio": 30
}

2️⃣ EDITAR PARCIALMENTE PROVEEDOR:
PATCH /api/admin/proveedores/1/
Body: {
    "nombre": "Nuevo Nombre",
    "telefono": "0987654321"
}

3️⃣ EDITAR CONTACTO DE PROVEEDOR (NUEVO ✨):
PATCH /api/admin/proveedores/1/editar_contacto/
Body: {
    "email": "nuevo@email.com",
    "first_name": "Juan",
    "last_name": "Pérez"
}

4️⃣ EDITAR REPARTIDOR:
PUT /api/admin/repartidores/1/
Body: {
    "cedula": "1234567890",
    "telefono": "0987654321",
    "latitud": -0.2123,
    "longitud": -78.4567
}

5️⃣ EDITAR CONTACTO DE REPARTIDOR:
PATCH /api/admin/repartidores/1/editar_contacto/
Body: {
    "email": "nuevo@email.com",
    "first_name": "Carlos",
    "last_name": "González"
}

6️⃣ VERIFICAR PROVEEDOR:
POST /api/admin/proveedores/456/verificar/
Body: {"verificado": true, "motivo": "Documentación completa"}

7️⃣ LISTAR PROVEEDORES PENDIENTES:
GET /api/admin/proveedores/pendientes/

8️⃣ CAMBIAR ROL DE USUARIO:
POST /api/admin/usuarios/123/cambiar_rol/
Body: {"nuevo_rol": "REPARTIDOR", "motivo": "Solicitud aprobada"}

9️⃣ VER ALERTAS DEL SISTEMA:
GET /api/admin/dashboard/alertas/

🔟 VER MIS ACCIONES ADMINISTRATIVAS:
GET /api/admin/acciones/mis_acciones/

═══════════════════════════════════════════════════════════════════════════════════

⚠️  NOTAS IMPORTANTES:

❌ No se puede modificar superusuarios desde estos endpoints
❌ No puedes desactivar tu propia cuenta de administrador
❌ No puedes cambiar tu propio rol
❌ Las verificaciones de proveedores/repartidores no son reversibles manualmente
❌ Los cambios en configuración afectan a TODO el sistema inmediatamente

✅ Todas las acciones quedan registradas en el log de auditoría
✅ Cada acción incluye IP, User Agent y timestamp
✅ Los cambios de email y contacto también se registran
✅ La edición parcial (PATCH) solo modifica los campos enviados

═══════════════════════════════════════════════════════════════════════════════════
"""