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
from .throttles import LoginRateThrottle, RegisterRateThrottle, PasswordResetRateThrottle
import logging
import random
from datetime import timedelta

logger = logging.getLogger('authentication')


# ==========================================
# CONSTANTES
# ==========================================
CODIGO_EXPIRACION_MINUTOS = 15
MAX_INTENTOS_CODIGO = 5


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_tokens_for_user(user):
    """Genera tokens JWT para un usuario"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generar_codigo_recuperacion():
    """
    ✅ Genera un código de 6 dígitos aleatorio
    """
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


def serializar_usuario_basico(user):
    """
    ✅ NUEVO: Serializa datos básicos del usuario para respuestas
    """
    return {
        'id': user.id,
        'email': user.email,
        'nombre': user.first_name,
        'apellido': user.last_name,
        'celular': user.celular,
        'rol': user.rol
    }


# ==========================================
# AUTENTICACIÓN BÁSICA
# ==========================================

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
def registro(request):
    """
    ✅ ACTUALIZADO: Registra usuario y crea perfil automáticamente
    - REPARTIDOR: Crea perfil en app repartidores
    - PROVEEDOR: Crea perfil en app proveedores
    - USUARIO: Solo crea User
    """
    try:
        # ============================================
        # VALIDAR CAMPOS BÁSICOS
        # ============================================
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '').strip()
        password2 = request.data.get('password2', '').strip()
        first_name = request.data.get('first_name', '').strip()
        last_name = request.data.get('last_name', '').strip()
        username = request.data.get('username', '').strip()
        celular = request.data.get('celular', '').strip()
        fecha_nacimiento = request.data.get('fecha_nacimiento')
        terminos_aceptados = request.data.get('terminos_aceptados', False)

        # ROL
        rol = request.data.get('rol', User.RolChoices.USUARIO)

        # Validar campos requeridos
        if not all([email, password, password2, first_name, last_name, username, celular]):
            return Response({
                'error': 'Todos los campos son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validar contraseñas
        if password != password2:
            return Response({
                'error': 'Las contraseñas no coinciden'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validar términos
        if not terminos_aceptados:
            return Response({
                'error': 'Debes aceptar los términos y condiciones'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validar celular
        if not celular.startswith('09') or len(celular) != 10:
            return Response({
                'error': 'El celular debe comenzar con 09 y tener 10 dígitos'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar duplicados
        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'Este email ya está registrado'
            }, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(celular=celular).exists():
            return Response({
                'error': 'Este celular ya está registrado'
            }, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username.lower()).exists():
            return Response({
                'error': 'Este usuario ya está en uso'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validar contraseña segura
        try:
            User.validar_password(password)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # ============================================
        # ✅ VALIDAR CAMPOS ESPECÍFICOS POR ROL
        # ============================================

        # --- REPARTIDOR ---
        if rol == User.RolChoices.REPARTIDOR:
            cedula = request.data.get('cedula', '').strip()
            telefono = request.data.get('telefono', celular).strip()
            tipo_vehiculo = request.data.get('tipo_vehiculo', 'motocicleta')
            placa_vehiculo = request.data.get('placa_vehiculo', '').strip()
            licencia_conducir = request.data.get('licencia_conducir', '').strip()

            # Validar cédula obligatoria
            if not cedula:
                return Response({
                    'error': 'La cédula es requerida para repartidores'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validar formato cédula (10 dígitos)
            if not cedula.isdigit() or len(cedula) != 10:
                return Response({
                    'error': 'La cédula debe tener 10 dígitos numéricos'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validar cédula única
            from repartidores.models import Repartidor
            if Repartidor.objects.filter(cedula=cedula).exists():
                return Response({
                    'error': 'Esta cédula ya está registrada'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validar tipo de vehículo
            from repartidores.models import TipoVehiculo
            if tipo_vehiculo not in dict(TipoVehiculo.choices):
                return Response({
                    'error': f'Tipo de vehículo inválido. Opciones: {", ".join(dict(TipoVehiculo.choices).keys())}'
                }, status=status.HTTP_400_BAD_REQUEST)

        # --- PROVEEDOR ---
        elif rol == User.RolChoices.PROVEEDOR:
            nombre_negocio = request.data.get('nombre_negocio', '').strip()
            ruc = request.data.get('ruc', '').strip()
            direccion_negocio = request.data.get('direccion_negocio', '').strip()
            tipo_proveedor = request.data.get('tipo_proveedor', 'restaurante')
            ciudad = request.data.get('ciudad', '').strip()
            descripcion = request.data.get('descripcion', '').strip()

            # Validar campos obligatorios
            if not nombre_negocio:
                return Response({
                    'error': 'El nombre del negocio es requerido para proveedores'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not ruc:
                return Response({
                    'error': 'El RUC es requerido para proveedores'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validar formato RUC (13 dígitos)
            if not ruc.isdigit() or len(ruc) != 13:
                return Response({
                    'error': 'El RUC debe tener 13 dígitos numéricos'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validar RUC único en Proveedor
            from proveedores.models import Proveedor
            if Proveedor.objects.filter(ruc=ruc).exists():
                return Response({
                    'error': 'Este RUC ya está registrado como proveedor'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validar tipo de proveedor
            tipos_validos = ['restaurante', 'farmacia', 'supermercado', 'tienda', 'otro']
            if tipo_proveedor not in tipos_validos:
                return Response({
                    'error': f'Tipo de proveedor inválido. Opciones: {", ".join(tipos_validos)}'
                }, status=status.HTTP_400_BAD_REQUEST)

        # ============================================
        # ✅ CREAR USUARIO CON TRANSACCIÓN ATÓMICA
        # ============================================
        from django.db import transaction

        with transaction.atomic():
            # Crear User base
            user_data = {
                'username': username.lower(),
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'celular': celular,
                'password': make_password(password),
                'terminos_aceptados': True,
                'terminos_fecha_aceptacion': timezone.now(),
                'terminos_version_aceptada': '1.0',
                'terminos_ip_aceptacion': get_client_ip(request),
                'rol': rol,
            }

            if fecha_nacimiento:
                user_data['fecha_nacimiento'] = fecha_nacimiento

            # Agregar campos de proveedor en User (para compatibilidad)
            if rol == User.RolChoices.PROVEEDOR:
                user_data['nombre_negocio'] = nombre_negocio
                user_data['ruc'] = ruc
                if direccion_negocio:
                    user_data['direccion_negocio'] = direccion_negocio
                if request.data.get('categoria_negocio'):
                    user_data['categoria_negocio'] = request.data['categoria_negocio']

            # CREAR USUARIO
            user = User.objects.create(**user_data)

            # ============================================
            # ✅ CREAR PERFIL DE REPARTIDOR
            # ============================================
            if rol == User.RolChoices.REPARTIDOR:
                from repartidores.models import Repartidor, RepartidorVehiculo

                repartidor = Repartidor.objects.create(
                    user=user,
                    cedula=cedula,
                    telefono=telefono,
                    estado='fuera_servicio',
                    verificado=False,
                    activo=True,
                )

                RepartidorVehiculo.objects.create(
                    repartidor=repartidor,
                    tipo=tipo_vehiculo,
                    placa=placa_vehiculo if placa_vehiculo else None,
                    activo=True,
                )

                logger.info(f"✅ Repartidor creado: {user.email} (Cédula: {cedula})")

            # ============================================
            # ✅ CREAR PERFIL DE PROVEEDOR
            # ============================================
            elif rol == User.RolChoices.PROVEEDOR:
                from proveedores.models import Proveedor

                proveedor = Proveedor.objects.create(
                    user=user,  # ✅ Vincular con User
                    nombre=nombre_negocio,
                    ruc=ruc,
                    telefono=user.celular,
                    email=user.email,
                    direccion=direccion_negocio if direccion_negocio else '',
                    ciudad=ciudad if ciudad else '',
                    tipo_proveedor=tipo_proveedor,
                    descripcion=descripcion if descripcion else '',
                    activo=True,
                    verificado=False,  # ✅ Requiere verificación del admin
                    comision_porcentaje=10.00,
                )

                logger.info(f"✅ Proveedor creado: {user.email} (RUC: {ruc}, Negocio: {nombre_negocio})")

        # ============================================
        # ENVIAR EMAIL DE BIENVENIDA
        # ============================================
        try:
            from .email_utils import enviar_email_bienvenida
            enviar_email_bienvenida(user)
            logger.info(f"✅ Email de bienvenida enviado a: {email}")
        except Exception as email_error:
            logger.error(f"❌ Error enviando email: {email_error}")

        # ============================================
        # GENERAR TOKENS JWT
        # ============================================
        tokens = get_tokens_for_user(user)

        # ============================================
        # RESPUESTA DIFERENCIADA POR ROL
        # ============================================
        usuario_data = serializar_usuario_basico(user)

        mensaje = 'Usuario registrado exitosamente'
        advertencia = None

        if rol == User.RolChoices.PROVEEDOR:
            usuario_data['verificado'] = False
            usuario_data['nombre_negocio'] = nombre_negocio
            usuario_data['ruc'] = ruc
            usuario_data['tipo_proveedor'] = tipo_proveedor
            advertencia = '⚠️ Tu cuenta debe ser verificada por un administrador para poder operar'

        elif rol == User.RolChoices.REPARTIDOR:
            usuario_data['verificado'] = False
            usuario_data['cedula'] = cedula
            advertencia = '⚠️ Tu cuenta debe ser verificada por un administrador antes de recibir pedidos'

        logger.info(f"✅ Usuario registrado: {email} (Rol: {rol})")

        response_data = {
            'mensaje': mensaje,
            'usuario': usuario_data,
            'tokens': tokens
        }

        if advertencia:
            response_data['advertencia'] = advertencia

        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"❌ Error en registro: {e}", exc_info=True)
        return Response({
            'error': 'Error al registrar usuario',
            'detalle': str(e) if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login(request):
    """
    Inicia sesión de usuario con rate limiting automático
    """
    try:
        # Obtener credenciales
        identificador = (
            request.data.get('email') or
            request.data.get('username') or
            request.data.get('usuario')
        )

        if identificador:
            identificador = identificador.strip().lower()

        password = request.data.get('password')

        if not identificador or not password:
            return Response({
                'error': 'Usuario/Email y contraseña son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Buscar usuario
        try:
            if '@' in identificador:
                user = User.objects.get(email=identificador)
            else:
                user = User.objects.filter(
                    models.Q(username=identificador) |
                    models.Q(celular=identificador)
                ).first()

                if not user:
                    raise User.DoesNotExist

            # Verificar cuenta bloqueada
            if user.esta_bloqueado():
                tiempo_restante = (user.cuenta_bloqueada_hasta - timezone.now()).seconds // 60
                return Response({
                    'error': f'Cuenta bloqueada por múltiples intentos fallidos. Intenta en {tiempo_restante} minutos',
                    'bloqueado': True
                }, status=status.HTTP_403_FORBIDDEN)

            # Verificar cuenta desactivada
            if user.cuenta_desactivada:
                return Response({
                    'error': 'Esta cuenta ha sido desactivada. Contacta con soporte si necesitas reactivarla',
                    'desactivada': True
                }, status=status.HTTP_403_FORBIDDEN)

            # Autenticar
            authenticated_user = authenticate(request, username=user.email, password=password)

            if authenticated_user is not None:
                ip_address = get_client_ip(request)
                user.registrar_login_exitoso(ip_address)

                tokens = get_tokens_for_user(user)

                logger.info(f"✅ [OK] Login exitoso: {user.email} desde IP {ip_address}")

                usuario_data = serializar_usuario_basico(user)
                if user.es_proveedor():
                    usuario_data['verificado'] = user.verificado

                return Response({
                    'mensaje': 'Login exitoso',
                    'usuario': usuario_data,
                    'tokens': tokens
                }, status=status.HTTP_200_OK)
            else:
                user.registrar_login_fallido()
                logger.warning(f"⚠️ [!] Login fallido: {identificador}")
                return Response({
                    'error': 'Credenciales inválidas'
                }, status=status.HTTP_401_UNAUTHORIZED)

        except User.DoesNotExist:
            logger.warning(f"⚠️ [!] Intento de login con identificador no registrado: {identificador}")
            return Response({
                'error': 'Credenciales inválidas'
            }, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error en login: {e}")
        return Response({
            'error': 'Error al iniciar sesión',
            'detalle': str(e) if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    """
    Inicia sesión con Google OAuth
    """
    try:
        return Response({
            'error': 'Google login no implementado aún. Usa django-allauth endpoints'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error en Google login: {e}")
        return Response({
            'error': 'Error al iniciar sesión con Google'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Cierra sesión del usuario
    """
    try:
        refresh_token = request.data.get('refresh_token')

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception as e:
                logger.warning(f"⚠️ [!] Error al blacklistear token: {e}")

        logger.info(f"✅ [OK] Logout exitoso: {request.user.email}")

        return Response({
            'mensaje': 'Logout exitoso'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error en logout: {e}")
        return Response({
            'error': 'Error al cerrar sesión'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# PERFIL Y CONFIGURACIÓN
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil(request):
    """
    Obtiene el perfil del usuario autenticado
    """
    try:
        user = request.user

        usuario_data = {
            'id': user.id,
            'email': user.email,
            'nombre': user.first_name,
            'apellido': user.last_name,
            'username': user.username,
            'celular': user.celular,
            'rol': user.rol,
            'fecha_nacimiento': user.fecha_nacimiento,
            'edad': user.get_edad(),
            'fecha_registro': user.date_joined,
            'ultimo_acceso': user.last_login,
            'google_picture': user.google_picture,
            'es_google': user.es_autenticacion_google(),
            'notificaciones_email': user.notificaciones_email,
            'notificaciones_push': user.notificaciones_push,
            'notificaciones_marketing': user.notificaciones_marketing,
            'notificaciones_pedidos': user.notificaciones_pedidos,
        }

        # Agregar campos específicos por rol
        if user.es_proveedor():
            usuario_data.update({
                'nombre_negocio': user.nombre_negocio,
                'verificado': user.verificado,
                'ruc': user.ruc,
                'direccion_negocio': user.direccion_negocio,
                'categoria_negocio': user.categoria_negocio
            })
        elif user.es_repartidor():
            usuario_data.update({
                'disponible': user.disponible,
                'vehiculo': user.vehiculo,
                'placa_vehiculo': user.placa_vehiculo,
                'licencia_conducir': user.licencia_conducir
            })

        return Response({
            'usuario': usuario_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error obteniendo perfil: {e}")
        return Response({
            'error': 'Error al obtener perfil'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def actualizar_perfil(request):
    """
    Actualiza el perfil del usuario
    """
    try:
        user = request.user

        # Campos actualizables base
        campos_actualizables = [
            'first_name', 'last_name', 'celular', 'fecha_nacimiento',
            'notificaciones_email', 'notificaciones_push',
            'notificaciones_marketing', 'notificaciones_pedidos'
        ]

        # Agregar campos específicos por rol
        if user.es_repartidor():
            campos_actualizables.extend(['vehiculo', 'placa_vehiculo', 'licencia_conducir', 'disponible'])
        elif user.es_proveedor():
            campos_actualizables.extend(['nombre_negocio', 'direccion_negocio', 'categoria_negocio'])

        # Actualizar campos
        for campo in campos_actualizables:
            if campo in request.data:
                setattr(user, campo, request.data[campo])

        user.save()

        logger.info(f"✅ [OK] Perfil actualizado: {user.email}")

        return Response({
            'mensaje': 'Perfil actualizado exitosamente',
            'usuario': serializar_usuario_basico(user)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error actualizando perfil: {e}")
        return Response({
            'error': 'Error al actualizar perfil',
            'detalle': str(e) if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def info_rol(request):
    """
    Obtiene información del rol del usuario
    """
    try:
        user = request.user

        return Response({
            'rol': user.rol,
            'rol_display': user.get_rol_display(),
            'permisos': {
                'es_usuario': user.es_usuario(),
                'es_repartidor': user.es_repartidor(),
                'es_proveedor': user.es_proveedor(),
                'es_administrador': user.es_administrador(),
                'puede_crear_rifas': user.puede_crear_rifas(),
                'puede_gestionar_usuarios': user.puede_gestionar_usuarios(),
                'puede_verificar_proveedores': user.puede_verificar_proveedores(),
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error obteniendo info de rol: {e}")
        return Response({
            'error': 'Error al obtener información de rol'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verificar_token(request):
    """
    Verifica si el token JWT es válido
    """
    return Response({
        'valido': True,
        'usuario': {
            'id': request.user.id,
            'email': request.user.email,
            'rol': request.user.rol
        }
    }, status=status.HTTP_200_OK)


# ==========================================
# GESTIÓN DE CONTRASEÑA
# ==========================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cambiar_password(request):
    """
    Cambia la contraseña del usuario autenticado
    """
    try:
        user = request.user
        password_actual = request.data.get('password_actual')
        password_nueva = request.data.get('password_nueva')

        if not password_actual or not password_nueva:
            return Response({
                'error': 'Se requiere contraseña actual y nueva'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password_actual):
            return Response({
                'error': 'Contraseña actual incorrecta'
            }, status=status.HTTP_401_UNAUTHORIZED)

        try:
            User.validar_password(password_nueva)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password_nueva)
        user.save()

        logger.info(f"✅ [OK] Contraseña cambiada: {user.email}")

        return Response({
            'mensaje': 'Contraseña cambiada exitosamente'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error cambiando contraseña: {e}")
        return Response({
            'error': 'Error al cambiar contraseña'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def solicitar_codigo_recuperacion(request):
    """
    ✅ ACTUALIZADO: Solicita un código de 6 dígitos hasheado para recuperación de contraseña

    Request body:
        {
            "email": "usuario@ejemplo.com"
        }

    Response:
        {
            "mensaje": "Si el email existe, recibirás un código de verificación"
        }
    """
    try:
        email = request.data.get('email', '').strip().lower()

        if not email:
            return Response({
                'error': 'Email es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            # Verificar si puede recibir emails
            if not user.notificaciones_email:
                return Response({
                    'error': 'No podemos enviarte un correo porque has desactivado las notificaciones por email'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Verificar cuenta desactivada
            if user.cuenta_desactivada:
                return Response({
                    'error': 'Esta cuenta está desactivada. Contacta con soporte.'
                }, status=status.HTTP_403_FORBIDDEN)

            # ✅ Generar código de 6 dígitos
            codigo = generar_codigo_recuperacion()
            codigo_hasheado = make_password(codigo)  # ✅ Hashear antes de guardar

            # ✅ Guardar código hasheado y resetear intentos
            user.reset_password_code = codigo_hasheado
            user.reset_password_expire = timezone.now() + timedelta(minutes=CODIGO_EXPIRACION_MINUTOS)
            user.reset_password_attempts = 0  # ✅ Resetear intentos
            user.save(update_fields=['reset_password_code', 'reset_password_expire', 'reset_password_attempts'])

            # Enviar email con el código (en texto plano al email)
            try:
                from .email_utils import enviar_codigo_recuperacion_password
                email_enviado = enviar_codigo_recuperacion_password(user, codigo)  # ✅ Enviar código original

                if email_enviado:
                    logger.info(f"✅ [OK] Código de recuperación enviado a: {email}")
                else:
                    logger.warning(f"⚠️ [!] No se pudo enviar código a: {email}")

            except Exception as email_error:
                logger.error(f"❌ [ERROR] Error enviando código: {email_error}")

        except User.DoesNotExist:
            # Por seguridad, no revelamos si el email existe
            logger.warning(f"⚠️ [!] Intento de recuperación para email no existente: {email}")
            pass

        # Siempre retornar el mismo mensaje (seguridad)
        return Response({
            'mensaje': 'Si el email existe, recibirás un código de verificación en unos minutos',
            'expiracion_minutos': CODIGO_EXPIRACION_MINUTOS
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error en solicitar_codigo_recuperacion: {e}")
        return Response({
            'error': 'Error al procesar la solicitud',
            'detalle': str(e) if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def verificar_codigo_recuperacion(request):
    """
    ✅ ACTUALIZADO CON SEGURIDAD: Verifica el código hasheado con límite de intentos

    Request body:
        {
            "email": "usuario@ejemplo.com",
            "codigo": "123456"
        }

    Response:
        {
            "valido": true,
            "mensaje": "Código válido"
        }
    """
    try:
        email = request.data.get('email', '').strip().lower()
        codigo = request.data.get('codigo', '').strip()

        if not email or not codigo:
            return Response({
                'error': 'Email y código son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validar formato del código (6 dígitos)
        if not codigo.isdigit() or len(codigo) != 6:
            return Response({
                'error': 'El código debe tener 6 dígitos'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # ✅ Buscar usuario solo por email y expiración
            user = User.objects.get(
                email=email,
                reset_password_expire__gt=timezone.now()
            )

            # ✅ NUEVO: Verificar límite de intentos
            if user.reset_password_attempts >= MAX_INTENTOS_CODIGO:
                tiempo_restante = (user.reset_password_expire - timezone.now()).seconds // 60
                return Response({
                    'error': f'Demasiados intentos fallidos. Solicita un nuevo código o espera {tiempo_restante} minutos',
                    'bloqueado': True
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            # ✅ NUEVO: Verificar código hasheado
            if not user.reset_password_code or not check_password(codigo, user.reset_password_code):
                # Incrementar contador de intentos
                user.reset_password_attempts += 1
                user.save(update_fields=['reset_password_attempts'])

                intentos_restantes = MAX_INTENTOS_CODIGO - user.reset_password_attempts

                logger.warning(f"⚠️ [!] Código inválido para: {email} (Intento {user.reset_password_attempts}/{MAX_INTENTOS_CODIGO})")

                return Response({
                    'error': 'Código inválido',
                    'valido': False,
                    'intentos_restantes': intentos_restantes
                }, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Código correcto
            logger.info(f"✅ [OK] Código verificado correctamente para: {email}")

            return Response({
                'valido': True,
                'mensaje': 'Código válido. Ahora puedes cambiar tu contraseña',
                'email': user.email
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            logger.warning(f"⚠️ [!] Código inválido o expirado para: {email}")
            return Response({
                'error': 'Código inválido o expirado',
                'valido': False
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error verificando código: {e}")
        return Response({
            'error': 'Error al verificar código'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_con_codigo(request):
    """
    ✅ ACTUALIZADO CON SEGURIDAD: Resetea la contraseña verificando código hasheado

    Request body:
        {
            "email": "usuario@ejemplo.com",
            "codigo": "123456",
            "password": "nuevaPassword123"
        }

    Response:
        {
            "mensaje": "Contraseña cambiada exitosamente"
        }
    """
    try:
        email = request.data.get('email', '').strip().lower()
        codigo = request.data.get('codigo', '').strip()
        nueva_password = request.data.get('password')

        if not email or not codigo or not nueva_password:
            return Response({
                'error': 'Email, código y nueva contraseña son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validar formato del código
        if not codigo.isdigit() or len(codigo) != 6:
            return Response({
                'error': 'El código debe tener 6 dígitos'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validar contraseña
        try:
            User.validar_password(nueva_password)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # ✅ Buscar usuario (sin código en query)
            user = User.objects.get(
                email=email,
                reset_password_expire__gt=timezone.now()
            )

            # ✅ NUEVO: Verificar límite de intentos
            if user.reset_password_attempts >= MAX_INTENTOS_CODIGO:
                return Response({
                    'error': 'Demasiados intentos fallidos. Solicita un nuevo código',
                    'bloqueado': True
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            # ✅ NUEVO: Verificar código hasheado
            if not user.reset_password_code or not check_password(codigo, user.reset_password_code):
                user.reset_password_attempts += 1
                user.save(update_fields=['reset_password_attempts'])

                logger.warning(f"⚠️ [!] Código inválido en reset_password para: {email}")

                return Response({
                    'error': 'Código inválido o expirado',
                    'exito': False
                }, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Cambiar contraseña
            user.set_password(nueva_password)
            user.reset_password_code = None
            user.reset_password_expire = None
            user.reset_password_attempts = 0  # ✅ Resetear intentos
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

            return Response({
                'mensaje': 'Contraseña cambiada exitosamente',
                'exito': True
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            logger.warning(f"⚠️ [!] Código inválido o expirado para: {email}")
            return Response({
                'error': 'Código inválido o expirado',
                'exito': False
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error reseteando contraseña: {e}")
        return Response({
            'error': 'Error al resetear contraseña',
            'detalle': str(e) if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# MÉTODOS ANTIGUOS (MANTENER POR COMPATIBILIDAD)
# ==========================================

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def solicitar_reset_password(request):
    """
    MÉTODO ANTIGUO: Mantener por compatibilidad con versiones anteriores
    """
    return solicitar_codigo_recuperacion(request)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request, token):
    """
    MÉTODO ANTIGUO: Mantener por compatibilidad (aunque ya no se usará)
    """
    return Response({
        'error': 'Este método ha sido reemplazado. Usa el sistema de código de 6 dígitos',
        'endpoints': {
            'solicitar_codigo': '/api/auth/solicitar-codigo-recuperacion/',
            'verificar_codigo': '/api/auth/verificar-codigo/',
            'cambiar_password': '/api/auth/reset-password-con-codigo/'
        }
    }, status=status.HTTP_410_GONE)


# ==========================================
# PREFERENCIAS Y CUENTA
# ==========================================

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def preferencias_notificaciones(request):
    """
    Obtiene o actualiza preferencias de notificaciones
    """
    try:
        user = request.user

        if request.method == 'GET':
            return Response({
                'notificaciones_email': user.notificaciones_email,
                'notificaciones_push': user.notificaciones_push,
                'notificaciones_marketing': user.notificaciones_marketing,
                'notificaciones_pedidos': user.notificaciones_pedidos
            }, status=status.HTTP_200_OK)

        # PUT - Actualizar preferencias
        campos_notificaciones = [
            'notificaciones_email',
            'notificaciones_push',
            'notificaciones_marketing',
            'notificaciones_pedidos'
        ]

        for campo in campos_notificaciones:
            if campo in request.data:
                setattr(user, campo, request.data[campo])

        user.save()

        logger.info(f"✅ [OK] Preferencias de notificaciones actualizadas: {user.email}")

        return Response({
            'mensaje': 'Preferencias actualizadas exitosamente'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error con preferencias: {e}")
        return Response({
            'error': 'Error al gestionar preferencias'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def desactivar_cuenta(request):
    """
    Desactiva la cuenta del usuario
    """
    try:
        user = request.user
        password = request.data.get('password')
        razon = request.data.get('razon', '')

        if not password:
            return Response({
                'error': 'Contraseña requerida para confirmar'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({
                'error': 'Contraseña incorrecta'
            }, status=status.HTTP_401_UNAUTHORIZED)

        user.desactivar_cuenta(razon=razon)

        logger.info(f"✅ [OK] Cuenta desactivada: {user.email} - Razón: {razon}")

        return Response({
            'mensaje': 'Cuenta desactivada exitosamente'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error desactivando cuenta: {e}")
        return Response({
            'error': 'Error al desactivar cuenta'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# UNSUBSCRIBE (DARSE DE BAJA DE EMAILS)
# ==========================================

@api_view(['GET', 'POST'])
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
            return Response({
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        if not default_token_generator.check_token(user, token):
            return Response({
                'error': 'Token inválido o expirado'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Desactivar todas las notificaciones por email
        user.notificaciones_email = False
        user.notificaciones_marketing = False
        user.notificaciones_pedidos = False
        user.save()

        # Enviar confirmación
        try:
            from .email_utils import enviar_email_confirmacion_baja
            enviar_email_confirmacion_baja(user)
        except Exception as email_error:
            logger.error(f"❌ [ERROR] Error enviando confirmación de baja: {email_error}")

        logger.info(f"✅ [OK] Usuario dado de baja de emails: {user.email}")

        return Response({
            'mensaje': 'Te has dado de baja exitosamente de nuestras notificaciones',
            'usuario': {
                'email': user.email,
                'nombre': user.first_name
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ [ERROR] Error en unsubscribe: {e}")
        return Response({
            'error': 'Error al procesar la solicitud de baja'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# DEBUGGING
# ==========================================

@api_view(['GET'])
@permission_classes([AllowAny])
def debug_rate_limit(request):
    """
    Endpoint de debugging para ver info de rate limiting
    (Solo disponible en desarrollo)
    """
    if not settings.DEBUG:
        return Response({
            'error': 'No disponible en producción'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        ip = get_client_ip(request)

        # Intentar obtener info de cache
        login_key = f'throttle_login_{ip}'
        register_key = f'throttle_register_{ip}'

        return Response({
            'ip': ip,
            'cache_info': {
                'login_throttle_key': login_key,
                'register_throttle_key': register_key,
            },
            'rate_limit_config': {
                'login_rate': '20/minute' if settings.DEBUG else '5/minute',
                'register_rate': '20/hour' if settings.DEBUG else '5/hour',
                'password_reset_rate': '10/hour' if settings.DEBUG else '3/hour',
                'enable_login_blocking': getattr(settings, 'ENABLE_LOGIN_BLOCKING', False)
            },
            'constantes': {
                'codigo_expiracion_minutos': CODIGO_EXPIRACION_MINUTOS,
                'max_intentos_codigo': MAX_INTENTOS_CODIGO
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
