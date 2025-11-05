import 'dart:convert';
import 'dart:io';
import 'dart:async';
import 'dart:math';
import 'dart:developer' as developer;
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../config/api_config.dart';
import '../helpers/api_exception.dart';

/// Cliente HTTP puro - CON SOPORTE MULTIPART
/// ✅ VERSIÓN CORREGIDA: Sin reintentos automáticos en multipart
/// ✅ CON PERSISTENCIA DE ROL DE USUARIO
class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;
  ApiClient._internal();
  static const _secureStorage = FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
      resetOnError: true,
    ),
    iOptions: IOSOptions(
      accessibility: KeychainAccessibility.first_unlock,
      synchronizable: false,
    ),
  );
  // ══════════════════════════════════════════════════════════════════════════
  // ✅ VARIABLES DE INSTANCIA (CON ROL Y USER ID)
  // ══════════════════════════════════════════════════════════════════════════
  String? _accessToken;
  String? _refreshToken;
  String? _userRole; // ✅ NUEVO: Rol del usuario
  int? _userId; // ✅ NUEVO: ID del usuario
  bool _isRefreshing = false;
  Completer<bool>? _refreshCompleter;
  // ══════════════════════════════════════════════════════════════════════════
  // ✅ CONSTANTES PARA SECURE STORAGE (CON LLAVES NUEVAS)
  // ══════════════════════════════════════════════════════════════════════════
  static const String _keyAccessToken = 'jp_access_token';
  static const String _keyRefreshToken = 'jp_refresh_token';
  static const String _keyTokenTimestamp = 'jp_token_timestamp';
  static const String _keyUserRole = 'jp_user_role'; // ✅ NUEVO
  static const String _keyUserId = 'jp_user_id'; // ✅ NUEVO
  // ══════════════════════════════════════════════════════════════════════════
  // ✅ GETTERS PÚBLICOS (CON ROL Y USER ID)
  // ══════════════════════════════════════════════════════════════════════════
  bool get isAuthenticated => _accessToken != null;
  String? get accessToken => _accessToken;
  String? get refreshToken => _refreshToken;
  String? get userRole => _userRole; // ✅ NUEVO
  int? get userId => _userId; // ✅ NUEVO
  void _log(String message, {Object? error, StackTrace? stackTrace}) {
    developer.log(
      message,
      name: 'ApiClient',
      error: error,
      stackTrace: stackTrace,
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // ✅ TOKEN MANAGEMENT (MODIFICADO PARA INCLUIR ROL)
  // ══════════════════════════════════════════════════════════════════════════
  /// ✅ MODIFICADO: Ahora acepta rol y userId como parámetros opcionales
  Future<void> saveTokens(
    String access,
    String refresh, {
    String? role, // ✅ NUEVO: Parámetro opcional para el rol
    int? userId, // ✅ NUEVO: Parámetro opcional para el ID
  }) async {
    try {
      _accessToken = access;
      _refreshToken = refresh;
      _userRole = role; // ✅ NUEVO
      _userId = userId; // ✅ NUEVO
      await _secureStorage.write(key: _keyAccessToken, value: access);
      await _secureStorage.write(key: _keyRefreshToken, value: refresh);
      await _secureStorage.write(
        key: _keyTokenTimestamp,
        value: DateTime.now().toIso8601String(),
      );

      // ✅ NUEVO: Guardar rol si existe
      if (role != null) {
        await _secureStorage.write(key: _keyUserRole, value: role);
        _log('✅ Rol guardado: $role');
      }

      // ✅ NUEVO: Guardar userId si existe
      if (userId != null) {
        await _secureStorage.write(key: _keyUserId, value: userId.toString());
        _log('✅ User ID guardado: $userId');
      }

      _log('✅ Tokens guardados');
    } catch (e, stackTrace) {
      _log('❌ Error guardando tokens', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// ✅ MODIFICADO: Ahora carga también el rol y userId
  Future<void> loadTokens() async {
    try {
      _accessToken = await _secureStorage.read(key: _keyAccessToken);
      _refreshToken = await _secureStorage.read(key: _keyRefreshToken);
      _userRole = await _secureStorage.read(key: _keyUserRole); // ✅ NUEVO
      // ✅ NUEVO: Cargar userId
      final userIdStr = await _secureStorage.read(key: _keyUserId);
      if (userIdStr != null) {
        _userId = int.tryParse(userIdStr);
      }

      if (_accessToken != null) {
        final timestamp = await _secureStorage.read(key: _keyTokenTimestamp);
        _log('✅ Tokens cargados (guardados: $timestamp)');
        _log('🔑 Token presente: ${_accessToken!.substring(0, 20)}...');

        // ✅ NUEVO: Log del rol y userId cargados
        if (_userRole != null) {
          _log('👤 Rol cargado: $_userRole');
        }
        if (_userId != null) {
          _log('🆔 User ID cargado: $_userId');
        }
      } else {
        _log('ℹ️ No hay tokens guardados');
      }
    } catch (e, stackTrace) {
      _log('❌ Error cargando tokens', error: e, stackTrace: stackTrace);
      await clearTokens();
    }
  }

  /// ✅ MODIFICADO: Ahora limpia también el rol y userId
  Future<void> clearTokens() async {
    try {
      _accessToken = null;
      _refreshToken = null;
      _userRole = null; // ✅ NUEVO
      _userId = null; // ✅ NUEVO
      _isRefreshing = false;
      _refreshCompleter = null;
      await _secureStorage.delete(key: _keyAccessToken);
      await _secureStorage.delete(key: _keyRefreshToken);
      await _secureStorage.delete(key: _keyTokenTimestamp);
      await _secureStorage.delete(key: _keyUserRole); // ✅ NUEVO
      await _secureStorage.delete(key: _keyUserId); // ✅ NUEVO

      _log('🗑️ Tokens y datos de usuario eliminados');
    } catch (e, stackTrace) {
      _log('⚠️ Error eliminando tokens', error: e, stackTrace: stackTrace);
    }
  }

  Future<bool> hasStoredTokens() async {
    try {
      final access = await _secureStorage.read(key: _keyAccessToken);
      return access != null;
    } catch (e) {
      return false;
    }
  }

  Future<bool> refreshAccessToken() async {
    if (_refreshToken == null) return false;
    if (_isRefreshing) return await _refreshCompleter!.future;
    _isRefreshing = true;
    _refreshCompleter = Completer<bool>();

    try {
      _log('🔄 Refrescando token...');
      final response = await http
          .post(
            Uri.parse(ApiConfig.tokenRefresh),
            headers: {
              'Content-Type': 'application/json',
              'X-API-Key': ApiConfig.apiKeyMobile,
            },
            body: json.encode({'refresh': _refreshToken}),
          )
          .timeout(ApiConfig.connectTimeout);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);

        // ✅ MODIFICADO: Mantener rol y userId al refrescar token
        await saveTokens(
          data['access'],
          _refreshToken!,
          role: _userRole, // ✅ Mantener rol existente
          userId: _userId, // ✅ Mantener userId existente
        );

        _log('✅ Token refrescado');
        _refreshCompleter!.complete(true);
        return true;
      }

      if (response.statusCode == 401) await clearTokens();
      _refreshCompleter!.complete(false);
      return false;
    } catch (e, stackTrace) {
      _log('❌ Excepción al refrescar', error: e, stackTrace: stackTrace);
      _refreshCompleter!.complete(false);
      return false;
    } finally {
      _isRefreshing = false;
      _refreshCompleter = null;
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // REQUEST WITH RETRY
  // ══════════════════════════════════════════════════════════════════════════
  Future<http.Response> _requestWithRetry(
    Future<http.Response> Function() request, {
    int maxRetries = 3,
    int retryCount = 0,
  }) async {
    try {
      final response = await request().timeout(ApiConfig.receiveTimeout);
      if (response.statusCode == 401 && retryCount == 0) {
        _log('⚠️ Token expirado, refrescando...');
        final refreshed = await refreshAccessToken();
        if (refreshed) {
          _log('🔄 Reintentando con nuevo token');
          return await _requestWithRetry(
            request,
            maxRetries: maxRetries,
            retryCount: 1,
          );
        }
        throw ApiException(
          statusCode: 401,
          message: ApiConfig.errorUnauthorized,
          errors: {'detail': 'Sesión expirada'},
          stackTrace: StackTrace.current,
        );
      }
      return response;
    } on TimeoutException catch (e, stackTrace) {
      if (retryCount < maxRetries) {
        final delaySeconds = pow(2, retryCount).toInt();
        _log(
          '⏱️ Timeout, reintentando en ${delaySeconds}s (${retryCount + 1}/$maxRetries)',
        );
        await Future.delayed(Duration(seconds: delaySeconds));
        return await _requestWithRetry(
          request,
          maxRetries: maxRetries,
          retryCount: retryCount + 1,
        );
      }
      throw ApiException(
        statusCode: 0,
        message: ApiConfig.errorTimeout,
        errors: {'error': 'Timeout después de $maxRetries intentos'},
        stackTrace: stackTrace,
      );
    } on SocketException catch (e, stackTrace) {
      if (retryCount < maxRetries) {
        final delaySeconds = pow(2, retryCount).toInt();
        _log(
          '🌐 Sin conexión, reintentando en ${delaySeconds}s (${retryCount + 1}/$maxRetries)',
        );
        await Future.delayed(Duration(seconds: delaySeconds));
        return await _requestWithRetry(
          request,
          maxRetries: maxRetries,
          retryCount: retryCount + 1,
        );
      }
      throw ApiException(
        statusCode: 0,
        message: ApiConfig.errorNetwork,
        errors: {'error': 'Sin conexión después de $maxRetries intentos'},
        stackTrace: stackTrace,
      );
    } catch (e, stackTrace) {
      if (e is ApiException) rethrow;
      throw ApiException(
        statusCode: 0,
        message: ApiConfig.errorUnknown,
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // ✅ HEADERS (MÉTODO HELPER MEJORADO)
  // ══════════════════════════════════════════════════════════════════════════
  Map<String, String> _getHeaders() {
    _log(
      '🔑 Token actual: ${_accessToken != null ? "PRESENTE (${_accessToken!.substring(0, 20)}...)" : "AUSENTE"}',
    );

    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-API-Key': ApiConfig.apiKeyMobile,
      if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
    };
  }

  /// ✅ Headers específicos para multipart (sin Content-Type)
  Map<String, String> _getMultipartHeaders() {
    return {
      'Accept': 'application/json',
      'X-API-Key': ApiConfig.apiKeyMobile,
      if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
    };
  }

  // ══════════════════════════════════════════════════════════════════════════
  // HTTP METHODS
  // ══════════════════════════════════════════════════════════════════════════
  Future<Map<String, dynamic>> get(String endpoint) async {
    await loadTokens();
    _log('📥 GET: $endpoint');
    final response = await _requestWithRetry(
      () => http.get(Uri.parse(endpoint), headers: _getHeaders()),
    );
    return _handleResponse(response);
  }

  Future<Map<String, dynamic>> post(
    String endpoint,
    Map<String, dynamic> body,
  ) async {
    await loadTokens();
    _log('📤 POST: $endpoint');
    final response = await _requestWithRetry(
      () => http.post(
        Uri.parse(endpoint),
        headers: _getHeaders(),
        body: json.encode(body),
      ),
    );
    return _handleResponse(response);
  }

  Future<Map<String, dynamic>> put(
    String endpoint,
    Map<String, dynamic> body,
  ) async {
    await loadTokens();
    _log('📤 PUT: $endpoint');
    final response = await _requestWithRetry(
      () => http.put(
        Uri.parse(endpoint),
        headers: _getHeaders(),
        body: json.encode(body),
      ),
    );
    return _handleResponse(response);
  }

  Future<Map<String, dynamic>> patch(
    String endpoint,
    Map<String, dynamic> body,
  ) async {
    await loadTokens();
    _log('📤 PATCH: $endpoint');
    final response = await _requestWithRetry(
      () => http.patch(
        Uri.parse(endpoint),
        headers: _getHeaders(),
        body: json.encode(body),
      ),
    );
    return _handleResponse(response);
  }

  Future<Map<String, dynamic>> delete(String endpoint) async {
    await loadTokens();
    _log('🗑️ DELETE: $endpoint');
    final response = await _requestWithRetry(
      () => http.delete(Uri.parse(endpoint), headers: _getHeaders()),
    );
    return _handleResponse(response);
  }

  // ══════════════════════════════════════════════════════════════════════════
  // ✅ MÉTODO MULTIPART (SIN REINTENTOS AUTOMÁTICOS)
  // ══════════════════════════════════════════════════════════════════════════
  Future<Map<String, dynamic>> multipart(
    String method,
    String endpoint,
    Map<String, String> fields,
    Map<String, File> files,
  ) async {
    await loadTokens();
    _log('📤 $method (multipart - SIN reintentos): $endpoint');
    _log('📦 Fields: ${fields.keys.join(", ")}');
    _log('📸 Files: ${files.keys.join(", ")}');
    // Validar archivos
    await _validarArchivosMultipart(files);

    try {
      final uri = Uri.parse(endpoint);
      final request = http.MultipartRequest(method, uri);

      // ✅ Agregar headers
      request.headers.addAll(_getMultipartHeaders());

      _log('📋 Headers multipart:');
      request.headers.forEach((key, value) {
        _log(
          '   $key: ${key.toLowerCase().contains("auth") ? "[OCULTO]" : value}',
        );
      });

      // Agregar campos
      request.fields.addAll(fields);

      // Agregar archivos
      for (final entry in files.entries) {
        final fieldName = entry.key;
        final file = entry.value;

        final stream = http.ByteStream(file.openRead());
        final length = await file.length();
        final extension = file.path.split('.').last.toLowerCase();
        final contentType = _getContentType(extension);

        final multipartFile = http.MultipartFile(
          fieldName,
          stream,
          length,
          filename: file.path.split('/').last,
          contentType: contentType,
        );

        request.files.add(multipartFile);
        _log('✅ Archivo agregado: ${multipartFile.filename} ($length bytes)');
      }

      // ✅ CAMBIO PRINCIPAL: Enviar SIN reintentos, solo con timeout extendido
      _log('📤 Enviando petición multipart (1 intento, timeout: 90s)...');

      final streamedResponse = await request.send().timeout(
        ApiConfig.receiveTimeout * 3, // 90 segundos
        onTimeout: () {
          throw TimeoutException(
            'La subida tardó demasiado. Verifica tu conexión.',
          );
        },
      );

      final response = await http.Response.fromStream(streamedResponse);

      // ✅ Manejo especial de 401 (token expirado)
      if (response.statusCode == 401) {
        _log('⚠️ Token expirado en multipart, refrescando...');
        final refreshed = await refreshAccessToken();

        if (refreshed) {
          _log('🔄 Reintentando multipart UNA VEZ con nuevo token');

          // Recrear request con nuevo token
          final retryRequest = http.MultipartRequest(method, uri);
          retryRequest.headers.addAll(_getMultipartHeaders());
          retryRequest.fields.addAll(fields);

          // Re-agregar archivos
          for (final entry in files.entries) {
            final file = entry.value;
            final stream = http.ByteStream(file.openRead());
            final length = await file.length();
            final extension = file.path.split('.').last.toLowerCase();

            retryRequest.files.add(
              http.MultipartFile(
                entry.key,
                stream,
                length,
                filename: file.path.split('/').last,
                contentType: _getContentType(extension),
              ),
            );
          }

          final retryStreamedResponse = await retryRequest.send().timeout(
            ApiConfig.receiveTimeout * 3,
          );

          return _handleResponse(
            await http.Response.fromStream(retryStreamedResponse),
          );
        }

        throw ApiException(
          statusCode: 401,
          message: ApiConfig.errorUnauthorized,
          errors: {'detail': 'Sesión expirada'},
          stackTrace: StackTrace.current,
        );
      }

      return _handleResponse(response);
    } on TimeoutException catch (e, stackTrace) {
      _log('⏱️ Timeout en subida de archivo', error: e);
      throw ApiException(
        statusCode: 0,
        message:
            'La subida tardó demasiado. Verifica tu conexión e intenta nuevamente.',
        errors: {
          'timeout':
              'Operación expiró después de ${(ApiConfig.receiveTimeout.inSeconds * 3)} segundos',
        },
        stackTrace: stackTrace,
      );
    } on SocketException catch (e, stackTrace) {
      _log('🌐 Sin conexión durante subida', error: e);
      throw ApiException(
        statusCode: 0,
        message: ApiConfig.errorNetwork,
        errors: {'conexion': 'No hay conexión a internet'},
        stackTrace: stackTrace,
      );
    } catch (e, stackTrace) {
      if (e is ApiException) rethrow;
      _log('❌ Error en multipart', error: e, stackTrace: stackTrace);
      throw ApiException(
        statusCode: 0,
        message: 'Error al enviar archivos',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // VALIDACIÓN DE ARCHIVOS
  // ══════════════════════════════════════════════════════════════════════════
  Future<void> _validarArchivosMultipart(Map<String, File> files) async {
    for (final entry in files.entries) {
      final fieldName = entry.key;
      final file = entry.value;
      if (!await file.exists()) {
        throw ApiException(
          statusCode: 400,
          message: 'Archivo no encontrado: ${file.path}',
          errors: {fieldName: 'El archivo no existe'},
          stackTrace: StackTrace.current,
        );
      }

      final fileStats = await file.stat();
      if (fileStats.type != FileSystemEntityType.file) {
        throw ApiException(
          statusCode: 400,
          message: 'No es un archivo válido: ${file.path}',
          errors: {fieldName: 'Debe ser un archivo'},
          stackTrace: StackTrace.current,
        );
      }

      final tamanoBytes = await file.length();
      final tamanoMB = tamanoBytes / (1024 * 1024);

      if (tamanoMB > 10) {
        throw ApiException(
          statusCode: 400,
          message:
              'Archivo demasiado grande: ${tamanoMB.toStringAsFixed(1)} MB',
          errors: {fieldName: 'Tamaño máximo: 10 MB'},
          stackTrace: StackTrace.current,
        );
      }

      final extension = file.path.split('.').last.toLowerCase();
      final extensionesValidas = [
        'jpg',
        'jpeg',
        'png',
        'gif',
        'webp',
        'bmp',
        'pdf',
        'doc',
        'docx',
        'mp4',
        'mov',
      ];

      if (!extensionesValidas.contains(extension)) {
        throw ApiException(
          statusCode: 400,
          message: 'Formato inválido: .$extension',
          errors: {fieldName: 'Formatos: ${extensionesValidas.join(", ")}'},
          stackTrace: StackTrace.current,
        );
      }

      _log('✅ Validación OK: ${file.path.split('/').last}');
    }
  }

  MediaType _getContentType(String extension) {
    switch (extension) {
      case 'jpg':
      case 'jpeg':
        return MediaType('image', 'jpeg');
      case 'png':
        return MediaType('image', 'png');
      case 'gif':
        return MediaType('image', 'gif');
      case 'webp':
        return MediaType('image', 'webp');
      default:
        return MediaType('application', 'octet-stream');
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // RESPONSE HANDLING
  // ══════════════════════════════════════════════════════════════════════════
  Map<String, dynamic> _handleResponse(http.Response response) {
    _log('📨 Response: ${response.statusCode}');
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) return {'success': true};
      try {
        return json.decode(response.body) as Map<String, dynamic>;
      } catch (e) {
        return {'success': true, 'data': response.body};
      }
    }

    Map<String, dynamic> error = {};
    try {
      if (response.body.isNotEmpty) {
        error = json.decode(response.body) as Map<String, dynamic>;
      }
    } catch (e) {
      error = {'error': response.body};
    }

    _log('❌ Error HTTP ${response.statusCode}', error: error);
    String errorMessage = _extractErrorMessage(error, response.statusCode);

    throw ApiException(
      statusCode: response.statusCode,
      message: errorMessage,
      errors: error,
      details: _extractRateLimitDetails(error, response.statusCode),
      stackTrace: StackTrace.current,
    );
  }

  Map<String, dynamic>? _extractRateLimitDetails(
    Map<String, dynamic> error,
    int statusCode,
  ) {
    if (statusCode == 429) {
      return {
        'retry_after': error['tiempo_espera'],
        'tipo': error['tipo'],
        'bloqueado_hasta': error['bloqueado_hasta'],
        'bloqueado': error['bloqueado'] ?? true,
      };
    }
    return null;
  }

  String _extractErrorMessage(Map<String, dynamic> error, int statusCode) {
    if (statusCode == 429) {
      return error['error'] ?? 'Demasiados intentos';
    }
    if (statusCode == 401) return ApiConfig.errorUnauthorized;
    if (statusCode == 403) return error['error'] ?? 'Sin permisos';
    if (statusCode == 404) return 'Recurso no encontrado';
    if (statusCode >= 500) return ApiConfig.errorServer;
    if (error.containsKey('message')) return error['message'].toString();
    if (error.containsKey('detail')) return error['detail'].toString();
    if (error.containsKey('error')) return error['error'].toString();

    return 'Error en la petición';
  }
}
