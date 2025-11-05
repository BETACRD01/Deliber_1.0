// lib/services/auth_service.dart

import '../apis/subapis/http_client.dart';
import '../config/api_config.dart';
import '../apis/helpers/api_validators.dart';
import '../apis/helpers/api_exception.dart';
import 'dart:developer' as developer;

/// Servicio de Autenticación - SOLO lógica de autenticación
/// ✅ CON PERSISTENCIA DE ROL DE USUARIO
class AuthService {
  // ============================================
  // SINGLETON
  // ============================================
  static final AuthService _instance = AuthService._internal();
  factory AuthService() => _instance;
  AuthService._internal();

  // ============================================
  // CLIENTE HTTP
  // ============================================
  final _client = ApiClient();

  // ============================================
  // LOGGING
  // ============================================
  void _log(String message, {Object? error, StackTrace? stackTrace}) {
    developer.log(
      message,
      name: 'AuthService',
      error: error,
      stackTrace: stackTrace,
    );
  }

  // ============================================
  // ✅ REGISTRO (MODIFICADO PARA GUARDAR ROL)
  // ============================================

  Future<Map<String, dynamic>> register(Map<String, dynamic> data) async {
    _log('📝 Iniciando registro para: ${data['email']}');

    _normalizarDatosRegistro(data);
    _logDatosRegistro(data);
    _validarCamposRequeridos(data);
    _validarCoincidenciaPasswords(data);

    try {
      final response = await _client.post(ApiConfig.registro, data);

      if (response.containsKey('tokens')) {
        final tokens = response['tokens'];

        // ✅ NUEVO: Extraer rol y userId del response
        final String? rol = response['rol'] as String?;
        final int? userId = response['user_id'] as int?;

        // ✅ NUEVO: Guardar tokens CON rol y userId
        await _client.saveTokens(
          tokens['access'],
          tokens['refresh'],
          role: rol,
          userId: userId,
        );

        _log('✅ Usuario registrado exitosamente');
        _log('👤 Rol asignado: $rol');
        _log('🆔 User ID: $userId');
      }

      return response;
    } on ApiException {
      rethrow;
    } catch (e, stackTrace) {
      _log('❌ Error inesperado en registro', error: e, stackTrace: stackTrace);
      throw ApiException(
        statusCode: 0,
        message: 'Error al registrar usuario',
        errors: {'error': e.toString()},
        stackTrace: stackTrace,
      );
    }
  }

  // ============================================
  // ✅ LOGIN (MODIFICADO PARA GUARDAR ROL)
  // ============================================

  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    _log('🔐 Login para: $email');

    final response = await _client.post(ApiConfig.login, {
      'email': email,
      'password': password,
    });

    if (response.containsKey('tokens')) {
      final tokens = response['tokens'];

      // ✅ NUEVO: Extraer rol y userId del response
      final String? rol = response['rol'] as String?;
      final int? userId = response['user_id'] as int?;

      // ✅ NUEVO: Guardar tokens CON rol y userId
      await _client.saveTokens(
        tokens['access'],
        tokens['refresh'],
        role: rol,
        userId: userId,
      );

      _log('✅ Login exitoso');
      _log('👤 Rol: $rol');
      _log('🆔 User ID: $userId');
    }

    return response;
  }

  // ============================================
  // ✅ LOGIN CON GOOGLE (MODIFICADO PARA GUARDAR ROL)
  // ============================================

  Future<Map<String, dynamic>> loginWithGoogle({
    required String accessToken,
  }) async {
    _log('🔐 Login con Google');

    final response = await _client.post(ApiConfig.googleLogin, {
      'access_token': accessToken,
    });

    if (response.containsKey('tokens')) {
      final tokens = response['tokens'];

      // ✅ NUEVO: Extraer rol y userId del response
      final String? rol = response['rol'] as String?;
      final int? userId = response['user_id'] as int?;

      // ✅ NUEVO: Guardar tokens CON rol y userId
      await _client.saveTokens(
        tokens['access'],
        tokens['refresh'],
        role: rol,
        userId: userId,
      );

      _log('✅ Login con Google exitoso');
      _log('👤 Rol: $rol');
      _log('🆔 User ID: $userId');
    }

    return response;
  }

  // ============================================
  // LOGOUT
  // ============================================

  Future<void> logout() async {
    try {
      _log('👋 Cerrando sesión...');
      if (_client.refreshToken != null) {
        await _client.post(ApiConfig.logout, {
          'refresh_token': _client.refreshToken,
        });
      }
      _log('✅ Logout exitoso');
    } catch (e) {
      _log('⚠️ Error en logout del servidor');
    } finally {
      await _client.clearTokens();
    }
  }

  // ============================================
  // PERFIL
  // ============================================

  Future<Map<String, dynamic>> getPerfil() async {
    return await _client.get(ApiConfig.perfil);
  }

  Future<Map<String, dynamic>> actualizarPerfil(
    Map<String, dynamic> data,
  ) async {
    return await _client.put(ApiConfig.actualizarPerfil, data);
  }

  Future<Map<String, dynamic>> getInfoRol() async {
    return await _client.get(ApiConfig.infoRol);
  }

  Future<bool> verificarToken() async {
    try {
      await _client.get(ApiConfig.verificarToken);
      return true;
    } catch (e) {
      return false;
    }
  }

  // ============================================
  // GESTIÓN DE CONTRASEÑA
  // ============================================

  Future<Map<String, dynamic>> cambiarPassword({
    required String passwordActual,
    required String passwordNueva,
  }) async {
    return await _client.post(ApiConfig.cambiarPassword, {
      'password_actual': passwordActual,
      'password_nueva': passwordNueva,
    });
  }

  Future<Map<String, dynamic>> solicitarCodigoRecuperacion({
    required String email,
  }) async {
    if (!ApiValidators.esEmailValido(email)) {
      throw ApiException(
        statusCode: 400,
        message: 'Email inválido',
        errors: {'email': 'Formato incorrecto'},
        stackTrace: StackTrace.current,
      );
    }
    return await _client.post(ApiConfig.solicitarCodigoRecuperacion, {
      'email': email,
    });
  }

  Future<Map<String, dynamic>> verificarCodigoRecuperacion({
    required String email,
    required String codigo,
  }) async {
    if (!ApiValidators.esCodigoValido(codigo)) {
      throw ApiException(
        statusCode: 400,
        message: 'Código debe tener ${ApiConfig.codigoLongitud} dígitos',
        errors: {'codigo': 'Formato inválido'},
        stackTrace: StackTrace.current,
      );
    }
    return await _client.post(ApiConfig.verificarCodigoRecuperacion, {
      'email': email,
      'codigo': codigo,
    });
  }

  Future<Map<String, dynamic>> resetPasswordConCodigo({
    required String email,
    required String codigo,
    required String password,
  }) async {
    if (!ApiValidators.esCodigoValido(codigo)) {
      throw ApiException(
        statusCode: 400,
        message: 'Código inválido',
        errors: {'codigo': 'Formato incorrecto'},
        stackTrace: StackTrace.current,
      );
    }
    final validacion = ApiValidators.validarPassword(password);
    if (!validacion['valida']) {
      final errores = validacion['errores'] as List<String>;
      throw ApiException(
        statusCode: 400,
        message: errores.join('\n'),
        errors: {'password': errores},
        stackTrace: StackTrace.current,
      );
    }
    return await _client.post(ApiConfig.resetPasswordConCodigo, {
      'email': email,
      'codigo': codigo,
      'password': password,
    });
  }

  // ============================================
  // PREFERENCIAS Y CUENTA
  // ============================================

  Future<Map<String, dynamic>> actualizarPreferencias(
    Map<String, dynamic> preferencias,
  ) async {
    return await _client.put(ApiConfig.actualizarPreferencias, preferencias);
  }

  Future<Map<String, dynamic>> desactivarCuenta({
    required String password,
    String? razon,
  }) async {
    return await _client.post(ApiConfig.desactivarCuenta, {
      'password': password,
      if (razon != null) 'razon': razon,
    });
  }

  // ============================================
  // ✅ NUEVOS MÉTODOS PÚBLICOS PARA GESTIÓN DE ROL
  // ============================================

  /// Obtiene el rol cacheado del usuario sin hacer petición al servidor
  String? getRolCacheado() {
    return _client.userRole;
  }

  /// Obtiene el ID del usuario cacheado
  int? getUserIdCacheado() {
    return _client.userId;
  }

  /// Verifica si el usuario actual es repartidor
  bool esRepartidor() {
    final rol = _client.userRole?.toUpperCase();
    return rol == ApiConfig.rolRepartidor;
  }

  /// Verifica si el usuario actual es un usuario normal
  bool esUsuario() {
    final rol = _client.userRole?.toUpperCase();
    return rol == ApiConfig.rolUsuario;
  }

  /// Verifica si el usuario actual es proveedor
  bool esProveedor() {
    final rol = _client.userRole?.toUpperCase();
    return rol == ApiConfig.rolProveedor;
  }

  /// Verifica si el usuario actual es administrador
  bool esAdministrador() {
    final rol = _client.userRole?.toUpperCase();
    return rol == ApiConfig.rolAdministrador;
  }

  /// Verifica si el rol cacheado coincide con el esperado
  bool tieneRol(String rolEsperado) {
    final rol = _client.userRole?.toUpperCase();
    return rol == rolEsperado.toUpperCase();
  }

  /// Imprime información de debug del estado actual
  void imprimirEstadoAuth() {
    _log('═══════════════════════════════════════════════════════════════');
    _log('📊 ESTADO DE AUTENTICACIÓN');
    _log('═══════════════════════════════════════════════════════════════');
    _log('🔐 Autenticado: ${_client.isAuthenticated}');
    _log('👤 Rol cacheado: ${_client.userRole ?? "null"}');
    _log('🆔 User ID: ${_client.userId ?? "null"}');
    _log('🔑 Token presente: ${_client.accessToken != null}');
    _log('🔄 Refresh token presente: ${_client.refreshToken != null}');
    _log('═══════════════════════════════════════════════════════════════');
  }

  // ============================================
  // HELPERS PRIVADOS PARA REGISTRO
  // ============================================

  void _normalizarDatosRegistro(Map<String, dynamic> data) {
    if (data.containsKey('email')) {
      data['email'] = data['email'].toString().trim().toLowerCase();
    }

    final camposTexto = ['first_name', 'last_name', 'username', 'celular'];
    for (final campo in camposTexto) {
      if (data.containsKey(campo) && data[campo] != null) {
        data[campo] = data[campo].toString().trim();
      }
    }

    for (final campo in ['password', 'password2']) {
      if (data.containsKey(campo) && data[campo] != null) {
        data[campo] = data[campo].toString().trim();
      }
    }

    if (!data.containsKey('terminos_aceptados')) {
      data['terminos_aceptados'] = true;
    }
  }

  void _logDatosRegistro(Map<String, dynamic> data) {
    _log('📦 Datos después de normalizar:');
    data.forEach((key, value) {
      if (key != 'password' && key != 'password2') {
        _log('  $key: "$value"');
      } else {
        _log('  $key: [OCULTO] (${value?.toString().length ?? 0} chars)');
      }
    });
  }

  void _validarCamposRequeridos(Map<String, dynamic> data) {
    final camposRequeridos = {
      'first_name': 'Nombre',
      'last_name': 'Apellido',
      'email': 'Email',
      'celular': 'Celular',
      'password': 'Contraseña',
      'password2': 'Confirmar contraseña',
    };

    final errores = <String>[];

    camposRequeridos.forEach((campo, nombre) {
      if (!data.containsKey(campo)) {
        errores.add('$nombre no está presente');
        return;
      }

      final valor = data[campo];

      if (valor == null) {
        errores.add('$nombre es null');
        return;
      }

      if (valor.toString().trim().isEmpty) {
        errores.add('$nombre está vacío');
      }
    });

    if (errores.isNotEmpty) {
      final mensaje = 'Faltan campos:\n${errores.join('\n')}';
      _log('❌ $mensaje');

      throw ApiException(
        statusCode: 400,
        message: mensaje,
        errors: {'campos_faltantes': errores},
        stackTrace: StackTrace.current,
      );
    }
  }

  void _validarCoincidenciaPasswords(Map<String, dynamic> data) {
    final password = data['password']?.toString().trim() ?? '';
    final password2 = data['password2']?.toString().trim() ?? '';

    if (password.isEmpty) {
      throw ApiException(
        statusCode: 400,
        message: 'La contraseña no puede estar vacía',
        errors: {'password': 'Contraseña requerida'},
        stackTrace: StackTrace.current,
      );
    }

    if (password != password2) {
      _log('❌ Las contraseñas no coinciden');
      _log('  password: ${password.length} chars');
      _log('  password2: ${password2.length} chars');

      throw ApiException(
        statusCode: 400,
        message: 'Las contraseñas no coinciden',
        errors: {'password2': 'No coincide con la contraseña'},
        stackTrace: StackTrace.current,
      );
    }
  }

  // ============================================
  // MÉTODOS ESTÁTICOS DE UTILIDAD
  // ============================================

  static String formatearTiempoEspera(int segundos) {
    final duracion = Duration(seconds: segundos);
    final minutos = duracion.inMinutes;
    final segundosRestantes = duracion.inSeconds % 60;

    if (minutos > 0) {
      return '${minutos}m ${segundosRestantes}s';
    } else {
      return '${segundosRestantes}s';
    }
  }

  // ============================================
  // MÉTODOS PÚBLICOS DE UTILIDAD
  // ============================================

  Future<bool> hasStoredTokens() async {
    return await _client.hasStoredTokens();
  }

  Future<void> loadTokens() async {
    await _client.loadTokens();
  }

  bool get isAuthenticated => _client.isAuthenticated;
}
