// lib/services/repartidor_service.dart

import 'dart:io';
import 'dart:developer' as developer;
import '../apis/subapis/http_client.dart';
import '../apis/helpers/api_exception.dart';
import '../config/api_config.dart';
import '../models/repartidor.dart';
import '../models/pedido.dart';

/// Servicio completo de Repartidor - SOLO lógica de API
/// ✅ Sin mezclar con UI
/// ✅ Manejo de errores robusto
/// ✅ Caché opcional de datos
/// ✅ Tipado completo
class RepartidorService {
  // ══════════════════════════════════════════════════════════════════════════
  // SINGLETON
  // ══════════════════════════════════════════════════════════════════════════

  static final RepartidorService _instance = RepartidorService._internal();
  factory RepartidorService() => _instance;
  RepartidorService._internal();

  // ══════════════════════════════════════════════════════════════════════════
  // CLIENTE HTTP
  // ══════════════════════════════════════════════════════════════════════════

  final _client = ApiClient();

  // ══════════════════════════════════════════════════════════════════════════
  // CACHÉ DE DATOS (opcional)
  // ══════════════════════════════════════════════════════════════════════════

  PerfilRepartidorModel? _perfilCache;
  EstadisticasRepartidorModel? _estadisticasCache;
  List<VehiculoRepartidorModel>? _vehiculosCache;

  // ✅ NUEVO: Getter público para acceder al cliente (necesario para UbicacionService)
  ApiClient get client => _client;

  // ══════════════════════════════════════════════════════════════════════════
  // LOGGING
  // ══════════════════════════════════════════════════════════════════════════

  void _log(String message, {Object? error, StackTrace? stackTrace}) {
    developer.log(
      message,
      name: 'RepartidorService',
      error: error,
      stackTrace: stackTrace,
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 👤 PERFIL DEL REPARTIDOR
  // ══════════════════════════════════════════════════════════════════════════

  /// GET /api/repartidores/perfil/
  /// Obtiene el perfil completo del repartidor autenticado
  Future<PerfilRepartidorModel> obtenerPerfil({
    bool forzarRecarga = false,
  }) async {
    try {
      // Usar caché si existe y no se fuerza recarga
      if (!forzarRecarga && _perfilCache != null) {
        _log('✅ Retornando perfil desde caché');
        return _perfilCache!;
      }

      _log('📥 GET: Obtener perfil del repartidor');

      final response = await _client.get(ApiConfig.repartidorPerfil);

      final perfil = PerfilRepartidorModel.fromJson(response);

      // Guardar en caché
      _perfilCache = perfil;

      _log('✅ Perfil obtenido correctamente');
      return perfil;
    } on ApiException {
      _log('❌ Error obteniendo perfil');
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error inesperado obteniendo perfil',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al obtener perfil del repartidor',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// PATCH /api/repartidores/perfil/actualizar/
  /// Actualiza el perfil del repartidor (teléfono, foto)
  /// Soporta multipart/form-data para subir foto
  Future<PerfilRepartidorModel> actualizarPerfil({
    String? telefono,
    File? fotoPerfil,
  }) async {
    try {
      _log('📤 PATCH: Actualizar perfil del repartidor');
      if (telefono != null) _log('   📞 Teléfono: $telefono');
      if (fotoPerfil != null) _log('   📸 Foto: ${fotoPerfil.path}');

      Map<String, dynamic> response;

      // Si hay foto, usar multipart
      if (fotoPerfil != null) {
        final fields = <String, String>{};
        if (telefono != null && telefono.isNotEmpty) {
          fields['telefono'] = telefono;
        }

        final files = <String, File>{'foto_perfil': fotoPerfil};

        response = await _client.multipart(
          'PATCH',
          ApiConfig.repartidorPerfilActualizar,
          fields,
          files,
        );
      } else {
        // Sin foto, usar PATCH normal
        final data = <String, dynamic>{};
        if (telefono != null && telefono.isNotEmpty) {
          data['telefono'] = telefono;
        }

        response = await _client.patch(
          ApiConfig.repartidorPerfilActualizar,
          data,
        );
      }

      // Parsear respuesta
      final perfilData = response['perfil'] as Map<String, dynamic>;
      final perfil = PerfilRepartidorModel.fromJson(perfilData);

      // Actualizar caché
      _perfilCache = perfil;

      _log('✅ Perfil actualizado correctamente');
      return perfil;
    } on ApiException {
      _log('❌ Error actualizando perfil');
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error inesperado actualizando perfil',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al actualizar perfil',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// GET /api/repartidores/perfil/estadisticas/
  /// Obtiene estadísticas detalladas del repartidor
  Future<EstadisticasRepartidorModel> obtenerEstadisticas({
    bool forzarRecarga = false,
  }) async {
    try {
      if (!forzarRecarga && _estadisticasCache != null) {
        _log('✅ Retornando estadísticas desde caché');
        return _estadisticasCache!;
      }

      _log('📥 GET: Obtener estadísticas del repartidor');

      final response = await _client.get(ApiConfig.repartidorEstadisticas);

      final estadisticas = EstadisticasRepartidorModel.fromJson(response);

      _estadisticasCache = estadisticas;

      _log('✅ Estadísticas obtenidas');
      return estadisticas;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log('❌ Error obteniendo estadísticas', error: e, stackTrace: stackTrace);
      throw ApiException(
        statusCode: 0,
        message: 'Error al obtener estadísticas',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🔄 GESTIÓN DE ESTADO
  // ══════════════════════════════════════════════════════════════════════════

  /// PATCH /api/repartidores/estado/
  /// Cambia el estado del repartidor (disponible/ocupado/fuera_servicio)
  Future<CambioEstadoResponse> cambiarEstado(
    EstadoRepartidor nuevoEstado,
  ) async {
    try {
      _log('📤 PATCH: Cambiar estado a ${nuevoEstado.nombre}');

      final response = await _client.patch(ApiConfig.repartidorEstado, {
        'estado': nuevoEstado.valor,
      });

      final cambioEstado = CambioEstadoResponse.fromJson(response);

      // Actualizar caché del perfil si existe
      if (_perfilCache != null) {
        _perfilCache = _perfilCache!.copyWith(estado: nuevoEstado);
      }

      _log(
        '✅ Estado cambiado: ${cambioEstado.estadoAnterior.nombre} → ${cambioEstado.estadoNuevo.nombre}',
      );
      return cambioEstado;
    } on ApiException {
      _log('❌ Error cambiando estado');
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error inesperado cambiando estado',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al cambiar estado',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// GET /api/repartidores/estado/historial/
  /// Obtiene el historial de cambios de estado
  Future<List<EstadoLogModel>> obtenerHistorialEstados({
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      _log('📥 GET: Obtener historial de estados (página $page)');

      final url = _buildUrlWithParams(ApiConfig.repartidorEstadoHistorial, {
        'page': page.toString(),
        'page_size': pageSize.toString(),
      });

      final response = await _client.get(url);

      // Puede venir paginado o no
      final results = response['results'] ?? response;

      final historial = (results as List)
          .map((log) => EstadoLogModel.fromJson(log as Map<String, dynamic>))
          .toList();

      _log('✅ Historial obtenido: ${historial.length} registros');
      return historial;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error obteniendo historial de estados',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al obtener historial',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📍 UBICACIÓN EN TIEMPO REAL
  // ══════════════════════════════════════════════════════════════════════════

  /// PATCH /api/repartidores/ubicacion/
  /// Actualiza la ubicación del repartidor
  Future<UbicacionActualizadaResponse> actualizarUbicacion({
    required double latitud,
    required double longitud,
  }) async {
    try {
      _log('📤 PATCH: Actualizar ubicación');
      _log('   📍 Coordenadas: ($latitud, $longitud)');

      final response = await _client.patch(ApiConfig.repartidorUbicacion, {
        'latitud': latitud,
        'longitud': longitud,
      });

      final ubicacion = UbicacionActualizadaResponse.fromJson(response);

      // Actualizar caché del perfil
      if (_perfilCache != null) {
        _perfilCache = _perfilCache!.copyWith(
          latitud: latitud,
          longitud: longitud,
          ultimaLocalizacion: ubicacion.timestamp,
        );
      }

      _log('✅ Ubicación actualizada');
      return ubicacion;
    } on ApiException {
      _log('❌ Error actualizando ubicación');
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error inesperado actualizando ubicación',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al actualizar ubicación',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// GET /api/repartidores/ubicacion/historial/
  /// Obtiene el historial de ubicaciones
  Future<List<UbicacionHistorialModel>> obtenerHistorialUbicaciones({
    String? fechaInicio,
    String? fechaFin,
    int page = 1,
    int pageSize = 50,
  }) async {
    try {
      _log('📥 GET: Obtener historial de ubicaciones');

      final params = <String, String>{
        'page': page.toString(),
        'page_size': pageSize.toString(),
      };

      if (fechaInicio != null) params['fecha_inicio'] = fechaInicio;
      if (fechaFin != null) params['fecha_fin'] = fechaFin;

      final url = _buildUrlWithParams(
        ApiConfig.repartidorUbicacionHistorial,
        params,
      );

      final response = await _client.get(url);

      final results = response['results'] ?? response;

      final historial = (results as List)
          .map(
            (ub) =>
                UbicacionHistorialModel.fromJson(ub as Map<String, dynamic>),
          )
          .toList();

      _log(
        '✅ Historial de ubicaciones obtenido: ${historial.length} registros',
      );
      return historial;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error obteniendo historial de ubicaciones',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al obtener historial de ubicaciones',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🗺️ PEDIDOS DISPONIBLES Y MAPA
  // ══════════════════════════════════════════════════════════════════════════

  /// GET /api/repartidores/pedidos-disponibles/
  /// Obtiene pedidos cercanos al repartidor
  /// ✅ CORREGIDO: Envía coordenadas explícitas si están disponibles
  Future<PedidosDisponiblesResponse> obtenerPedidosDisponibles({
    double radioKm = 15.0,
    double? latitud,
    double? longitud,
  }) async {
    try {
      _log('📥 GET: Obtener pedidos disponibles (radio: ${radioKm}km)');

      final params = <String, String>{'radio': radioKm.toString()};

      // ✅ Enviar coordenadas si están disponibles
      if (latitud != null && longitud != null) {
        params['latitud'] = latitud.toString();
        params['longitud'] = longitud.toString();
        _log('   📍 Coordenadas enviadas: ($latitud, $longitud)');
      } else {
        _log('   ℹ️ Sin coordenadas - usando ubicación guardada del backend');
      }

      final url = _buildUrlWithParams(
        ApiConfig.repartidorPedidosDisponibles,
        params,
      );

      final response = await _client.get(url);

      final pedidosResponse = PedidosDisponiblesResponse.fromJson(response);

      _log('✅ ${pedidosResponse.totalPedidos} pedidos disponibles');
      return pedidosResponse;
    } on ApiException {
      _log('❌ Error obteniendo pedidos disponibles');
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error inesperado obteniendo pedidos',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al obtener pedidos disponibles',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// POST /api/repartidores/pedidos/{id}/aceptar/
  /// Acepta un pedido disponible
  Future<Map<String, dynamic>> aceptarPedido(int pedidoId) async {
    try {
      _log('📤 POST: Aceptar pedido #$pedidoId');

      final response = await _client.post(
        ApiConfig.repartidorPedidoAceptar(pedidoId),
        {},
      );

      _log('✅ Pedido #$pedidoId aceptado');
      return response;
    } on ApiException {
      _log('❌ Error aceptando pedido #$pedidoId');
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error inesperado aceptando pedido',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al aceptar pedido',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// POST /api/repartidores/pedidos/{id}/rechazar/
  /// Rechaza un pedido
  Future<Map<String, dynamic>> rechazarPedido(
    int pedidoId, {
    String motivo = 'Muy lejos',
  }) async {
    try {
      _log('📤 POST: Rechazar pedido #$pedidoId (motivo: $motivo)');

      final response = await _client.post(
        ApiConfig.repartidorPedidoRechazar(pedidoId),
        {'motivo': motivo},
      );

      _log('✅ Pedido #$pedidoId rechazado');
      return response;
    } on ApiException {
      _log('❌ Error rechazando pedido #$pedidoId');
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error inesperado rechazando pedido',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al rechazar pedido',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// POST /api/repartidores/calificaciones/clientes/{pedidoId}/
  /// Califica a un cliente después de completar un pedido
  Future<Map<String, dynamic>> calificarCliente({
    required int pedidoId,
    required double puntuacion,
    String? comentario,
  }) async {
    try {
      _log('📤 POST: Calificar cliente (pedido #$pedidoId)');
      _log('   ⭐ Puntuación: $puntuacion');

      final data = <String, dynamic>{'puntuacion': puntuacion};

      if (comentario != null && comentario.isNotEmpty) {
        data['comentario'] = comentario;
      }

      final response = await _client.post(
        ApiConfig.repartidorCalificarCliente(pedidoId),
        data,
      );

      _log('✅ Cliente calificado correctamente');
      return response;
    } on ApiException {
      _log('❌ Error calificando cliente');
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error inesperado calificando cliente',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al calificar cliente',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🚗 VEHÍCULOS - CRUD COMPLETO
  // ══════════════════════════════════════════════════════════════════════════

  /// GET /api/repartidores/vehiculos/
  /// Lista todos los vehículos del repartidor
  Future<List<VehiculoRepartidorModel>> listarVehiculos({
    bool forzarRecarga = false,
  }) async {
    try {
      if (!forzarRecarga && _vehiculosCache != null) {
        _log('✅ Retornando vehículos desde caché');
        return _vehiculosCache!;
      }

      _log('📥 GET: Listar vehículos');

      final response = await _client.get(ApiConfig.repartidorVehiculos);

      final vehiculosResponse = VehiculosResponse.fromJson(response);

      _vehiculosCache = vehiculosResponse.vehiculos;

      _log('✅ ${vehiculosResponse.total} vehículos obtenidos');
      return vehiculosResponse.vehiculos;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log('❌ Error listando vehículos', error: e, stackTrace: stackTrace);
      throw ApiException(
        statusCode: 0,
        message: 'Error al listar vehículos',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// POST /api/repartidores/vehiculos/crear/
  /// Crea un nuevo vehículo
  Future<VehiculoRepartidorModel> crearVehiculo({
    required TipoVehiculo tipo,
    String? placa,
    bool activo = false,
  }) async {
    try {
      _log('📤 POST: Crear vehículo (${tipo.nombre})');

      final data = {'tipo': tipo.valor, 'activo': activo};

      if (placa != null && placa.isNotEmpty) {
        data['placa'] = placa.toUpperCase();
      }

      final response = await _client.post(
        ApiConfig.repartidorVehiculosCrear,
        data,
      );

      final vehiculoData = response['vehiculo'] as Map<String, dynamic>;
      final vehiculo = VehiculoRepartidorModel.fromJson(vehiculoData);

      // Limpiar caché
      _vehiculosCache = null;

      _log('✅ Vehículo creado: ${vehiculo.tipo.nombre}');
      return vehiculo;
    } on ApiException {
      _log('❌ Error creando vehículo');
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error inesperado creando vehículo',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al crear vehículo',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// GET /api/repartidores/vehiculos/{id}/
  /// Obtiene detalles de un vehículo específico
  Future<VehiculoRepartidorModel> obtenerVehiculo(int vehiculoId) async {
    try {
      _log('📥 GET: Obtener vehículo #$vehiculoId');

      final response = await _client.get(
        ApiConfig.repartidorVehiculo(vehiculoId),
      );

      final vehiculo = VehiculoRepartidorModel.fromJson(response);

      _log('✅ Vehículo obtenido');
      return vehiculo;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log('❌ Error obteniendo vehículo', error: e, stackTrace: stackTrace);
      throw ApiException(
        statusCode: 0,
        message: 'Error al obtener vehículo',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// PATCH /api/repartidores/vehiculo/actualizar-datos/
  /// ✅ NUEVO: Actualiza datos del vehículo activo (tipo, placa, licencia)
  Future<VehiculoRepartidorModel> actualizarDatosVehiculo({
    TipoVehiculo? tipo,
    String? placa,
    File? licenciaFoto,
  }) async {
    try {
      _log('📤 PATCH: Actualizar datos de vehículo activo');

      Map<String, dynamic> response;

      // Si hay foto de licencia, usar multipart
      if (licenciaFoto != null) {
        final fields = <String, String>{};

        if (tipo != null) fields['tipo'] = tipo.valor;
        if (placa != null && placa.isNotEmpty) {
          fields['placa'] = placa.toUpperCase();
        }

        final files = <String, File>{'licencia_foto': licenciaFoto};

        // ✅ IMPORTANTE: El endpoint es diferente
        final endpoint = '${ApiConfig.repartidorVehiculos}/actualizar-datos/';

        response = await _client.multipart('PATCH', endpoint, fields, files);
      } else {
        // Sin foto, usar PATCH normal
        final data = <String, dynamic>{};

        if (tipo != null) data['tipo'] = tipo.valor;
        if (placa != null && placa.isNotEmpty) {
          data['placa'] = placa.toUpperCase();
        }

        final endpoint = '${ApiConfig.repartidorVehiculos}/actualizar-datos/';

        response = await _client.patch(endpoint, data);
      }

      final vehiculoData = response['vehiculo'] as Map<String, dynamic>;
      final vehiculo = VehiculoRepartidorModel.fromJson(vehiculoData);

      // Limpiar caché
      _vehiculosCache = null;

      _log('✅ Datos de vehículo actualizados');
      return vehiculo;
    } on ApiException {
      _log('❌ Error actualizando datos de vehículo');
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error inesperado actualizando vehículo',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al actualizar vehículo',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// PATCH /api/repartidores/vehiculos/{id}/
  /// Actualiza un vehículo existente (datos básicos)
  Future<VehiculoRepartidorModel> actualizarVehiculo(
    int vehiculoId,
    Map<String, dynamic> data,
  ) async {
    try {
      _log('📤 PATCH: Actualizar vehículo #$vehiculoId');

      final response = await _client.patch(
        ApiConfig.repartidorVehiculo(vehiculoId),
        data,
      );

      final vehiculoData = response['vehiculo'] as Map<String, dynamic>;
      final vehiculo = VehiculoRepartidorModel.fromJson(vehiculoData);

      // Limpiar caché
      _vehiculosCache = null;

      _log('✅ Vehículo actualizado');
      return vehiculo;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log('❌ Error actualizando vehículo', error: e, stackTrace: stackTrace);
      throw ApiException(
        statusCode: 0,
        message: 'Error al actualizar vehículo',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// DELETE /api/repartidores/vehiculos/{id}/
  /// Elimina un vehículo
  Future<void> eliminarVehiculo(int vehiculoId) async {
    try {
      _log('📤 DELETE: Eliminar vehículo #$vehiculoId');

      await _client.delete(ApiConfig.repartidorVehiculo(vehiculoId));

      // Limpiar caché
      _vehiculosCache = null;

      _log('✅ Vehículo eliminado');
    } on ApiException {
      _log('❌ Error eliminando vehículo');
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error inesperado eliminando vehículo',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al eliminar vehículo',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// PATCH /api/repartidores/vehiculos/{id}/activar/
  /// Activa un vehículo (desactiva los demás automáticamente)
  Future<VehiculoRepartidorModel> activarVehiculo(int vehiculoId) async {
    try {
      _log('📤 PATCH: Activar vehículo #$vehiculoId');

      final response = await _client.patch(
        ApiConfig.repartidorVehiculoActivar(vehiculoId),
        {},
      );

      final vehiculoData = response['vehiculo'] as Map<String, dynamic>;
      final vehiculo = VehiculoRepartidorModel.fromJson(vehiculoData);

      // Limpiar caché
      _vehiculosCache = null;

      _log('✅ Vehículo activado');
      return vehiculo;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log('❌ Error activando vehículo', error: e, stackTrace: stackTrace);
      throw ApiException(
        statusCode: 0,
        message: 'Error al activar vehículo',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // ⭐ CALIFICACIONES
  // ══════════════════════════════════════════════════════════════════════════

  /// GET /api/repartidores/calificaciones/
  /// Lista las calificaciones recibidas
  Future<List<CalificacionRepartidorModel>> listarCalificaciones({
    int? puntuacion,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      _log('📥 GET: Listar calificaciones');

      final params = <String, String>{
        'page': page.toString(),
        'page_size': pageSize.toString(),
      };

      if (puntuacion != null) {
        params['puntuacion'] = puntuacion.toString();
      }

      final url = _buildUrlWithParams(
        ApiConfig.repartidorCalificaciones,
        params,
      );

      final response = await _client.get(url);

      final results = response['results'] ?? response;

      final calificaciones = (results as List)
          .map(
            (c) =>
                CalificacionRepartidorModel.fromJson(c as Map<String, dynamic>),
          )
          .toList();

      _log('✅ ${calificaciones.length} calificaciones obtenidas');
      return calificaciones;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log('❌ Error listando calificaciones', error: e, stackTrace: stackTrace);
      throw ApiException(
        statusCode: 0,
        message: 'Error al listar calificaciones',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🧹 GESTIÓN DE CACHÉ
  // ══════════════════════════════════════════════════════════════════════════

  /// Limpia toda la caché del servicio
  void limpiarCache() {
    _log('🧹 Limpiando caché completa');
    _perfilCache = null;
    _estadisticasCache = null;
    _vehiculosCache = null;
  }

  /// Limpia solo la caché del perfil
  void limpiarCachePerfil() {
    _log('🧹 Limpiando caché de perfil');
    _perfilCache = null;
    _estadisticasCache = null;
  }

  /// Limpia solo la caché de vehículos
  void limpiarCacheVehiculos() {
    _log('🧹 Limpiando caché de vehículos');
    _vehiculosCache = null;
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📊 GETTERS DE CACHÉ (para acceso rápido sin peticiones)
  // ══════════════════════════════════════════════════════════════════════════

  /// Perfil cacheado (puede ser null si no se ha cargado)
  PerfilRepartidorModel? get perfilActual => _perfilCache;

  /// Estadísticas cacheadas
  EstadisticasRepartidorModel? get estadisticasActuales => _estadisticasCache;

  /// Vehículos cacheados
  List<VehiculoRepartidorModel>? get vehiculosActuales => _vehiculosCache;

  /// ¿Hay perfil cargado en caché?
  bool get tienePerfil => _perfilCache != null;

  /// ¿El repartidor está disponible? (según caché)
  bool get estaDisponible {
    return _perfilCache?.estado == EstadoRepartidor.disponible;
  }

  /// ¿El repartidor está ocupado? (según caché)
  bool get estaOcupado {
    return _perfilCache?.estado == EstadoRepartidor.ocupado;
  }

  /// ¿El repartidor puede recibir pedidos? (según caché)
  bool get puedeRecibirPedidos {
    return _perfilCache?.puedeRecibirPedidos ?? false;
  }

  /// Vehículo activo actual (según caché)
  VehiculoRepartidorModel? get vehiculoActivo {
    return _perfilCache?.vehiculoActivo ??
        _vehiculosCache?.firstWhere(
          (v) => v.activo,
          orElse: () => _vehiculosCache!.first,
        );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🔧 UTILIDADES PRIVADAS
  // ══════════════════════════════════════════════════════════════════════════

  /// Construye URL con query parameters
  String _buildUrlWithParams(String endpoint, Map<String, String>? params) {
    if (params == null || params.isEmpty) return endpoint;

    final queryString = params.entries
        .map(
          (e) =>
              '${Uri.encodeComponent(e.key)}=${Uri.encodeComponent(e.value)}',
        )
        .join('&');

    return endpoint.contains('?')
        ? '$endpoint&$queryString'
        : '$endpoint?$queryString';
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🔍 MÉTODOS DE VALIDACIÓN
  // ══════════════════════════════════════════════════════════════════════════

  /// Valida que el repartidor esté autenticado
  bool get estaAutenticado => _client.isAuthenticated;

  /// Valida que el perfil esté verificado (requiere haber cargado perfil)
  bool get estaVerificado => _perfilCache?.verificado ?? false;

  /// Valida que el perfil esté activo (requiere haber cargado perfil)
  bool get estaActivo => _perfilCache?.activo ?? false;

  /// Valida que tenga ubicación registrada
  bool get tieneUbicacion => _perfilCache?.tieneUbicacion ?? false;

  // ══════════════════════════════════════════════════════════════════════════
  // 📈 ESTADÍSTICAS Y MÉTRICAS (desde caché)
  // ══════════════════════════════════════════════════════════════════════════

  /// Total de entregas realizadas (desde caché)
  int get totalEntregas => _perfilCache?.entregasCompletadas ?? 0;

  /// Calificación promedio (desde caché)
  double get calificacionPromedio => _perfilCache?.calificacionPromedio ?? 5.0;

  /// Total de calificaciones recibidas (desde caché)
  int get totalCalificaciones => _perfilCache?.totalCalificaciones ?? 0;

  /// Nivel de experiencia (desde caché)
  String get nivelExperiencia => _perfilCache?.nivelExperiencia ?? 'Sin datos';

  // ══════════════════════════════════════════════════════════════════════════
  // 🎯 MÉTODOS DE CONVENIENCIA
  // ══════════════════════════════════════════════════════════════════════════

  /// Marca al repartidor como disponible
  Future<CambioEstadoResponse> marcarDisponible() async {
    return await cambiarEstado(EstadoRepartidor.disponible);
  }

  /// Marca al repartidor como ocupado
  Future<CambioEstadoResponse> marcarOcupado() async {
    return await cambiarEstado(EstadoRepartidor.ocupado);
  }

  /// Marca al repartidor como fuera de servicio
  Future<CambioEstadoResponse> marcarFueraServicio() async {
    return await cambiarEstado(EstadoRepartidor.fueraServicio);
  }

  /// Toggle entre disponible y fuera de servicio
  Future<CambioEstadoResponse> toggleDisponibilidad() async {
    final estadoActual = _perfilCache?.estado ?? EstadoRepartidor.fueraServicio;

    if (estadoActual == EstadoRepartidor.disponible) {
      return await marcarFueraServicio();
    } else {
      return await marcarDisponible();
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🔄 RECARGA COMPLETA DE DATOS
  // ══════════════════════════════════════════════════════════════════════════

  /// Recarga todos los datos del repartidor (perfil, estadísticas, vehículos)
  Future<void> recargarTodo() async {
    _log('🔄 Recargando todos los datos del repartidor...');

    try {
      await Future.wait([
        obtenerPerfil(forzarRecarga: true),
        obtenerEstadisticas(forzarRecarga: true),
        listarVehiculos(forzarRecarga: true),
      ]);

      _log('✅ Todos los datos recargados correctamente');
    } catch (e, stackTrace) {
      _log('❌ Error recargando datos', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🐛 DEBUG Y LOGGING
  // ══════════════════════════════════════════════════════════════════════════

  /// Imprime el estado actual del servicio (para debugging)
  void imprimirEstado() {
    _log('═══════════════════════════════════════════════════════════════');
    _log('📊 ESTADO DEL REPARTIDOR SERVICE');
    _log('═══════════════════════════════════════════════════════════════');
    _log('🔐 Autenticado: $estaAutenticado');
    _log('👤 Perfil cargado: $tienePerfil');

    if (_perfilCache != null) {
      _log('   ID: ${_perfilCache!.id}');
      _log('   Nombre: ${_perfilCache!.nombreCompleto}');
      _log('   Estado: ${_perfilCache!.estado.nombre}');
      _log('   Verificado: ${_perfilCache!.verificado}');
      _log('   Activo: ${_perfilCache!.activo}');
      _log('   Entregas: ${_perfilCache!.entregasCompletadas}');
      _log('   Rating: ${_perfilCache!.calificacionPromedio}⭐');
      _log('   Ubicación: ${_perfilCache!.tieneUbicacion ? "Sí" : "No"}');
    }

    if (_estadisticasCache != null) {
      _log('📈 Estadísticas cargadas:');
      _log(
        '   Total calificaciones: ${_estadisticasCache!.totalCalificaciones}',
      );
      _log('   5⭐: ${_estadisticasCache!.calificaciones5Estrellas}');
    }

    if (_vehiculosCache != null) {
      _log('🚗 Vehículos cargados: ${_vehiculosCache!.length}');
      final activo = vehiculoActivo;
      if (activo != null) {
        _log(
          '   Activo: ${activo.tipo.nombre} (${activo.placa ?? "Sin placa"})',
        );
      }
    }

    _log('═══════════════════════════════════════════════════════════════');
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🧪 VALIDACIONES DE DATOS
  // ══════════════════════════════════════════════════════════════════════════

  /// Valida que los datos mínimos estén completos para trabajar
  bool validarDatosMinimos() {
    if (!estaAutenticado) {
      _log('❌ Validación: No autenticado');
      return false;
    }

    if (!tienePerfil) {
      _log('⚠️ Validación: Perfil no cargado');
      return false;
    }

    if (!estaVerificado) {
      _log('⚠️ Validación: Repartidor no verificado');
      return false;
    }

    if (!estaActivo) {
      _log('⚠️ Validación: Cuenta inactiva');
      return false;
    }

    if (vehiculoActivo == null) {
      _log('⚠️ Validación: Sin vehículo activo');
      return false;
    }

    _log('✅ Validación: Datos mínimos completos');
    return true;
  }

  /// Obtiene una lista de problemas/advertencias del perfil
  List<String> obtenerAdvertencias() {
    final advertencias = <String>[];

    if (!estaAutenticado) {
      advertencias.add('No estás autenticado');
      return advertencias;
    }

    if (!tienePerfil) {
      advertencias.add('Perfil no cargado');
      return advertencias;
    }

    if (!estaVerificado) {
      advertencias.add('Tu cuenta no está verificada por un administrador');
    }

    if (!estaActivo) {
      advertencias.add('Tu cuenta está desactivada');
    }

    if (!tieneUbicacion) {
      advertencias.add('No has registrado tu ubicación');
    }

    if (vehiculoActivo == null) {
      advertencias.add('No tienes un vehículo activo configurado');
    }

    if (totalEntregas == 0) {
      advertencias.add('Aún no has realizado entregas');
    }

    return advertencias;
  }
}
