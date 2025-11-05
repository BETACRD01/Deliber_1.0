# repartidores/urls.py
from django.urls import path
from . import views

app_name = 'repartidores'

urlpatterns = [
    # ==========================================================
    # PERFIL DEL REPARTIDOR (propio)
    # ==========================================================
    path(
        "perfil/",
        views.obtener_mi_perfil,
        name="perfil"
    ),
    path(
        "perfil/actualizar/",
        views.actualizar_mi_perfil,
        name="actualizar_perfil"
    ),
    path(
        "perfil/estadisticas/",
        views.obtener_estadisticas,
        name="estadisticas"
    ),

    # ==========================================================
    # ESTADO LABORAL (disponible / ocupado / fuera de servicio)
    # ==========================================================
    path(
        "estado/",
        views.cambiar_estado,
        name="cambiar_estado"
    ),
    path(
        "estado/historial/",
        views.historial_estados,
        name="historial_estados"
    ),

    # ==========================================================
    # UBICACIÓN EN TIEMPO REAL
    # ==========================================================
    path(
        "ubicacion/",
        views.actualizar_ubicacion,
        name="actualizar_ubicacion"
    ),
    path(
        "ubicacion/historial/",
        views.historial_ubicaciones,
        name="historial_ubicaciones"
    ),

    # ==========================================================
    # VEHÍCULOS
    # ==========================================================
    path(
        "vehiculos/",
        views.listar_vehiculos,
        name="listar_vehiculos"
    ),
    path(
        "vehiculos/crear/",
        views.crear_vehiculo,
        name="crear_vehiculo"
    ),
    path(
        "vehiculos/<int:vehiculo_id>/",
        views.detalle_vehiculo,
        name="detalle_vehiculo"
    ),
    path(
        "vehiculos/<int:vehiculo_id>/activar/",
        views.activar_vehiculo,
        name="activar_vehiculo"
    ),
    # ✅ NUEVO: Actualizar datos del vehículo activo (tipo, placa, licencia)
    path(
        "vehiculo/actualizar-datos/",
        views.actualizar_datos_vehiculo,
        name="actualizar_datos_vehiculo"
    ),

    # ==========================================================
    # CALIFICACIONES
    # ==========================================================
    path(
        "calificaciones/",
        views.listar_mis_calificaciones,
        name="listar_calificaciones"
    ),
    path(
        "calificaciones/clientes/<int:pedido_id>/",
        views.calificar_cliente,
        name="calificar_cliente"
    ),

    # ==========================================================
    # PERFIL PÚBLICO (visto por el cliente)
    # ==========================================================
    path(
        "publico/<int:pedido_id>/",
        views.perfil_repartidor_por_pedido,
        name="perfil_publico_por_pedido"
    ),
    path(
        "publico/<int:repartidor_id>/info/",
        views.info_repartidor_publico,
        name="info_repartidor_publico"
    ),

    # ==========================================================
    # MAPA DE PEDIDOS (nuevos endpoints)
    # ==========================================================
    path(
        "pedidos-disponibles/",
        views.obtener_pedidos_disponibles_mapa,
        name="pedidos_disponibles_mapa"
    ),
    path(
        "pedidos/<int:pedido_id>/aceptar/",
        views.aceptar_pedido,
        name="aceptar_pedido"
    ),
    path(
        "pedidos/<int:pedido_id>/rechazar/",
        views.rechazar_pedido,
        name="rechazar_pedido"
    ),
]
