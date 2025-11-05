// lib/config/api_config.dart
import 'dart:developer' as developer;
import 'package:network_info_plus/network_info_plus.dart';

class ApiConfig {
  // ==========================================
  // 🌐 CONFIGURACIÓN DE REDES
  // ==========================================

  static const String redCasaPrefix = '192.168.1';
  static const String ipServidorCasa = '192.168.1.4';

  static const String redInstitucionalPrefix = '172.16';
  static const String ipServidorInstitucional = '172.16.60.4';

  static const String redHotspotPrefix = '192.168.137';
  static const String ipServidorHotspot = '192.168.137.1';

  static const String puertoServidor = '8000';

  static String? _cachedServerIp;
  static String? _lastDetectedNetwork;

  // ==========================================
  // ✅ DETECCIÓN AUTOMÁTICA DE RED
  // ==========================================

  static Future<String> detectServerIp() async {
    try {
      final info = NetworkInfo();
      final wifiIP = await info.getWifiIP();

      if (wifiIP == null || wifiIP.isEmpty) {
        developer.log(
          '⚠️ No se pudo detectar IP WiFi, usando servidor casa',
          name: 'JP Express API',
        );
        return _buildUrl(ipServidorCasa);
      }

      developer.log('📱 IP Dispositivo: $wifiIP', name: 'JP Express API');

      if (wifiIP.startsWith(redCasaPrefix)) {
        _lastDetectedNetwork = 'CASA';
        _cachedServerIp = ipServidorCasa;
        developer.log('🏠 Red detectada: CASA', name: 'JP Express API');
        return _buildUrl(ipServidorCasa);
      } else if (wifiIP.startsWith(redHotspotPrefix)) {
        _lastDetectedNetwork = 'HOTSPOT';
        _cachedServerIp = ipServidorHotspot;
        developer.log('📱 Red detectada: HOTSPOT', name: 'JP Express API');
        return _buildUrl(ipServidorHotspot);
      } else if (wifiIP.startsWith(redInstitucionalPrefix)) {
        _lastDetectedNetwork = 'INSTITUCIONAL';
        _cachedServerIp = ipServidorInstitucional;
        developer.log(
          '🏢 Red detectada: INSTITUCIONAL',
          name: 'JP Express API',
        );
        return _buildUrl(ipServidorInstitucional);
      } else {
        developer.log(
          '❓ Red desconocida: $wifiIP, usando servidor casa',
          name: 'JP Express API',
        );
        _lastDetectedNetwork = 'DESCONOCIDA';
        _cachedServerIp = ipServidorCasa;
        return _buildUrl(ipServidorCasa);
      }
    } catch (e) {
      developer.log(
        '❌ Error detectando red: $e',
        name: 'JP Express API',
        error: e,
      );
      _cachedServerIp = ipServidorCasa;
      return _buildUrl(ipServidorCasa);
    }
  }

  static String _buildUrl(String ip) {
    return 'http://$ip:$puertoServidor';
  }

  static Future<String> getBaseUrl() async {
    const bool isProduction = bool.fromEnvironment('dart.vm.product');

    if (isProduction) {
      return 'https://api.jpexpress.com';
    } else {
      if (_cachedServerIp != null) {
        return _buildUrl(_cachedServerIp!);
      }
      return await detectServerIp();
    }
  }

  static Future<String> refreshNetworkDetection() async {
    _cachedServerIp = null;
    _lastDetectedNetwork = null;
    developer.log('🔄 Forzando re-detección de red...', name: 'JP Express API');
    return await detectServerIp();
  }

  // ==========================================
  // 🔧 MODO MANUAL (Para debugging)
  // ==========================================

  static bool _forceManualIp = false;
  static String? _manualIp;

  static void setManualIp(String ip) {
    _forceManualIp = true;
    _manualIp = ip;
    _cachedServerIp = ip;
    developer.log('🔧 IP manual forzada: $ip', name: 'JP Express API');
  }

  static void disableManualIp() {
    _forceManualIp = false;
    _manualIp = null;
    _cachedServerIp = null;
    developer.log('🔄 Modo automático activado', name: 'JP Express API');
  }

  // ==========================================
  // 🎯 URL BASE INTELIGENTE
  // ==========================================

  static String get baseUrl {
    const bool isProduction = bool.fromEnvironment('dart.vm.product');

    if (isProduction) {
      return 'https://api.jpexpress.com';
    }

    if (_forceManualIp && _manualIp != null) {
      return _buildUrl(_manualIp!);
    }

    if (_cachedServerIp != null) {
      return _buildUrl(_cachedServerIp!);
    }

    return _buildUrl(ipServidorCasa);
  }

  static String get apiUrl => '$baseUrl/api';

  // ==========================================
  // 🔐 AUTH ENDPOINTS
  // ==========================================
  static String get registro => '$apiUrl/auth/registro/';
  static String get login => '$apiUrl/auth/login/';
  static String get googleLogin => '$apiUrl/auth/google-login/';
  static String get perfil => '$apiUrl/auth/perfil/';
  static String get logout => '$apiUrl/auth/logout/';
  static String get infoRol => '$apiUrl/auth/info-rol/';
  static String get verificarToken => '$apiUrl/auth/verificar-token/';
  static String get actualizarPerfil => '$apiUrl/auth/actualizar-perfil/';
  static String get cambiarPassword => '$apiUrl/auth/cambiar-password/';
  static String get solicitarCodigoRecuperacion =>
      '$apiUrl/auth/solicitar-codigo-recuperacion/';
  static String get verificarCodigoRecuperacion =>
      '$apiUrl/auth/verificar-codigo/';
  static String get resetPasswordConCodigo =>
      '$apiUrl/auth/reset-password-con-codigo/';
  static String get actualizarPreferencias =>
      '$apiUrl/auth/preferencias-notificaciones/';
  static String get desactivarCuenta => '$apiUrl/auth/desactivar-cuenta/';
  static String get tokenRefresh => '$apiUrl/auth/token/refresh/';

  // ==========================================
  // 👤 USUARIOS ENDPOINTS
  // ==========================================

  // Perfil
  static String get usuariosPerfil => '$apiUrl/usuarios/perfil/';
  static String get usuariosActualizarPerfil =>
      '$apiUrl/usuarios/perfil/actualizar/';
  static String get usuariosEstadisticas =>
      '$apiUrl/usuarios/perfil/estadisticas/';
  static String usuariosPerfilPublico(int userId) =>
      '$apiUrl/usuarios/perfil/publico/$userId/';
  static String get usuariosFotoPerfil => '$apiUrl/usuarios/perfil/foto/';

  // Direcciones
  static String get usuariosDirecciones => '$apiUrl/usuarios/direcciones/';
  static String usuariosDireccion(String id) =>
      '$apiUrl/usuarios/direcciones/$id/';
  static String get usuariosDireccionPredeterminada =>
      '$apiUrl/usuarios/direcciones/predeterminada/';

  // Ubicación tiempo real
  static String get usuariosUbicacionActualizar =>
      "$apiUrl/usuarios/ubicacion/actualizar/";
  static String get usuariosUbicacionMia => "$apiUrl/usuarios/ubicacion/mia/";

  // Métodos de pago
  static String get usuariosMetodosPago => '$apiUrl/usuarios/metodos-pago/';
  static String usuariosMetodoPago(String id) =>
      '$apiUrl/usuarios/metodos-pago/$id/';
  static String get usuariosMetodoPagoPredeterminado =>
      '$apiUrl/usuarios/metodos-pago/predeterminado/';

  // Notificaciones FCM
  static String get usuariosFCMToken => '$apiUrl/usuarios/fcm-token/';
  static String get usuariosEliminarFCMToken =>
      '$apiUrl/usuarios/fcm-token/eliminar/';
  static String get usuariosEstadoNotificaciones =>
      '$apiUrl/usuarios/notificaciones/';

  // ==========================================
  // 🚚 REPARTIDOR ENDPOINTS
  // ==========================================

  // Perfil
  static String get repartidorPerfil => '$apiUrl/repartidores/perfil/';
  static String get repartidorPerfilActualizar =>
      '$apiUrl/repartidores/perfil/actualizar/';
  static String get repartidorEstadisticas =>
      '$apiUrl/repartidores/perfil/estadisticas/';

  // Estado
  static String get repartidorEstado => '$apiUrl/repartidores/estado/';
  static String get repartidorEstadoHistorial =>
      '$apiUrl/repartidores/estado/historial/';

  // Ubicación
  static String get repartidorUbicacion => '$apiUrl/repartidores/ubicacion/';
  static String get repartidorUbicacionHistorial =>
      '$apiUrl/repartidores/ubicacion/historial/';

  // Pedidos
  static String get repartidorPedidosDisponibles =>
      '$apiUrl/repartidores/pedidos-disponibles/';
  static String repartidorPedidoAceptar(int id) =>
      '$apiUrl/repartidores/pedidos/$id/aceptar/';
  static String repartidorPedidoRechazar(int id) =>
      '$apiUrl/repartidores/pedidos/$id/rechazar/';

  // Vehículos
  static String get repartidorVehiculos => '$apiUrl/repartidores/vehiculos/';
  static String get repartidorVehiculosCrear =>
      '$apiUrl/repartidores/vehiculos/crear/';
  static String repartidorVehiculo(int id) =>
      '$apiUrl/repartidores/vehiculos/$id/';
  static String repartidorVehiculoActivar(int id) =>
      '$apiUrl/repartidores/vehiculos/$id/activar/';

  // Calificaciones
  static String get repartidorCalificaciones =>
      '$apiUrl/repartidores/calificaciones/';
  static String repartidorCalificarCliente(int pedidoId) =>
      '$apiUrl/repartidores/calificaciones/clientes/$pedidoId/';

  // ══════════════════════════════════════════════════════════════════════════
  // 🔑 API KEYS PARA DOBLE AUTENTICACIÓN
  // ══════════════════════════════════════════════════════════════════════════

  /// API Key para la aplicación móvil
  /// IMPORTANTE: Esta clave debe coincidir con API_KEY_MOBILE en el backend (.env)
  static const String apiKeyMobile =
      'mobile_app_deliber_2025_aW7xK3pM9qR5tL2nV8jH4cF6gB1dY0sZ';

  /// API Key para el panel web admin (por si creas uno en Flutter Web)
  static const String apiKeyWeb =
      'web_admin_deliber_2025_XkJ9mP3nQ7wR2vL5zT8hF1cY4gN6sB0d';

  /// API Key actual (por defecto móvil)
  static String get currentApiKey => apiKeyMobile;

  // ==========================================
  // ⏱️ CONFIGURACIÓN DE TIMEOUTS
  // ==========================================
  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);
  static const Duration sendTimeout = Duration(seconds: 30);

  // ==========================================
  // 🔄 CONFIGURACIÓN DE RETRY
  // ==========================================
  static const int maxRetries = 3;
  static const Duration retryDelay = Duration(seconds: 2);

  // ==========================================
  // 🎯 CONFIGURACIÓN DE CÓDIGO DE RECUPERACIÓN
  // ==========================================
  static const int codigoLongitud = 6;
  static const int codigoExpiracionMinutos = 15;
  static const int maxIntentosVerificacion = 5;

  // ==========================================
  // 👥 ROLES DISPONIBLES
  // ==========================================
  static const String rolUsuario = 'USUARIO';
  static const String rolRepartidor = 'REPARTIDOR';
  static const String rolProveedor = 'PROVEEDOR';
  static const String rolAdministrador = 'ADMINISTRADOR';

  // ==========================================
  // 📊 CÓDIGOS DE RESPUESTA HTTP
  // ==========================================
  static const int statusOk = 200;
  static const int statusCreated = 201;
  static const int statusBadRequest = 400;
  static const int statusUnauthorized = 401;
  static const int statusForbidden = 403;
  static const int statusNotFound = 404;
  static const int statusTooManyRequests = 429;
  static const int statusServerError = 500;

  // ==========================================
  // ❌ MENSAJES DE ERROR
  // ==========================================
  static const String errorNetwork = 'Error de conexión. Verifica tu internet.';
  static const String errorTimeout =
      'La petición tardó demasiado. Intenta de nuevo.';
  static const String errorUnauthorized =
      'Sesión expirada. Inicia sesión nuevamente.';
  static const String errorServer = 'Error del servidor. Intenta más tarde.';
  static const String errorUnknown = 'Ocurrió un error inesperado.';
  static const String errorRateLimit =
      'Demasiados intentos. Espera un momento e intenta nuevamente.';

  // ==========================================
  // 📱 INFORMACIÓN DE DEBUG
  // ==========================================
  static Future<void> printDebugInfo() async {
    const bool isProduction = bool.fromEnvironment('dart.vm.product');
    final currentUrl = await getBaseUrl();

    developer.log(
      '╔═══════════════════════════════════════╗',
      name: 'JP Express API',
    );
    developer.log('🏢 JP Express API Configuration', name: 'JP Express API');
    developer.log(
      '╠═══════════════════════════════════════╣',
      name: 'JP Express API',
    );
    developer.log(
      'Environment: ${isProduction ? "🚀 PRODUCTION" : "🛠️ DEVELOPMENT"}',
      name: 'JP Express API',
    );
    developer.log('Base URL: $currentUrl', name: 'JP Express API');
    developer.log('API URL: $apiUrl', name: 'JP Express API');

    if (_lastDetectedNetwork != null) {
      String emoji = _lastDetectedNetwork == 'CASA'
          ? '🏠'
          : _lastDetectedNetwork == 'HOTSPOT'
          ? '📱'
          : _lastDetectedNetwork == 'INSTITUCIONAL'
          ? '🏢'
          : '❓';
      developer.log(
        'Red Actual: $emoji $_lastDetectedNetwork',
        name: 'JP Express API',
      );
    }

    if (_forceManualIp) {
      developer.log('🔧 Modo Manual: $_manualIp', name: 'JP Express API');
    }

    developer.log(
      'Protocol: ${currentUrl.startsWith("https") ? "🔒 HTTPS" : "🔓 HTTP"}',
      name: 'JP Express API',
    );
    developer.log(
      '╠═══════════════════════════════════════╣',
      name: 'JP Express API',
    );
    developer.log('✅ Endpoints Auth:', name: 'JP Express API');
    developer.log('  Login: $login', name: 'JP Express API');
    developer.log('  Registro: $registro', name: 'JP Express API');
    developer.log(
      '╠═══════════════════════════════════════╣',
      name: 'JP Express API',
    );
    developer.log('✅ Endpoints Usuarios:', name: 'JP Express API');
    developer.log('  Perfil: $usuariosPerfil', name: 'JP Express API');
    developer.log(
      '  Direcciones: $usuariosDirecciones',
      name: 'JP Express API',
    );
    developer.log(
      '╠═══════════════════════════════════════╣',
      name: 'JP Express API',
    );
    developer.log('✅ Endpoints Repartidores:', name: 'JP Express API');
    developer.log('  Perfil: $repartidorPerfil', name: 'JP Express API');
    developer.log('  Ubicación: $repartidorUbicacion', name: 'JP Express API');
    developer.log(
      '  Pedidos: $repartidorPedidosDisponibles',
      name: 'JP Express API',
    );
    developer.log(
      '╚═══════════════════════════════════════╝',
      name: 'JP Express API',
    );
  }

  // ==========================================
  // 🔧 UTILIDADES
  // ==========================================
  static bool get isProduction => bool.fromEnvironment('dart.vm.product');
  static bool get isDevelopment => !isProduction;
  static bool get isHttps => baseUrl.startsWith('https');
  static bool get isHttp => baseUrl.startsWith('http://');
  static String? get currentNetwork => _lastDetectedNetwork;
  static String? get currentServerIp => _cachedServerIp;

  static String getMediaUrl(String? path) {
    if (path == null || path.isEmpty) return '';
    if (path.startsWith('http')) return path;
    return '$baseUrl$path';
  }

  static bool isValidUrl(String url) {
    try {
      final uri = Uri.parse(url);
      return uri.hasScheme && (uri.scheme == 'http' || uri.scheme == 'https');
    } catch (e) {
      return false;
    }
  }
}
