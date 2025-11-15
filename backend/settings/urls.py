# settings/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse


def home(request):
    """
    Página de inicio de la API - Muestra endpoints disponibles
    """
    return JsonResponse({
        'message': '¡Bienvenido a Deliber API! 🚀',
        'version': '1.0.0',
        'status': 'online',
        'endpoints': {
            'autenticación': {
                'registro': '/api/auth/registro/',
                'login': '/api/auth/login/',
                'google_login': '/api/auth/google-login/',
                'perfil': '/api/auth/perfil/ (requiere token)',
                'logout': '/api/auth/logout/ (requiere token)',
                'solicitar_codigo_recuperacion': '/api/auth/solicitar-codigo-recuperacion/',
                'verificar_codigo': '/api/auth/verificar-codigo/',
                'reset_password_con_codigo': '/api/auth/reset-password-con-codigo/',
            },
            'usuarios': {
                'perfil': '/api/usuarios/perfil/',
                'perfil_publico': '/api/usuarios/perfil/publico/<user_id>/',
                'actualizar_perfil': '/api/usuarios/perfil/actualizar/',
                'estadisticas': '/api/usuarios/perfil/estadisticas/',
                'foto_perfil': '/api/usuarios/perfil/foto/',
                'direcciones': '/api/usuarios/direcciones/',
                'metodos_pago': '/api/usuarios/metodos-pago/',
                'fcm_token': '/api/usuarios/fcm-token/',
                'notificaciones': '/api/usuarios/notificaciones/',
                'solicitudes_cambio_rol': '/api/usuarios/solicitudes-cambio-rol/',
                'solicitud_detalle': '/api/usuarios/solicitudes-cambio-rol/<uuid>/',
                'cambiar_rol_activo': '/api/usuarios/cambiar-rol-activo/',
                'mis_roles': '/api/usuarios/mis-roles/',
            },
            'proveedores': {
                'listar': '/api/proveedores/',
                'crear': '/api/proveedores/ (POST, admin only)',
                'detalle': '/api/proveedores/<id>/',
                'mi_proveedor': '/api/proveedores/mi_proveedor/',
                'activos': '/api/proveedores/activos/',
                'abiertos': '/api/proveedores/abiertos/',
                'por_tipo': '/api/proveedores/por_tipo/?tipo=restaurante',
            },
            'productos': {
                'categorias': '/api/categorias/',
                'productos': '/api/productos/',
                'destacados': '/api/productos/destacados/',
                'ofertas': '/api/productos/ofertas/',
                'buscar': '/api/productos/buscar/?q=...',
                'variantes': '/api/variantes/',
            },
            'pedidos': {
                'listar_crear': '/api/pedidos/',
                'detalle': '/api/pedidos/<id>/',
                'aceptar_repartidor': '/api/pedidos/<id>/aceptar-repartidor/',
                'confirmar_proveedor': '/api/pedidos/<id>/confirmar-proveedor/',
                'cambiar_estado': '/api/pedidos/<id>/estado/',
                'cancelar': '/api/pedidos/<id>/cancelar/',
                'ganancias': '/api/pedidos/<id>/ganancias/',
            },
            'repartidores': {
                'perfil': '/api/repartidores/perfil/',
                'estadisticas': '/api/repartidores/perfil/estadisticas/',
                'estado': '/api/repartidores/estado/',
                'ubicacion': '/api/repartidores/ubicacion/',
                'vehiculos': '/api/repartidores/vehiculos/',
                'pedidos_disponibles': '/api/repartidores/pedidos-disponibles/',
                'aceptar_pedido': '/api/repartidores/pedidos/<id>/aceptar/',
            },
            'pagos': {
                'metodos': '/api/pagos/metodos/',
                'crear_pago': '/api/pagos/pagos/ (POST)',
                'mis_pagos': '/api/pagos/pagos/mis_pagos/',
                'pendientes_verificacion': '/api/pagos/pagos/pendientes_verificacion/',
                'webhook_stripe': '/api/pagos/webhook/stripe/',
                'webhook_kushki': '/api/pagos/webhook/kushki/',
            },
            'rifas': {
                'listar': '/api/rifas/rifas/',
                'activa': '/api/rifas/rifas/activa/',
                'elegibilidad': '/api/rifas/rifas/<id>/elegibilidad/',
                'mis_participaciones': '/api/rifas/participaciones/mis-participaciones/',
            },
            'notificaciones': {
                'listar': '/api/notificaciones/',
                'no_leidas': '/api/notificaciones/no_leidas/',
                'marcar_leida': '/api/notificaciones/<id>/marcar_leida/',
                'estadisticas': '/api/notificaciones/estadisticas/',
            },
            'chat': {
                'chats': '/api/chat/chats/',
                'crear_soporte': '/api/chat/chats/soporte/',
                'mensajes': '/api/chat/chats/<id>/mensajes/',
                'enviar_mensaje': '/api/chat/chats/<id>/mensajes/ (POST)',
            },
            'reportes': {
                'admin': '/api/reportes/admin/',
                'admin_estadisticas': '/api/reportes/admin/estadisticas/',
                'admin_exportar': '/api/reportes/admin/exportar/',
                'proveedor': '/api/reportes/proveedor/',
                'proveedor_estadisticas': '/api/reportes/proveedor/estadisticas/',
                'repartidor': '/api/reportes/repartidor/',
                'repartidor_estadisticas': '/api/reportes/repartidor/estadisticas/',
            },
            'administración': {
                'usuarios': '/api/admin/usuarios/',
                'proveedores': '/api/admin/proveedores/',
                'repartidores': '/api/admin/repartidores/',
                'dashboard': '/api/admin/dashboard/',
                'alertas': '/api/admin/dashboard/alertas/',
                'configuracion': '/api/admin/configuracion/',
                'solicitudes_cambio_rol': '/api/admin/solicitudes-cambio-rol/',
                'solicitudes_pendientes': '/api/admin/solicitudes-cambio-rol/pendientes/',
                'solicitudes_estadisticas': '/api/admin/solicitudes-cambio-rol/estadisticas/',
                'admin_panel': '/admin/',
            },
        },
        'documentación': {
            'postman_collection': 'Próximamente',
            'swagger': 'Próximamente',
        },
        'tecnologías': {
            'framework': 'Django + DRF',
            'base_de_datos': 'PostgreSQL',
            'cache': 'Redis',
            'storage': 'Local (Media Files)',
            'autenticación': 'JWT + OAuth2',
        }
    }, json_dumps_params={'ensure_ascii': False, 'indent': 2})


urlpatterns = [
    # ==========================================
    # PÁGINA DE INICIO
    # ==========================================
    path('', home, name='home'),

    # ==========================================
    # ADMINISTRACIÓN DJANGO
    # ==========================================
    path('admin/', admin.site.urls),

    # ==========================================
    # APIs - AUTENTICACIÓN Y USUARIOS
    # ==========================================
    path('api/auth/', include('authentication.urls')),
    path('api/usuarios/', include('usuarios.urls')),

    # ==========================================
    # APIs - CORE BUSINESS
    # ==========================================
    path('api/', include('proveedores.urls')),        # /api/proveedores/
    path('api/', include('productos.urls')),          # /api/categorias/, /api/productos/
    path('api/pedidos/', include('pedidos.urls')),    # /api/pedidos/
    path('api/repartidores/', include('repartidores.urls')),  # /api/repartidores/

    # ==========================================
    # APIs - PAGOS Y TRANSACCIONES
    # ==========================================
    path('api/pagos/', include('pagos.urls')),        # /api/pagos/

    # ==========================================
    # APIs - RIFAS
    # ==========================================
    path('api/rifas/', include('rifas.urls')),        # /api/rifas/

    # ==========================================
    # APIs - COMUNICACIÓN
    # ==========================================
    path('api/', include('notificaciones.urls')),    # /api/notificaciones/
    path('api/chat/', include('chat.urls')),          # /api/chat/

    # ==========================================
    # APIs - REPORTES Y ADMINISTRACIÓN
    # ==========================================
    path('api/reportes/', include('reportes.urls')), # /api/reportes/
    path('api/admin/', include('administradores.urls')),  # /api/admin/

    # ==========================================
    # OAUTH (Google)
    # ==========================================
    path('accounts/', include('allauth.urls')),
]

# ============================================
# ✅ URLS PERSONALIZADAS DEL ADMIN (MAPA)
# ============================================
try:
    from repartidores.admin import get_admin_urls
    urlpatterns += get_admin_urls()
    print('✅ Mapa de repartidores registrado: /admin/repartidores/mapa/')
except ImportError as e:
    print(f'⚠️ No se pudo cargar el mapa de repartidores: {e}')

# ============================================
# ✅ CRÍTICO: SERVIR ARCHIVOS MEDIA Y STATIC EN DESARROLLO
# ============================================
if settings.DEBUG:
    # Servir archivos media (fotos de perfil, comprobantes, etc.)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Servir archivos static (CSS, JS, imágenes estáticas)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    print('\n' + '='*60)
    print('✅ SERVIDOR DE DESARROLLO - CONFIGURACIÓN ACTIVA')
    print('='*60)
    print(f'📁 MEDIA_URL: {settings.MEDIA_URL}')
    print(f'📂 MEDIA_ROOT: {settings.MEDIA_ROOT}')
    print(f'🌐 Acceso: http://192.168.1.4:8000{settings.MEDIA_URL}')
    print('\n📡 APIs REGISTRADAS:')
    print('   ✔ Autenticación:    /api/auth/')
    print('   ✔ Usuarios:         /api/usuarios/')
    print('   ✔ Proveedores:      /api/proveedores/')
    print('   ✔ Productos:        /api/productos/ y /api/categorias/')
    print('   ✔ Pedidos:          /api/pedidos/')
    print('   ✔ Repartidores:     /api/repartidores/')
    print('   ✔ Pagos:            /api/pagos/')
    print('   ✔ Rifas:            /api/rifas/')
    print('   ✔ Notificaciones:   /api/notificaciones/')
    print('   ✔ Chat:             /api/chat/')
    print('   ✔ Reportes:         /api/reportes/')
    print('   ✔ Administración:   /api/admin/')
    print('='*60 + '\n')