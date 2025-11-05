// lib/services/servicio_usuario.dart

import 'dart:io';
import 'dart:developer' as developer;
import '../apis/usuarios_api.dart';
import '../models/usuario.dart';
import '../apis/helpers/api_exception.dart';
import 'package:image/image.dart' as img;

/// Servicio de Usuario - Capa de lógica de negocio
/// Conecta la API con la UI, maneja modelos y errores
/// ✅ CON SOPORTE PARA COMPROBANTES DE PAGO
/// ✅ CORRECCIÓN: Gestión de caché mejorada para direcciones
class UsuarioService {
  // ══════════════════════════════════════════════════════════════════════════
  // SINGLETON
  // ══════════════════════════════════════════════════════════════════════════

  static final UsuarioService _instance = UsuarioService._internal();
  factory UsuarioService() => _instance;
  UsuarioService._internal();

  // ══════════════════════════════════════════════════════════════════════════
  // API CLIENT
  // ══════════════════════════════════════════════════════════════════════════

  final _api = UsuariosApi();

  // ══════════════════════════════════════════════════════════════════════════
  // CACHE (opcional, para optimización)
  // ══════════════════════════════════════════════════════════════════════════

  PerfilModel? _perfilCache;
  List<DireccionModel>? _direccionesCache;
  List<MetodoPagoModel>? _metodosPagoCache;
  EstadisticasModel? _estadisticasCache;

  // ══════════════════════════════════════════════════════════════════════════
  // LOGGING
  // ══════════════════════════════════════════════════════════════════════════

  void _log(String message, {Object? error, StackTrace? stackTrace}) {
    developer.log(
      message,
      name: 'UsuarioService',
      error: error,
      stackTrace: stackTrace,
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 👤 PERFIL
  // ══════════════════════════════════════════════════════════════════════════

  /// Obtiene el perfil del usuario autenticado
  Future<PerfilModel> obtenerPerfil({bool forzarRecarga = false}) async {
    try {
      // Usar cache si existe y no se fuerza recarga
      if (!forzarRecarga && _perfilCache != null) {
        _log('✅ Retornando perfil desde cache');
        return _perfilCache!;
      }

      _log('📥 Obteniendo perfil desde API...');
      final response = await _api.obtenerPerfil();

      // Extraer perfil del response
      final perfilData = response['perfil'] as Map<String, dynamic>;
      final perfil = PerfilModel.fromJson(perfilData);

      // Guardar en cache
      _perfilCache = perfil;

      _log('✅ Perfil obtenido y cacheado');
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
        message: 'Error al obtener perfil',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// Obtiene el perfil público de otro usuario
  Future<PerfilModel> obtenerPerfilPublico(int userId) async {
    try {
      _log('📥 Obteniendo perfil público de usuario $userId...');
      final response = await _api.obtenerPerfilPublico(userId);

      final perfilData = response['perfil'] as Map<String, dynamic>;
      final perfil = PerfilModel.fromJson(perfilData);

      _log('✅ Perfil público obtenido');
      return perfil;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error obteniendo perfil público',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al obtener perfil público',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// Actualiza el perfil del usuario
  Future<PerfilModel> actualizarPerfil(Map<String, dynamic> data) async {
    try {
      _log('📤 Actualizando perfil...');
      final response = await _api.actualizarPerfil(data);

      final perfilData = response['perfil'] as Map<String, dynamic>;
      final perfil = PerfilModel.fromJson(perfilData);

      // Actualizar cache
      _perfilCache = perfil;

      _log('✅ Perfil actualizado');
      return perfil;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log('❌ Error actualizando perfil', error: e, stackTrace: stackTrace);
      throw ApiException(
        statusCode: 0,
        message: 'Error al actualizar perfil',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// Obtiene las estadísticas del usuario
  Future<EstadisticasModel> obtenerEstadisticas({
    bool forzarRecarga = false,
  }) async {
    try {
      if (!forzarRecarga && _estadisticasCache != null) {
        _log('✅ Retornando estadísticas desde cache');
        return _estadisticasCache!;
      }

      _log('📥 Obteniendo estadísticas...');
      final response = await _api.obtenerEstadisticas();

      final estadisticasData = response['estadisticas'] as Map<String, dynamic>;
      final estadisticas = EstadisticasModel.fromJson(estadisticasData);

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
  // 📍 DIRECCIONES - ✅ COMPLETAMENTE CORREGIDO
  // ══════════════════════════════════════════════════════════════════════════

  /// Lista todas las direcciones del usuario
  /// ✅ CORRECCIÓN CRÍTICA: Gestión de caché mejorada
  Future<List<DireccionModel>> listarDirecciones({
    bool forzarRecarga = false,
  }) async {
    try {
      // ✅ CRÍTICO: Si se fuerza recarga, limpiar caché ANTES de hacer fetch
      if (forzarRecarga) {
        _log('🧹 Limpiando caché por forzarRecarga=true');
        _direccionesCache = null;
      }

      // ✅ Solo usar caché si NO es null, NO está vacío Y NO se fuerza recarga
      if (!forzarRecarga &&
          _direccionesCache != null &&
          _direccionesCache!.isNotEmpty) {
        _log(
          '✅ Retornando ${_direccionesCache!.length} direcciones desde cache',
        );
        return _direccionesCache!;
      }

      _log('📥 Obteniendo direcciones desde API...');
      _log('   forzarRecarga: $forzarRecarga');
      _log('   caché actual: ${_direccionesCache?.length ?? "null"}');

      final response = await _api.listarDirecciones();

      // ✅ Intentar primero 'direcciones' (sin paginación), luego 'results' (con paginación)
      final direccionesData = response['direcciones'] ?? response['results'];

      // ✅ Validar tipo de datos
      if (direccionesData == null) {
        _log('⚠️ Response no contiene direcciones ni results');
        _direccionesCache = [];
        return [];
      }

      if (direccionesData is! List) {
        _log(
          '⚠️ direccionesData no es una lista: ${direccionesData.runtimeType}',
        );
        _direccionesCache = [];
        return [];
      }

      // ✅ Parsear direcciones
      _log('📦 Parseando ${direccionesData.length} direcciones...');

      final List<DireccionModel> direcciones = [];

      for (var i = 0; i < direccionesData.length; i++) {
        try {
          final json = direccionesData[i] as Map<String, dynamic>;
          final dir = DireccionModel.fromJson(json);
          direcciones.add(dir);
          _log('   ✓ [$i] ${dir.etiqueta}: "${dir.direccion}"');
        } catch (e) {
          _log('   ✗ [$i] Error parseando dirección: $e');
        }
      }

      // ✅ Cachear resultado (incluso si está vacío)
      _direccionesCache = direcciones;

      _log('✅ ${direcciones.length} direcciones obtenidas y cacheadas');
      return direcciones;
    } on ApiException catch (e) {
      _log('❌ ApiException en listarDirecciones: ${e.message}');
      // ✅ Limpiar caché en caso de error
      _direccionesCache = null;
      rethrow;
    } catch (e, stackTrace) {
      _log('❌ Error listando direcciones', error: e, stackTrace: stackTrace);
      // ✅ Limpiar caché en caso de error
      _direccionesCache = null;

      throw ApiException(
        statusCode: 0,
        message: 'Error al listar direcciones',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// Crea una nueva dirección
  /// ✅ Adaptado para soportar respuestas planas, duplicadas y actualizaciones automáticas
  Future<DireccionModel> crearDireccion(DireccionModel direccion) async {
    try {
      _log('📤 Creando dirección...');
      _log('   Dirección: "${direccion.direccion}"');
      _log('   Ciudad: "${direccion.ciudad}"');
      _log('   Coordenadas: (${direccion.latitud}, ${direccion.longitud})');

      final response = await _api.crearDireccion(direccion.toCreateJson());

      _log('📩 Respuesta del backend: ${response.keys.join(", ")}');

      Map<String, dynamic>? data;

      // ✅ Caso 1: respuesta estándar envuelta {"direccion": {...}}
      if (response.containsKey('direccion')) {
        data = response['direccion'] as Map<String, dynamic>;
        _log('📦 Dirección encontrada bajo clave "direccion"');
      }
      // ✅ Caso 2: respuesta plana {...} (DRF estándar)
      else if (response.containsKey('id') && response.containsKey('etiqueta')) {
        data = response;
        _log('📦 Dirección detectada en formato plano');
      }
      // ✅ Caso 3: respuesta dentro de "data" (backend personalizado)
      else if (response.containsKey('data') &&
          response['data'] is Map<String, dynamic>) {
        data = response['data'] as Map<String, dynamic>;
        _log('📦 Dirección encontrada bajo clave "data"');
      }

      if (data == null) {
        _log('⚠️ Response sin estructura válida');
        throw ApiException(
          statusCode: 0,
          message: 'Respuesta inválida del servidor',
          errors: {'error': 'No se recibió la dirección creada correctamente'},
          stackTrace: StackTrace.current,
        );
      }

      final nuevaDireccion = DireccionModel.fromJson(data);

      _direccionesCache = null;
      _log('🧹 Caché de direcciones limpiado después de crear');
      _log('✅ Dirección creada exitosamente: ${nuevaDireccion.direccion}');
      return nuevaDireccion;
    } on ApiException catch (e) {
      _log('❌ ApiException creando dirección: ${e.message}');
      _log('   Status Code: ${e.statusCode}');
      _log('   Errors: ${e.errors}');
      _direccionesCache = null;

      // ===============================================================
      // 🧩 CASO: DIRECCIÓN DUPLICADA (etiqueta o ubicación cercana)
      // ===============================================================
      final esDuplicadaUbicacion =
          e.errors.containsKey('non_field_errors') &&
          e.errors['non_field_errors'].toString().contains('muy cercana');

      final esDuplicadaEtiqueta =
          e.errors.containsKey('etiqueta') &&
          e.errors['etiqueta'].toString().contains(
            'Ya tienes una dirección guardada',
          );

      if (esDuplicadaUbicacion || esDuplicadaEtiqueta) {
        _log('⚠️ Dirección duplicada detectada. Intentando actualizar...');

        final direcciones = await listarDirecciones(forzarRecarga: true);
        final existente = direcciones.firstWhere((d) {
          final mismaEtiqueta = esDuplicadaEtiqueta
              ? d.etiqueta == direccion.etiqueta
              : false;
          final mismaUbicacion = esDuplicadaUbicacion
              ? (d.latitud - direccion.latitud).abs() < 0.0003 &&
                    (d.longitud - direccion.longitud).abs() < 0.0003
              : false;
          return mismaEtiqueta || mismaUbicacion;
        }, orElse: () => direccion);

        // ✅ Actualizar dirección duplicada en el backend
        final actualizada = await actualizarDireccion(
          existente.id,
          direccion.toCreateJson(),
        );

        _log(
          '🔁 Dirección duplicada actualizada correctamente: ${actualizada.id}',
        );

        // ✅ Refrescar lista
        await listarDirecciones(forzarRecarga: true);

        return actualizada;
      }

      rethrow;
    } catch (e, stackTrace) {
      _log('❌ Error creando dirección', error: e, stackTrace: stackTrace);
      _direccionesCache = null;
      throw ApiException(
        statusCode: 0,
        message: 'Error al crear dirección',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// Obtiene una dirección específica
  Future<DireccionModel> obtenerDireccion(String direccionId) async {
    try {
      _log('📥 Obteniendo dirección $direccionId...');
      final response = await _api.obtenerDireccion(direccionId);

      final direccion = DireccionModel.fromJson(response);

      _log('✅ Dirección obtenida');
      return direccion;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log('❌ Error obteniendo dirección', error: e, stackTrace: stackTrace);
      throw ApiException(
        statusCode: 0,
        message: 'Error al obtener dirección',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// Actualiza una dirección existente
  /// ✅ CORRECCIÓN: Ahora limpia caché correctamente
  Future<DireccionModel> actualizarDireccion(
    String direccionId,
    Map<String, dynamic> data,
  ) async {
    try {
      _log('📤 Actualizando dirección $direccionId...');
      _log('   Datos a actualizar: ${data.keys.join(", ")}');

      // ✅ Limpiar caché ANTES de la petición
      _direccionesCache = null;
      _log('🧹 Caché limpiado antes de actualizar');

      final response = await _api.actualizarDireccion(direccionId, data);
      final direccionData = response['direccion'] as Map<String, dynamic>;
      final direccion = DireccionModel.fromJson(direccionData);

      _log('✅ Dirección actualizada: ${direccion.etiqueta}');
      return direccion;
    } on ApiException catch (e) {
      _log('❌ Error API actualizando dirección: ${e.message}');
      // ✅ Forzar recarga en caso de error
      _direccionesCache = null;
      rethrow;
    } catch (e, stackTrace) {
      _log('❌ Error actualizando dirección', error: e, stackTrace: stackTrace);
      // ✅ Forzar recarga en caso de error
      _direccionesCache = null;

      throw ApiException(
        statusCode: 0,
        message: 'Error al actualizar dirección',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// Elimina una dirección
  /// ✅ CORRECCIÓN: Limpia caché correctamente
  Future<void> eliminarDireccion(String direccionId) async {
    try {
      _log('🗑️ Eliminando dirección $direccionId...');
      await _api.eliminarDireccion(direccionId);

      // ✅ Limpiar cache después de eliminar
      _direccionesCache = null;
      _log('🧹 Caché limpiado después de eliminar');

      _log('✅ Dirección eliminada exitosamente');
    } on ApiException {
      // ✅ También limpiar en error
      _direccionesCache = null;
      rethrow;
    } catch (e, stackTrace) {
      _log('❌ Error eliminando dirección', error: e, stackTrace: stackTrace);
      // ✅ También limpiar en error
      _direccionesCache = null;

      throw ApiException(
        statusCode: 0,
        message: 'Error al eliminar dirección',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// Obtiene la dirección predeterminada
  Future<DireccionModel?> obtenerDireccionPredeterminada() async {
    try {
      _log('📥 Obteniendo dirección predeterminada...');
      final response = await _api.obtenerDireccionPredeterminada();

      final direccionData = response['direccion'] as Map<String, dynamic>;
      final direccion = DireccionModel.fromJson(direccionData);

      _log('✅ Dirección predeterminada obtenida');
      return direccion;
    } on ApiException catch (e) {
      if (e.statusCode == 404) {
        _log('ℹ️ No hay dirección predeterminada');
        return null;
      }
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error obteniendo dirección predeterminada',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al obtener dirección predeterminada',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 💳 MÉTODOS DE PAGO (BÁSICOS - SIN COMPROBANTES)
  // ══════════════════════════════════════════════════════════════════════════

  /// Lista todos los métodos de pago
  Future<List<MetodoPagoModel>> listarMetodosPago({
    bool forzarRecarga = false,
  }) async {
    try {
      if (!forzarRecarga && _metodosPagoCache != null) {
        _log('✅ Retornando métodos de pago desde cache');
        return _metodosPagoCache!;
      }

      _log('📥 Obteniendo métodos de pago...');
      final response = await _api.listarMetodosPago();

      final metodosData = response['metodos_pago'] as List;
      final metodos = metodosData
          .map((json) => MetodoPagoModel.fromJson(json as Map<String, dynamic>))
          .toList();

      _metodosPagoCache = metodos;

      _log('✅ ${metodos.length} métodos de pago obtenidos');
      return metodos;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error listando métodos de pago',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al listar métodos de pago',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// Crea un nuevo método de pago (SIN comprobante - solo efectivo)
  Future<MetodoPagoModel> crearMetodoPago(MetodoPagoModel metodo) async {
    try {
      _log('📤 Creando método de pago...');
      final response = await _api.crearMetodoPago(metodo.toCreateJson());

      final metodoData = response['metodo_pago'] as Map<String, dynamic>;
      final nuevoMetodo = MetodoPagoModel.fromJson(metodoData);

      // Limpiar cache
      _metodosPagoCache = null;

      _log('✅ Método de pago creado: ${nuevoMetodo.alias}');
      return nuevoMetodo;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log('❌ Error creando método de pago', error: e, stackTrace: stackTrace);
      throw ApiException(
        statusCode: 0,
        message: 'Error al crear método de pago',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// Actualiza un método de pago (SIN comprobante)
  Future<MetodoPagoModel> actualizarMetodoPago(
    String metodoId,
    Map<String, dynamic> data,
  ) async {
    try {
      _log('📤 Actualizando método de pago $metodoId...');
      final response = await _api.actualizarMetodoPago(metodoId, data);

      final metodoData = response['metodo_pago'] as Map<String, dynamic>;
      final metodo = MetodoPagoModel.fromJson(metodoData);

      // Limpiar cache
      _metodosPagoCache = null;

      _log('✅ Método de pago actualizado');
      return metodo;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error actualizando método de pago',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al actualizar método de pago',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// Elimina un método de pago
  Future<void> eliminarMetodoPago(String metodoId) async {
    try {
      _log('🗑️ Eliminando método de pago $metodoId...');
      await _api.eliminarMetodoPago(metodoId);

      // Limpiar cache
      _metodosPagoCache = null;

      _log('✅ Método de pago eliminado');
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error eliminando método de pago',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al eliminar método de pago',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// Obtiene el método de pago predeterminado
  Future<MetodoPagoModel?> obtenerMetodoPagoPredeterminado() async {
    try {
      _log('📥 Obteniendo método de pago predeterminado...');
      final response = await _api.obtenerMetodoPagoPredeterminado();

      final metodoData = response['metodo_pago'] as Map<String, dynamic>;
      final metodo = MetodoPagoModel.fromJson(metodoData);

      _log('✅ Método de pago predeterminado obtenido');
      return metodo;
    } on ApiException catch (e) {
      if (e.statusCode == 404) {
        _log('ℹ️ No hay método de pago predeterminado');
        return null;
      }
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error obteniendo método de pago predeterminado',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al obtener método de pago predeterminado',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  Future<MetodoPagoModel> obtenerMetodoPago(String metodoId) async {
    try {
      _log('📥 Obteniendo método de pago $metodoId...');
      final response = await _api.obtenerMetodoPago(metodoId);

      final metodo = MetodoPagoModel.fromJson(response);

      _log('✅ Método de pago obtenido');
      return metodo;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error obteniendo método de pago',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al obtener método de pago',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // ✅ MÉTODOS DE PAGO CON COMPROBANTES
  // ══════════════════════════════════════════════════════════════════════════

  /// Crea un método de pago CON comprobante de imagen
  Future<MetodoPagoModel> crearMetodoPagoConComprobante({
    required String tipo,
    required String alias,
    File? comprobanteImagen,
    String? observaciones,
    bool esPredeterminado = false,
  }) async {
    try {
      _log('📤 Creando método de pago con comprobante...');
      _log('📦 Tipo: $tipo, Alias: $alias');

      // ✅ VALIDAR: Transferencias requieren comprobante
      if (tipo == 'transferencia' && comprobanteImagen == null) {
        _log('❌ Falta comprobante para transferencia');
        throw ApiException(
          statusCode: 400,
          message: 'Las transferencias requieren comprobante',
          errors: {
            'comprobante_pago': 'Debes subir el comprobante de transferencia',
          },
          stackTrace: StackTrace.current,
        );
      }

      // ✅ AGREGAR VALIDACIÓN
      if (alias.trim().isEmpty) {
        throw ApiException(
          statusCode: 400,
          message: 'El alias no puede estar vacío',
          errors: {'alias': 'Campo requerido'},
          stackTrace: StackTrace.current,
        );
      }

      // ✅ VALIDAR: Efectivo NO debe tener comprobante
      if (tipo == 'efectivo' && comprobanteImagen != null) {
        _log('⚠️ Efectivo no requiere comprobante, ignorando imagen');
        comprobanteImagen = null; // Ignorar imagen
      }

      // ✅ VALIDAR: Observaciones no excedan 100 caracteres
      if (observaciones != null && observaciones.length > 100) {
        _log('❌ Observaciones demasiado largas');
        throw ApiException(
          statusCode: 400,
          message: 'Las observaciones no pueden exceder 100 caracteres',
          errors: {'observaciones': 'Máximo 100 caracteres'},
          stackTrace: StackTrace.current,
        );
      }

      // ✅ VALIDAR: Archivo existe y es accesible
      if (comprobanteImagen != null && !await comprobanteImagen.exists()) {
        _log('❌ Archivo de comprobante no existe');
        throw ApiException(
          statusCode: 400,
          message: 'El archivo de comprobante no existe o no es accesible',
          errors: {'comprobante_pago': 'Archivo inválido'},
          stackTrace: StackTrace.current,
        );
      }

      // ✅ Llamar a la API
      final response = await _api.crearMetodoPagoConComprobante(
        tipo: tipo,
        alias: alias,
        comprobanteImagen: comprobanteImagen,
        observaciones: observaciones,
        esPredeterminado: esPredeterminado,
      );

      // ✅ Parsear respuesta
      final metodoData = response['metodo_pago'] as Map<String, dynamic>;
      final nuevoMetodo = MetodoPagoModel.fromJson(metodoData);

      // ✅ Limpiar cache para forzar recarga
      _metodosPagoCache = null;

      _log('✅ Método de pago con comprobante creado: ${nuevoMetodo.alias}');
      _log('📸 Comprobante: ${nuevoMetodo.tieneComprobante ? "Sí" : "No"}');

      return nuevoMetodo;
    } on ApiException {
      _log('❌ Error de API creando método con comprobante');
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error inesperado creando método con comprobante',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al crear método de pago con comprobante',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// Actualiza un método de pago CON nuevo comprobante
  Future<MetodoPagoModel> actualizarMetodoPagoConComprobante({
    required String metodoId,
    String? alias,
    File? comprobanteImagen,
    String? observaciones,
    bool? esPredeterminado,
  }) async {
    try {
      _log('📤 Actualizando método de pago $metodoId con comprobante...');

      // ✅ VALIDAR: Observaciones no excedan 100 caracteres
      if (observaciones != null && observaciones.length > 100) {
        _log('❌ Observaciones demasiado largas');
        throw ApiException(
          statusCode: 400,
          message: 'Las observaciones no pueden exceder 100 caracteres',
          errors: {'observaciones': 'Máximo 100 caracteres'},
          stackTrace: StackTrace.current,
        );
      }
      // ✅ VALIDAR: Archivo existe si se proporciona
      if (comprobanteImagen != null && !await comprobanteImagen.exists()) {
        _log('❌ Nuevo archivo de comprobante no existe');
        throw ApiException(
          statusCode: 400,
          message: 'El archivo de comprobante no existe',
          errors: {'comprobante_pago': 'Archivo inválido'},
          stackTrace: StackTrace.current,
        );
      }

      // ✅ Llamar a la API
      final response = await _api.actualizarMetodoPagoConComprobante(
        metodoId: metodoId,
        alias: alias,
        comprobanteImagen: comprobanteImagen,
        observaciones: observaciones,
        esPredeterminado: esPredeterminado,
      );

      // ✅ Parsear respuesta
      final metodoData = response['metodo_pago'] as Map<String, dynamic>;
      final metodoActualizado = MetodoPagoModel.fromJson(metodoData);

      // ✅ Limpiar cache
      _metodosPagoCache = null;

      _log('✅ Método de pago actualizado: ${metodoActualizado.alias}');
      if (comprobanteImagen != null) {
        _log('📸 Comprobante actualizado');
      }

      return metodoActualizado;
    } on ApiException {
      _log('❌ Error de API actualizando método con comprobante');
      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error inesperado actualizando método con comprobante',
        error: e,
        stackTrace: stackTrace,
      );
      throw ApiException(
        statusCode: 0,
        message: 'Error al actualizar método de pago',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// Valida un archivo de imagen antes de subirlo
  Future<bool> validarComprobanteImagen(File imagen) async {
    try {
      // Validar existencia
      if (!await imagen.exists()) {
        throw ApiException(
          statusCode: 400,
          message: 'El archivo no existe',
          errors: {'imagen': 'Archivo no encontrado'},
          stackTrace: StackTrace.current,
        );
      }

      // Validar tamaño (5 MB máximo)
      final bytes = await imagen.readAsBytes();
      final tamanoMB = bytes.length / (1024 * 1024);

      if (tamanoMB > 5) {
        throw ApiException(
          statusCode: 400,
          message:
              'Archivo demasiado grande: ${tamanoMB.toStringAsFixed(1)} MB',
          errors: {'imagen': 'Tamaño máximo: 5 MB'},
          stackTrace: StackTrace.current,
        );
      }

      // ✅ Validar que la imagen sea decodificable
      final decodedImage = img.decodeImage(bytes);

      if (decodedImage == null) {
        throw ApiException(
          statusCode: 400,
          message: 'El archivo no es una imagen válida o está corrupto',
          errors: {'imagen': 'Archivo corrupto'},
          stackTrace: StackTrace.current,
        );
      }

      // ✅ Validar dimensiones mínimas (opcional)
      if (decodedImage.width < 100 || decodedImage.height < 100) {
        throw ApiException(
          statusCode: 400,
          message: 'La imagen es demasiado pequeña (mín. 100x100 px)',
          errors: {'imagen': 'Tamaño insuficiente'},
          stackTrace: StackTrace.current,
        );
      }

      _log('✅ Imagen válida: ${decodedImage.width}x${decodedImage.height}');
      return true;
    } catch (e) {
      _log('❌ Error validando imagen', error: e);
      rethrow;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // 🧹 UTILIDADES - ✅ MEJORADO CON MÉTODO DE LIMPIEZA ESPECÍFICO
  // ══════════════════════════════════════════════════════════════════════════

  /// Limpia toda la cache
  void limpiarCache() {
    _log('🧹 Limpiando cache completa...');
    _perfilCache = null;
    _direccionesCache = null;
    _metodosPagoCache = null;
    _estadisticasCache = null;
    _log('✅ Cache limpiada');
  }

  /// Limpia solo cache de perfil
  void limpiarCachePerfil() {
    _log('🧹 Limpiando cache de perfil...');
    _perfilCache = null;
    _estadisticasCache = null;
  }

  /// Limpia solo cache de direcciones
  /// ✅ NUEVO: Método público para forzar limpieza desde controlador
  void limpiarCacheDirecciones() {
    _log('🧹 Limpiando cache de direcciones...');
    _direccionesCache = null;
  }

  /// Limpia solo cache de métodos de pago
  void limpiarCacheMetodosPago() {
    _log('🧹 Limpiando cache de métodos de pago...');
    _metodosPagoCache = null;
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📊 GETTERS DE CACHE
  // ══════════════════════════════════════════════════════════════════════════

  PerfilModel? get perfilActual => _perfilCache;
  List<DireccionModel>? get direccionesActuales => _direccionesCache;
  List<MetodoPagoModel>? get metodosPagoActuales => _metodosPagoCache;
  EstadisticasModel? get estadisticasActuales => _estadisticasCache;

  // ══════════════════════════════════════════════════════════════════════════
  // 🔍 UTILIDADES ADICIONALES PARA MÉTODOS DE PAGO
  // ══════════════════════════════════════════════════════════════════════════

  /// Filtra métodos de pago por tipo
  List<MetodoPagoModel> filtrarPorTipo(String tipo) {
    if (_metodosPagoCache == null) return [];
    return _metodosPagoCache!.where((m) => m.tipo == tipo).toList();
  }

  /// Obtiene solo métodos de pago válidos (que se pueden usar)
  List<MetodoPagoModel> obtenerMetodosValidos() {
    if (_metodosPagoCache == null) return [];
    return _metodosPagoCache!.where((m) => m.puedeUsarse).toList();
  }

  /// Obtiene métodos de pago con problemas (tienen observaciones)
  List<MetodoPagoModel> obtenerMetodosConProblemas() {
    if (_metodosPagoCache == null) return [];
    return _metodosPagoCache!.where((m) => m.tieneProblemas).toList();
  }

  /// Obtiene métodos de pago pendientes de verificación
  List<MetodoPagoModel> obtenerMetodosPendientes() {
    if (_metodosPagoCache == null) return [];
    return _metodosPagoCache!
        .where((m) => m.tipo == 'transferencia' && m.requiereVerificacion)
        .toList();
  }

  /// Cuenta cuántos métodos de cada tipo tiene el usuario
  Map<String, int> contarMetodosPorTipo() {
    if (_metodosPagoCache == null) {
      return {'efectivo': 0, 'transferencia': 0, 'tarjeta': 0};
    }

    final contadores = {'efectivo': 0, 'transferencia': 0, 'tarjeta': 0};

    for (final metodo in _metodosPagoCache!) {
      if (contadores.containsKey(metodo.tipo)) {
        contadores[metodo.tipo] = contadores[metodo.tipo]! + 1;
      }
    }

    return contadores;
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📸 FOTO DE PERFIL
  // ══════════════════════════════════════════════════════════════════════════

  /// Sube o actualiza la foto de perfil
  Future<PerfilModel> subirFotoPerfil(File imagen) async {
    try {
      _log('📤 Subiendo foto de perfil...');

      final response = await _api.subirFotoPerfil(imagen);

      final perfilData = response['perfil'] as Map<String, dynamic>;
      final perfil = PerfilModel.fromJson(perfilData);

      // Actualizar cache
      _perfilCache = perfil;

      _log('✅ Foto de perfil actualizada');
      return perfil;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log('❌ Error subiendo foto', error: e, stackTrace: stackTrace);
      throw ApiException(
        statusCode: 0,
        message: 'Error al subir foto de perfil',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// Elimina la foto de perfil
  Future<PerfilModel> eliminarFotoPerfil() async {
    try {
      _log('🗑️ Eliminando foto de perfil...');

      final response = await _api.eliminarFotoPerfil();

      final perfilData = response['perfil'] as Map<String, dynamic>;
      final perfil = PerfilModel.fromJson(perfilData);

      // Actualizar cache
      _perfilCache = perfil;

      _log('✅ Foto eliminada');
      return perfil;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log('❌ Error eliminando foto', error: e, stackTrace: stackTrace);
      throw ApiException(
        statusCode: 0,
        message: 'Error al eliminar foto',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  /// Verifica si el usuario tiene al menos un método de pago válido
  bool tieneMetodoValido() {
    return obtenerMetodosValidos().isNotEmpty;
  }

  /// Verifica si el usuario tiene métodos pendientes de verificación
  bool tienePendientesVerificacion() {
    return obtenerMetodosPendientes().isNotEmpty;
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📈 ESTADÍSTICAS DE MÉTODOS DE PAGO
  // ══════════════════════════════════════════════════════════════════════════

  /// Obtiene un resumen estadístico de los métodos de pago
  Map<String, dynamic> obtenerEstadisticasMetodosPago() {
    if (_metodosPagoCache == null) {
      return {
        'total': 0,
        'activos': 0,
        'con_comprobante': 0,
        'pendientes': 0,
        'con_problemas': 0,
        'por_tipo': contarMetodosPorTipo(),
      };
    }

    return {
      'total': _metodosPagoCache!.length,
      'activos': _metodosPagoCache!.where((m) => m.activo).length,
      'con_comprobante': _metodosPagoCache!
          .where((m) => m.tieneComprobante)
          .length,
      'pendientes': obtenerMetodosPendientes().length,
      'con_problemas': obtenerMetodosConProblemas().length,
      'por_tipo': contarMetodosPorTipo(),
      'validos': obtenerMetodosValidos().length,
    };
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🔧 HELPERS PARA DEBUGGING
  // ══════════════════════════════════════════════════════════════════════════

  /// Imprime información de debug sobre el estado actual del servicio
  void imprimirEstadoDebug() {
    _log('═══════════════════════════════════════════════════════════════');
    _log('📊 ESTADO DEL SERVICIO DE USUARIO');
    _log('═══════════════════════════════════════════════════════════════');

    // Perfil
    _log('👤 Perfil: ${_perfilCache != null ? "✅ Cacheado" : "❌ Sin cache"}');
    if (_perfilCache != null) {
      _log('   Email: ${_perfilCache!.usuarioEmail}');
      _log('   Nombre: ${_perfilCache!.usuarioNombre}');
    }

    // Estadísticas
    _log(
      '📈 Estadísticas: ${_estadisticasCache != null ? "✅ Cacheadas" : "❌ Sin cache"}',
    );
    if (_estadisticasCache != null) {
      _log('   Pedidos: ${_estadisticasCache!.totalPedidos}');
      _log('   Calificación: ${_estadisticasCache!.calificacion}/5.0');
    }

    // Direcciones
    _log(
      '📍 Direcciones: ${_direccionesCache != null ? "✅ Cacheadas (${_direccionesCache!.length})" : "❌ Sin cache"}',
    );
    if (_direccionesCache != null && _direccionesCache!.isNotEmpty) {
      for (var dir in _direccionesCache!) {
        _log('   - ${dir.etiqueta}: ${dir.direccion}');
      }
    }

    // Métodos de pago
    _log(
      '💳 Métodos de pago: ${_metodosPagoCache != null ? "✅ Cacheados (${_metodosPagoCache!.length})" : "❌ Sin cache"}',
    );
    if (_metodosPagoCache != null && _metodosPagoCache!.isNotEmpty) {
      final stats = obtenerEstadisticasMetodosPago();
      _log('   Total: ${stats['total']}');
      _log('   Activos: ${stats['activos']}');
      _log('   Con comprobante: ${stats['con_comprobante']}');
      _log('   Pendientes: ${stats['pendientes']}');
      _log('   Válidos: ${stats['validos']}');

      final porTipo = stats['por_tipo'] as Map<String, int>;
      _log('   Por tipo:');
      porTipo.forEach((tipo, cantidad) {
        _log('     - $tipo: $cantidad');
      });
    }

    _log('═══════════════════════════════════════════════════════════════');
  }
}
