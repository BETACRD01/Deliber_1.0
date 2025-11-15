# -*- coding: utf-8 -*-
# usuarios/urls.py

from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # ==========================================
    # PERFIL
    # ==========================================
    path('perfil/', views.obtener_perfil, name='obtener_perfil'),
    path('perfil/publico/<int:user_id>/', views.obtener_perfil_publico, name='perfil_publico'),
    path('perfil/actualizar/', views.actualizar_perfil, name='actualizar_perfil'),
    path('perfil/estadisticas/', views.estadisticas_usuario, name='estadisticas_usuario'),

    # ==========================================
    # ✅ NOTIFICACIONES PUSH (FCM)
    # ==========================================
    path('fcm-token/', views.registrar_fcm_token, name='registrar_fcm_token'),
    path('fcm-token/eliminar/', views.eliminar_fcm_token, name='eliminar_fcm_token'),
    path('notificaciones/', views.estado_notificaciones, name='estado_notificaciones'),
    # foto de perfil
    path('perfil/foto/', views.subir_foto_perfil, name='subir_foto_perfil'),

    # Ubicación en tiempo real (REST)
    path('ubicacion/actualizar/', views.actualizar_ubicacion, name='actualizar_ubicacion'),
    path('ubicacion/mia/', views.mi_ubicacion, name='mi_ubicacion'),

    # ==========================================
    # DIRECCIONES
    # ==========================================
    path('direcciones/', views.direcciones_favoritas, name='direcciones_favoritas'),
    path('direcciones/<uuid:direccion_id>/', views.detalle_direccion, name='detalle_direccion'),
    path('direcciones/predeterminada/', views.direccion_predeterminada, name='direccion_predeterminada'),

    # ==========================================
    # MÉTODOS DE PAGO
    # ==========================================
    path('metodos-pago/', views.metodos_pago, name='metodos_pago'),
    path('metodos-pago/<uuid:metodo_id>/', views.detalle_metodo_pago, name='detalle_metodo_pago'),
    path('metodos-pago/predeterminado/', views.metodo_pago_predeterminado, name='metodo_pago_predeterminado'),

    # ==========================================
    # SOLICITUDES DE CAMBIO DE ROL (USUARIO)
    # ==========================================
    path('solicitudes-cambio-rol/', views.mis_solicitudes_cambio_rol, name='mis-solicitudes'),
    path('solicitudes-cambio-rol/<uuid:solicitud_id>/', views.detalle_solicitud_cambio_rol, name='detalle-solicitud'),
    path('cambiar-rol-activo/', views.cambiar_rol_activo, name='cambiar-rol-activo'),
    path('mis-roles/', views.mis_roles, name='mis-roles'),
]