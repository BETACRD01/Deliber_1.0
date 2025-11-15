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
    path('logout/', views.logout, name='logout'),
    
    # ==========================================
    # PERFIL Y CONFIGURACIÓN
    # ==========================================
    path('perfil/', views.perfil, name='perfil'),
    path('actualizar-perfil/', views.actualizar_perfil, name='actualizar_perfil'),
    path('verificar-token/', views.verificar_token, name='verificar_token'),
    
    # ==========================================
    # GESTIÓN DE CONTRASEÑA
    # ==========================================
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),
    
    # Sistema de código de 6 dígitos para recuperación
    path('solicitar-codigo-recuperacion/', views.solicitar_codigo_recuperacion, name='solicitar_codigo_recuperacion'),
    path('verificar-codigo/', views.verificar_codigo_recuperacion, name='verificar_codigo_recuperacion'),
    path('reset-password-con-codigo/', views.reset_password_con_codigo, name='reset_password_con_codigo'),
    
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
]