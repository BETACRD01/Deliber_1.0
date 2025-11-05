# usuarios/views.py - VERSIÓN COMPLETA CON LOGS DE DEBUG

from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.conf import settings
from .models import Perfil, DireccionFavorita, MetodoPago, UbicacionUsuario
from .serializers import (
    PerfilSerializer,
    PerfilPublicoSerializer,
    DireccionFavoritaSerializer,
    CrearDireccionSerializer,
    ActualizarDireccionSerializer,
    ActualizarPerfilSerializer,
    MetodoPagoSerializer,
    CrearMetodoPagoSerializer,
    ActualizarMetodoPagoSerializer,
    EstadisticasUsuarioSerializer,
    FCMTokenSerializer,
    EstadoNotificacionesSerializer,
    UbicacionUsuarioSerializer,
    ActualizarUbicacionSerializer,
)
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import logging
import os

logger = logging.getLogger('usuarios')


# ============================================
# ✅ THROTTLING CORREGIDO
# ============================================

class UploadThrottle(UserRateThrottle):
    """Límite para subida de archivos (imágenes, comprobantes)"""
    rate = '30/hour'  # ✅ AUMENTADO: 10 → 30


class FCMThrottle(UserRateThrottle):
    """Límite para registro de tokens FCM"""
    rate = '60/hour'  # ✅ AUMENTADO: 20 → 60


class UbicacionThrottle(UserRateThrottle):
    """✅ NUEVO: Límite más generoso para ubicación"""
    rate = '300/hour'  # 5 por minuto, ideal para updates cada 30s


class PerfilThrottle(UserRateThrottle):
    """✅ NUEVO: Límite específico para actualización de perfil"""
    rate = '30/hour'


# ============================================
# PAGINACIÓN
# ============================================

class StandardResultsSetPagination(PageNumberPagination):
    """Paginación estándar para listados"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ============================================
# PERFIL DEL USUARIO
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_perfil(request):
    """
    Obtiene el perfil del usuario autenticado
    ✅ Optimizado con select_related
    """
    try:
        user = request.user

        # Optimización: select_related para evitar query adicional
        perfil = get_object_or_404(
            Perfil.objects.select_related('user'),
            user=user
        )

        serializer = PerfilSerializer(perfil)

        logger.info(f"Perfil obtenido: {user.email}")

        return Response({
            'perfil': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error obteniendo perfil: {e}", exc_info=True)
        return Response({
            'error': 'Error al obtener perfil'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_perfil_publico(request, user_id):
    """
    Obtiene el perfil público de otro usuario (sin datos sensibles)
    ✅ Optimizado con select_related
    """
    try:
        perfil = get_object_or_404(
            Perfil.objects.select_related('user'),
            user_id=user_id
        )

        serializer = PerfilPublicoSerializer(perfil)

        logger.info(f"Perfil público consultado: user_id={user_id} por {request.user.email}")

        return Response({
            'perfil': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error obteniendo perfil público: {e}", exc_info=True)
        return Response({
            'error': 'Perfil no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)


# usuarios/views.py (línea ~160, en actualizar_perfil)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
#@throttle_classes([PerfilThrottle])
def actualizar_perfil(request):
    """
    Actualiza la información del perfil
    ✅ SOPORTA actualización de celular en User
    """
    try:
        user = request.user
        perfil = get_object_or_404(Perfil.objects.select_related('user'), user=user)

        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)

        # ✅ NUEVO: Si viene 'telefono', actualizar user.celular
        if 'telefono' in data:
            nuevo_celular = data.pop('telefono')  # Remover de data del perfil

            # Validar formato (09 + 8 dígitos)
            import re
            if not re.match(r'^09\d{8}$', nuevo_celular):
                return Response({
                    'error': 'El celular debe comenzar con 09 y tener 10 dígitos'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Verificar que no esté en uso por otro usuario
            from authentication.models import User
            if User.objects.filter(celular=nuevo_celular).exclude(id=user.id).exists():
                return Response({
                    'error': 'Este celular ya está registrado'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Actualizar celular del User
            user.celular = nuevo_celular
            user.save(update_fields=['celular'])
            logger.info(f"📱 Celular actualizado: {user.email} -> {nuevo_celular}")

        # Manejar caso especial: borrar foto
        if 'foto_perfil' in data and data['foto_perfil'] in [None, '', 'null']:
            data['foto_perfil'] = None

        # Actualizar perfil
        serializer = ActualizarPerfilSerializer(perfil, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            logger.info(f"✅ Perfil actualizado: {user.email}")

            # Devolver perfil completo actualizado
            perfil.refresh_from_db()
            return Response({
                'mensaje': 'Perfil actualizado exitosamente',
                'perfil': PerfilSerializer(perfil, context={'request': request}).data
            }, status=status.HTTP_200_OK)

        logger.warning(f"⚠️ Validación fallida: {serializer.errors}")
        return Response({
            'error': 'Error de validación',
            'detalles': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"❌ Error actualizando perfil: {e}", exc_info=True)
        return Response({
            'error': 'Error al actualizar perfil',
            'detalle': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estadisticas_usuario(request):
    """
    Obtiene las estadísticas del usuario
    ✅ CORREGIDO: Manejo de errores robusto y creación de perfil si no existe
    """
    try:
        user = request.user

        # ✅ CRÍTICO: Crear perfil si no existe (por si la señal falló)
        perfil, created = Perfil.objects.get_or_create(user=user)

        if created:
            logger.warning(f"⚠️ Perfil creado tardíamente para {user.email}")

        # ✅ Optimización: usar count() con manejo de errores individual
        try:
            total_direcciones = user.direcciones_favoritas.filter(activa=True).count()
        except Exception as e:
            logger.error(f"❌ Error contando direcciones: {e}")
            total_direcciones = 0

        try:
            total_metodos_pago = user.metodos_pago.filter(activo=True).count()
        except Exception as e:
            logger.error(f"❌ Error contando métodos de pago: {e}")
            total_metodos_pago = 0

        # ✅ Construir estadísticas con valores seguros
        estadisticas = {
            'total_pedidos': perfil.total_pedidos if perfil.total_pedidos is not None else 0,
            'pedidos_mes_actual': perfil.pedidos_mes_actual if perfil.pedidos_mes_actual is not None else 0,
            'calificacion': float(perfil.calificacion) if perfil.calificacion is not None else 5.0,
            'total_resenas': perfil.total_resenas if perfil.total_resenas is not None else 0,
            'es_cliente_frecuente': perfil.es_cliente_frecuente,
            'puede_participar_rifa': perfil.puede_participar_rifa,
            'total_direcciones': total_direcciones,
            'total_metodos_pago': total_metodos_pago
        }

        serializer = EstadisticasUsuarioSerializer(estadisticas)

        logger.info(f"✅ Estadísticas consultadas: {user.email}")

        return Response({
            'estadisticas': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}", exc_info=True)
        return Response({
            'error': 'Error al obtener estadísticas',
            'detalle': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================
# ✅ FOTO DE PERFIL CON VALIDACIÓN, THROTTLING Y DEBUG
# ============================================

@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
# @throttle_classes([UploadThrottle])  # ✅ COMENTADO en desarrollo
def subir_foto_perfil(request):
    """
    POST: Sube o actualiza la foto de perfil
    DELETE: Elimina la foto de perfil
    ✅ Con validación de imagen, throttling y LOGS DE DEBUG
    """
    try:
        user = request.user
        perfil = get_object_or_404(
            Perfil.objects.select_related('user'),
            user=user
        )

        if request.method == 'POST':
            # ✅ LOG 1: Inicio del proceso
            logger.info(f'🚀 Iniciando subida de foto: {user.email}')

            # Validar que venga la foto
            if 'foto_perfil' not in request.FILES:
                logger.warning(f'❌ No se envió archivo: {user.email}')
                return Response({
                    'error': 'Debes enviar el archivo con el nombre "foto_perfil"'
                }, status=status.HTTP_400_BAD_REQUEST)

            foto = request.FILES['foto_perfil']

            # ✅ LOG 2: Información del archivo recibido
            logger.info(f'📥 Archivo recibido:')
            logger.info(f'   - Nombre: {foto.name}')
            logger.info(f'   - Tamaño: {foto.size} bytes ({foto.size / 1024:.2f} KB)')
            logger.info(f'   - Content-Type: {foto.content_type}')

            # Validar tamaño (5MB máximo)
            max_size = 5 * 1024 * 1024
            if foto.size > max_size:
                tamano_mb = foto.size / (1024 * 1024)
                logger.warning(f'❌ Archivo muy grande: {tamano_mb:.1f}MB')
                return Response({
                    'error': f'La imagen no puede superar 5MB (tamaño actual: {tamano_mb:.1f}MB)'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validar extensión
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            ext = os.path.splitext(foto.name)[1].lower()
            if ext not in valid_extensions:
                logger.warning(f'❌ Extensión no válida: {ext}')
                return Response({
                    'error': f'Formato no válido. Use: {", ".join(valid_extensions)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            # ✅ LOG 3: Configuración de Django
            logger.info(f'📂 Configuración Django:')
            logger.info(f'   - MEDIA_ROOT: {settings.MEDIA_ROOT}')
            logger.info(f'   - MEDIA_URL: {settings.MEDIA_URL}')
            logger.info(f'   - BASE_DIR: {settings.BASE_DIR}')

            # ✅ LOG 4: Verificar que MEDIA_ROOT existe
            if not os.path.exists(settings.MEDIA_ROOT):
                logger.error(f'❌ MEDIA_ROOT NO EXISTE: {settings.MEDIA_ROOT}')
                logger.info(f'📁 Intentando crear MEDIA_ROOT...')
                try:
                    os.makedirs(settings.MEDIA_ROOT, mode=0o755, exist_ok=True)
                    logger.info(f'✅ MEDIA_ROOT creado: {settings.MEDIA_ROOT}')
                except Exception as e:
                    logger.error(f'❌ Error creando MEDIA_ROOT: {e}')
            else:
                logger.info(f'✅ MEDIA_ROOT existe')
                # Verificar permisos
                import stat
                permisos = oct(os.stat(settings.MEDIA_ROOT).st_mode)[-3:]
                logger.info(f'🔐 Permisos MEDIA_ROOT: {permisos}')

            # ✅ LOG 5: Procesar imagen con PIL (redimensionar)
            try:
                logger.info(f'🖼️  Procesando imagen con PIL...')
                img = Image.open(foto)
                logger.info(f'   - Formato original: {img.format}')
                logger.info(f'   - Modo: {img.mode}')
                logger.info(f'   - Tamaño: {img.size}')

                # Redimensionar
                img.thumbnail((800, 800), Image.Resampling.LANCZOS)
                logger.info(f'   - Nuevo tamaño: {img.size}')

                # Convertir a RGB si es necesario
                if img.mode in ('RGBA', 'P', 'LA'):
                    logger.info(f'   - Convirtiendo {img.mode} → RGB')
                    img = img.convert('RGB')

                # Guardar en memoria
                output = BytesIO()
                img.save(output, format='JPEG', quality=85, optimize=True)
                output.seek(0)

                # Crear nuevo archivo
                foto = InMemoryUploadedFile(
                    output,
                    'ImageField',
                    f'scaled_{os.path.basename(foto.name)}',
                    'image/jpeg',
                    output.getbuffer().nbytes,
                    None
                )

                logger.info(f'✅ Imagen procesada: {foto.size} bytes ({foto.size / 1024:.2f} KB)')

            except Exception as e:
                logger.error(f'❌ Error procesando imagen: {str(e)}')
                logger.exception('Traceback completo:')
                return Response({
                    'error': f'Error al procesar imagen: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            # ✅ LOG 6: Antes de guardar en el modelo
            logger.info(f'💾 Guardando en modelo Django...')
            logger.info(f'   - Perfil ID: {perfil.id}')
            logger.info(f'   - Usuario: {perfil.user.email}')

            # Guardar foto anterior para eliminarla después
            foto_anterior = perfil.foto_perfil.name if perfil.foto_perfil else None
            if foto_anterior:
                logger.info(f'   - Foto anterior: {foto_anterior}')

            # Actualizar foto
            perfil.foto_perfil = foto
            perfil.save(update_fields=['foto_perfil', 'actualizado_en'])

            # ✅ LOG 7: Después de guardar
            logger.info(f'📸 Foto de perfil actualizada: {user.email}')
            logger.info(f'📁 Información del archivo guardado:')
            logger.info(f'   - Ruta completa: {perfil.foto_perfil.path}')
            logger.info(f'   - Ruta relativa: {perfil.foto_perfil.name}')
            logger.info(f'   - URL pública: {perfil.foto_perfil.url}')

            # ✅ LOG 8: Verificar que existe físicamente
            if os.path.exists(perfil.foto_perfil.path):
                tamaño = os.path.getsize(perfil.foto_perfil.path)
                logger.info(f'✅ ¡ARCHIVO EXISTE FÍSICAMENTE!')
                logger.info(f'   - Tamaño en disco: {tamaño} bytes ({tamaño / 1024:.2f} KB)')

                # Permisos del archivo
                import stat
                permisos = oct(os.stat(perfil.foto_perfil.path).st_mode)[-3:]
                logger.info(f'   - Permisos: {permisos}')

            else:
                logger.error(f'❌ ¡ARCHIVO NO EXISTE FÍSICAMENTE!')
                logger.error(f'❌ Ruta esperada: {perfil.foto_perfil.path}')
                logger.error(f'❌ Esto es un ERROR CRÍTICO')

            # ✅ LOG 9: Verificar directorio
            directorio = os.path.dirname(perfil.foto_perfil.path)
            logger.info(f'📂 Verificando directorio:')
            logger.info(f'   - Ruta: {directorio}')

            if os.path.exists(directorio):
                logger.info(f'   - ✅ Directorio existe')

                # Listar archivos
                try:
                    archivos = os.listdir(directorio)
                    logger.info(f'   - Archivos en directorio: {archivos}')
                    logger.info(f'   - Total de archivos: {len(archivos)}')

                    # Permisos del directorio
                    import stat
                    permisos_dir = oct(os.stat(directorio).st_mode)[-3:]
                    logger.info(f'   - Permisos del directorio: {permisos_dir}')

                except Exception as e:
                    logger.error(f'   - ❌ Error listando directorio: {e}')

            else:
                logger.error(f'   - ❌ Directorio NO existe')
                logger.info(f'   - 📁 Intentando crear directorio...')
                try:
                    os.makedirs(directorio, mode=0o755, exist_ok=True)
                    logger.info(f'   - ✅ Directorio creado')
                except Exception as e:
                    logger.error(f'   - ❌ Error creando directorio: {e}')

            # ✅ Refrescar perfil y devolver serializado completo
            perfil.refresh_from_db()

            logger.info(f'✅ Respuesta enviada con perfil completo')

            return Response({
                'mensaje': 'Foto de perfil actualizada exitosamente',
                'perfil': PerfilSerializer(perfil).data
            }, status=status.HTTP_200_OK)

        # DELETE - Eliminar foto
        else:
            if not perfil.foto_perfil:
                logger.warning(f'⚠️ No hay foto para eliminar: {user.email}')
                return Response({
                    'mensaje': 'No tienes foto de perfil para eliminar'
                }, status=status.HTTP_404_NOT_FOUND)

            # Obtener ruta antes de eliminar
            ruta_foto = perfil.foto_perfil.path if perfil.foto_perfil else None

            # Eliminar foto
            perfil.foto_perfil.delete(save=False)
            perfil.foto_perfil = None
            perfil.save(update_fields=['foto_perfil', 'actualizado_en'])

            logger.info(f'🗑️ Foto de perfil eliminada: {user.email}')
            if ruta_foto:
                logger.info(f'   - Archivo eliminado: {ruta_foto}')

            # ✅ Refrescar y devolver perfil completo
            perfil.refresh_from_db()

            return Response({
                'mensaje': 'Foto de perfil eliminada exitosamente',
                'perfil': PerfilSerializer(perfil).data
            }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f'❌ ERROR CRÍTICO en subir_foto_perfil: {str(e)}')
        logger.exception('Traceback completo:')
        return Response({
            'error': f'Error al gestionar foto de perfil: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================
# ✅ NOTIFICACIONES PUSH (FCM)
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
#@throttle_classes([FCMThrottle])
def registrar_fcm_token(request):
    """
    Registra o actualiza el token FCM del dispositivo para notificaciones push
    ✅ CORREGIDO: Throttling más generoso (60/hour)

    Body:
    {
        "fcm_token": "string"
    }
    """
    try:
        user = request.user
        serializer = FCMTokenSerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"⚠️ Token FCM inválido: {user.email} - {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data['fcm_token']

        # Obtener perfil y actualizar token
        perfil = get_object_or_404(Perfil, user=user)

        if perfil.actualizar_fcm_token(token):
            logger.info(f"✅ Token FCM registrado: {user.email}")

            return Response({
                'mensaje': 'Token FCM registrado exitosamente',
                'puede_recibir_notificaciones': perfil.puede_recibir_notificaciones,
                'notificaciones_pedido': perfil.notificaciones_pedido,
                'notificaciones_promociones': perfil.notificaciones_promociones
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'No se pudo registrar el token'
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"❌ Error registrando token FCM: {e}", exc_info=True)
        return Response({
            'error': 'Error al registrar token FCM'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_fcm_token(request):
    """
    Elimina el token FCM del dispositivo (para cerrar sesión)
    """
    try:
        user = request.user
        perfil = get_object_or_404(Perfil, user=user)

        perfil.eliminar_fcm_token()

        logger.info(f"🔒 Token FCM eliminado: {user.email}")

        return Response({
            'mensaje': 'Token FCM eliminado exitosamente'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ Error eliminando token FCM: {e}", exc_info=True)
        return Response({
            'error': 'Error al eliminar token FCM'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estado_notificaciones(request):
    """
    Obtiene el estado actual de las notificaciones del usuario
    """
    try:
        user = request.user
        perfil = get_object_or_404(
            Perfil.objects.select_related('user'),
            user=user
        )

        estado = {
            'puede_recibir_notificaciones': perfil.puede_recibir_notificaciones,
            'notificaciones_pedido': perfil.notificaciones_pedido,
            'notificaciones_promociones': perfil.notificaciones_promociones,
            'token_actualizado': perfil.fcm_token_actualizado
        }

        serializer = EstadoNotificacionesSerializer(estado)

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ Error obteniendo estado de notificaciones: {e}", exc_info=True)
        return Response({
            'error': 'Error al obtener estado de notificaciones'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================
# DIRECCIONES FAVORITAS
# ============================================
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def direcciones_favoritas(request):
    """
    GET: Obtiene todas las direcciones guardadas (con paginación)
    POST: Crea una nueva dirección
    ✅ Con paginación en GET y manejo mejorado de errores
    """
    try:
        user = request.user

        # ===========================================================
        # 🟢 GET - Listar direcciones favoritas activas del usuario
        # ===========================================================
        if request.method == 'GET':
            direcciones = user.direcciones_favoritas.filter(activa=True).order_by(
                '-es_predeterminada',
                '-ultimo_uso',
                '-created_at'
            )

            # Aplicar paginación estándar
            paginator = StandardResultsSetPagination()
            page = paginator.paginate_queryset(direcciones, request)

            if page is not None:
                serializer = DireccionFavoritaSerializer(page, many=True)
                logger.info(f"Direcciones consultadas (paginadas): {user.email}")
                return paginator.get_paginated_response(serializer.data)

            # Sin paginación (fallback)
            serializer = DireccionFavoritaSerializer(direcciones, many=True)
            logger.info(f"Direcciones consultadas: {user.email} ({direcciones.count()} direcciones)")

            return Response({
                'direcciones': serializer.data,
                'total': direcciones.count()
            }, status=status.HTTP_200_OK)

        # ===========================================================
        # 🔵 POST - Crear nueva dirección favorita
        # ===========================================================
        elif request.method == 'POST':
            logger.info(f"📩 Creando dirección para {user.email}")

            serializer = CrearDireccionSerializer(
                data=request.data,
                context={'request': request}
            )

            # 🔍 Validación previa
            if not serializer.is_valid():
                logger.warning(f"⚠️ Validación fallida al crear dirección: {serializer.errors}")
                return Response({
                    'error': 'Error de validación',
                    'detalles': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                # ✅ Intentar guardar la dirección
                direccion = serializer.save()
                logger.info(f"✅ Dirección creada exitosamente: {user.email} - {direccion.etiqueta}")

                return Response({
                    'mensaje': 'Dirección guardada exitosamente',
                    'direccion': DireccionFavoritaSerializer(direccion).data
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                from rest_framework.exceptions import ValidationError as DRFValidationError
                from django.db import IntegrityError
                from django.core.exceptions import ValidationError as DjangoValidationError

                # ✅ CASO 1: ValidationError de Django (full_clean → unique_together)
                if isinstance(e, DjangoValidationError):
                    logger.warning(f"⚠️ Django ValidationError: {e.message_dict if hasattr(e, 'message_dict') else str(e)}")

                    # Extraer mensaje del error
                    if hasattr(e, 'message_dict') and '__all__' in e.message_dict:
                        mensaje_original = e.message_dict['__all__'][0]

                        # Detectar si es problema de etiqueta duplicada
                        if 'etiqueta' in mensaje_original.lower() or 'ya existe' in mensaje_original.lower():
                            return Response({
                                'error': 'Ya tienes una dirección con esta etiqueta',
                                'detalles': {
                                    'etiqueta': ['Usa otra etiqueta o actualiza la dirección existente.']
                                }
                            }, status=status.HTTP_400_BAD_REQUEST)

                    # Mensaje genérico
                    return Response({
                        'error': 'Error de validación en la dirección',
                        'detalles': e.message_dict if hasattr(e, 'message_dict') else str(e)
                    }, status=status.HTTP_400_BAD_REQUEST)

                # ✅ CASO 2: ValidationError de DRF
                if isinstance(e, DRFValidationError):
                    logger.warning(f"⚠️ DRF ValidationError: {e.detail}")
                    return Response({
                        'error': 'Error de validación',
                        'detalles': e.detail
                    }, status=status.HTTP_400_BAD_REQUEST)

                # ✅ CASO 3: IntegrityError (constraint de BD)
                if isinstance(e, IntegrityError):
                    error_msg = str(e).lower()
                    logger.warning(f"⚠️ IntegrityError: {error_msg}")

                    # Detectar tipo de constraint violada
                    if 'unique' in error_msg or 'duplicate' in error_msg:
                        if 'etiqueta' in error_msg or 'user' in error_msg:
                            return Response({
                                'error': 'Ya tienes una dirección con esta etiqueta',
                                'detalles': {
                                    'etiqueta': ['Usa otra etiqueta o actualiza la dirección existente.']
                                }
                            }, status=status.HTTP_400_BAD_REQUEST)

                        # Constraint genérico
                        return Response({
                            'error': 'Esta dirección ya existe',
                            'detalle': 'Verifica que no tengas una dirección similar.'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    # Otro tipo de IntegrityError
                    return Response({
                        'error': 'Error de integridad en la base de datos'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # ✅ CASO 4: Error inesperado
                logger.error(f"💥 Error inesperado al crear dirección: {type(e).__name__}: {str(e)}", exc_info=True)
                return Response({
                    'error': 'Error interno al crear dirección',
                    'detalle': 'Ocurrió un error inesperado. Intenta nuevamente.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ===============================================================
    # 🚨 Captura de cualquier error general fuera del flujo principal
    # ===============================================================
    except Exception as e:
        logger.error(f"❌ Error general en direcciones_favoritas: {e}", exc_info=True)
        return Response({
            'error': 'Error al gestionar direcciones',
            'detalle': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def detalle_direccion(request, direccion_id):
    """
    GET: Obtiene una dirección específica
    PUT/PATCH: Actualiza una dirección
    DELETE: Elimina (desactiva) una dirección
    ✅ CORREGIDO: Race condition eliminada
    """
    try:
        user = request.user
        direccion = get_object_or_404(
            DireccionFavorita,
            id=direccion_id,
            user=user,
            activa=True
        )

        if request.method == 'GET':
            serializer = DireccionFavoritaSerializer(direccion)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method in ['PUT', 'PATCH']:
            serializer = ActualizarDireccionSerializer(
                direccion,
                data=request.data,
                partial=True,
                context={'request': request}
            )

            if serializer.is_valid():
                # ✅ CORREGIDO: Si se marca como predeterminada, usar select_for_update
                if 'es_predeterminada' in request.data and request.data['es_predeterminada'] is True:
                    with transaction.atomic():
                        user.direcciones_favoritas.select_for_update().filter(
                            activa=True
                        ).exclude(id=direccion_id).update(es_predeterminada=False)
                        serializer.save()
                else:
                    serializer.save()

                logger.info(f"✅ Dirección actualizada: {user.email} - {direccion.etiqueta}")

                return Response({
                    'mensaje': 'Dirección actualizada exitosamente',
                    'direccion': DireccionFavoritaSerializer(direccion).data
                }, status=status.HTTP_200_OK)

            logger.warning(f"⚠️ Validación fallida al actualizar dirección: {user.email} - {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # DELETE - Desactivar en lugar de eliminar
        else:
            direccion.desactivar()

            logger.info(f"🗑️ Dirección desactivada: {user.email} - {direccion.etiqueta}")

            return Response({
                'mensaje': 'Dirección eliminada exitosamente'
            }, status=status.HTTP_200_OK)

    except DireccionFavorita.DoesNotExist:
        logger.warning(f"⚠️ Dirección no encontrada: {direccion_id} - Usuario: {request.user.email}")
        return Response({
            'error': 'Dirección no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"❌ Error con dirección: {e}", exc_info=True)
        return Response({
            'error': 'Error al gestionar dirección'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def direccion_predeterminada(request):
    """
    Obtiene la dirección predeterminada del usuario
    """
    try:
        user = request.user
        direccion = user.direcciones_favoritas.filter(
            es_predeterminada=True,
            activa=True
        ).first()

        if not direccion:
            return Response({
                'mensaje': 'No tienes una dirección predeterminada'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = DireccionFavoritaSerializer(direccion)
        return Response({
            'direccion': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ Error obteniendo dirección predeterminada: {e}", exc_info=True)
        return Response({
            'error': 'Error al obtener dirección'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================
# ✅ MÉTODOS DE PAGO CON COMPROBANTES
# ============================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
#@throttle_classes([UploadThrottle])
def metodos_pago(request):
    """
    GET: Obtiene todos los métodos de pago guardados (con paginación)
    POST: Crea un nuevo método de pago (con comprobante si es transferencia)
    ✅ Con paginación en GET y throttling en POST
    """
    try:
        user = request.user

        if request.method == 'GET':
            # Solo métodos activos, ordenados
            metodos = user.metodos_pago.filter(activo=True).order_by(
                '-es_predeterminado',
                '-created_at'
            )

            # Aplicar paginación
            paginator = StandardResultsSetPagination()
            page = paginator.paginate_queryset(metodos, request)

            if page is not None:
                serializer = MetodoPagoSerializer(page, many=True)
                logger.info(f"💳 Métodos de pago consultados: {user.email} (página)")
                return paginator.get_paginated_response(serializer.data)

            # Sin paginación (fallback)
            serializer = MetodoPagoSerializer(metodos, many=True)
            logger.info(f"💳 Métodos de pago consultados: {user.email} ({metodos.count()} métodos)")

            return Response({
                'metodos_pago': serializer.data,
                'total': metodos.count()
            }, status=status.HTTP_200_OK)

        # POST - Crear nuevo método
        serializer = CrearMetodoPagoSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            metodo = serializer.save()

            logger.info(
                f"💳 Método de pago creado: {user.email} - {metodo.get_tipo_display()} - "
                f"Comprobante: {'Sí' if metodo.tiene_comprobante else 'No'}"
            )

            return Response({
                'mensaje': 'Método de pago guardado exitosamente',
                'metodo_pago': MetodoPagoSerializer(metodo).data
            }, status=status.HTTP_201_CREATED)

        logger.warning(f"⚠️ Validación fallida al crear método de pago: {user.email} - {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"❌ Error con métodos de pago: {e}", exc_info=True)
        return Response({
            'error': 'Error al gestionar métodos de pago'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
#@throttle_classes([UploadThrottle])
def detalle_metodo_pago(request, metodo_id):
    """
    GET: Obtiene un método de pago específico
    PUT/PATCH: Actualiza un método de pago
    DELETE: Elimina (desactiva) un método de pago
    ✅ CORREGIDO: Race condition eliminada
    """
    try:
        user = request.user
        metodo = get_object_or_404(
            MetodoPago,
            id=metodo_id,
            user=user,
            activo=True
        )

        if request.method == 'GET':
            serializer = MetodoPagoSerializer(metodo)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method in ['PUT', 'PATCH']:
            serializer = ActualizarMetodoPagoSerializer(
                metodo,
                data=request.data,
                partial=True,
                context={'request': request}
            )

            if serializer.is_valid():
                # ✅ CORREGIDO: Si se marca como predeterminado, usar select_for_update
                if request.data.get('es_predeterminado'):
                    with transaction.atomic():
                        user.metodos_pago.select_for_update().filter(
                            activo=True
                        ).exclude(id=metodo_id).update(es_predeterminado=False)
                        serializer.save()
                else:
                    serializer.save()

                logger.info(f"✅ Método de pago actualizado: {user.email} - {metodo.alias}")

                return Response({
                    'mensaje': 'Método de pago actualizado exitosamente',
                    'metodo_pago': MetodoPagoSerializer(metodo).data
                }, status=status.HTTP_200_OK)

            logger.warning(f"⚠️ Validación fallida al actualizar método de pago: {user.email} - {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # DELETE - Desactivar
        else:
            metodo.activo = False
            if metodo.es_predeterminado:
                metodo.es_predeterminado = False
            metodo.save()

            logger.info(f"🗑️ Método de pago desactivado: {user.email} - {metodo.alias}")

            return Response({
                'mensaje': 'Método de pago eliminado exitosamente'
            }, status=status.HTTP_200_OK)

    except MetodoPago.DoesNotExist:
        logger.warning(f"⚠️ Método de pago no encontrado: {metodo_id} - Usuario: {request.user.email}")
        return Response({
            'error': 'Método de pago no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"❌ Error con método de pago: {e}", exc_info=True)
        return Response({
            'error': 'Error al gestionar método de pago'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def metodo_pago_predeterminado(request):
    """
    Obtiene el método de pago predeterminado del usuario
    """
    try:
        user = request.user
        metodo = user.metodos_pago.filter(
            es_predeterminado=True,
            activo=True
        ).first()

        if not metodo:
            # Si no hay predeterminado, devolver el primero
            metodo = user.metodos_pago.filter(activo=True).first()

            if not metodo:
                return Response({
                    'mensaje': 'No tienes métodos de pago guardados'
                }, status=status.HTTP_404_NOT_FOUND)

        serializer = MetodoPagoSerializer(metodo)
        return Response({
            'metodo_pago': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ Error obteniendo método de pago predeterminado: {e}", exc_info=True)
        return Response({
            'error': 'Error al obtener método de pago'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================
# ✅ UBICACIÓN EN TIEMPO REAL (REST) - CORREGIDO
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
#@throttle_classes([UbicacionThrottle])
def actualizar_ubicacion(request):
    """
    Actualiza la ubicación del usuario
    ✅ CORREGIDO: Throttle más generoso (300/hour = 5/minuto)

    Body JSON o form-data:
      latitud: float
      longitud: float
    """
    try:
        ser = ActualizarUbicacionSerializer(data=request.data)
        if not ser.is_valid():
            logger.warning(f"⚠️ Ubicación inválida {request.user.email}: {ser.errors}")
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        lat, lon = ser.validated_data['latitud'], ser.validated_data['longitud']

        with transaction.atomic():
            ubic, _ = UbicacionUsuario.objects.select_for_update().update_or_create(
                user=request.user,
                defaults={'latitud': lat, 'longitud': lon}
            )

        logger.info(f"📡 Ubicación actualizada: {request.user.email} -> ({lat}, {lon})")
        return Response({
            'mensaje': 'Ubicación actualizada',
            'ubicacion': UbicacionUsuarioSerializer(ubic).data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ Error actualizando ubicación: {e}", exc_info=True)
        return Response({
            'error': 'Error al actualizar ubicación'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mi_ubicacion(request):
    """
    Devuelve la última ubicación del usuario autenticado
    """
    try:
        ubic = UbicacionUsuario.objects.select_related('user').filter(user=request.user).first()
        if not ubic:
            return Response({
                'mensaje': 'Aún no reportas ubicación'
            }, status=status.HTTP_404_NOT_FOUND)

        return Response(
            UbicacionUsuarioSerializer(ubic).data,
            status=status.HTTP_200_OK
        )

    except Exception as e:
        logger.error(f"❌ Error obteniendo mi ubicación: {e}", exc_info=True)
        return Response({
            'error': 'Error al obtener ubicación'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
