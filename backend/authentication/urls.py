# -*- coding: utf-8 -*-
# authentication/urls.py

from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # ==========================================
    # AUTENTICACIÓN BÁSICA
    # ==========================================
    path('registro/', views.registro, name='registro'),
    path('login/', views.login, name='login'),
    path('google-login/', views.google_login, name='google_login'),
    path('logout/', views.logout, name='logout'),
    
    # ==========================================
    # PERFIL Y CONFIGURACIÓN
    # ==========================================
    path('perfil/', views.perfil, name='perfil'),
    path('actualizar-perfil/', views.actualizar_perfil, name='actualizar_perfil'),
    path('info-rol/', views.info_rol, name='info_rol'),
    path('verificar-token/', views.verificar_token, name='verificar_token'),
    
    # ==========================================
    # GESTIÓN DE CONTRASEÑA
    # ==========================================
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),
    
    # ✅ NUEVO: Sistema de código de 6 dígitos
    path('solicitar-codigo-recuperacion/', views.solicitar_codigo_recuperacion, name='solicitar_codigo_recuperacion'),
    path('verificar-codigo/', views.verificar_codigo_recuperacion, name='verificar_codigo_recuperacion'),
    path('reset-password-con-codigo/', views.reset_password_con_codigo, name='reset_password_con_codigo'),
    
    # OBSOLETO: Mantener por compatibilidad (redirige al nuevo sistema)
    path('solicitar-reset-password/', views.solicitar_reset_password, name='solicitar_reset_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    
    # ==========================================
    # PREFERENCIAS Y CUENTA
    # ==========================================
    path('preferencias-notificaciones/', views.preferencias_notificaciones, name='preferencias_notificaciones'),
    path('desactivar-cuenta/', views.desactivar_cuenta, name='desactivar_cuenta'),
    
    # ==========================================
    # UNSUBSCRIBE (DARSE DE BAJA)
    # ==========================================
    path('unsubscribe/<int:user_id>/<str:token>/', views.unsubscribe_emails, name='unsubscribe_emails'),
    
    # ==========================================
    # JWT TOKEN REFRESH
    # ==========================================
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ==========================================
    # DEBUGGING (solo desarrollo)
    # ==========================================
    path('debug/rate-limit/', views.debug_rate_limit, name='debug_rate_limit'),
]