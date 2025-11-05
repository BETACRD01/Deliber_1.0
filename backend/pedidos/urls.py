# pedidos/urls.py
from django.urls import path
from . import views

app_name = "pedidos"

urlpatterns = [
    # ==========================================================
    # 📦 PEDIDOS PRINCIPALES (crear / listar)
    # ==========================================================
    path(
        "",
        views.pedidos_view,
        name="pedidos_view"
    ),
    # GET: Lista pedidos según rol del usuario
    # POST: Crea un nuevo pedido (solo clientes)
    # Query params opcionales: ?estado=confirmado&tipo=proveedor&page=1

    # ==========================================================
    # 🔍 DETALLE DEL PEDIDO
    # ==========================================================
    path(
        "<int:pedido_id>/",
        views.pedido_detalle,
        name="pedido_detalle"
    ),
    # GET: Obtiene información completa de un pedido específico
    # Permisos: cliente dueño, proveedor, repartidor asignado o admin

    # ==========================================================
    # 🛵 ACEPTACIÓN DEL PEDIDO (REPARTIDOR)
    # ==========================================================
    path(
        "<int:pedido_id>/aceptar-repartidor/",
        views.aceptar_pedido_repartidor,
        name="aceptar_pedido_repartidor"
    ),
    # PATCH: Repartidor acepta un pedido disponible
    # Solo repartidores con estado "disponible"

    # ==========================================================
    # 🍳 CONFIRMACIÓN DEL PROVEEDOR
    # ==========================================================
    path(
        "<int:pedido_id>/confirmar-proveedor/",
        views.confirmar_pedido_proveedor,
        name="confirmar_pedido_proveedor"
    ),
    # PATCH: Proveedor confirma que está preparando el pedido
    # Solo el proveedor asignado al pedido

    # ==========================================================
    # 🚚 CAMBIO DE ESTADO (GENERAL)
    # ==========================================================
    path(
        "<int:pedido_id>/estado/",
        views.cambiar_estado_pedido,
        name="cambiar_estado_pedido"
    ),
    # PATCH: Cambia el estado del pedido
    # Body: {"nuevo_estado": "en_ruta"}
    # Permisos: proveedor, repartidor asignado o admin
    # Estados permitidos: confirmado, en_preparacion, en_ruta, entregado, cancelado

    # ==========================================================
    # 🚫 CANCELACIÓN DEL PEDIDO
    # ==========================================================
    path(
        "<int:pedido_id>/cancelar/",
        views.cancelar_pedido,
        name="cancelar_pedido"
    ),
    # POST: Cancela un pedido con motivo
    # Body: {"motivo": "Cliente no disponible"}
    # Permisos: cliente dueño, proveedor, repartidor asignado o admin

    # ==========================================================
    # 💰 GANANCIAS / COMISIONES DEL PEDIDO
    # ==========================================================
    path(
        "<int:pedido_id>/ganancias/",
        views.ver_ganancias_pedido,
        name="ver_ganancias_pedido"
    ),
    # GET: Muestra la distribución de comisiones del pedido
    # Permisos: proveedor del pedido, repartidor asignado o admin

    # ==========================================================
    # 📊 ESTADÍSTICAS (OPCIONAL - Para futuras implementaciones)
    # ==========================================================
    # path(
    #     "estadisticas/",
    #     views.estadisticas_pedidos,
    #     name="estadisticas_pedidos"
    # ),
    # GET: Retorna estadísticas generales de pedidos
    # Permisos: solo admin

    # ==========================================================
    # 🔍 BÚSQUEDA Y FILTROS AVANZADOS (OPCIONAL)
    # ==========================================================
    # path(
    #     "buscar/",
    #     views.buscar_pedidos,
    #     name="buscar_pedidos"
    # ),
    # GET: Búsqueda avanzada de pedidos
    # Query params: ?q=término&fecha_desde=2024-01-01&fecha_hasta=2024-12-31

    # ==========================================================
    # 📍 TRACKING EN TIEMPO REAL (OPCIONAL)
    # ==========================================================
    # path(
    #     "<int:pedido_id>/tracking/",
    #     views.tracking_pedido,
    #     name="tracking_pedido"
    # ),
    # GET: Obtiene la ubicación actual del repartidor
    # Permisos: cliente dueño o admin

    # ==========================================================
    # 📝 HISTORIAL DE CAMBIOS (OPCIONAL)
    # ==========================================================
    # path(
    #     "<int:pedido_id>/historial/",
    #     views.historial_pedido,
    #     name="historial_pedido"
    # ),
    # GET: Muestra el historial completo de cambios del pedido
    # Permisos: admin
]

"""
==========================================================
📖 DOCUMENTACIÓN DE ENDPOINTS
==========================================================

BASE URL: /api/pedidos/

ENDPOINTS DISPONIBLES:
---------------------

1. GET /api/pedidos/
   - Lista todos los pedidos según el rol del usuario
   - Filtros: ?estado=confirmado&tipo=proveedor&page=1&page_size=20
   - Respuesta: Lista paginada de pedidos

2. POST /api/pedidos/
   - Crea un nuevo pedido (solo clientes)
   - Body: {
       "tipo": "proveedor|directo",
       "descripcion": "...",
       "proveedor": id,
       "direccion_origen": "...",
       "direccion_entrega": "...",
       "metodo_pago": "efectivo|tarjeta",
       "total": 25.50
     }

3. GET /api/pedidos/{id}/
   - Obtiene detalles completos de un pedido

4. PATCH /api/pedidos/{id}/aceptar-repartidor/
   - Repartidor acepta el pedido
   - Body automático (usa el repartidor del usuario logueado)

5. PATCH /api/pedidos/{id}/confirmar-proveedor/
   - Proveedor confirma preparación
   - Body automático (usa el proveedor del usuario logueado)

6. PATCH /api/pedidos/{id}/estado/
   - Cambia el estado del pedido
   - Body: {"nuevo_estado": "en_ruta"}

7. POST /api/pedidos/{id}/cancelar/
   - Cancela un pedido
   - Body: {"motivo": "Razón de cancelación"}

8. GET /api/pedidos/{id}/ganancias/
   - Ver distribución de comisiones

==========================================================
ESTADOS DEL PEDIDO:
- confirmado: Pedido creado, esperando aceptación
- en_preparacion: Proveedor preparando el pedido
- en_ruta: Repartidor en camino al cliente
- entregado: Pedido completado exitosamente
- cancelado: Pedido cancelado

TRANSICIONES VÁLIDAS:
- confirmado → en_preparacion | cancelado
- en_preparacion → en_ruta | cancelado
- en_ruta → entregado | cancelado

==========================================================
PERMISOS POR ROL:
- Cliente: Crear pedidos, ver sus pedidos, cancelar
- Proveedor: Ver sus pedidos, confirmar, cambiar estado
- Repartidor: Ver disponibles y asignados, aceptar, cambiar estado
- Admin: Acceso completo a todas las operaciones

==========================================================
"""
