// lib/services/roles_service.dart

import '../apis/subapis/http_client.dart';
import '../config/api_config.dart';
import 'dart:developer' as developer;

/// 🎭 Servicio para gestión de roles múltiples
/// Maneja consulta y cambio de roles del usuario
class RolesService {
  // ════════════════════════════════════════════════════════════════════════
  // SINGLETON
  // ════════════════════════════════════════════════════════════════════════
  static final RolesService _instance = RolesService._internal();
  factory RolesService() => _instance;
  RolesService._internal();

  // ════════════════════════════════════════════════════════════════════════
  // CLIENTE HTTP
  // ════════════════════════════════════════════════════════════════════════
  final _client = ApiClient();

  // ════════════════════════════════════════════════════════════════════════
  // LOGGING
  // ════════════════════════════════════════════════════════════════════════
  void _log(String message, {Object? error, StackTrace? stackTrace}) {
    developer.log(
      message,
      name: 'RolesService',
      error: error,
      stackTrace: stackTrace,
    );
  }

  // ════════════════════════════════════════════════════════════════════════
  // 🎯 OBTENER ROLES DISPONIBLES
  // ════════════════════════════════════════════════════════════════════════

  /// Obtiene la lista de roles disponibles para el usuario actual
  ///
  /// Retorna:
  /// ```dart
  /// {
  ///   'roles_disponibles': ['USUARIO', 'PROVEEDOR'],
  ///   'rol_activo': 'USUARIO'
  /// }
  /// ```
  Future<Map<String, dynamic>> obtenerRolesDisponibles() async {
    try {
      _log('🎭 Obteniendo roles disponibles...');

      final response = await _client.get(ApiConfig.usuariosMisRoles);

      _log('✅ Roles obtenidos exitosamente');
      _log('   Roles disponibles: ${response['roles_disponibles']}');
      _log('   Rol activo: ${response['rol_activo']}');

      return response;
    } catch (e, stackTrace) {
      _log('❌ Error obteniendo roles', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // 🔄 CAMBIAR ROL ACTIVO
  // ════════════════════════════════════════════════════════════════════════

  /// Cambia el rol activo del usuario
  ///
  /// [nuevoRol] - Rol a activar (USUARIO, PROVEEDOR, REPARTIDOR)
  ///
  /// Retorna:
  /// ```dart
  /// {
  ///   'message': 'Rol cambiado exitosamente',
  ///   'tokens': {
  ///     'access': '...',
  ///     'refresh': '...',
  ///     'rol': 'PROVEEDOR'
  ///   }
  /// }
  /// ```
  Future<Map<String, dynamic>> cambiarRolActivo(String nuevoRol) async {
    try {
      _log('🔄 Cambiando rol activo a: $nuevoRol');

      final response = await _client.post(ApiConfig.usuariosCambiarRolActivo, {
        'rol': nuevoRol.toUpperCase(),
      });

      // ✅ Actualizar tokens con el nuevo rol
      if (response.containsKey('tokens')) {
        final tokens = response['tokens'];

        await _client.saveTokens(
          tokens['access'],
          tokens['refresh'],
          role: tokens['rol'] as String?,
          userId: _client.userId, // Mantener el mismo userId
          tokenLifetime: const Duration(hours: 12),
        );

        _log('✅ Rol cambiado exitosamente a: ${tokens['rol']}');
        _log('   Tokens actualizados');
      }

      return response;
    } catch (e, stackTrace) {
      _log('❌ Error cambiando rol', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // 🛡️ VALIDACIONES
  // ════════════════════════════════════════════════════════════════════════

  /// Verifica si un rol es válido
  bool esRolValido(String rol) {
    final rolesValidos = [
      ApiConfig.rolUsuario,
      ApiConfig.rolProveedor,
      ApiConfig.rolRepartidor,
      ApiConfig.rolAdministrador,
    ];

    return rolesValidos.contains(rol.toUpperCase());
  }

  /// Obtiene el nombre display del rol
  String obtenerNombreRol(String rol) {
    switch (rol.toUpperCase()) {
      case 'USUARIO':
        return 'Usuario';
      case 'PROVEEDOR':
        return 'Proveedor';
      case 'REPARTIDOR':
        return 'Repartidor';
      case 'ADMINISTRADOR':
        return 'Administrador';
      default:
        return rol;
    }
  }

  /// Obtiene el icono del rol
  String obtenerIconoRol(String rol) {
    switch (rol.toUpperCase()) {
      case 'USUARIO':
        return '👤';
      case 'PROVEEDOR':
        return '🏪';
      case 'REPARTIDOR':
        return '🚚';
      case 'ADMINISTRADOR':
        return '👨‍💼';
      default:
        return '❓';
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // 📊 DEBUG
  // ════════════════════════════════════════════════════════════════════════

  /// Imprime información de debug sobre roles
  void imprimirDebugRoles() {
    _log('╔══════════════════════════════════════════════════════════╗');
    _log('║  🎭 INFORMACIÓN DE ROLES                                  ║');
    _log('╟──────────────────────────────────────────────────────────╢');
    _log('║  Rol actual: ${_client.userRole ?? "null"}');
    _log('║  User ID: ${_client.userId ?? "null"}');
    _log('╚══════════════════════════════════════════════════════════╝');
  }
}
