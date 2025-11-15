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

/// Cliente HTTP con AUTO-REFRESH INTELIGENTE de tokens
/// ✅ OPTIMIZADO: Evita cargas redundantes de tokens
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

  // ════════════════════════════════════════════════════════════════════════
  // ✅ NUEVAS VARIABLES PARA GESTIÓN DE EXPIRACIÓN
  // ════════════════════════════════════════════════════════════════════════

  String? _accessToken;
  String? _refreshToken;
  String? _userRole;
  int? _userId;
  DateTime? _tokenExpiry;
  bool _isRefreshing = false;
  Completer<bool>? _refreshCompleter;
  bool _tokensLoaded = false;

  // ════════════════════════════════════════════════════════════════════════
  // CONSTANTES
  // ════════════════════════════════════════════════════════════════════════

  static const String _keyAccessToken = 'jp_access_token';
  static const String _keyRefreshToken = 'jp_refresh_token';
  static const String _keyTokenTimestamp = 'jp_token_timestamp';
  static const String _keyTokenExpiry = 'jp_token_expiry';
  static const String _keyUserRole = 'jp_user_role';
  static const String _keyUserId = 'jp_user_id';

  // ════════════════════════════════════════════════════════════════════════
  // GETTERS
  // ════════════════════════════════════════════════════════════════════════

  bool get isAuthenticated => _accessToken != null;
  String? get accessToken => _accessToken;
  String? get refreshToken => _refreshToken;
  String? get userRole => _userRole;
  int? get userId => _userId;
  DateTime? get tokenExpiry => _tokenExpiry;
  bool get tokensLoaded => _tokensLoaded;

  void _log(String message, {Object? error, StackTrace? stackTrace}) {
    developer.log(
      message,
      name: 'ApiClient',
      error: error,
      stackTrace: stackTrace,
    );
  }

  // ════════════════════════════════════════════════════════════════════════
  // ✅ TOKEN MANAGEMENT OPTIMIZADO
  // ════════════════════════════════════════════════════════════════════════

  Future<void> saveTokens(
    String access,
    String refresh, {
    String? role,
    int? userId,
    Duration? tokenLifetime,
  }) async {
    try {
      _accessToken = access;
      _refreshToken = refresh;
      _userRole = role;
      _userId = userId;
      _tokensLoaded = true;

      final lifetime = tokenLifetime ?? const Duration(hours: 12);
      _tokenExpiry = DateTime.now().add(lifetime);

      await _secureStorage.write(key: _keyAccessToken, value: access);
      await _secureStorage.write(key: _keyRefreshToken, value: refresh);
      await _secureStorage.write(
        key: _keyTokenTimestamp,
        value: DateTime.now().toIso8601String(),
      );
      await _secureStorage.write(
        key: _keyTokenExpiry,
        value: _tokenExpiry!.toIso8601String(),
      );

      if (role != null) {
        await _secureStorage.write(key: _keyUserRole, value: role);
      }

      if (userId != null) {
        await _secureStorage.write(key: _keyUserId, value: userId.toString());
      }

      _log('✅ Tokens guardados (expiran: ${_tokenExpiry!.toIso8601String()})');
    } catch (e, stackTrace) {
      _log('❌ Error guardando tokens', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  Future<void> loadTokens() async {
    if (_tokensLoaded && _accessToken != null) {
      _log('ℹ️ Tokens ya cargados en memoria, omitiendo recarga');
      return;
    }

    try {
      _accessToken = await _secureStorage.read(key: _keyAccessToken);
      _refreshToken = await _secureStorage.read(key: _keyRefreshToken);
      _userRole = await _secureStorage.read(key: _keyUserRole);

      final userIdStr = await _secureStorage.read(key: _keyUserId);
      if (userIdStr != null) {
        _userId = int.tryParse(userIdStr);
      }

      final expiryStr = await _secureStorage.read(key: _keyTokenExpiry);
      if (expiryStr != null) {
        _tokenExpiry = DateTime.tryParse(expiryStr);
      }

      if (_accessToken != null) {
        _tokensLoaded = true;

        final timestamp = await _secureStorage.read(key: _keyTokenTimestamp);
        _log('✅ Tokens cargados desde storage (guardados: $timestamp)');
        _log(
          '🔐 Token presente: ${_accessToken!.substring(0, min(20, _accessToken!.length))}...',
        );

        if (_tokenExpiry != null) {
          final remaining = _tokenExpiry!.difference(DateTime.now());
          if (remaining.isNegative) {
            _log('⏰ Token EXPIRADO hace ${remaining.abs().inMinutes} minutos');
          } else {
            _log('⏰ Token expira en ${remaining.inMinutes} minutos');
          }
        }

        if (_userRole != null) _log('👤 Rol cargado: $_userRole');
        if (_userId != null) _log('🆔 User ID cargado: $_userId');
      } else {
        _tokensLoaded = false;
        _log('ℹ️ No hay tokens guardados en storage');
      }
    } catch (e, stackTrace) {
      _log('❌ Error cargando tokens', error: e, stackTrace: stackTrace);
      _tokensLoaded = false;
      await clearTokens();
    }
  }

  Future<void> clearTokens() async {
    try {
      _accessToken = null;
      _refreshToken = null;
      _userRole = null;
      _userId = null;
      _tokenExpiry = null;
      _isRefreshing = false;
      _refreshCompleter = null;
      _tokensLoaded = false;

      await _secureStorage.delete(key: _keyAccessToken);
      await _secureStorage.delete(key: _keyRefreshToken);
      await _secureStorage.delete(key: _keyTokenTimestamp);
      await _secureStorage.delete(key: _keyTokenExpiry);
      await _secureStorage.delete(key: _keyUserRole);
      await _secureStorage.delete(key: _keyUserId);

      _log('🗑️ Tokens y datos de usuario eliminados');
    } catch (e, stackTrace) {
      _log('⚠️ Error eliminando tokens', error: e, stackTrace: stackTrace);
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // VALIDACIÓN DE EXPIRACIÓN
  // ════════════════════════════════════════════════════════════════════════

  bool _isTokenExpiredOrExpiring() {
    if (_tokenExpiry == null) {
      _log('⚠️ No hay fecha de expiración guardada');
      return true;
    }

    final now = DateTime.now();
    final margin = const Duration(minutes: 5);
    final expiryWithMargin = _tokenExpiry!.subtract(margin);

    final isExpiring = now.isAfter(expiryWithMargin);

    if (isExpiring) {
      final remaining = _tokenExpiry!.difference(now);
      if (remaining.isNegative) {
        _log('⏰ Token EXPIRADO hace ${remaining.abs().inMinutes} minutos');
      } else {
        _log(
          '⏰ Token expira en ${remaining.inMinutes} minutos - refrescando preventivamente',
        );
      }
    }

    return isExpiring;
  }

  Future<bool> _ensureValidToken() async {
    if (_accessToken == null) return false;

    if (!_isTokenExpiredOrExpiring()) return true;

    _log('🔄 Token expirado/expirando - refrescando automáticamente...');
    return await refreshAccessToken();
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
    if (_refreshToken == null) {
      _log('❌ No hay refresh token disponible');
      return false;
    }

    if (_isRefreshing) {
      _log('⏳ Ya hay un refresh en proceso, esperando...');
      return await _refreshCompleter!.future;
    }

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

        await saveTokens(
          data['access'],
          _refreshToken!,
          role: _userRole,
          userId: _userId,
          tokenLifetime: const Duration(hours: 12),
        );

        _log('✅ Token refrescado exitosamente');
        _refreshCompleter!.complete(true);
        return true;
      }

      if (response.statusCode == 401) {
        _log('❌ Refresh token inválido - limpiando sesión');
        await clearTokens();
      }

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

  // ════════════════════════════════════════════════════════════════════════
  // ✅ REQUEST WITH RETRY Y AUTO-REFRESH
  // ════════════════════════════════════════════════════════════════════════

  Future<http.Response> _requestWithRetry(
    Future<http.Response> Function() request, {
    int maxRetries = 3,
    int retryCount = 0,
  }) async {
    try {
      final response = await request().timeout(ApiConfig.receiveTimeout);

      if (response.statusCode == 401 && retryCount == 0) {
        _log('⚠️ 401 recibido - intentando refresh automático...');
        final refreshed = await refreshAccessToken();

        if (refreshed) {
          _log('🔄 Reintentando petición con nuevo token');
          return await _requestWithRetry(
            request,
            maxRetries: maxRetries,
            retryCount: 1,
          );
        }

        throw ApiException(
          statusCode: 401,
          message: ApiConfig.errorUnauthorized,
          errors: {
            'detail': 'Sesión expirada - por favor inicia sesión nuevamente',
          },
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
          '📡 Sin conexión, reintentando en ${delaySeconds}s (${retryCount + 1}/$maxRetries)',
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

  // ════════════════════════════════════════════════════════════════════════
  // HEADERS
  // ════════════════════════════════════════════════════════════════════════

  Map<String, String> _getHeaders() {
    _log(
      '🔐 Token actual: ${_accessToken != null ? "PRESENTE (${_accessToken!.substring(0, 20)}...)" : "AUSENTE"}',
    );

    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-API-Key': ApiConfig.apiKeyMobile,
      if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
    };
  }

  Map<String, String> _getMultipartHeaders() {
    return {
      'Accept': 'application/json',
      'X-API-Key': ApiConfig.apiKeyMobile,
      if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
    };
  }

  // ════════════════════════════════════════════════════════════════════════
  // ✅ HTTP METHODS OPTIMIZADOS
  // ════════════════════════════════════════════════════════════════════════

  Future<Map<String, dynamic>> get(String endpoint) async {
    await _ensureValidToken();
    _log('➡️ GET: $endpoint');
    final response = await _requestWithRetry(
      () => http.get(Uri.parse(endpoint), headers: _getHeaders()),
    );
    return _handleResponse(response);
  }

  Future<Map<String, dynamic>> post(
    String endpoint,
    Map<String, dynamic> body,
  ) async {
    await _ensureValidToken();
    _log('➡️ POST: $endpoint');
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
    await _ensureValidToken();
    _log('➡️ PUT: $endpoint');
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
    await _ensureValidToken();
    _log('➡️ PATCH: $endpoint');
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
    await _ensureValidToken();
    _log('➡️ DELETE: $endpoint');
    final response = await _requestWithRetry(
      () => http.delete(Uri.parse(endpoint), headers: _getHeaders()),
    );
    return _handleResponse(response);
  }

  // ════════════════════════════════════════════════════════════════════════
  // MULTIPART
  // ════════════════════════════════════════════════════════════════════════

  Future<Map<String, dynamic>> multipart(
    String method,
    String endpoint,
    Map<String, String> fields,
    Map<String, File> files,
  ) async {
    await _ensureValidToken();
    _log('➡️ $method (multipart): $endpoint');
    _log('📦 Fields: ${fields.keys.join(", ")}');
    _log('📸 Files: ${files.keys.join(", ")}');

    await _validarArchivosMultipart(files);

    try {
      final uri = Uri.parse(endpoint);
      final request = http.MultipartRequest(method, uri);

      request.headers.addAll(_getMultipartHeaders());

      _log('📋 Headers multipart:');
      request.headers.forEach((key, value) {
        _log(
          '   $key: ${key.toLowerCase().contains("auth") ? "[OCULTO]" : value}',
        );
      });

      request.fields.addAll(fields);

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

      _log('📤 Enviando petición multipart...');

      final streamedResponse = await request.send().timeout(
        ApiConfig.receiveTimeout * 3,
        onTimeout: () {
          throw TimeoutException(
            'La subida tardó demasiado. Verifica tu conexión.',
          );
        },
      );

      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 401) {
        _log('⚠️ Token expirado en multipart, refrescando...');
        final refreshed = await refreshAccessToken();

        if (refreshed) {
          _log('🔄 Reintentando multipart con nuevo token');

          final retryRequest = http.MultipartRequest(method, uri);
          retryRequest.headers.addAll(_getMultipartHeaders());
          retryRequest.fields.addAll(fields);

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
      _log('📡 Sin conexión durante subida', error: e);
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

  // ════════════════════════════════════════════════════════════════════════
  // UTILIDADES
  // ════════════════════════════════════════════════════════════════════════

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

  // ════════════════════════════════════════════════════════════════════════
  // ✅ _handleResponse - MEJORADO CON LOGGING
  // ════════════════════════════════════════════════════════════════════════

  Map<String, dynamic> _handleResponse(http.Response response) {
    final statusCode = response.statusCode;
    final bodyLength = response.body.length;

    _log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    _log('📨 RESPUESTA HTTP RECIBIDA');
    _log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    _log('📊 Status Code: $statusCode');
    _log('📏 Body Length: $bodyLength bytes');

    if (response.body.isNotEmpty) {
      _log('📄 Response Body (completo):');
      _log(response.body);
    } else {
      _log('📄 Response Body: (vacío)');
    }

    // ✅ ÉXITO - Parsear JSON
    if (statusCode >= 200 && statusCode < 300) {
      _log('✅ Status $statusCode - ÉXITO');

      if (response.body.isEmpty) {
        _log('✅ Respuesta vacía (esperado para DELETE o similar)');
        return {'success': true};
      }

      try {
        final parsed = json.decode(response.body) as Map<String, dynamic>;
        _log('✅ JSON parseado correctamente');
        _log('🔑 Keys disponibles: ${parsed.keys.join(", ")}');

        if (parsed.containsKey('id')) {
          _log('✅ Campo "id" presente: ${parsed['id']}');
        } else {
          _log('⚠️ ADVERTENCIA: Campo "id" AUSENTE en respuesta');
          _log('💡 Estructura recibida: ${parsed.keys.toList()}');
          _log(
            '💡 Posible problema: Backend devuelve {"success": true} sin objeto',
          );
        }

        if (parsed.containsKey('nombre')) {
          _log('✅ Campo "nombre" presente: ${parsed['nombre']}');
        }

        if (parsed.containsKey('user_id')) {
          _log('✅ Campo "user_id" presente: ${parsed['user_id']}');
        }

        _log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        return parsed;
      } catch (e) {
        _log('❌ Error parseando JSON: $e');
        _log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        return {'success': true, 'data': response.body};
      }
    }

    // ❌ ERROR - Parsear error
    _log('❌ Status $statusCode - ERROR');

    Map<String, dynamic> error = {};
    try {
      if (response.body.isNotEmpty) {
        error = json.decode(response.body) as Map<String, dynamic>;
        _log('📋 Error JSON recibido:');
        _log(error.toString());
      }
    } catch (e) {
      _log('⚠️ No se pudo parsear error como JSON');
      error = {'error': response.body};
    }

    _log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

    String errorMessage = _extractErrorMessage(error, statusCode);

    throw ApiException(
      statusCode: statusCode,
      message: errorMessage,
      errors: error,
      details: _extractRateLimitDetails(error, statusCode),
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
