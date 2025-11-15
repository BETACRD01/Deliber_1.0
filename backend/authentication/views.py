# -*- coding: utf-8 -*-
# authentication/views.py

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from django.utils import timezone
from django.db import models
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
    Genera tokens JWT con claims personalizados
    """
    refresh = RefreshToken.for_user(user)

    # Agregar claims personalizados al token
    refresh["user_id"] = user.id
    refresh["email"] = user.email

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user_id": user.id,
        "email": user.email,
    }


def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def generar_codigo_recuperacion():
    """
    Genera un código de 6 dígitos aleatorio
    """
    return "".join([str(random.randint(0, 9)) for _ in range(6)])


def serializar_usuario_basico(user):
    """
    Serializa datos básicos del usuario
    """
    return {
        "id": user.id,
        "email": user.email,
        "nombre": user.first_name,
        "apellido": user.last_name,
        "celular": user.celular,
        "username": user.username,
    }


# ==========================================
# AUTENTICACIÓN BÁSICA
# ==========================================


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
def registro(request):
    """
    Registra un nuevo usuario con creación garantizada de Perfil
    """
    try:
        serializer = RegistroSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"ðŸ'¤ Usuario creado: {user.email}")

            try:
                from usuarios.models import Perfil

                perfil, created = Perfil.objects.get_or_create(user=user)

                if created:
                    logger.info(f"âœ… Perfil creado para usuario: {user.email}")
                else:
                    logger.info(f"ðŸ'ï¸ Perfil ya existía para: {user.email}")

            except Exception as perfil_error:
                logger.error(
                    f"âŒ Error creando perfil para {user.email}: {perfil_error}",
                    exc_info=True,
                )

            tokens = get_tokens_for_user(user)
            usuario_data = UserSerializer(user).data

            try:
                from .email_utils import enviar_email_bienvenida

                enviar_email_bienvenida(user)
                logger.info(f"âœ… Email de bienvenida enviado a: {user.email}")
            except Exception as email_error:
                logger.error(f"âŒ Error enviando email: {email_error}")

            logger.info(f"âœ… [OK] Registro exitoso: {user.email}")

            return Response(
                {
                    "mensaje": "Usuario registrado exitosamente",
                    "usuario": usuario_data,
                    "tokens": tokens,
                },
                status=status.HTTP_201_CREATED,
            )

        logger.warning(f"âš ï¸ ValidaciÃ³n fallida en registro: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"âŒ Error en registro: {e}", exc_info=True)
        return Response(
            {
                "error": "Error al registrar usuario",
                "detalle": str(e) if settings.DEBUG else None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login(request):
    """
    Inicia sesión de usuario

    Request body:
        {
            "identificador": "juan@ejemplo.com",  // email o username
            "password": "SecurePass123"
        }
    """
    try:
        serializer = LoginSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            ip_address = get_client_ip(request)
            user.registrar_login_exitoso(ip_address)

            tokens = get_tokens_for_user(user)
            usuario_data = UserSerializer(user).data

            logger.info(f"✅ [OK] Login exitoso: {user.email} desde IP {ip_address}")

            return Response(
                {"mensaje": "Login exitoso", "usuario": usuario_data, "tokens": tokens},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error en login: {e}")
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
    """
    Cierra sesión del usuario

    Request body:
        {
            "refresh_token": "token_aqui"
        }
    """
    try:
        refresh_token = request.data.get("refresh_token")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception as e:
                logger.warning(f"⚠️ [!] Error al blacklistear token: {e}")

        logger.info(f"✅ [OK] Logout exitoso: {request.user.email}")

        return Response({"mensaje": "Logout exitoso"}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error en logout: {e}")
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
    """
    Obtiene el perfil del usuario autenticado
    """
    try:
        user = request.user
        usuario_data = UserSerializer(user).data

        return Response({"usuario": usuario_data}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error obteniendo perfil: {e}")
        return Response(
            {"error": "Error al obtener perfil"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def actualizar_perfil(request):
    """
    Actualiza el perfil del usuario autenticado

    Request body:
        {
            "first_name": "Juan",
            "last_name": "Pérez",
            "celular": "0987654321",
            "fecha_nacimiento": "1990-01-15",
            "notificaciones_email": true,
            "notificaciones_marketing": false,
            "notificaciones_push": true
        }
    """
    try:
        user = request.user
        serializer = ActualizarPerfilSerializer(
            user, data=request.data, partial=True, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            logger.info(f"✅ [OK] Perfil actualizado: {user.email}")

            return Response(
                {
                    "mensaje": "Perfil actualizado exitosamente",
                    "usuario": UserSerializer(user).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error actualizando perfil: {e}")
        return Response(
            {
                "error": "Error al actualizar perfil",
                "detalle": str(e) if settings.DEBUG else None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def verificar_token(request):
    """
    Verifica si el token JWT es válido
    """
    return Response(
        {
            "valido": True,
            "usuario": {
                "id": request.user.id,
                "email": request.user.email,
                "nombre": request.user.first_name,
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
    """
    Cambia la contraseña del usuario autenticado

    Request body:
        {
            "password_actual": "ViejaPass123",
            "password_nueva": "NuevaPass123",
            "password_nueva2": "NuevaPass123"
        }
    """
    try:
        serializer = CambiarPasswordSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            logger.info(f"✅ [OK] Contraseña cambiada: {request.user.email}")

            return Response(
                {"mensaje": "Contraseña cambiada exitosamente"},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error cambiando contraseña: {e}")
        return Response(
            {"error": "Error al cambiar contraseña"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def solicitar_codigo_recuperacion(request):
    """
    Solicita un código de 6 dígitos hasheado para recuperación de contraseña

    Request body:
        {
            "email": "usuario@ejemplo.com"
        }
    """
    try:
        serializer = SolicitarCodigoRecuperacionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)

            # Generar código de 6 dígitos
            codigo = generar_codigo_recuperacion()
            codigo_hasheado = make_password(codigo)

            # Guardar código hasheado
            user.reset_password_code = codigo_hasheado
            user.reset_password_expire = timezone.now() + timedelta(
                minutes=CODIGO_EXPIRACION_MINUTOS
            )
            user.reset_password_attempts = 0
            user.save(
                update_fields=[
                    "reset_password_code",
                    "reset_password_expire",
                    "reset_password_attempts",
                ]
            )

            # Enviar email con el código
            try:
                from .email_utils import enviar_codigo_recuperacion_password

                enviar_codigo_recuperacion_password(user, codigo)
                logger.info(f"✅ [OK] Código de recuperación enviado a: {email}")
            except Exception as email_error:
                logger.error(f"❌ [ERROR] Error enviando código: {email_error}")

        except User.DoesNotExist:
            logger.warning(
                f"⚠️ [!] Intento de recuperación para email no existente: {email}"
            )

        # Siempre retornar el mismo mensaje (por seguridad)
        return Response(
            {
                "mensaje": "Si el email existe, recibirás un código de verificación en unos minutos",
                "expiracion_minutos": CODIGO_EXPIRACION_MINUTOS,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"❌ [ERROR] Error en solicitar_codigo_recuperacion: {e}")
        return Response(
            {
                "error": "Error al procesar la solicitud",
                "detalle": str(e) if settings.DEBUG else None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def verificar_codigo_recuperacion(request):
    """
    Verifica el código hasheado con límite de intentos

    Request body:
        {
            "email": "usuario@ejemplo.com",
            "codigo": "123456"
        }
    """
    try:
        serializer = VerificarCodigoRecuperacionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        codigo = serializer.validated_data["codigo"]

        try:
            user = User.objects.get(
                email=email, reset_password_expire__gt=timezone.now()
            )

            # Verificar límite de intentos
            if user.reset_password_attempts >= MAX_INTENTOS_CODIGO:
                tiempo_restante = (
                    user.reset_password_expire - timezone.now()
                ).seconds // 60
                return Response(
                    {
                        "error": f"Demasiados intentos fallidos. Espera {tiempo_restante} minutos",
                        "bloqueado": True,
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            # Verificar código hasheado
            if not user.reset_password_code or not check_password(
                codigo, user.reset_password_code
            ):
                user.reset_password_attempts += 1
                user.save(update_fields=["reset_password_attempts"])

                intentos_restantes = MAX_INTENTOS_CODIGO - user.reset_password_attempts

                logger.warning(f"⚠️ [!] Código inválido para: {email}")

                return Response(
                    {
                        "error": "Código inválido",
                        "valido": False,
                        "intentos_restantes": intentos_restantes,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            logger.info(f"✅ [OK] Código verificado correctamente para: {email}")

            return Response(
                {
                    "valido": True,
                    "mensaje": "Código válido. Ahora puedes cambiar tu contraseña",
                    "email": user.email,
                },
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            logger.warning(f"⚠️ [!] Código inválido o expirado para: {email}")
            return Response(
                {"error": "Código inválido o expirado", "valido": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        logger.error(f"❌ [ERROR] Error verificando código: {e}")
        return Response(
            {"error": "Error al verificar código"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password_con_codigo(request):
    """
    Resetea la contraseña verificando código hasheado

    Request body:
        {
            "email": "usuario@ejemplo.com",
            "codigo": "123456",
            "password": "NuevaPassword123",
            "password2": "NuevaPassword123"
        }
    """
    try:
        serializer = ResetPasswordConCodigoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        codigo = serializer.validated_data["codigo"]
        nueva_password = serializer.validated_data["password"]

        try:
            user = User.objects.get(
                email=email, reset_password_expire__gt=timezone.now()
            )

            # Verificar límite de intentos
            if user.reset_password_attempts >= MAX_INTENTOS_CODIGO:
                return Response(
                    {
                        "error": "Demasiados intentos fallidos. Solicita un nuevo código",
                        "bloqueado": True,
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            # Verificar código hasheado
            if not user.reset_password_code or not check_password(
                codigo, user.reset_password_code
            ):
                user.reset_password_attempts += 1
                user.save(update_fields=["reset_password_attempts"])

                logger.warning(f"⚠️ [!] Código inválido en reset_password para: {email}")

                return Response(
                    {"error": "Código inválido o expirado", "exito": False},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Cambiar contraseña
            user.set_password(nueva_password)
            user.reset_password_code = None
            user.reset_password_expire = None
            user.reset_password_attempts = 0
            user.intentos_login_fallidos = 0
            user.cuenta_bloqueada_hasta = None
            user.save()

            # Enviar email de confirmación
            try:
                from .email_utils import enviar_confirmacion_cambio_password

                enviar_confirmacion_cambio_password(user)
            except Exception as email_error:
                logger.error(f"❌ [ERROR] Error enviando confirmación: {email_error}")

            logger.info(f"✅ [OK] Contraseña reseteada exitosamente: {user.email}")

            return Response(
                {"mensaje": "Contraseña cambiada exitosamente", "exito": True},
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            logger.warning(f"⚠️ [!] Código inválido o expirado para: {email}")
            return Response(
                {"error": "Código inválido o expirado", "exito": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        logger.error(f"❌ [ERROR] Error reseteando contraseña: {e}")
        return Response(
            {
                "error": "Error al resetear contraseña",
                "detalle": str(e) if settings.DEBUG else None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ==========================================
# PREFERENCIAS Y CUENTA
# ==========================================


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def preferencias_notificaciones(request):
    """
    Obtiene o actualiza preferencias de notificaciones

    GET: Retorna preferencias actuales
    PUT: Actualiza preferencias
        {
            "notificaciones_email": true,
            "notificaciones_marketing": false,
            "notificaciones_push": true
        }
    """
    try:
        user = request.user

        if request.method == "GET":
            serializer = PreferenciasNotificacionesSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # PUT - Actualizar preferencias
        serializer = PreferenciasNotificacionesSerializer(
            user, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            logger.info(f"✅ [OK] Preferencias actualizadas: {user.email}")

            return Response(
                {"mensaje": "Preferencias actualizadas exitosamente"},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error con preferencias: {e}")
        return Response(
            {"error": "Error al gestionar preferencias"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def desactivar_cuenta(request):
    """
    Desactiva la cuenta del usuario

    Request body:
        {
            "password": "TuContraseña123",
            "razon": "Ya no lo necesito (opcional)"
        }
    """
    try:
        serializer = DesactivarCuentaSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            logger.info(f"✅ [OK] Cuenta desactivada: {request.user.email}")

            return Response(
                {"mensaje": "Cuenta desactivada exitosamente"},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error desactivando cuenta: {e}")
        return Response(
            {"error": "Error al desactivar cuenta"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ==========================================
# UNSUBSCRIBE (DARSE DE BAJA DE EMAILS)
# ==========================================


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def unsubscribe_emails(request, user_id, token):
    """
    Permite a los usuarios darse de baja de las notificaciones por email
    """
    try:
        from django.contrib.auth.tokens import default_token_generator

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"error": "Token inválido o expirado"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Desactivar todas las notificaciones por email
        user.notificaciones_email = False
        user.notificaciones_marketing = False
        user.save()

        # Enviar confirmación
        try:
            from .email_utils import enviar_email_confirmacion_baja

            enviar_email_confirmacion_baja(user)
        except Exception as email_error:
            logger.error(
                f"❌ [ERROR] Error enviando confirmación de baja: {email_error}"
            )

        logger.info(f"✅ [OK] Usuario dado de baja de emails: {user.email}")

        return Response(
            {
                "mensaje": "Te has dado de baja exitosamente de nuestras notificaciones",
                "usuario": {"email": user.email, "nombre": user.first_name},
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"❌ [ERROR] Error en unsubscribe: {e}")
        return Response(
            {"error": "Error al procesar la solicitud de baja"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
