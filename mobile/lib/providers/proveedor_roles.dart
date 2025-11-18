// lib/providers/proveedor_roles.dart

import 'package:flutter/material.dart';
import '../services/roles_service.dart';
import '../services/auth_service.dart';

/// 🎭 Provider para gestión de roles múltiples
/// Maneja roles disponibles, rol activo y cambios entre roles
class ProveedorRoles extends ChangeNotifier {
  // ══════════════════════════════════════════════════════════════════════════════
  // 📋 ESTADO
  // ══════════════════════════════════════════════════════════════════════════════

  List<String> _rolesDisponibles = [];
  String? _rolActivo;
  bool _isLoading = false;
  String? _error;

  final _rolesService = RolesService();
  final _authService = AuthService();

  // ══════════════════════════════════════════════════════════════════════════════
  // 🔍 GETTERS
  // ══════════════════════════════════════════════════════════════════════════════

  List<String> get rolesDisponibles => _rolesDisponibles;
  String? get rolActivo => _rolActivo;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// ¿Tiene múltiples roles?
  bool get tieneMultiplesRoles => _rolesDisponibles.length > 1;

  /// ¿Puede cambiar de rol?
  bool get puedeCambiarRol => tieneMultiplesRoles && !_isLoading;

  /// Roles disponibles para cambiar (excluye el activo)
  List<String> get rolesParaCambiar {
    if (_rolActivo == null) return [];
    return _rolesDisponibles.where((r) => r != _rolActivo).toList();
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 🚀 INICIALIZACIÓN
  // ══════════════════════════════════════════════════════════════════════════════

  /// Inicializa el provider cargando roles desde el servidor
  Future<void> inicializar() async {
    debugPrint('🎭 Inicializando ProveedorRoles...');

    // Cargar rol cacheado primero
    _rolActivo = _authService.getRolCacheado();
    debugPrint('   Rol cacheado: $_rolActivo');

    // Cargar roles desde servidor
    await cargarRoles();
  }

  /// Carga los roles disponibles del usuario desde el servidor
  Future<void> cargarRoles() async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      debugPrint('📥 Cargando roles del servidor...');

      final response = await _rolesService.obtenerRolesDisponibles();

      _rolesDisponibles = List<String>.from(
        response['roles_disponibles'] ?? [],
      );
      _rolActivo = response['rol_activo'] as String?;

      debugPrint('✅ Roles cargados:');
      debugPrint('   Disponibles: $_rolesDisponibles');
      debugPrint('   Activo: $_rolActivo');

      _error = null;
    } catch (e) {
      debugPrint('❌ Error cargando roles: $e');
      _error = 'Error al cargar roles: $e';

      // Fallback: usar rol cacheado
      if (_rolActivo == null) {
        _rolActivo = _authService.getRolCacheado();
        if (_rolActivo != null) {
          _rolesDisponibles = [_rolActivo!];
        }
      }
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 🔄 CAMBIO DE ROL
  // ══════════════════════════════════════════════════════════════════════════════

  /// Cambia al rol especificado
  ///
  /// Retorna true si el cambio fue exitoso
  Future<bool> cambiarARol(String nuevoRol) async {
    if (_isLoading) {
      debugPrint('⚠️ Ya hay un cambio de rol en progreso');
      return false;
    }

    if (nuevoRol == _rolActivo) {
      debugPrint('⚠️ El rol $nuevoRol ya está activo');
      return false;
    }

    if (!_rolesDisponibles.contains(nuevoRol)) {
      debugPrint('❌ El rol $nuevoRol no está disponible');
      _error = 'El rol $nuevoRol no está disponible';
      notifyListeners();
      return false;
    }

    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      debugPrint('═══════════════════════════════════════════════════════');
      debugPrint('🔄 CAMBIANDO ROL');
      debugPrint('   De: $_rolActivo → A: $nuevoRol');
      debugPrint('═══════════════════════════════════════════════════════');

      await _rolesService.cambiarRolActivo(nuevoRol);

      // Actualizar estado local
      _rolActivo = nuevoRol;

      debugPrint('✅ Rol cambiado exitosamente a: $nuevoRol');

      _error = null;
      return true;
    } catch (e) {
      debugPrint('❌ Error cambiando rol: $e');
      _error = 'Error al cambiar rol: $e';
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 🎨 HELPERS DE UI
  // ══════════════════════════════════════════════════════════════════════════════

  /// Nombre display del rol
  String obtenerNombreRol(String rol) {
    return _rolesService.obtenerNombreRol(rol);
  }

  /// Icono del rol
  String obtenerIconoRol(String rol) {
    return _rolesService.obtenerIconoRol(rol);
  }

  /// ¿Es el rol activo?
  bool esRolActivo(String rol) {
    return rol == _rolActivo;
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 🧹 LIMPIEZA
  // ══════════════════════════════════════════════════════════════════════════════

  /// Limpia el estado del provider (al cerrar sesión)
  void limpiar() {
    _rolesDisponibles = [];
    _rolActivo = null;
    _isLoading = false;
    _error = null;
    notifyListeners();

    debugPrint('🧹 ProveedorRoles limpiado');
  }
}
