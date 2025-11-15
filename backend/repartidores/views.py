from django.db import transaction
from django.shortcuts import get_object_or_404
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db.models import Count, Avg, Q
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from rest_framework.pagination import PageNumberPagination
from decimal import Decimal
from math import radians, cos, sin, sqrt, atan2
import logging

from .models import (
    Repartidor,
    RepartidorVehiculo,
    HistorialUbicacion,
    RepartidorEstadoLog,
    CalificacionRepartidor,
    CalificacionCliente,
)
from .serializers import (
    RepartidorPerfilSerializer,
    RepartidorUpdateSerializer,
    RepartidorEstadoSerializer,
    RepartidorUbicacionSerializer,
    RepartidorPublicoSerializer,
    RepartidorVehiculoSerializer,
    HistorialUbicacionSerializer,
    RepartidorEstadoLogSerializer,
    CalificacionRepartidorSerializer,
    CalificacionClienteCreateSerializer,
)
from .permissions import IsRepartidor

logger = logging.getLogger("repartidores")


# ==========================================================
# THROTTLING – Limita frecuencia para evitar abusos
# ==========================================================
class PerfilThrottle(UserRateThrottle):
    rate = "120/hour"   # 2 por minuto


class EstadoThrottle(UserRateThrottle):
    rate = "60/hour"    # 1 por minuto


class UbicacionThrottle(UserRateThrottle):
    rate = "300/hour"   # 5 por minuto


class VehiculoThrottle(UserRateThrottle):
    rate = "30/hour"    # ~0.5 por minuto


class CalificacionThrottle(UserRateThrottle):
    rate = "20/hour"


# ==========================================================
# PAGINACIÓN
# ==========================================================
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ==========================================
# ✅ AGREGAR ESTE HELPER AL INICIO DE views.py
# (después de los imports)
# ==========================================

def construir_url_media_view(file_field, request):
    """
    Construye URL completa para archivos media desde vistas.
    
    Args:
        file_field: Campo de archivo (FileField/ImageField)
        request: Request HTTP
    
    Returns:
        str: URL completa del archivo, o None si no hay archivo
    """
    if not file_field:
        return None
    
    try:
        return request.build_absolute_uri(file_field.url)
    except Exception as e:
        logger.error(f"Error construyendo URL: {e}")
        return None


def construir_perfil_response(repartidor, request):
    """
    ✅ HELPER: Construye respuesta de perfil con URLs completas.
    Usar en lugar de construir el dict manualmente.
    """
    return {
        'id': repartidor.id,
        'nombre_completo': repartidor.user.get_full_name(),
        'email': repartidor.user.email,
        'foto_perfil': construir_url_media_view(repartidor.foto_perfil, request),
        'cedula': repartidor.cedula,
        'telefono': repartidor.telefono,
        'estado': repartidor.estado,
        'verificado': repartidor.verificado,
        'activo': repartidor.activo,
        'calificacion_promedio': float(repartidor.calificacion_promedio),
        'entregas_completadas': repartidor.entregas_completadas,
    }


def construir_vehiculo_response(vehiculo, request):
    """
    ✅ HELPER: Construye respuesta de vehículo con URLs completas.
    """
    return {
        'id': vehiculo.id,
        'tipo': vehiculo.tipo,
        'tipo_display': vehiculo.get_tipo_display(),
        'placa': vehiculo.placa,
        'licencia_foto': construir_url_media_view(vehiculo.licencia_foto, request),
        'activo': vehiculo.activo,
    }


# ==========================================
# ✅ IMPORTANTE: Actualizar obtener_mi_perfil() para pasar context
# ==========================================

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsRepartidor])
@throttle_classes([PerfilThrottle])
def obtener_mi_perfil(request):
    """
    Devuelve el perfil completo del repartidor autenticado.
    ✅ Con URLs completas de imágenes
    """
    try:
        repartidor = request.user.repartidor
        # ✅ CRÍTICO: Pasar request en context para construir URLs completas
        serializer = RepartidorPerfilSerializer(repartidor, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except AttributeError:
        logger.error(f"Usuario {request.user.email} no tiene perfil de repartidor")
        return Response(
            {"error": "No tienes perfil de repartidor asociado."},
            status=status.HTTP_404_NOT_FOUND
        )

# ==========================================
# ✅ REEMPLAZAR actualizar_mi_perfil() CON ESTA VERSIÓN
# ==========================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsRepartidor])
@throttle_classes([PerfilThrottle])
def actualizar_mi_perfil(request):
    """
    ✅ ACTUALIZADO: Permite actualizar teléfono, foto de perfil y datos del repartidor.
    Soporta multipart/form-data para subir archivos.
    ✅ URLs completas en respuesta
    """
    try:
        repartidor = request.user.repartidor

        # ✅ Manejar eliminación de foto
        eliminar_foto = request.data.get('eliminar_foto_perfil', 'false')
        if eliminar_foto in ['true', True, '1', 1]:
            if repartidor.foto_perfil:
                try:
                    repartidor.foto_perfil.delete(save=False)
                except Exception as e:
                    logger.warning(f"Error eliminando archivo de foto: {e}")
                
                repartidor.foto_perfil = None
                repartidor.save()
                
                logger.info(f"✅ Foto eliminada: {repartidor.user.email}")
                
                return Response({
                    "mensaje": "Foto de perfil eliminada correctamente",
                    "perfil": construir_perfil_response(repartidor, request)
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "mensaje": "No hay foto de perfil para eliminar",
                    "perfil": construir_perfil_response(repartidor, request)
                }, status=status.HTTP_200_OK)

        # ✅ Manejar foto de perfil (archivo)
        foto_perfil = request.FILES.get('foto_perfil')
        if foto_perfil:
            # Validar tamaño (máximo 5MB)
            if foto_perfil.size > 5 * 1024 * 1024:
                return Response({
                    'error': 'La imagen no puede superar 5MB'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validar extensión
            valid_extensions = ['jpg', 'jpeg', 'png', 'webp']
            ext = foto_perfil.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                return Response({
                    'error': f'Formato no válido. Usa: {", ".join(valid_extensions)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Asignar foto
            repartidor.foto_perfil = foto_perfil

        # ✅ Actualizar teléfono si viene
        telefono = request.data.get('telefono')
        if telefono:
            # Validar formato básico
            import re
            if not re.match(r'^\+?[0-9]{7,15}$', telefono):
                return Response({
                    'error': 'Número de teléfono inválido. Formato: +593987654321 o 0987654321'
                }, status=status.HTTP_400_BAD_REQUEST)

            repartidor.telefono = telefono

        # Guardar cambios
        repartidor.save()

        logger.info(f"✅ Perfil actualizado: {repartidor.user.email}")

        return Response({
            "mensaje": "Perfil actualizado correctamente",
            "perfil": construir_perfil_response(repartidor, request)
        }, status=status.HTTP_200_OK)

    except AttributeError:
        return Response(
            {"error": "No tienes perfil de repartidor asociado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"❌ Error al actualizar perfil: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al actualizar perfil."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==========================================
# ✅ REEMPLAZAR actualizar_datos_vehiculo() CON ESTA VERSIÓN
# ==========================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsRepartidor])
@throttle_classes([VehiculoThrottle])
def actualizar_datos_vehiculo(request):
    """
    ✅ ACTUALIZADO: Permite actualizar tipo, placa y subir foto de licencia del vehículo activo.
    ✅ URLs completas en respuesta
    """
    try:
        repartidor = request.user.repartidor

        # Obtener vehículo activo
        vehiculo_activo = repartidor.vehiculos.filter(activo=True).first()

        if not vehiculo_activo:
            return Response({
                'error': 'No tienes un vehículo activo registrado'
            }, status=status.HTTP_404_NOT_FOUND)

        # Actualizar tipo de vehículo
        tipo_vehiculo = request.data.get('tipo')
        if tipo_vehiculo:
            from repartidores.models import TipoVehiculo
            if tipo_vehiculo not in dict(TipoVehiculo.choices):
                return Response({
                    'error': f'Tipo de vehículo inválido. Opciones: {", ".join(dict(TipoVehiculo.choices).keys())}'
                }, status=status.HTTP_400_BAD_REQUEST)

            vehiculo_activo.tipo = tipo_vehiculo

        # Actualizar placa
        placa = request.data.get('placa')
        if placa:
            vehiculo_activo.placa = placa.strip().upper()

        # ✅ Subir foto de licencia
        licencia_foto = request.FILES.get('licencia_foto')
        if licencia_foto:
            # Validar tamaño (máximo 5MB)
            if licencia_foto.size > 5 * 1024 * 1024:
                return Response({
                    'error': 'La imagen no puede superar 5MB'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validar extensión
            valid_extensions = ['jpg', 'jpeg', 'png', 'webp', 'pdf']
            ext = licencia_foto.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                return Response({
                    'error': f'Formato no válido. Usa: {", ".join(valid_extensions)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            vehiculo_activo.licencia_foto = licencia_foto

        # Guardar cambios
        vehiculo_activo.save()

        logger.info(f"✅ Vehículo actualizado: {vehiculo_activo.tipo} para {repartidor.user.email}")

        return Response({
            "mensaje": "Datos del vehículo actualizados correctamente",
            "vehiculo": construir_vehiculo_response(vehiculo_activo, request)
        }, status=status.HTTP_200_OK)

    except AttributeError:
        return Response(
            {"error": "No tienes perfil de repartidor asociado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"❌ Error al actualizar vehículo: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al actualizar vehículo."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsRepartidor])
@throttle_classes([PerfilThrottle])
def obtener_estadisticas(request):
    """
    Devuelve estadísticas detalladas del repartidor autenticado.
    Incluye métricas de entregas, calificaciones y tasa de aceptación.
    """
    try:
        repartidor = request.user.repartidor

        # Calcular estadísticas de calificaciones
        calificaciones_stats = repartidor.calificaciones.aggregate(
            total=Count('id'),
            promedio=Avg('puntuacion'),
            cinco_estrellas=Count('id', filter=Q(puntuacion=5)),
            cuatro_estrellas=Count('id', filter=Q(puntuacion=4)),
            tres_estrellas=Count('id', filter=Q(puntuacion=3)),
            dos_estrellas=Count('id', filter=Q(puntuacion=2)),
            una_estrella=Count('id', filter=Q(puntuacion=1)),
        )

        # Calcular tasa de aceptación (si existe campo de pedidos rechazados)
        # Ajustar según tu modelo de pedidos
        total_calificaciones = calificaciones_stats['total'] or 0
        entregas = repartidor.entregas_completadas

        estadisticas = {
            "entregas_completadas": entregas,
            "calificacion_promedio": float(repartidor.calificacion_promedio),
            "total_calificaciones": total_calificaciones,
            "desglose_calificaciones": {
                "5_estrellas": calificaciones_stats['cinco_estrellas'] or 0,
                "4_estrellas": calificaciones_stats['cuatro_estrellas'] or 0,
                "3_estrellas": calificaciones_stats['tres_estrellas'] or 0,
                "2_estrellas": calificaciones_stats['dos_estrellas'] or 0,
                "1_estrella": calificaciones_stats['una_estrella'] or 0,
            },
            "porcentaje_5_estrellas": round(
                (calificaciones_stats['cinco_estrellas'] or 0) / total_calificaciones * 100, 2
            ) if total_calificaciones > 0 else 0,
            "estado_actual": repartidor.estado,
            "verificado": repartidor.verificado,
            "activo": repartidor.activo,
        }

        logger.info(f"Estadísticas consultadas: {repartidor.user.email}")

        return Response(estadisticas, status=status.HTTP_200_OK)

    except AttributeError:
        return Response(
            {"error": "No tienes perfil de repartidor asociado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al obtener estadísticas."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==========================================================
# CAMBIO DE ESTADO
# ==========================================================
@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsRepartidor])
@throttle_classes([EstadoThrottle])
def cambiar_estado(request):
    """
    Cambia el estado del repartidor (disponible / ocupado / fuera_servicio).
    Valida que el repartidor esté verificado y activo según el nuevo estado.
    """
    try:
        repartidor = request.user.repartidor
        serializer = RepartidorEstadoSerializer(
            data=request.data,
            context={"repartidor": repartidor}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        nuevo_estado = serializer.validated_data["estado"]
        anterior = repartidor.estado

        with transaction.atomic():
            if nuevo_estado == "disponible":
                repartidor.marcar_disponible()
            elif nuevo_estado == "ocupado":
                repartidor.marcar_ocupado()
            else:
                repartidor.marcar_fuera_servicio()

        logger.info(f"Estado cambiado: {anterior} → {nuevo_estado} ({repartidor.user.email})")

        return Response({
            "mensaje": "Estado actualizado correctamente",
            "estado_anterior": anterior,
            "estado_nuevo": repartidor.estado
        }, status=status.HTTP_200_OK)

    except ValidationError as e:
        logger.warning(f"Validación fallida al cambiar estado: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except ValueError as e:
        logger.warning(f"Valor inválido al cambiar estado: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except AttributeError:
        return Response(
            {"error": "No tienes perfil de repartidor asociado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error al cambiar estado: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al actualizar estado."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsRepartidor])
@throttle_classes([EstadoThrottle])
def historial_estados(request):
    """
    Devuelve el historial de cambios de estado del repartidor autenticado.
    Soporta paginación.
    """
    try:
        repartidor = request.user.repartidor

        # Obtener logs ordenados por fecha descendente
        logs = RepartidorEstadoLog.objects.filter(
            repartidor=repartidor
        ).order_by('-timestamp')

        # Aplicar paginación
        paginator = StandardResultsSetPagination()
        paginated_logs = paginator.paginate_queryset(logs, request)

        serializer = RepartidorEstadoLogSerializer(paginated_logs, many=True)

        return paginator.get_paginated_response(serializer.data)

    except AttributeError:
        return Response(
            {"error": "No tienes perfil de repartidor asociado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error al obtener historial de estados: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al obtener historial."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==========================================================
# ACTUALIZAR UBICACIÓN EN TIEMPO REAL
# ==========================================================
@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsRepartidor])
@throttle_classes([UbicacionThrottle])
def actualizar_ubicacion(request):
    """
    Actualiza la ubicación (latitud, longitud) del repartidor autenticado.
    Guarda también en el historial.
    Solo repartidores activos y verificados pueden actualizar ubicación.
    """
    try:
        repartidor = request.user.repartidor
        serializer = RepartidorUbicacionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        lat = serializer.validated_data["latitud"]
        lon = serializer.validated_data["longitud"]

        with transaction.atomic():
            repartidor.actualizar_ubicacion(lat, lon, save_historial=True)

        logger.debug(f"Ubicación actualizada: {repartidor.user.email} → ({lat}, {lon})")

        return Response({
            "mensaje": "Ubicación actualizada correctamente",
            "latitud": lat,
            "longitud": lon,
            "timestamp": repartidor.ultima_localizacion
        }, status=status.HTTP_200_OK)

    except ValidationError as e:
        logger.warning(f"Validación fallida al actualizar ubicación: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except AttributeError:
        return Response(
            {"error": "No tienes perfil de repartidor asociado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error al actualizar ubicación: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al actualizar ubicación."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsRepartidor])
@throttle_classes([UbicacionThrottle])
def historial_ubicaciones(request):
    """
    Devuelve el historial de ubicaciones del repartidor autenticado.
    Soporta paginación y filtros por fecha.
    """
    try:
        repartidor = request.user.repartidor

        # Obtener historial ordenado por fecha descendente
        ubicaciones = HistorialUbicacion.objects.filter(
            repartidor=repartidor
        ).order_by('-timestamp')

        # Filtros opcionales por rango de fechas
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')

        if fecha_inicio:
            ubicaciones = ubicaciones.filter(timestamp__gte=fecha_inicio)

        if fecha_fin:
            ubicaciones = ubicaciones.filter(timestamp__lte=fecha_fin)

        # Aplicar paginación
        paginator = StandardResultsSetPagination()
        paginated_ubicaciones = paginator.paginate_queryset(ubicaciones, request)

        serializer = HistorialUbicacionSerializer(paginated_ubicaciones, many=True)

        return paginator.get_paginated_response(serializer.data)

    except AttributeError:
        return Response(
            {"error": "No tienes perfil de repartidor asociado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error al obtener historial de ubicaciones: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al obtener historial."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==========================================================
# VEHÍCULOS
# ==========================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsRepartidor])
@throttle_classes([VehiculoThrottle])
def listar_vehiculos(request):
    """
    Lista todos los vehículos del repartidor autenticado.
    """
    try:
        repartidor = request.user.repartidor
        vehiculos = repartidor.vehiculos.all().order_by('-activo', '-creado_en')

        serializer = RepartidorVehiculoSerializer(vehiculos, many=True)

        return Response({
            "total": vehiculos.count(),
            "vehiculos": serializer.data
        }, status=status.HTTP_200_OK)

    except AttributeError:
        return Response(
            {"error": "No tienes perfil de repartidor asociado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error al listar vehículos: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al listar vehículos."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsRepartidor])
@throttle_classes([VehiculoThrottle])
def crear_vehiculo(request):
    """
    Crea un nuevo vehículo para el repartidor autenticado.
    """
    try:
        repartidor = request.user.repartidor
        serializer = RepartidorVehiculoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            vehiculo = serializer.save(repartidor=repartidor)

        logger.info(f"Vehículo creado: {vehiculo.tipo} para {repartidor.user.email}")

        return Response({
            "mensaje": "Vehículo creado correctamente",
            "vehiculo": RepartidorVehiculoSerializer(vehiculo).data
        }, status=status.HTTP_201_CREATED)

    except AttributeError:
        return Response(
            {"error": "No tienes perfil de repartidor asociado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error al crear vehículo: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al crear vehículo."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsRepartidor])
@throttle_classes([VehiculoThrottle])
def detalle_vehiculo(request, vehiculo_id):
    """
    Obtiene, actualiza o elimina un vehículo específico.
    Solo el propietario puede acceder.
    """
    try:
        repartidor = request.user.repartidor
        vehiculo = get_object_or_404(
            RepartidorVehiculo,
            id=vehiculo_id,
            repartidor=repartidor
        )

        if request.method == "GET":
            serializer = RepartidorVehiculoSerializer(vehiculo)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == "PATCH":
            serializer = RepartidorVehiculoSerializer(
                vehiculo,
                data=request.data,
                partial=True
            )

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
            logger.info(f"Vehículo actualizado: {vehiculo.id}")

            return Response({
                "mensaje": "Vehículo actualizado correctamente",
                "vehiculo": serializer.data
            }, status=status.HTTP_200_OK)

        elif request.method == "DELETE":
            # No eliminar si es el único vehículo activo
            if vehiculo.activo and repartidor.vehiculos.filter(activo=True).count() == 1:
                return Response(
                    {"error": "No puedes eliminar tu único vehículo activo."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            vehiculo.delete()
            logger.info(f"Vehículo eliminado: {vehiculo_id}")

            return Response(
                {"mensaje": "Vehículo eliminado correctamente"},
                status=status.HTTP_204_NO_CONTENT
            )

    except AttributeError:
        return Response(
            {"error": "No tienes perfil de repartidor asociado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error en detalle_vehiculo: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al procesar solicitud."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsRepartidor])
@throttle_classes([VehiculoThrottle])
def activar_vehiculo(request, vehiculo_id):
    """
    Activa un vehículo específico y desactiva los demás automáticamente.
    """
    try:
        repartidor = request.user.repartidor
        vehiculo = get_object_or_404(
            RepartidorVehiculo,
            id=vehiculo_id,
            repartidor=repartidor
        )

        with transaction.atomic():
            # Desactivar todos los demás vehículos
            RepartidorVehiculo.objects.filter(
                repartidor=repartidor
            ).exclude(id=vehiculo_id).update(activo=False)

            # Activar el vehículo seleccionado
            vehiculo.activo = True
            vehiculo.save()

        logger.info(f"Vehículo activado: {vehiculo.tipo} ({vehiculo_id})")

        return Response({
            "mensaje": "Vehículo activado correctamente",
            "vehiculo": RepartidorVehiculoSerializer(vehiculo).data
        }, status=status.HTTP_200_OK)

    except AttributeError:
        return Response(
            {"error": "No tienes perfil de repartidor asociado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error al activar vehículo: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al activar vehículo."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==========================================================
# CALIFICACIONES
# ==========================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsRepartidor])
@throttle_classes([CalificacionThrottle])
def listar_mis_calificaciones(request):
    """
    Lista todas las calificaciones recibidas por el repartidor autenticado.
    Soporta paginación y filtros.
    """
    try:
        repartidor = request.user.repartidor

        calificaciones = CalificacionRepartidor.objects.filter(
            repartidor=repartidor
        ).select_related('cliente').order_by('-creado_en')

        # Filtro opcional por puntuación
        puntuacion = request.query_params.get('puntuacion')
        if puntuacion:
            calificaciones = calificaciones.filter(puntuacion=puntuacion)

        # Aplicar paginación
        paginator = StandardResultsSetPagination()
        paginated_calificaciones = paginator.paginate_queryset(calificaciones, request)

        serializer = CalificacionRepartidorSerializer(paginated_calificaciones, many=True)

        return paginator.get_paginated_response(serializer.data)

    except AttributeError:
        return Response(
            {"error": "No tienes perfil de repartidor asociado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error al listar calificaciones: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al listar calificaciones."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsRepartidor])
@throttle_classes([CalificacionThrottle])
def calificar_cliente(request, pedido_id):
    """
    Permite al repartidor calificar a un cliente después de completar un pedido.
    Solo se puede calificar una vez por pedido.
    """
    try:
        repartidor = request.user.repartidor

        # Lazy loading del modelo Pedido
        Pedido = apps.get_model('pedidos', 'Pedido')

        # Verificar que el pedido existe y fue entregado por este repartidor
        pedido = get_object_or_404(
            Pedido.objects.select_related('cliente', 'repartidor'),
            pk=pedido_id,
            repartidor=repartidor
        )

        # Verificar que el pedido está completado (ajustar según tu modelo)
        # if pedido.estado != 'entregado':
        #     return Response(
        #         {"error": "Solo puedes calificar pedidos completados."},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )

        # Verificar que no haya calificado antes
        if CalificacionCliente.objects.filter(
            cliente=pedido.cliente,
            repartidor=repartidor,
            pedido_id=str(pedido_id)
        ).exists():
            return Response(
                {"error": "Ya has calificado a este cliente por este pedido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crear calificación
        serializer = CalificacionClienteCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            calificacion = serializer.save(
                cliente=pedido.cliente,
                repartidor=repartidor,
                pedido_id=str(pedido_id)
            )

        logger.info(
            f"Repartidor {repartidor.id} calificó cliente {pedido.cliente.id} "
            f"con {calificacion.puntuacion} estrellas (pedido {pedido_id})"
        )

        return Response({
            "mensaje": "Calificación enviada correctamente",
            "calificacion": {
                "puntuacion": float(calificacion.puntuacion),
                "comentario": calificacion.comentario,
                "pedido_id": calificacion.pedido_id,
            }
        }, status=status.HTTP_201_CREATED)

    except AttributeError:
        return Response(
            {"error": "No tienes perfil de repartidor asociado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except LookupError:
        logger.error("Modelo 'Pedido' no encontrado en la app 'pedidos'")
        return Response(
            {"error": "Configuración del sistema incorrecta."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Error al calificar cliente: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al enviar calificación."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==========================================================
# PERFIL PÚBLICO (visto por el cliente)
# ==========================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def perfil_repartidor_por_pedido(request, pedido_id):
    """
    Devuelve el perfil público del repartidor asignado a un pedido.
    Solo el cliente dueño del pedido puede acceder.

    Usa lazy loading para evitar dependencia circular con la app 'pedidos'.
    """
    try:
        # Lazy loading del modelo Pedido para evitar import circular
        Pedido = apps.get_model('pedidos', 'Pedido')

        pedido = get_object_or_404(
            Pedido.objects.select_related("repartidor__user", "cliente"),
            pk=pedido_id
        )

        # Validación de autorización: solo el cliente dueño puede ver
        if pedido.cliente != request.user:
            logger.warning(
                f"Acceso no autorizado: usuario {request.user.email} "
                f"intentó acceder al pedido {pedido_id} del cliente {pedido.cliente.email}"
            )
            return Response(
                {"error": "No tienes autorización para ver este pedido."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validar que el pedido tenga repartidor asignado
        if not pedido.repartidor:
            return Response(
                {"mensaje": "Este pedido aún no tiene repartidor asignado."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = RepartidorPublicoSerializer(pedido.repartidor)

        return Response({
            "pedido_id": pedido.id,
            "repartidor": serializer.data
        }, status=status.HTTP_200_OK)

    except LookupError:
        logger.error("Modelo 'Pedido' no encontrado en la app 'pedidos'")
        return Response(
            {"error": "Configuración del sistema incorrecta."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Error al obtener perfil público de repartidor: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al obtener información del repartidor."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def info_repartidor_publico(request, repartidor_id):
    """
    Devuelve información pública básica de un repartidor por su ID.
    Útil para mostrar perfiles públicos o rankings.
    """
    try:
        repartidor = get_object_or_404(
            Repartidor.objects.select_related('user').prefetch_related('vehiculos'),
            pk=repartidor_id,
            activo=True,
            verificado=True
        )

        serializer = RepartidorPublicoSerializer(repartidor)

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error al obtener info pública de repartidor: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al obtener información del repartidor."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ==========================================================
# ENDPOINTS PARA MAPA DE PEDIDOS DISPONIBLES
# ==========================================================
# INSTRUCCIONES: Copiar este código AL FINAL de tu archivo views.py existente

def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en kilómetros entre dos puntos usando Haversine.
    """
    if not all([lat1, lon1, lat2, lon2]):
        return None

    try:
        R = 6371.0  # Radio de la Tierra en km
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])

        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)

        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return round(R * c, 2)
    except (ValueError, TypeError):
        return None


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsRepartidor])
def obtener_pedidos_disponibles_mapa(request):
    """
    Devuelve pedidos disponibles cercanos al repartidor con sus ubicaciones.
    Incluye distancia calculada desde la ubicación actual del repartidor.

    Query params opcionales:
    - radio: Radio de búsqueda en km (default: 15)
    - latitud: Latitud actual del repartidor (opcional, prioridad sobre BD)
    - longitud: Longitud actual del repartidor (opcional, prioridad sobre BD)
    """
    try:
        repartidor = request.user.repartidor

        # ✅ PRIORIDAD 1: Usar coordenadas del request si están presentes
        lat_param = request.query_params.get('latitud')
        lon_param = request.query_params.get('longitud')

        if lat_param and lon_param:
            try:
                latitud_repartidor = float(lat_param)
                longitud_repartidor = float(lon_param)

                # Validar rangos de Ecuador
                if not (-5.0 <= latitud_repartidor <= 2.0):
                    return Response({
                        "error": "Latitud fuera del rango válido de Ecuador.",
                        "pedidos": []
                    }, status=status.HTTP_400_BAD_REQUEST)

                if not (-92.0 <= longitud_repartidor <= -75.0):
                    return Response({
                        "error": "Longitud fuera del rango válido de Ecuador.",
                        "pedidos": []
                    }, status=status.HTTP_400_BAD_REQUEST)

                logger.debug(
                    f"Usando coordenadas del request: ({latitud_repartidor}, {longitud_repartidor})"
                )
            except ValueError:
                return Response({
                    "error": "Coordenadas inválidas en los parámetros.",
                    "pedidos": []
                }, status=status.HTTP_400_BAD_REQUEST)

        # ✅ PRIORIDAD 2: Fallback a ubicación guardada en BD
        elif repartidor.latitud and repartidor.longitud:
            latitud_repartidor = float(repartidor.latitud)
            longitud_repartidor = float(repartidor.longitud)
            logger.debug(
                f"Usando coordenadas de BD: ({latitud_repartidor}, {longitud_repartidor})"
            )

        # ❌ Sin ubicación disponible
        else:
            return Response({
                "error": "Debes activar tu ubicación para ver pedidos cercanos.",
                "pedidos": []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Radio de búsqueda (default 15km)
        radio_km = float(request.query_params.get('radio', 15.0))

        # Lazy loading del modelo Pedido
        Pedido = apps.get_model('pedidos', 'Pedido')

        # ✅ CORREGIDO: Usar 'proveedor' en lugar de 'restaurante'
        pedidos_query = Pedido.objects.filter(
            repartidor__isnull=True,  # Sin repartidor asignado
            # estado='pendiente',  # Descomenta y ajusta según tu modelo
        ).select_related('cliente', 'proveedor')

        # Filtrar por distancia y preparar respuesta
        pedidos_cercanos = []

        for pedido in pedidos_query:
            # Asume que el pedido tiene latitud_destino y longitud_destino
            lat_destino = getattr(pedido, 'latitud_destino', None)
            lon_destino = getattr(pedido, 'longitud_destino', None)

            if not lat_destino or not lon_destino:
                continue

            # Calcular distancia usando las coordenadas del repartidor
            distancia = calcular_distancia_haversine(
                latitud_repartidor,
                longitud_repartidor,
                lat_destino,
                lon_destino
            )

            if distancia and distancia <= radio_km:
                pedidos_cercanos.append({
                    'id': pedido.id,
                    'cliente_nombre': pedido.cliente.get_full_name() if hasattr(pedido, 'cliente') else 'Cliente',
                    'direccion_entrega': getattr(pedido, 'direccion_entrega', 'Dirección no disponible'),
                    'latitud': float(lat_destino),
                    'longitud': float(lon_destino),
                    'distancia_km': distancia,
                    'tiempo_estimado_min': max(int(distancia / 0.5), 5),  # ~30km/h
                    'monto_total': float(getattr(pedido, 'total', 0)),
                    'creado_en': pedido.creado_en.isoformat() if hasattr(pedido, 'creado_en') else None,
                })

        # Ordenar por distancia
        pedidos_cercanos.sort(key=lambda x: x['distancia_km'])

        logger.info(
            f"Repartidor {repartidor.id} consultó mapa: "
            f"{len(pedidos_cercanos)} pedidos en radio de {radio_km}km "
            f"desde ({latitud_repartidor}, {longitud_repartidor})"
        )

        return Response({
            'repartidor_ubicacion': {
                'latitud': latitud_repartidor,
                'longitud': longitud_repartidor,
            },
            'radio_km': radio_km,
            'total_pedidos': len(pedidos_cercanos),
            'pedidos': pedidos_cercanos,
        }, status=status.HTTP_200_OK)

    except AttributeError:
        return Response(
            {"error": "No tienes perfil de repartidor asociado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except LookupError:
        logger.error("Modelo 'Pedido' no encontrado en la app 'pedidos'")
        return Response(
            {"error": "Configuración del sistema incorrecta."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Error al obtener pedidos disponibles: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al obtener pedidos."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsRepartidor])
def aceptar_pedido(request, pedido_id):
    """
    Permite al repartidor aceptar un pedido disponible.
    Valida que el pedido esté disponible y actualiza su estado.
    """
    try:
        repartidor = request.user.repartidor

        # Validar que el repartidor esté disponible
        if repartidor.estado != 'disponible':
            return Response(
                {"error": "Debes estar en estado DISPONIBLE para aceptar pedidos."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Lazy loading del modelo Pedido
        Pedido = apps.get_model('pedidos', 'Pedido')

        # Buscar el pedido
        pedido = get_object_or_404(Pedido, pk=pedido_id)

        # Validar que el pedido esté disponible
        if pedido.repartidor is not None:
            return Response(
                {"error": "Este pedido ya fue asignado a otro repartidor."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Asignar pedido al repartidor
        with transaction.atomic():
            pedido.repartidor = repartidor
            # pedido.estado = 'aceptado'  # Descomenta y ajusta según tu modelo
            pedido.save()

            # Cambiar estado del repartidor a ocupado
            repartidor.marcar_ocupado()

        logger.info(f"Repartidor {repartidor.id} aceptó pedido {pedido_id}")

        return Response({
            "mensaje": "Pedido aceptado correctamente",
            "pedido_id": pedido.id,
            "estado_repartidor": repartidor.estado,
        }, status=status.HTTP_200_OK)

    except AttributeError:
        return Response(
            {"error": "No tienes perfil de repartidor asociado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except LookupError:
        logger.error("Modelo 'Pedido' no encontrado")
        return Response(
            {"error": "Configuración del sistema incorrecta."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Error al aceptar pedido: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al aceptar pedido."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsRepartidor])
def rechazar_pedido(request, pedido_id):
    """
    Permite al repartidor rechazar un pedido (opcional).
    Registra el rechazo para análisis posterior.
    """
    try:
        repartidor = request.user.repartidor

        # Lazy loading del modelo Pedido
        Pedido = apps.get_model('pedidos', 'Pedido')

        # Verificar que el pedido existe
        pedido = get_object_or_404(Pedido, pk=pedido_id)

        # Validar que el pedido no esté asignado a este repartidor
        if pedido.repartidor == repartidor:
            return Response(
                {"error": "No puedes rechazar un pedido que ya aceptaste."},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(f"Repartidor {repartidor.id} rechazó pedido {pedido_id}")

        # Aquí podrías registrar el rechazo en una tabla de auditoría si existe

        return Response({
            "mensaje": "Pedido rechazado",
            "pedido_id": pedido.id,
        }, status=status.HTTP_200_OK)

    except AttributeError:
        return Response(
            {"error": "No tienes perfil de repartidor asociado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except LookupError:
        logger.error("Modelo 'Pedido' no encontrado")
        return Response(
            {"error": "Configuración del sistema incorrecta."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Error al rechazar pedido: {e}", exc_info=True)
        return Response(
            {"error": "Error interno al rechazar pedido."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
