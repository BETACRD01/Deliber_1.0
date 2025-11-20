# -*- coding: utf-8 -*-
# authentication/views.py

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from django.utils import timezone
from django.db import transaction  # <--- CRÍTICO: Para integridad de datos
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    RegistroSerializer,
    LoginSerializer,
    CambiarPasswordSerializer,
    SolicitarCodigoRecuperacionSerializer,
    VerificarCodigoRecuperacionSerializer,
    ResetPasswordConCodigoSerializer,
    ActualizarPerfilSerializer,
    PreferenciasNotificacionesSerializer,
    DesactivarCuentaSerializer,
    UserSerializer,
)
from .throttles import (
    LoginRateThrottle,
    RegisterRateThrottle,
    PasswordResetRateThrottle,
)
from .email_utils import (
    enviar_email_bienvenida,
    enviar_codigo_recuperacion_password,
    enviar_confirmacion_cambio_password,
    enviar_email_confirmacion_baja
)

import logging
import random
from datetime import timedelta

logger = logging.getLogger("authentication")


# ==========================================
# CONSTANTES
# ==========================================
CODIGO_EXPIRACION_MINUTOS = 15
MAX_INTENTOS_CODIGO = 5


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_tokens_for_user(user):
    """
    Genera tokens JWT con claims personalizados.
    Optimizado: Usa configuración SIMPLE_JWT de settings.
    """
    refresh = RefreshToken.for_user(user)

    # Claims personalizados útiles para el Frontend
    refresh["user_id"] = user.id
    refresh["email"] = user.email
    # Añadimos rol si existe para evitar request extra
    if hasattr(user, 'rol'):
        refresh["rol"] = user.rol

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user_id": user.id,
        "email": user.email,
    }


def get_client_ip(request):
    """Obtiene la IP real del cliente (Soporte Docker/Proxy)"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def generar_codigo_recuperacion():
    """Genera un código de 6 dígitos aleatorio"""
    return "".join([str(random.randint(0, 9)) for _ in range(6)])


# ==========================================
# AUTENTICACIÓN BÁSICA
# ==========================================

@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
def registro(request):
    """
    Registra un nuevo usuario con ATOMICIDAD garantizada.
    Si falla la creación del perfil, se deshace la creación del usuario.
    """
    try:
        serializer = RegistroSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            # ⚡ OPTIMIZACIÓN: Atomicidad
            # Todo lo que ocurra aquí dentro es "todo o nada"
            with transaction.atomic():
                # 1. Crear Usuario
                user = serializer.save()
                logger.info(f"👤 Usuario base creado: {user.email}")

                # 2. Crear Perfil (Safe Import para evitar ciclos)
                try:
                    from usuarios.models import Perfil
                    # get_or_create es redundante en registro nuevo, create es más rápido
                    # pero lo dejamos así por seguridad.
                    perfil, created = Perfil.objects.get_or_create(user=user)
                    
                    if created:
                        logger.info(f"✅ Perfil vinculado exitosamente: {user.email}")
                
                except Exception as perfil_error:
                    # Si falla el perfil, lanzamos error para que transaction.atomic
                    # deshaga la creación del usuario (evita usuarios corruptos)
                    logger.error(f"⛔ Error creando perfil, revirtiendo usuario: {perfil_error}")
                    raise Exception(f"Error crítico al crear perfil: {str(perfil_error)}")

                # 3. Preparar respuesta (dentro de la transacción para asegurar lectura consistente)
                tokens = get_tokens_for_user(user)
                usuario_data = UserSerializer(user).data

            # 4. Enviar Email (FUERA de la transacción para no bloquear DB si el email tarda,
            # aunque ya es asíncrono gracias a nuestro arreglo anterior)
            try:
                enviar_email_bienvenida(user)
            except Exception as e:
                logger.warning(f"⚠️ Usuario creado pero falló email bienvenida: {e}")

            return Response(
                {
                    "mensaje": "Usuario registrado exitosamente",
                    "usuario": usuario_data,
                    "tokens": tokens,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"❌ Error crítico en registro: {e}", exc_info=True)
        return Response(
            {
                "error": "Error al registrar usuario",
                "detalle": str(e) if settings.DEBUG else "Contacte a soporte",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login(request):
    """
    Inicia sesión de usuario.
    Optimizado para responder rápido.
    """
    try:
        serializer = LoginSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            
            # Tarea liviana de DB
            ip_address = get_client_ip(request)
            user.registrar_login_exitoso(ip_address)

            # Generación rápida de tokens (CPU bound, no I/O bound)
            tokens = get_tokens_for_user(user)
            usuario_data = UserSerializer(user).data

            logger.info(f"✅ Login exitoso: {user.email} desde IP {ip_address}")

            return Response(
                {"mensaje": "Login exitoso", "usuario": usuario_data, "tokens": tokens},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        logger.error(f"❌ Error en login: {e}")
        return Response(
            {
                "error": "Error al iniciar sesión",
                "detalle": str(e) if settings.DEBUG else None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """Cierra sesión del usuario (Blacklist token)"""
    try:
        refresh_token = request.data.get("refresh_token")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception as e:
                logger.warning(f"⚠️ Token inválido en logout: {e}")

        return Response({"mensaje": "Logout exitoso"}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ Error en logout: {e}")
        return Response(
            {"error": "Error al cerrar sesión"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ==========================================
# PERFIL Y CONFIGURACIÓN
# ==========================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def perfil(request):
    """Obtiene el perfil del usuario"""
    try:
        # Serializer usa datos ya cargados en request.user, muy rápido
        usuario_data = UserSerializer(request.user).data
        return Response({"usuario": usuario_data}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"❌ Error obteniendo perfil: {e}")
        return Response({"error": "Error interno"}, status=500)


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def actualizar_perfil(request):
    """Actualiza el perfil"""
    try:
        user = request.user
        serializer = ActualizarPerfilSerializer(
            user, data=request.data, partial=True, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "mensaje": "Perfil actualizado",
                    "usuario": UserSerializer(user).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"❌ Error actualizando perfil: {e}")
        return Response({"error": "Error al actualizar"}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def verificar_token(request):
    """Ping simple para verificar validez del token"""
    return Response(
        {
            "valido": True,
            "usuario": {
                "id": request.user.id,
                "email": request.user.email,
                "rol": getattr(request.user, 'rol', 'USUARIO')
            },
        },
        status=status.HTTP_200_OK,
    )


# ==========================================
# GESTIÓN DE CONTRASEÑA
# ==========================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cambiar_password(request):
    """Cambia contraseña de usuario logueado"""
    try:
        serializer = CambiarPasswordSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            # Notificar cambio (Async)
            try:
                enviar_confirmacion_cambio_password(request.user)
            except: pass

            return Response({"mensaje": "Contraseña actualizada"}, status=200)

        return Response(serializer.errors, status=400)

    except Exception as e:
        logger.error(f"❌ Error cambiando password: {e}")
        return Response({"error": "Error interno"}, status=500)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def solicitar_codigo_recuperacion(request):
    """Solicita código de recuperación"""
    try:
        serializer = SolicitarCodigoRecuperacionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
            codigo = generar_codigo_recuperacion()
            
            # Optimizacion: update_fields para no reescribir toda la fila
            user.reset_password_code = make_password(codigo)
            user.reset_password_expire = timezone.now() + timedelta(minutes=CODIGO_EXPIRACION_MINUTOS)
            user.reset_password_attempts = 0
            user.save(update_fields=["reset_password_code", "reset_password_expire", "reset_password_attempts"])

            # Envío Async
            enviar_codigo_recuperacion_password(user, codigo)
            logger.info(f"✅ Código enviado a: {email}")

        except User.DoesNotExist:
            # Timing attack protection: tardar lo mismo que si existiera (opcional)
            pass

        return Response(
            {"mensaje": "Si el email existe, recibirás el código en breve"},
            status=200,
        )

    except Exception as e:
        logger.error(f"❌ Error solicitud recuperación: {e}")
        return Response({"error": "Error procesando solicitud"}, status=500)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def verificar_codigo_recuperacion(request):
    """Verifica si el código es válido"""
    try:
        serializer = VerificarCodigoRecuperacionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data["email"]
        codigo = serializer.validated_data["codigo"]

        try:
            user = User.objects.get(email=email, reset_password_expire__gt=timezone.now())

            if user.reset_password_attempts >= MAX_INTENTOS_CODIGO:
                return Response({"error": "Demasiados intentos. Solicita nuevo código"}, status=429)

            if not user.reset_password_code or not check_password(codigo, user.reset_password_code):
                user.reset_password_attempts += 1
                user.save(update_fields=["reset_password_attempts"])
                return Response({"error": "Código inválido", "valido": False}, status=400)

            return Response(
                {"valido": True, "mensaje": "Código correcto", "email": user.email},
                status=200,
            )

        except User.DoesNotExist:
            return Response({"error": "Código expirado o inválido"}, status=400)

    except Exception as e:
        logger.error(f"❌ Error verificando código: {e}")
        return Response({"error": "Error interno"}, status=500)


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password_con_codigo(request):
    """Resetea la contraseña final usando el código"""
    try:
        serializer = ResetPasswordConCodigoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data["email"]
        codigo = serializer.validated_data["codigo"]
        nueva_password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email, reset_password_expire__gt=timezone.now())

            if not user.reset_password_code or not check_password(codigo, user.reset_password_code):
                return Response({"error": "Código inválido"}, status=400)

            with transaction.atomic():
                user.set_password(nueva_password)
                user.reset_password_code = None
                user.reset_password_expire = None
                user.reset_password_attempts = 0
                user.save()

            try:
                enviar_confirmacion_cambio_password(user)
            except: pass

            return Response({"mensaje": "Contraseña cambiada con éxito", "exito": True}, status=200)

        except User.DoesNotExist:
            return Response({"error": "Solicitud inválida"}, status=400)

    except Exception as e:
        logger.error(f"❌ Error reset password: {e}")
        return Response({"error": "Error interno"}, status=500)


# ==========================================
# PREFERENCIAS Y CUENTA
# ==========================================

@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def preferencias_notificaciones(request):
    """Gestiona preferencias"""
    user = request.user
    if request.method == "GET":
        return Response(PreferenciasNotificacionesSerializer(user).data)

    serializer = PreferenciasNotificacionesSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"mensaje": "Preferencias guardadas"}, status=200)
    return Response(serializer.errors, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def desactivar_cuenta(request):
    """Desactiva la cuenta"""
    serializer = DesactivarCuentaSerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        serializer.save()
        try:
            enviar_email_confirmacion_baja(request.user)
        except: pass
        return Response({"mensaje": "Cuenta desactivada"}, status=200)
    return Response(serializer.errors, status=400)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def unsubscribe_emails(request, user_id, token):
    """Endpoint público para darse de baja"""
    from django.contrib.auth.tokens import default_token_generator
    try:
        user = User.objects.get(id=user_id)
        if not default_token_generator.check_token(user, token):
            return Response({"error": "Link inválido"}, status=400)

        user.notificaciones_email = False
        user.notificaciones_marketing = False
        user.save(update_fields=['notificaciones_email', 'notificaciones_marketing'])
        
        return Response({"mensaje": "Te has dado de baja correctamente"}, status=200)
    except User.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=404)
    except Exception as e:
        logger.error(f"Error unsubscribe: {e}")
        return Response({"error": "Error procesando solicitud"}, status=500)