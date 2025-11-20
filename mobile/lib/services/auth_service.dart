import '../apis/subapis/http_client.dart';
import '../config/api_config.dart';
import '../apis/helpers/api_validators.dart';
import '../apis/helpers/api_exception.dart';
import 'dart:developer' as developer;

// ============================================
// 👤 MODELO: UserInfo
// ============================================

class UserInfo {
  final String email;
  final List<String> roles;
  final int? userId;

  UserInfo({required this.email, required this.roles, this.userId});

  bool tieneRol(String rol) {
    return roles.any((r) => r.toUpperCase() == rol.toUpperCase());
  }

  bool get esProveedor => tieneRol('PROVEEDOR');
  bool get esRepartidor => tieneRol('REPARTIDOR');
  bool get esAdmin => tieneRol('ADMINISTRADOR');
  bool get esAnonimo => email.toLowerCase().contains('anonymous');

  @override
  String toString() =>
      'UserInfo(email: $email, roles: $roles, userId: $userId)';
}

// ============================================
// 🔐 AuthService
// ============================================

class AuthService {
  static final AuthService _instance = AuthService._internal();
  factory AuthService() => _instance;
  AuthService._internal();

  final _client = ApiClient();

  void _log(String message, {Object? error, StackTrace? stackTrace}) {
    developer.log(
      message,
      name: 'AuthService',
      error: error,
      stackTrace: stackTrace,
    );
  }

  // ============================================
  // ✅ REGISTRO (CORREGIDO - USA postPublic)
  // ============================================
  Future<Map<String, dynamic>> register(Map<String, dynamic> data) async {
    _log('📝 Iniciando registro para: ${data['email']}');

    _normalizarDatosRegistro(data);
    _logDatosRegistro(data);
    _validarCamposRequeridos(data);
    _validarCoincidenciaPasswords(data);

    try {
      // ✅ CORREGIDO: Usar postPublic en lugar de post
      final response = await _client.postPublic(ApiConfig.registro, data);

      if (response.containsKey('tokens')) {
        final tokens = response['tokens'];

        final String? rol = tokens['rol'] as String?;
        final int? userId = tokens['user_id'] as int?;

        final String? rolFallback = response['rol'] as String?;
        final int? userIdFallback =
            (response['user_id'] ?? response['id'] ?? response['usuario_id'])
                as int?;

        final String? rolFinal = rol ?? rolFallback;
        final int? userIdFinal = userId ?? userIdFallback;

        await _client.saveTokens(
          tokens['access'],
          tokens['refresh'],
          role: rolFinal,
          userId: userIdFinal,
          tokenLifetime: const Duration(hours: 12),
        );

        _log('✅ Registro exitoso');
        _log('👤 Rol: $rolFinal');
        _log('🆔 User ID: $userIdFinal');

        if (rolFinal == null) {
          _log('⚠️ ADVERTENCIA: No se recibió rol del backend');
        }
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
  // ✅ LOGIN (CORREGIDO - USA postPublic)
  // ============================================
  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    _log('🔐 Login para: $email');

    // ✅ CORREGIDO: Usar postPublic en lugar de post
    final response = await _client.postPublic(ApiConfig.login, {
      'identificador': email,
      'password': password,
    });

    if (response.containsKey('tokens')) {
      final tokens = response['tokens'];

      final String? rol = tokens['rol'] as String?;
      final int? userId = tokens['user_id'] as int?;

      final String? rolFallback = response['rol'] as String?;
      final int? userIdFallback = response['user_id'] as int?;

      final String? rolFinal;
      final int? userIdFinal;

      if (response.containsKey('usuario') && response['usuario'] is Map) {
        final usuario = response['usuario'] as Map<String, dynamic>;
        rolFinal = rol ?? rolFallback ?? usuario['rol'] as String?;
        userIdFinal = userId ?? userIdFallback ?? usuario['id'] as int?;
      } else {
        rolFinal = rol ?? rolFallback;
        userIdFinal = userId ?? userIdFallback;
      }

      await _client.saveTokens(
        tokens['access'],
        tokens['refresh'],
        role: rolFinal,
        userId: userIdFinal,
        tokenLifetime: const Duration(hours: 12),
      );

      _log('✅ Login exitoso');
      _log('👤 Rol guardado: $rolFinal');
      _log('🆔 User ID guardado: $userIdFinal');

      if (rolFinal == null) {
        _log('⚠️ ADVERTENCIA: No se pudo determinar el rol del usuario');
        _log('   Tokens: ${tokens.keys.join(", ")}');
        _log('   Response keys: ${response.keys.join(", ")}');
      }
    }

    return response;
  }

  // ============================================
  // ✅ LOGIN CON GOOGLE (CORREGIDO - USA postPublic)
  // ============================================
  Future<Map<String, dynamic>> loginWithGoogle({
    required String accessToken,
  }) async {
    _log('🔐 Login con Google');

    // ✅ CORREGIDO: Usar postPublic en lugar de post
    final response = await _client.postPublic(ApiConfig.googleLogin, {
      'access_token': accessToken,
    });

    if (response.containsKey('tokens')) {
      final tokens = response['tokens'];

      final String? rol = tokens['rol'] as String?;
      final int? userId = tokens['user_id'] as int?;

      final String? rolFallback = response['rol'] as String?;
      final int? userIdFallback = response['user_id'] as int?;

      final String? rolFinal = rol ?? rolFallback;
      final int? userIdFinal = userId ?? userIdFallback;

      await _client.saveTokens(
        tokens['access'],
        tokens['refresh'],
        role: rolFinal,
        userId: userIdFinal,
        tokenLifetime: const Duration(hours: 12),
      );

      _log('✅ Login con Google exitoso');
      _log('👤 Rol: $rolFinal');
      _log('🆔 User ID: $userIdFinal');
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
      _log('⚠️ Error en logout del servidor: $e');
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

  // ✅ CORREGIDO: Usar postPublic para recuperación de contraseña
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
    return await _client.postPublic(ApiConfig.solicitarCodigoRecuperacion, {
      'email': email,
    });
  }

  // ✅ CORREGIDO: Usar postPublic
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
    return await _client.postPublic(ApiConfig.verificarCodigoRecuperacion, {
      'email': email,
      'codigo': codigo,
    });
  }

  // ✅ CORREGIDO: Usar postPublic
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
    return await _client.postPublic(ApiConfig.resetPasswordConCodigo, {
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
  // MÉTODOS PÚBLICOS PARA GESTIÓN DE ROL
  // ============================================

  String? getRolCacheado() {
    final rol = _client.userRole;
    if (rol == null) {
      _log('⚠️ No hay rol cacheado');
    } else {
      _log('👤 Rol cacheado: $rol');
    }
    return rol;
  }

  int? getUserIdCacheado() {
    final userId = _client.userId;
    if (userId == null) {
      _log('⚠️ No hay userId cacheado');
    } else {
      _log('🆔 UserId cacheado: $userId');
    }
    return userId;
  }

  bool esRepartidor() {
    final rol = _client.userRole?.toUpperCase();
    final esRep = rol == ApiConfig.rolRepartidor;
    _log('🚚 ¿Es repartidor? $esRep (rol: $rol)');
    return esRep;
  }

  bool esUsuario() {
    final rol = _client.userRole?.toUpperCase();
    final esUs = rol == ApiConfig.rolUsuario;
    _log('👤 ¿Es usuario? $esUs (rol: $rol)');
    return esUs;
  }

  bool esProveedor() {
    final rol = _client.userRole?.toUpperCase();
    final esProv = rol == ApiConfig.rolProveedor;
    _log('🪙 ¿Es proveedor? $esProv (rol: $rol)');
    return esProv;
  }

  bool esAdministrador() {
    final rol = _client.userRole?.toUpperCase();
    final esAdmin = rol == ApiConfig.rolAdministrador;
    _log('👨‍💼 ¿Es administrador? $esAdmin (rol: $rol)');
    return esAdmin;
  }

  bool tieneRol(String rolEsperado) {
    final rol = _client.userRole?.toUpperCase();
    final coincide = rol == rolEsperado.toUpperCase();
    _log('🎭 ¿Tiene rol $rolEsperado? $coincide (rol actual: $rol)');
    return coincide;
  }

  void imprimirEstadoAuth() {
    _log('╔═══════════════════════════════════════════════════════════╗');
    _log('📊 ESTADO DE AUTENTICACIÓN');
    _log('╟───────────────────────────────────────────────────────────╣');
    _log('🔓 Autenticado: ${_client.isAuthenticated}');
    _log('👤 Rol cacheado: ${_client.userRole ?? "null"}');
    _log('🆔 User ID: ${_client.userId ?? "null"}');
    _log('🔑 Token presente: ${_client.accessToken != null}');
    _log('🔄 Refresh token presente: ${_client.refreshToken != null}');

    if (_client.tokenExpiry != null) {
      final remaining = _client.tokenExpiry!.difference(DateTime.now());
      if (remaining.isNegative) {
        _log('⏰ Token EXPIRADO hace ${remaining.abs().inMinutes} minutos');
      } else {
        _log('⏰ Token expira en ${remaining.inMinutes} minutos');
      }
    }

    _log('╚═══════════════════════════════════════════════════════════╝');
  }

  UserInfo? get user {
    if (!isAuthenticated) return null;

    final rol = getRolCacheado();
    final userId = getUserIdCacheado();

    if (rol == null) return null;

    return UserInfo(
      email: 'usuario@deliber.com',
      roles: [rol],
      userId: userId,
    );
  }

  // ============================================
  // GESTIÓN DE ROLES MÚLTIPLES
  // ============================================

  Future<Map<String, dynamic>> obtenerRolesDisponibles() async {
    return await _client.get(ApiConfig.usuariosMisRoles);
  }

  Future<Map<String, dynamic>> cambiarRolActivo(String nuevoRol) async {
    _log('🔄 Cambiando rol activo a: $nuevoRol');

    final response = await _client.post(ApiConfig.usuariosCambiarRolActivo, {
      'rol': nuevoRol.toUpperCase(),
    });

    if (response.containsKey('tokens')) {
      final tokens = response['tokens'];

      await _client.saveTokens(
        tokens['access'],
        tokens['refresh'],
        role: tokens['rol'] as String?,
        userId: _client.userId,
        tokenLifetime: const Duration(hours: 12),
      );

      _log('✅ Rol cambiado exitosamente a: ${tokens['rol']}');
      _log('   Tokens actualizados en memoria');
    }

    return response;
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

    if (_client.userRole == null) {
      _log('⚠️ ADVERTENCIA: Tokens cargados pero sin rol');
    } else {
      _log('✅ Tokens cargados con rol: ${_client.userRole}');
    }
  }

  bool get isAuthenticated => _client.isAuthenticated;
}