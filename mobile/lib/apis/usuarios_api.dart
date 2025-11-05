// lib/apis/usuarios_api.dart

import 'dart:io';
import 'dart:developer' as developer;
import 'subapis/http_client.dart';
import '../config/api_config.dart';
import 'helpers/api_exception.dart';

/// API de Usuarios - SOLO peticiones HTTP
/// NO contiene lógica de negocio, NO maneja modelos
/// ✅ CON SOPORTE PARA SUBIR IMÁGENES DE COMPROBANTES (REFACTORIZADO)
class UsuariosApi {
  // ══════════════════════════════════════════════════════════════════════════
  // SINGLETON
  // ══════════════════════════════════════════════════════════════════════════

  static final UsuariosApi _instance = UsuariosApi._internal();
  factory UsuariosApi() => _instance;
  UsuariosApi._internal();

  // ══════════════════════════════════════════════════════════════════════════
  // CLIENTE HTTP
  // ══════════════════════════════════════════════════════════════════════════

  final _client = ApiClient();

  // ══════════════════════════════════════════════════════════════════════════
  // LOGGING
  // ══════════════════════════════════════════════════════════════════════════

  void _log(String message, {Object? error, StackTrace? stackTrace}) {
    developer.log(
      message,
      name: 'UsuariosApi',
      error: error,
      stackTrace: stackTrace,
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // ENDPOINTS
  // ══════════════════════════════════════════════════════════════════════════

  // ──────────────────────────────────────────────────────────────────────────
  // Perfil
  // ──────────────────────────────────────────────────────────────────────────

  static String get _perfil => ApiConfig.usuariosPerfil;
  static String get _actualizarPerfil => ApiConfig.usuariosActualizarPerfil;
  static String get _estadisticas => ApiConfig.usuariosEstadisticas;
  static String _perfilPublico(int userId) =>
      ApiConfig.usuariosPerfilPublico(userId);

  // ──────────────────────────────────────────────────────────────────────────
  // ✅ Notificaciones FCM
  // ──────────────────────────────────────────────────────────────────────────

  static String get _fcmToken => ApiConfig.usuariosFCMToken;
  static String get _eliminarFcmToken => ApiConfig.usuariosEliminarFCMToken;
  static String get _estadoNotificaciones =>
      ApiConfig.usuariosEstadoNotificaciones;

  // ──────────────────────────────────────────────────────────────────────────
  // Direcciones
  // ──────────────────────────────────────────────────────────────────────────

  static String get _direcciones => ApiConfig.usuariosDirecciones;
  static String _direccion(String id) => ApiConfig.usuariosDireccion(id);
  static String get _direccionPredeterminada =>
      ApiConfig.usuariosDireccionPredeterminada;

  // ──────────────────────────────────────────────────────────────────────────
  // Métodos de pago
  // ──────────────────────────────────────────────────────────────────────────

  static String get _metodosPago => ApiConfig.usuariosMetodosPago;
  static String _metodoPago(String id) => ApiConfig.usuariosMetodoPago(id);
  static String get _metodoPagoPredeterminado =>
      ApiConfig.usuariosMetodoPagoPredeterminado;

  // ══════════════════════════════════════════════════════════════════════════
  // 👤 PERFIL - PETICIONES HTTP
  // ══════════════════════════════════════════════════════════════════════════

  /// GET /api/usuarios/perfil/
  /// Obtiene el perfil del usuario autenticado
  Future<Map<String, dynamic>> obtenerPerfil() async {
    _log('📥 GET: Obtener perfil');
    try {
      final response = await _client.get(_perfil);
      _log('✅ Perfil obtenido');
      return response;
    } catch (e, stackTrace) {
      _log('❌ Error obteniendo perfil', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// GET /api/usuarios/perfil/publico/{userId}/
  /// Obtiene el perfil público de otro usuario
  Future<Map<String, dynamic>> obtenerPerfilPublico(int userId) async {
    _log('📥 GET: Obtener perfil público de usuario $userId');
    try {
      final response = await _client.get(_perfilPublico(userId));
      _log('✅ Perfil público obtenido');
      return response;
    } catch (e, stackTrace) {
      _log(
        '❌ Error obteniendo perfil público',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// PATCH /api/usuarios/perfil/actualizar/
  /// Actualiza el perfil del usuario
  Future<Map<String, dynamic>> actualizarPerfil(
    Map<String, dynamic> data,
  ) async {
    _log('📤 PATCH: Actualizar perfil');
    _log('📦 Datos: ${data.keys.join(", ")}');
    try {
      final response = await _client.patch(_actualizarPerfil, data);
      _log('✅ Perfil actualizado');
      return response;
    } catch (e, stackTrace) {
      _log('❌ Error actualizando perfil', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// GET /api/usuarios/perfil/estadisticas/
  /// Obtiene las estadísticas del usuario
  Future<Map<String, dynamic>> obtenerEstadisticas() async {
    _log('📥 GET: Obtener estadísticas');
    try {
      final response = await _client.get(_estadisticas);
      _log('✅ Estadísticas obtenidas');
      return response;
    } catch (e, stackTrace) {
      _log('❌ Error obteniendo estadísticas', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🔔 NOTIFICACIONES FCM - PETICIONES HTTP
  // ══════════════════════════════════════════════════════════════════════════

  /// POST /api/usuarios/fcm-token/
  /// Registra o actualiza el token FCM del dispositivo
  Future<Map<String, dynamic>> registrarFCMToken(String token) async {
    _log('📤 POST: Registrar token FCM');
    _log('🔑 Token: ${token.substring(0, 20)}...');
    try {
      final response = await _client.post(_fcmToken, {'fcm_token': token});
      _log('✅ Token FCM registrado');
      return response;
    } catch (e, stackTrace) {
      _log('❌ Error registrando token FCM', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// DELETE /api/usuarios/fcm-token/eliminar/
  /// Elimina el token FCM del dispositivo (para cerrar sesión)
  Future<Map<String, dynamic>> eliminarFCMToken() async {
    _log('🗑️ DELETE: Eliminar token FCM');
    try {
      final response = await _client.delete(_eliminarFcmToken);
      _log('✅ Token FCM eliminado');
      return response;
    } catch (e, stackTrace) {
      _log('❌ Error eliminando token FCM', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// GET /api/usuarios/notificaciones/
  /// Obtiene el estado de las notificaciones del usuario
  Future<Map<String, dynamic>> obtenerEstadoNotificaciones() async {
    _log('📥 GET: Estado de notificaciones');
    try {
      final response = await _client.get(_estadoNotificaciones);
      _log('✅ Estado de notificaciones obtenido');
      return response;
    } catch (e, stackTrace) {
      _log(
        '❌ Error obteniendo estado de notificaciones',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📍 DIRECCIONES FAVORITAS - PETICIONES HTTP
  // ══════════════════════════════════════════════════════════════════════════

  /// GET /api/usuarios/direcciones/
  /// Lista todas las direcciones favoritas del usuario
  Future<Map<String, dynamic>> listarDirecciones() async {
    _log('📥 GET: Listar direcciones');
    try {
      final response = await _client.get(_direcciones);
      _log('✅ Direcciones listadas: ${response['total'] ?? 0}');
      return response;
    } catch (e, stackTrace) {
      _log('❌ Error listando direcciones', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  // =====================================================
  // 📡 API: Obtener direcciones del usuario autenticado
  // =====================================================
  Future<dynamic> getDirecciones() async {
    return await ApiClient().get(ApiConfig.usuariosDirecciones);
  }

  /// POST /api/usuarios/direcciones/
  Future<Map<String, dynamic>> crearDireccion(Map<String, dynamic> data) async {
    _log('📤 POST: Crear dirección');
    _log('📦 Etiqueta: ${data['etiqueta']}');
    try {
      final response = await _client.post(_direcciones, data);
      _log('✅ Dirección creada');
      return response;
    } on ApiException catch (e, stackTrace) {
      _log('❌ Error creando dirección', error: e, stackTrace: stackTrace);

      // Detectar error específico de etiqueta duplicada
      final errores = e.errors;
      if (errores.containsKey('etiqueta')) {
        final msg = errores['etiqueta'].toString();
        if (msg.contains('Ya tienes una dirección')) {
          _log('⚠️ Dirección duplicada detectada');
          return {'duplicado': true, 'mensaje': msg, 'data': data};
        }
      }

      rethrow;
    } catch (e, stackTrace) {
      _log(
        '💥 Error inesperado creando dirección',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// GET /api/usuarios/direcciones/{id}/
  /// Obtiene una dirección específica
  Future<Map<String, dynamic>> obtenerDireccion(String direccionId) async {
    _log('📥 GET: Obtener dirección $direccionId');
    try {
      final response = await _client.get(_direccion(direccionId));
      _log('✅ Dirección obtenida');
      return response;
    } catch (e, stackTrace) {
      _log('❌ Error obteniendo dirección', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// PATCH /api/usuarios/direcciones/{id}/
  /// Actualiza una dirección existente
  Future<Map<String, dynamic>> actualizarDireccion(
    String direccionId,
    Map<String, dynamic> data,
  ) async {
    _log('📤 PATCH: Actualizar dirección $direccionId');
    _log('📦 Datos: ${data.keys.join(", ")}');
    try {
      final response = await _client.patch(_direccion(direccionId), data);
      _log('✅ Dirección actualizada');
      return response;
    } catch (e, stackTrace) {
      _log('❌ Error actualizando dirección', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// DELETE /api/usuarios/direcciones/{id}/
  /// Elimina (desactiva) una dirección
  Future<Map<String, dynamic>> eliminarDireccion(String direccionId) async {
    _log('🗑️ DELETE: Eliminar dirección $direccionId');
    try {
      final response = await _client.delete(_direccion(direccionId));
      _log('✅ Dirección eliminada');
      return response;
    } catch (e, stackTrace) {
      _log('❌ Error eliminando dirección', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// GET /api/usuarios/direcciones/predeterminada/
  /// Obtiene la dirección predeterminada del usuario
  Future<Map<String, dynamic>> obtenerDireccionPredeterminada() async {
    _log('📥 GET: Obtener dirección predeterminada');
    try {
      final response = await _client.get(_direccionPredeterminada);
      _log('✅ Dirección predeterminada obtenida');
      return response;
    } catch (e, stackTrace) {
      _log(
        '❌ Error obteniendo dirección predeterminada',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 💳 MÉTODOS DE PAGO - PETICIONES HTTP (BÁSICAS SIN IMÁGENES)
  // ══════════════════════════════════════════════════════════════════════════

  /// GET /api/usuarios/metodos-pago/
  /// Lista todos los métodos de pago del usuario
  Future<Map<String, dynamic>> listarMetodosPago() async {
    _log('📥 GET: Listar métodos de pago');
    try {
      final response = await _client.get(_metodosPago);
      _log('✅ Métodos de pago listados: ${response['total'] ?? 0}');
      return response;
    } catch (e, stackTrace) {
      _log(
        '❌ Error listando métodos de pago',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// POST /api/usuarios/metodos-pago/
  /// Crea un nuevo método de pago (SIN imagen - solo efectivo)
  Future<Map<String, dynamic>> crearMetodoPago(
    Map<String, dynamic> data,
  ) async {
    _log('📤 POST: Crear método de pago');
    _log('📦 Alias: ${data['alias']}');
    try {
      final response = await _client.post(_metodosPago, data);
      _log('✅ Método de pago creado');
      return response;
    } catch (e, stackTrace) {
      _log('❌ Error creando método de pago', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// GET /api/usuarios/metodos-pago/{id}/
  /// Obtiene un método de pago específico
  Future<Map<String, dynamic>> obtenerMetodoPago(String metodoId) async {
    _log('📥 GET: Obtener método de pago $metodoId');
    try {
      final response = await _client.get(_metodoPago(metodoId));
      _log('✅ Método de pago obtenido');
      return response;
    } catch (e, stackTrace) {
      _log(
        '❌ Error obteniendo método de pago',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// PATCH /api/usuarios/metodos-pago/{id}/
  /// Actualiza un método de pago existente (SIN imagen)
  Future<Map<String, dynamic>> actualizarMetodoPago(
    String metodoId,
    Map<String, dynamic> data,
  ) async {
    _log('📤 PATCH: Actualizar método de pago $metodoId');
    _log('📦 Datos: ${data.keys.join(", ")}');
    try {
      final response = await _client.patch(_metodoPago(metodoId), data);
      _log('✅ Método de pago actualizado');
      return response;
    } catch (e, stackTrace) {
      _log(
        '❌ Error actualizando método de pago',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// DELETE /api/usuarios/metodos-pago/{id}/
  /// Elimina (desactiva) un método de pago
  Future<Map<String, dynamic>> eliminarMetodoPago(String metodoId) async {
    _log('🗑️ DELETE: Eliminar método de pago $metodoId');
    try {
      final response = await _client.delete(_metodoPago(metodoId));
      _log('✅ Método de pago eliminado');
      return response;
    } catch (e, stackTrace) {
      _log(
        '❌ Error eliminando método de pago',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// GET /api/usuarios/metodos-pago/predeterminado/
  /// Obtiene el método de pago predeterminado del usuario
  Future<Map<String, dynamic>> obtenerMetodoPagoPredeterminado() async {
    _log('📥 GET: Obtener método de pago predeterminado');
    try {
      final response = await _client.get(_metodoPagoPredeterminado);
      _log('✅ Método de pago predeterminado obtenido');
      return response;
    } catch (e, stackTrace) {
      _log(
        '❌ Error obteniendo método de pago predeterminado',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // ✅ MÉTODOS DE PAGO CON COMPROBANTES (REFACTORIZADO - USA ApiClient.multipart)
  // ══════════════════════════════════════════════════════════════════════════

  /// POST /api/usuarios/metodos-pago/ (CON COMPROBANTE DE IMAGEN)
  /// Crea un nuevo método de pago con comprobante de transferencia
  ///
  /// ✅ REFACTORIZADO: Ahora usa ApiClient.multipart()
  ///
  /// Parámetros:
  /// - [tipo]: 'efectivo' o 'transferencia'
  /// - [alias]: Nombre del método (ej: "Transferencia Pichincha")
  /// - [comprobanteImagen]: Archivo de imagen (obligatorio para transferencias)
  /// - [observaciones]: Notas opcionales (máx. 100 caracteres)
  /// - [esPredeterminado]: Si es el método predeterminado
  Future<Map<String, dynamic>> crearMetodoPagoConComprobante({
    required String tipo,
    required String alias,
    File? comprobanteImagen,
    String? observaciones,
    bool esPredeterminado = false,
  }) async {
    _log('📤 POST: Crear método de pago con comprobante (REFACTORIZADO)');
    _log('📦 Tipo: $tipo, Alias: $alias');

    try {
      // ✅ Preparar campos de texto
      final fields = <String, String>{
        'tipo': tipo,
        'alias': alias,
        'es_predeterminado': esPredeterminado.toString(),
      };

      // ✅ Agregar observaciones si existen
      if (observaciones != null && observaciones.isNotEmpty) {
        fields['observaciones'] = observaciones;
      }

      // ✅ Preparar archivos
      final files = <String, File>{};
      if (comprobanteImagen != null) {
        _log('📸 Adjuntando comprobante: ${comprobanteImagen.path}');
        files['comprobante_pago'] = comprobanteImagen;
      } else {
        _log('ℹ️ Sin comprobante (pago en efectivo)');
      }

      // ✅ Llamar al método multipart centralizado
      final response = await _client.multipart(
        'POST',
        _metodosPago,
        fields,
        files,
      );

      _log('✅ Método de pago con comprobante creado');
      return response;
    } catch (e, stackTrace) {
      _log(
        '❌ Error creando método de pago con comprobante',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// PATCH /api/usuarios/metodos-pago/{id}/ (CON COMPROBANTE)
  /// Actualiza un método de pago con nuevo comprobante
  ///
  /// ✅ REFACTORIZADO: Ahora usa ApiClient.multipart()
  ///
  /// Parámetros:
  /// - [metodoId]: ID del método de pago a actualizar
  /// - [tipo]: Nuevo tipo (opcional)
  /// - [alias]: Nuevo alias (opcional)
  /// - [comprobanteImagen]: Nueva imagen del comprobante (opcional)
  /// - [observaciones]: Nuevas observaciones (opcional)
  /// - [esPredeterminado]: Nuevo estado predeterminado (opcional)
  Future<Map<String, dynamic>> actualizarMetodoPagoConComprobante({
    required String metodoId,
    String? tipo,
    String? alias,
    File? comprobanteImagen,
    String? observaciones,
    bool? esPredeterminado,
  }) async {
    _log('📤 PATCH: Actualizar método de pago $metodoId (REFACTORIZADO)');

    try {
      // ✅ Preparar solo los campos que cambian
      final fields = <String, String>{};

      if (tipo != null) fields['tipo'] = tipo;
      if (alias != null) fields['alias'] = alias;
      if (observaciones != null) fields['observaciones'] = observaciones;
      if (esPredeterminado != null) {
        fields['es_predeterminado'] = esPredeterminado.toString();
      }

      // ✅ Preparar archivos
      final files = <String, File>{};
      if (comprobanteImagen != null) {
        _log('📸 Actualizando comprobante: ${comprobanteImagen.path}');
        files['comprobante_pago'] = comprobanteImagen;
      }

      // ✅ Llamar al método multipart centralizado
      final response = await _client.multipart(
        'PATCH',
        _metodoPago(metodoId),
        fields,
        files,
      );

      _log('✅ Método de pago actualizado');
      return response;
    } catch (e, stackTrace) {
      _log(
        '❌ Error actualizando método de pago',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  Future<Map<String, dynamic>> actualizarUbicacion(
    double lat,
    double lon,
  ) async {
    final data = {'latitud': lat.toString(), 'longitud': lon.toString()};
    return await _client.post(ApiConfig.usuariosUbicacionActualizar, data);
  }

  Future<Map<String, dynamic>> obtenerMiUbicacion() async {
    return await _client.get(ApiConfig.usuariosUbicacionMia);
  }

  /// POST /api/usuarios/perfil/foto/
  /// Sube o actualiza la foto de perfil
  Future<Map<String, dynamic>> subirFotoPerfil(File imagen) async {
    _log('📤 POST: Subir foto de perfil');
    _log('📸 Archivo: ${imagen.path}');
    try {
      final fields = <String, String>{}; // Sin campos adicionales
      final files = <String, File>{'foto_perfil': imagen};
      final response = await _client.multipart(
        'POST',
        ApiConfig.usuariosFotoPerfil,
        fields,
        files,
      );
      _log('✅ Foto de perfil subida');
      return response;
    } catch (e, stackTrace) {
      _log('❌ Error subiendo foto de perfil', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// DELETE /api/usuarios/perfil/foto/
  /// Elimina la foto de perfil
  Future<Map<String, dynamic>> eliminarFotoPerfil() async {
    _log('🗑️ DELETE: Eliminar foto de perfil');
    try {
      final response = await _client.delete(ApiConfig.usuariosFotoPerfil);
      _log('✅ Foto de perfil eliminada');
      return response;
    } catch (e, stackTrace) {
      _log('❌ Error eliminando foto', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// ══════════════════════════════════════════════════════════════════════════
  /// 🔧 UTILIDADES PÚBLICAS
  /// ══════════════════════════════════════════════════════════════════════════

  /// Verifica si hay conexión disponible
  bool get tieneConexion => _client.isAuthenticated;

  /// Limpia caché o datos temporales si es necesario
  Future<void> limpiarCache() async {
    _log('🧹 Limpiando caché de usuarios...');
    // Aquí podrías implementar limpieza de caché si usas alguno
    _log('✅ Caché limpiada');
  }
}
