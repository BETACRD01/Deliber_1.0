// lib/services/solicitudes_service.dart

import 'dart:developer' as developer;
import '../config/api_config.dart';
import '../apis/subapis/http_client.dart';
import '../apis/helpers/api_exception.dart';

/// ✅ Servicio para gestionar solicitudes de cambio de rol
/// USUARIO: Crear y consultar sus propias solicitudes
/// ADMIN: Ver y gestionar todas las solicitudes
class SolicitudesService {
  final ApiClient _client = ApiClient();

  // ════════════════════════════════════════════════════════════════════════
  // 👤 ENDPOINTS USUARIO
  // ════════════════════════════════════════════════════════════════════════

  /// GET - Obtener mis solicitudes de cambio de rol
  Future<Map<String, dynamic>> obtenerMisSolicitudes() async {
    try {
      developer.log(
        '📋 Obteniendo mis solicitudes de cambio de rol',
        name: 'SolicitudesService',
      );

      final response = await _client.get(
        ApiConfig.usuariosSolicitudesCambioRol,
      );

      developer.log(
        '✅ Solicitudes obtenidas: ${response['total'] ?? 0}',
        name: 'SolicitudesService',
      );

      return response;
    } on ApiException catch (e) {
      developer.log(
        '❌ Error obteniendo solicitudes: ${e.message}',
        name: 'SolicitudesService',
        error: e,
      );
      rethrow;
    }
  }

  /// POST - Crear solicitud para PROVEEDOR
  Future<Map<String, dynamic>> crearSolicitudProveedor({
    required String ruc,
    required String nombreComercial,
    required String tipoNegocio,
    required String descripcionNegocio,
    required String motivo,
    String? horarioApertura,
    String? horarioCierre,
  }) async {
    try {
      developer.log(
        '📝 Creando solicitud PROVEEDOR: $nombreComercial',
        name: 'SolicitudesService',
      );

      if (ruc.length != 13) {
        throw ApiException(
          statusCode: 400,
          message: 'El RUC debe tener exactamente 13 dígitos',
          errors: {
            'ruc': ['Debe tener 13 dígitos'],
          },
          stackTrace: StackTrace.current,
        );
      }

      if (motivo.length < 10) {
        throw ApiException(
          statusCode: 400,
          message: 'El motivo debe tener al menos 10 caracteres',
          errors: {
            'motivo': ['Mínimo 10 caracteres'],
          },
          stackTrace: StackTrace.current,
        );
      }

      final body = {
        'rol_solicitado': 'PROVEEDOR',
        'ruc': ruc,
        'nombre_comercial': nombreComercial,
        'tipo_negocio': tipoNegocio,
        'descripcion_negocio': descripcionNegocio,
        'motivo': motivo,
        if (horarioApertura != null) 'horario_apertura': horarioApertura,
        if (horarioCierre != null) 'horario_cierre': horarioCierre,
      };

      final response = await _client.post(
        ApiConfig.usuariosSolicitudesCambioRol,
        body,
      );

      developer.log(
        '✅ Solicitud PROVEEDOR creada: ${response['solicitud']?['id']}',
        name: 'SolicitudesService',
      );

      return response;
    } on ApiException catch (e) {
      developer.log(
        '❌ Error creando solicitud PROVEEDOR: ${e.message}',
        name: 'SolicitudesService',
        error: e,
      );
      rethrow;
    }
  }

  /// POST - Crear solicitud para REPARTIDOR
  Future<Map<String, dynamic>> crearSolicitudRepartidor({
    required String cedulaIdentidad,
    required String tipoVehiculo,
    required String zonaCobertura,
    required String motivo,
    Map<String, dynamic>? disponibilidad,
  }) async {
    try {
      developer.log(
        '📝 Creando solicitud REPARTIDOR: $cedulaIdentidad',
        name: 'SolicitudesService',
      );

      if (cedulaIdentidad.length < 10) {
        throw ApiException(
          statusCode: 400,
          message: 'La cédula debe tener al menos 10 dígitos',
          errors: {
            'cedula_identidad': ['Mínimo 10 dígitos'],
          },
          stackTrace: StackTrace.current,
        );
      }

      if (motivo.length < 10) {
        throw ApiException(
          statusCode: 400,
          message: 'El motivo debe tener al menos 10 caracteres',
          errors: {
            'motivo': ['Mínimo 10 caracteres'],
          },
          stackTrace: StackTrace.current,
        );
      }

      final body = {
        'rol_solicitado': 'REPARTIDOR',
        'cedula_identidad': cedulaIdentidad,
        'tipo_vehiculo': tipoVehiculo,
        'zona_cobertura': zonaCobertura,
        'motivo': motivo,
        if (disponibilidad != null) 'disponibilidad': disponibilidad,
      };

      final response = await _client.post(
        ApiConfig.usuariosSolicitudesCambioRol,
        body,
      );

      developer.log(
        '✅ Solicitud REPARTIDOR creada: ${response['solicitud']?['id']}',
        name: 'SolicitudesService',
      );

      return response;
    } on ApiException catch (e) {
      developer.log(
        '❌ Error creando solicitud REPARTIDOR: ${e.message}',
        name: 'SolicitudesService',
        error: e,
      );
      rethrow;
    }
  }

  /// GET - Obtener detalle de una solicitud específica
  Future<Map<String, dynamic>> obtenerDetalleSolicitud(
    String solicitudId,
  ) async {
    try {
      developer.log(
        '🔍 Obteniendo detalle de solicitud: $solicitudId',
        name: 'SolicitudesService',
      );

      final response = await _client.get(
        ApiConfig.usuariosSolicitudCambioRolDetalle(solicitudId),
      );

      developer.log(
        '✅ Detalle obtenido: ${response['rol_solicitado']}',
        name: 'SolicitudesService',
      );

      return response;
    } on ApiException catch (e) {
      developer.log(
        '❌ Error obteniendo detalle: ${e.message}',
        name: 'SolicitudesService',
        error: e,
      );
      rethrow;
    }
  }

  /// POST - Cambiar rol activo del usuario
  Future<Map<String, dynamic>> cambiarRolActivo(String nuevoRol) async {
    try {
      developer.log(
        '🔄 Cambiando rol activo a: $nuevoRol',
        name: 'SolicitudesService',
      );

      final response = await _client.post(ApiConfig.usuariosCambiarRolActivo, {
        'nuevo_rol': nuevoRol,
      });

      developer.log(
        '✅ Rol cambiado: ${response['rol_anterior']} → ${response['rol_nuevo']}',
        name: 'SolicitudesService',
      );

      return response;
    } on ApiException catch (e) {
      developer.log(
        '❌ Error cambiando rol: ${e.message}',
        name: 'SolicitudesService',
        error: e,
      );
      rethrow;
    }
  }

  /// GET - Obtener roles del usuario
  Future<Map<String, dynamic>> obtenerMisRoles() async {
    try {
      developer.log('🎭 Obteniendo mis roles', name: 'SolicitudesService');

      final response = await _client.get(ApiConfig.usuariosMisRoles);

      developer.log(
        '✅ Roles obtenidos: ${response['roles_disponibles']}',
        name: 'SolicitudesService',
      );

      return response;
    } on ApiException catch (e) {
      developer.log(
        '❌ Error obteniendo roles: ${e.message}',
        name: 'SolicitudesService',
        error: e,
      );
      rethrow;
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // 🛡️ ENDPOINTS ADMIN
  // ════════════════════════════════════════════════════════════════════════

  /// GET - Listar TODAS las solicitudes (ADMIN)
  Future<Map<String, dynamic>> adminListarSolicitudes({
    String? estado,
    String? rolSolicitado,
  }) async {
    try {
      developer.log(
        '🛡️ [ADMIN] Listando solicitudes',
        name: 'SolicitudesService',
      );

      String url = ApiConfig.adminSolicitudesCambioRol;

      final params = <String, String>{};
      if (estado != null) params['estado'] = estado;
      if (rolSolicitado != null) params['rol_solicitado'] = rolSolicitado;

      if (params.isNotEmpty) {
        final query = params.entries
            .map((e) => '${e.key}=${Uri.encodeComponent(e.value)}')
            .join('&');
        url = '$url?$query';
      }

      final response = await _client.get(url);

      developer.log(
        '✅ [ADMIN] Solicitudes obtenidas: ${response['total'] ?? 0}',
        name: 'SolicitudesService',
      );

      return response;
    } on ApiException catch (e) {
      developer.log(
        '❌ [ADMIN] Error listando solicitudes: ${e.message}',
        name: 'SolicitudesService',
        error: e,
      );
      rethrow;
    }
  }

  /// GET - Detalle de solicitud (ADMIN)
  Future<Map<String, dynamic>> adminObtenerDetalle(String solicitudId) async {
    try {
      developer.log(
        '🛡️ [ADMIN] Obteniendo detalle: $solicitudId',
        name: 'SolicitudesService',
      );

      final response = await _client.get(
        ApiConfig.adminSolicitudCambioRolDetalle(solicitudId),
      );

      developer.log('✅ [ADMIN] Detalle obtenido', name: 'SolicitudesService');

      return response;
    } on ApiException catch (e) {
      developer.log(
        '❌ [ADMIN] Error obteniendo detalle: ${e.message}',
        name: 'SolicitudesService',
        error: e,
      );
      rethrow;
    }
  }

  /// POST - Aceptar solicitud (ADMIN) - ✅ MEJORADO
  Future<Map<String, dynamic>> adminAceptarSolicitud(
    String solicitudId, {
    String? motivoRespuesta,
  }) async {
    try {
      developer.log(
        '✅ [ADMIN] Aceptando solicitud: $solicitudId',
        name: 'SolicitudesService',
      );

      final body = <String, dynamic>{};
      if (motivoRespuesta != null) {
        body['motivo_respuesta'] = motivoRespuesta;
      }

      // ✅ USAR ENDPOINT ESPECÍFICO
      final response = await _client.post(
        ApiConfig.adminAceptarSolicitud(solicitudId),
        body,
      );

      developer.log('✅ [ADMIN] Solicitud aceptada', name: 'SolicitudesService');

      return response;
    } on ApiException catch (e) {
      developer.log(
        '❌ [ADMIN] Error aceptando solicitud: ${e.message}',
        name: 'SolicitudesService',
        error: e,
      );
      rethrow;
    }
  }

  /// POST - Rechazar solicitud (ADMIN) - ✅ MEJORADO
  Future<Map<String, dynamic>> adminRechazarSolicitud(
    String solicitudId, {
    required String motivoRespuesta,
  }) async {
    try {
      developer.log(
        '❌ [ADMIN] Rechazando solicitud: $solicitudId',
        name: 'SolicitudesService',
      );

      if (motivoRespuesta.trim().isEmpty) {
        throw ApiException(
          statusCode: 400,
          message: 'El motivo de rechazo es obligatorio',
          errors: {
            'motivo_respuesta': ['Este campo es requerido'],
          },
          stackTrace: StackTrace.current,
        );
      }

      // ✅ USAR ENDPOINT ESPECÍFICO
      final response = await _client.post(
        ApiConfig.adminRechazarSolicitud(solicitudId),
        {'motivo_respuesta': motivoRespuesta},
      );

      developer.log(
        '✅ [ADMIN] Solicitud rechazada',
        name: 'SolicitudesService',
      );

      return response;
    } on ApiException catch (e) {
      developer.log(
        '❌ [ADMIN] Error rechazando solicitud: ${e.message}',
        name: 'SolicitudesService',
        error: e,
      );
      rethrow;
    }
  }

  /// GET - Listar solicitudes pendientes (ADMIN) - ✅ NUEVO
  Future<Map<String, dynamic>> adminListarPendientes() async {
    try {
      developer.log(
        '🛡️ [ADMIN] Listando solicitudes pendientes',
        name: 'SolicitudesService',
      );

      final response = await _client.get(ApiConfig.adminSolicitudesPendientes);

      developer.log(
        '✅ [ADMIN] Pendientes obtenidas: ${response['total'] ?? 0}',
        name: 'SolicitudesService',
      );

      return response;
    } on ApiException catch (e) {
      developer.log(
        '❌ [ADMIN] Error listando pendientes: ${e.message}',
        name: 'SolicitudesService',
        error: e,
      );
      rethrow;
    }
  }

  /// GET - Estadísticas de solicitudes (ADMIN) - ✅ NUEVO
  Future<Map<String, dynamic>> adminObtenerEstadisticas() async {
    try {
      developer.log(
        '📊 [ADMIN] Obteniendo estadísticas',
        name: 'SolicitudesService',
      );

      final response = await _client.get(
        ApiConfig.adminSolicitudesEstadisticas,
      );

      developer.log(
        '✅ [ADMIN] Estadísticas obtenidas',
        name: 'SolicitudesService',
      );

      return response;
    } on ApiException catch (e) {
      developer.log(
        '❌ [ADMIN] Error obteniendo estadísticas: ${e.message}',
        name: 'SolicitudesService',
        error: e,
      );
      rethrow;
    }
  }
}
