// lib/config/api_config.dart
import 'dart:developer' as developer;
import 'package:network_info_plus/network_info_plus.dart';
import 'package:flutter/material.dart';

class ApiConfig {
  // ════════════════════════════════════════════════════════════════════════
  // 🌐 CONFIGURACIÓN DE REDES
  // ════════════════════════════════════════════════════════════════════════

  // 🏠 RED CASA
  static const String redCasaPrefix = '192.168.1';

  // ✔ Tu casa
  static const String ipServidorCasaTuya = '192.168.1.5';

  // ✔ Casa del vecino (ACTUAL)
  static const String ipServidorCasaVecino = '192.168.1.22';

  // 🏢 RED INSTITUCIONAL
  static const String redInstitucionalPrefix = '172.16';
  static const String ipServidorInstitucional = '172.16.58.183';


  // 📱 HOTSPOT
  static const String redHotspotPrefix = '192.168.137';
  static const String ipServidorHotspot = '192.168.137.1';

  static const String puertoServidor = '8000';

  static String? _cachedServerIp;
  static String? _lastDetectedNetwork;
  static bool _isInitialized = false;

  // ════════════════════════════════════════════════════════════════════════
  // 🚀 INICIALIZACIÓN
  // ════════════════════════════════════════════════════════════════════════

  static Future<void> initialize() async {
    if (_isInitialized) {
      developer.log('ℹ️ ApiConfig ya inicializado', name: 'Deliber API');
      return;
    }

    try {
      developer.log('🌐 Detectando red...', name: 'Deliber API');
      await detectServerIp();
      _isInitialized = true;

      developer.log(
        '✅ ApiConfig inicializado correctamente',
        name: 'Deliber API',
      );

      await printDebugInfo();
    } catch (e) {
      developer.log(
        '❌ Error inicializando ApiConfig: $e',
        name: 'Deliber API',
        error: e,
      );
      // fallback por si falla
      _cachedServerIp = ipServidorCasaVecino;
      _lastDetectedNetwork = 'CASA (Fallback)';
      _isInitialized = true;
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // 🔥 DETECCIÓN AUTOMÁTICA DE RED (CORREGIDA)
  // ════════════════════════════════════════════════════════════════════════

  static Future<String> detectServerIp() async {
    try {
      final info = NetworkInfo();
      final wifiIP = await info.getWifiIP();

      if (wifiIP == null || wifiIP.isEmpty) {
        developer.log(
          '⚠️ No se pudo detectar IP WiFi, usando CASA (vecino)',
          name: 'Deliber API',
        );
        _cachedServerIp = ipServidorCasaVecino;
        _lastDetectedNetwork = 'CASA (Sin WiFi)';
        return _buildUrl(ipServidorCasaVecino);
      }

      developer.log('📱 IP Dispositivo: $wifiIP', name: 'Deliber API');

      // 🏠 CASA (dos posibles redes)
      if (wifiIP.startsWith(redCasaPrefix)) {
        _lastDetectedNetwork = 'CASA';

        // vecino
        if (wifiIP == ipServidorCasaVecino || wifiIP.endsWith('.22')) {
          _cachedServerIp = ipServidorCasaVecino;
          developer.log(
            '🏠 Red CASA (vecino): $ipServidorCasaVecino',
            name: 'Deliber API',
          );
          return _buildUrl(ipServidorCasaVecino);
        }

        // tu casa
        if (wifiIP == ipServidorCasaTuya || wifiIP.endsWith('.5')) {
          _cachedServerIp = ipServidorCasaTuya;
          developer.log(
            '🏠 Red CASA (tu casa): $ipServidorCasaTuya',
            name: 'Deliber API',
          );
          return _buildUrl(ipServidorCasaTuya);
        }

        // fallback → vecino
        _cachedServerIp = ipServidorCasaVecino;
        return _buildUrl(ipServidorCasaVecino);
      }

      // 📱 HOTSPOT
      if (wifiIP.startsWith(redHotspotPrefix)) {
        _lastDetectedNetwork = 'HOTSPOT';
        _cachedServerIp = ipServidorHotspot;
        return _buildUrl(ipServidorHotspot);
      }

      // 🏢 RED INSTITUCIONAL
      if (wifiIP.startsWith(redInstitucionalPrefix)) {
        _lastDetectedNetwork = 'INSTITUCIONAL';
        _cachedServerIp = ipServidorInstitucional;
        return _buildUrl(ipServidorInstitucional);
      }

      // ❓ DESCONOCIDA
      _lastDetectedNetwork = 'DESCONOCIDA';
      _cachedServerIp = ipServidorCasaVecino;
      return _buildUrl(ipServidorCasaVecino);
    } catch (e) {
      developer.log('❌ Error detectando red: $e', name: 'Deliber API');
      _cachedServerIp = ipServidorCasaVecino;
      _lastDetectedNetwork = 'ERROR';
      return _buildUrl(ipServidorCasaVecino);
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // 🔧 URL BUILDER
  // ════════════════════════════════════════════════════════════════════════

  static String _buildUrl(String ip) {
    return 'http://$ip:$puertoServidor';
  }

  static Future<String> getBaseUrl() async {
    const bool isProduction = bool.fromEnvironment('dart.vm.product');

    if (isProduction) return 'https://api.deliber.com';

    if (_cachedServerIp != null) return _buildUrl(_cachedServerIp!);

    return await detectServerIp();
  }

  static Future<String> refreshNetworkDetection() async {
    _cachedServerIp = null;
    _lastDetectedNetwork = null;

    developer.log('🔄 Re-detectando red...', name: 'Deliber API');

    return await detectServerIp();
  }

  // ════════════════════════════════════════════════════════════════════════
  // 🔧 MODO MANUAL
  // ════════════════════════════════════════════════════════════════════════

  static bool _forceManualIp = false;
  static String? _manualIp;

  static void setManualIp(String ip) {
    _forceManualIp = true;
    _manualIp = ip;
    _cachedServerIp = ip;

    developer.log('🔧 IP manual forzada: $ip', name: 'Deliber API');
  }

  static void disableManualIp() {
    _forceManualIp = false;
    _manualIp = null;
    _cachedServerIp = null;

    developer.log('🔄 Modo automático activado', name: 'Deliber API');
  }

  // ════════════════════════════════════════════════════════════════════════
  // 🎯 URL BASE INTELIGENTE
  // ════════════════════════════════════════════════════════════════════════

  static String get baseUrl {
    const bool isProduction = bool.fromEnvironment('dart.vm.product');

    if (isProduction) return 'https://api.deliber.com';

    if (_forceManualIp && _manualIp != null) {
      return _buildUrl(_manualIp!);
    }

    if (_cachedServerIp != null) {
      return _buildUrl(_cachedServerIp!);
    }

    return _buildUrl(ipServidorCasaVecino);
  }

  static String get apiUrl => '$baseUrl/api';

  // ════════════════════════════════════════════════════════════════════════
  // SOLICITUDES DE CAMBIO DE ROL
  // ════════════════════════════════════════════════════════════════════════

  // ─────────────────────────────────────────────
  // 👤 USUARIO – Solicitudes de Cambio de Rol
  // ─────────────────────────────────────────────

  /// GET/POST - Listar y crear mis solicitudes
  static String get usuariosSolicitudesCambioRol =>
      '$apiUrl/usuarios/solicitudes-cambio-rol/';

  /// GET - Detalle de una solicitud específica
  static String usuariosSolicitudCambioRolDetalle(String id) =>
      '$apiUrl/usuarios/solicitudes-cambio-rol/$id/';

  /// POST - Cambiar rol activo del usuario
  static String get usuariosCambiarRolActivo =>
      '$apiUrl/usuarios/cambiar-rol-activo/';

  /// GET - Obtener mis roles disponibles
  static String get usuariosMisRoles => '$apiUrl/usuarios/mis-roles/';

  // ─────────────────────────────────────────────
  // 🛡️ ADMIN – Solicitudes de Cambio de Rol
  // ─────────────────────────────────────────────

  /// GET - Listar todas las solicitudes (admin)
  static String get adminSolicitudesCambioRol =>
      '$apiUrl/admin/solicitudes-cambio-rol/';

  /// GET/PUT/PATCH/DELETE - Detalle de solicitud (admin)
  /// ✅ CORREGIDO: String (UUID) en lugar de int
  static String adminSolicitudCambioRolDetalle(String id) =>
      '$apiUrl/admin/solicitudes-cambio-rol/$id/';

  /// POST - Aceptar solicitud (admin)
  static String adminAceptarSolicitud(String id) =>
      '$apiUrl/admin/solicitudes-cambio-rol/$id/aceptar/';

  /// POST - Rechazar solicitud (admin)
  static String adminRechazarSolicitud(String id) =>
      '$apiUrl/admin/solicitudes-cambio-rol/$id/rechazar/';

  /// GET - Listar solicitudes pendientes (admin)
  static String get adminSolicitudesPendientes =>
      '$apiUrl/admin/solicitudes-cambio-rol/pendientes/';

  /// GET - Estadísticas de solicitudes (admin)
  static String get adminSolicitudesEstadisticas =>
      '$apiUrl/admin/solicitudes-cambio-rol/estadisticas/';

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 1: 📝 AUTH ENDPOINTS
  // ════════════════════════════════════════════════════════════════════════

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

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 2: 👤 USUARIOS ENDPOINTS
  // ════════════════════════════════════════════════════════════════════════

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

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 3: 🚚 REPARTIDOR ENDPOINTS
  // ════════════════════════════════════════════════════════════════════════

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

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 4: 🏪 PROVEEDORES ENDPOINTS
  // ════════════════════════════════════════════════════════════════════════

  /// GET - Listar todos los proveedores (filtrado por rol)
  /// POST - Crear proveedor (solo admin)
  static String get proveedores => '$apiUrl/proveedores/';

  /// GET - Detalle de un proveedor
  static String proveedorDetalle(int id) => '$apiUrl/proveedores/$id/';

  /// PUT - Actualizar proveedor completo
  /// PATCH - Actualizar proveedor parcial
  /// DELETE - Eliminar proveedor
  static String proveedorActualizar(int id) => '$apiUrl/proveedores/$id/';

  /// GET - Mi proveedor (usuario con rol PROVEEDOR)
  static String get miProveedor => '$apiUrl/proveedores/mi_proveedor/';

  static String get miProveedorEditarContacto =>
      '$apiUrl/proveedores/editar_contacto/';

  /// GET - Proveedores activos
  static String get proveedoresActivos => '$apiUrl/proveedores/activos/';

  /// GET - Proveedores abiertos ahora
  static String get proveedoresAbiertos => '$apiUrl/proveedores/abiertos/';

  /// GET - Filtrar por tipo (?tipo=restaurante)
  static String get proveedoresPorTipo => '$apiUrl/proveedores/por_tipo/';

  /// POST - Activar proveedor (admin only)
  static String proveedorActivar(int id) => '$apiUrl/proveedores/$id/activar/';

  /// POST - Desactivar proveedor (admin only)
  static String proveedorDesactivar(int id) =>
      '$apiUrl/proveedores/$id/desactivar/';

  /// POST - Verificar proveedor (admin only)
  static String proveedorVerificar(int id) =>
      '$apiUrl/proveedores/$id/verificar/';
  // BLOQUE 4: 🏪 PROVEEDORES ENDPOINTS

  /// Construir URL con query params
  static String buildProveedoresUrl({
    bool? activos,
    bool? verificados,
    String? tipo,
    String? ciudad,
    String? search,
  }) {
    final params = <String, String>{};

    if (activos != null) params['activos'] = activos.toString();
    if (verificados != null) params['verificados'] = verificados.toString();
    if (tipo != null) params['tipo_proveedor'] = tipo;
    if (ciudad != null) params['ciudad'] = ciudad;
    if (search != null) params['search'] = search;

    if (params.isEmpty) return proveedores;

    final queryString = params.entries
        .map((e) => '${e.key}=${Uri.encodeComponent(e.value)}')
        .join('&');

    return '$proveedores?$queryString';
  }

  /// URL para filtrar por tipo específico
  static String proveedoresPorTipoUrl(String tipo) =>
      '$proveedoresPorTipo?tipo=$tipo';

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 5: 🛡️ ADMIN ENDPOINTS - PROVEEDORES
  // ════════════════════════════════════════════════════════════════════════

  /// GET - Listar todos los proveedores (admin)
  /// Acceso: Solo administrador
  static String get adminProveedores => '$apiUrl/admin/proveedores/';

  /// GET - Detalle de un proveedor (admin)
  /// PUT - Editar información completa (admin)
  /// PATCH - Editar parcialmente (admin)
  /// DELETE - Eliminar (admin)
  static String adminProveedorDetalle(int id) =>
      '$apiUrl/admin/proveedores/$id/';

  /// PATCH - Editar CONTACTO del proveedor (email, nombre, apellido)
  /// Acceso: Solo administrador
  /// Body: {email, first_name, last_name}
  static String adminProveedorEditarContacto(int id) =>
      '$apiUrl/admin/proveedores/$id/editar_contacto/';

  /// POST - Verificar o rechazar proveedor
  /// Acceso: Solo administrador
  /// Body: {verificado: true/false, motivo: "..."}
  static String adminProveedorVerificar(int id) =>
      '$apiUrl/admin/proveedores/$id/verificar/';

  /// POST - Desactivar proveedor
  /// Acceso: Solo administrador
  static String adminProveedorDesactivar(int id) =>
      '$apiUrl/admin/proveedores/$id/desactivar/';

  /// POST - Activar proveedor
  /// Acceso: Solo administrador
  static String adminProveedorActivar(int id) =>
      '$apiUrl/admin/proveedores/$id/activar/';

  /// GET - Listar proveedores pendientes de verificación
  /// Acceso: Solo administrador
  static String get adminProveedoresPendientes =>
      '$apiUrl/admin/proveedores/pendientes/';

  // Builder para URLs admin con filtros
  static String buildAdminProveedoresUrl({
    bool? verificado,
    bool? activo,
    String? tipoProveedor,
    String? search,
  }) {
    final params = <String, String>{};

    if (verificado != null) params['verificado'] = verificado.toString();
    if (activo != null) params['activo'] = activo.toString();
    if (tipoProveedor != null) params['tipo_proveedor'] = tipoProveedor;
    if (search != null) params['search'] = search;

    if (params.isEmpty) return adminProveedores;

    final queryString = params.entries
        .map((e) => '${e.key}=${Uri.encodeComponent(e.value)}')
        .join('&');

    return '$adminProveedores?$queryString';
  }

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 6: 🛡️ ADMIN ENDPOINTS - REPARTIDORES
  // ════════════════════════════════════════════════════════════════════════

  /// GET - Listar todos los repartidores (admin)
  /// Acceso: Solo administrador
  static String get adminRepartidores => '$apiUrl/admin/repartidores/';

  /// GET - Detalle de un repartidor (admin)
  /// PUT - Editar información completa (admin)
  /// PATCH - Editar parcialmente (admin)
  /// DELETE - Eliminar (admin)
  static String adminRepartidorDetalle(int id) =>
      '$apiUrl/admin/repartidores/$id/';

  /// PATCH - Editar CONTACTO del repartidor (email, nombre, apellido)
  /// Acceso: Solo administrador
  /// Body: {email, first_name, last_name}
  static String adminRepartidorEditarContacto(int id) =>
      '$apiUrl/admin/repartidores/$id/editar_contacto/';

  /// POST - Verificar o rechazar repartidor
  /// Acceso: Solo administrador
  /// Body: {verificado: true/false, motivo: "..."}
  static String adminRepartidorVerificar(int id) =>
      '$apiUrl/admin/repartidores/$id/verificar/';

  /// POST - Desactivar repartidor
  /// Acceso: Solo administrador
  static String adminRepartidorDesactivar(int id) =>
      '$apiUrl/admin/repartidores/$id/desactivar/';

  /// POST - Activar repartidor
  /// Acceso: Solo administrador
  static String adminRepartidorActivar(int id) =>
      '$apiUrl/admin/repartidores/$id/activar/';

  /// GET - Listar repartidores pendientes de verificación
  /// Acceso: Solo administrador
  static String get adminRepartidoresPendientes =>
      '$apiUrl/admin/repartidores/pendientes/';

  // Builder para URLs admin con filtros
  static String buildAdminRepartidoresUrl({
    bool? verificado,
    bool? activo,
    String? estado,
    String? search,
  }) {
    final params = <String, String>{};

    if (verificado != null) params['verificado'] = verificado.toString();
    if (activo != null) params['activo'] = activo.toString();
    if (estado != null) params['estado'] = estado;
    if (search != null) params['search'] = search;

    if (params.isEmpty) return adminRepartidores;

    final queryString = params.entries
        .map((e) => '${e.key}=${Uri.encodeComponent(e.value)}')
        .join('&');

    return '$adminRepartidores?$queryString';
  }

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 7: 🔐 API KEYS PARA DOBLE AUTENTICACIÓN
  // ════════════════════════════════════════════════════════════════════════

  static const String apiKeyMobile =
      'mobile_app_deliber_2025_aW7xK3pM9qR5tL2nV8jH4cF6gB1dY0sZ';

  static const String apiKeyWeb =
      'web_admin_deliber_2025_XkJ9mP3nQ7wR2vL5zT8hF1cY4gN6sB0d';

  static String get currentApiKey => apiKeyMobile;

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 8: ⏱️ CONFIGURACIÓN DE TIMEOUTS
  // ════════════════════════════════════════════════════════════════════════

  static const Duration connectTimeout = Duration(seconds: 60);
  static const Duration receiveTimeout = Duration(seconds: 60);
  static const Duration sendTimeout = Duration(seconds: 60);

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 9: 📝 CONFIGURACIÓN DE RETRY
  // ════════════════════════════════════════════════════════════════════════

  static const int maxRetries = 3;
  static const Duration retryDelay = Duration(seconds: 2);

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 10: 🎯 CONFIGURACIÓN DE CÓDIGO DE RECUPERACIÓN
  // ════════════════════════════════════════════════════════════════════════

  static const int codigoLongitud = 6;
  static const int codigoExpiracionMinutos = 15;
  static const int maxIntentosVerificacion = 5;

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 11: 👥 ROLES DISPONIBLES
  // ════════════════════════════════════════════════════════════════════════

  static const String rolUsuario = 'USUARIO';
  static const String rolRepartidor = 'REPARTIDOR';
  static const String rolProveedor = 'PROVEEDOR';
  static const String rolAdministrador = 'ADMINISTRADOR';

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 12: 📊 TIPOS DE PROVEEDOR
  // ════════════════════════════════════════════════════════════════════════

  static const String tipoRestaurante = 'restaurante';
  static const String tipoFarmacia = 'farmacia';
  static const String tipoSupermercado = 'supermercado';
  static const String tipoTienda = 'tienda';
  static const String tipoOtro = 'otro';

  static const List<String> tiposProveedor = [
    tipoRestaurante,
    tipoFarmacia,
    tipoSupermercado,
    tipoTienda,
    tipoOtro,
  ];

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 13: 📊 CÓDIGOS DE RESPUESTA HTTP
  // ════════════════════════════════════════════════════════════════════════

  static const int statusOk = 200;
  static const int statusCreated = 201;
  static const int statusBadRequest = 400;
  static const int statusUnauthorized = 401;
  static const int statusForbidden = 403;
  static const int statusNotFound = 404;
  static const int statusTooManyRequests = 429;
  static const int statusServerError = 500;

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 14: ❌ MENSAJES DE ERROR
  // ════════════════════════════════════════════════════════════════════════

  static const String errorNetwork = 'Error de conexión. Verifica tu internet.';
  static const String errorTimeout =
      'La petición tardó demasiado. Intenta de nuevo.';
  static const String errorUnauthorized =
      'Sesión expirada. Inicia sesión nuevamente.';
  static const String errorServer = 'Error del servidor. Intenta más tarde.';
  static const String errorUnknown = 'Ocurrió un error inesperado.';
  static const String errorRateLimit =
      'Demasiados intentos. Espera un momento e intenta nuevamente.';

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 15: 📱 INFORMACIÓN DE DEBUG
  // ════════════════════════════════════════════════════════════════════════

  static Future<void> printDebugInfo() async {
    const bool isProduction = bool.fromEnvironment('dart.vm.product');
    final currentUrl = await getBaseUrl();

    developer.log(
      '╔════════════════════════════════════════════════════════════════╗',
      name: 'Deliber API',
    );
    developer.log('🢢 Deliber API Configuration', name: 'Deliber API');
    developer.log(
      '║ ════════════════════════════════════════════════════════════════',
      name: 'Deliber API',
    );
    developer.log(
      'Environment: ${isProduction ? "🚀 PRODUCTION" : "🛠️ DEVELOPMENT"}',
      name: 'Deliber API',
    );
    developer.log('Base URL: $currentUrl', name: 'Deliber API');
    developer.log('API URL: $apiUrl', name: 'Deliber API');

    if (_lastDetectedNetwork != null) {
      String emoji = _lastDetectedNetwork!.contains('CASA')
          ? '🏠'
          : _lastDetectedNetwork!.contains('HOTSPOT')
          ? '📱'
          : _lastDetectedNetwork!.contains('INSTITUCIONAL')
          ? '🏢'
          : '❓';
      developer.log(
        'Red Actual: $emoji $_lastDetectedNetwork',
        name: 'Deliber API',
      );
    }

    if (_cachedServerIp != null) {
      developer.log(
        'IP Servidor: $_cachedServerIp:$puertoServidor',
        name: 'Deliber API',
      );
    }

    if (_forceManualIp) {
      developer.log('🔧 Modo Manual: $_manualIp', name: 'Deliber API');
    }

    developer.log(
      'Protocol: ${currentUrl.startsWith("https") ? "🔒 HTTPS" : "🔓 HTTP"}',
      name: 'Deliber API',
    );
    developer.log(
      '║ ════════════════════════════════════════════════════════════════',
      name: 'Deliber API',
    );
    developer.log('✅ Endpoints Proveedores:', name: 'Deliber API');
    developer.log('  Mi Proveedor: $miProveedor', name: 'Deliber API');
    developer.log('  Lista: $proveedores', name: 'Deliber API');
    developer.log('  Activos: $proveedoresActivos', name: 'Deliber API');
    developer.log('✅ Endpoints Admin Proveedores:', name: 'Deliber API');
    developer.log('  Listar: $adminProveedores', name: 'Deliber API');
    developer.log(
      '  Editar Contacto: $adminProveedorEditarContacto(id)',
      name: 'Deliber API',
    );
    developer.log('✅ Endpoints Admin Repartidores:', name: 'Deliber API');
    developer.log('  Listar: $adminRepartidores', name: 'Deliber API');
    developer.log(
      '  Editar Contacto: $adminRepartidorEditarContacto(id)',
      name: 'Deliber API',
    );
    developer.log(
      '╚════════════════════════════════════════════════════════════════╝',
      name: 'Deliber API',
    );
  }

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 16: 🔧 UTILIDADES
  // ════════════════════════════════════════════════════════════════════════

  static bool get isProduction => bool.fromEnvironment('dart.vm.product');
  static bool get isDevelopment => !isProduction;
  static bool get isHttps => baseUrl.startsWith('https');
  static bool get isHttp => baseUrl.startsWith('http://');
  static String? get currentNetwork => _lastDetectedNetwork;
  static String? get currentServerIp => _cachedServerIp;
  static bool get isInitialized => _isInitialized;

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

  /// Validar horarios
  static bool validarHorarios(String? apertura, String? cierre) {
    if (apertura == null || cierre == null) return true;

    try {
      final aperturaTime = TimeOfDay(
        hour: int.parse(apertura.split(':')[0]),
        minute: int.parse(apertura.split(':')[1]),
      );

      final cierreTime = TimeOfDay(
        hour: int.parse(cierre.split(':')[0]),
        minute: int.parse(cierre.split(':')[1]),
      );

      final aperturaMinutes = aperturaTime.hour * 60 + aperturaTime.minute;
      final cierreMinutes = cierreTime.hour * 60 + cierreTime.minute;

      return cierreMinutes > aperturaMinutes;
    } catch (e) {
      return false;
    }
  }
}
