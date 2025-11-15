// lib/screens/delivery/controllers/repartidor_controller.dart

import 'package:flutter/material.dart';
import '../../../services/auth_service.dart';
import '../../../services/repartidor_service.dart';
import '../../../config/api_config.dart';
import '../../../apis/subapis/http_client.dart';
import '../../../apis/helpers/api_exception.dart';
import '../../../models/repartidor.dart';
import 'dart:developer' as developer;

/// 🎯 Controller para gestionar la lógica de negocio del repartidor
/// Separa completamente la lógica de la UI
class RepartidorController extends ChangeNotifier {
  // ============================================
  // SERVICIOS
  // ============================================
  final AuthService _authService;
  final RepartidorService _repartidorService;
  final ApiClient _apiClient;

  // ============================================
  // ESTADO
  // ============================================
  PerfilRepartidorModel? _perfil;
  EstadisticasRepartidorModel? _estadisticas;
  bool _loading = true;
  String? _error;

  // ============================================
  // GETTERS
  // ============================================
  PerfilRepartidorModel? get perfil => _perfil;
  EstadisticasRepartidorModel? get estadisticas => _estadisticas;
  bool get loading => _loading;
  String? get error => _error;
  bool get isAuthenticated => _apiClient.isAuthenticated;
  EstadoRepartidor get estadoActual =>
      _perfil?.estado ?? EstadoRepartidor.fueraServicio;
  bool get estaDisponible => estadoActual == EstadoRepartidor.disponible;

  // Estadísticas calculadas
  int get totalEntregas => _perfil?.entregasCompletadas ?? 0;
  double get rating => _perfil?.calificacionPromedio ?? 0.0;
  double get gananciasEstimadas => totalEntregas * 5.0;

  // ============================================
  // CONSTRUCTOR
  // ============================================
  RepartidorController({
    AuthService? authService,
    RepartidorService? repartidorService,
    ApiClient? apiClient,
  }) : _authService = authService ?? AuthService(),
       _repartidorService = repartidorService ?? RepartidorService(),
       _apiClient = apiClient ?? ApiClient();

  // ============================================
  // ✅ VERIFICACIÓN DE ACCESO
  // ============================================

  /// Verifica el acceso del usuario y carga los datos iniciales
  /// Retorna true si el acceso es válido, false si debe redirigir
  Future<bool> verificarAccesoYCargarDatos() async {
    _setLoading(true);
    _setError(null);

    try {
      developer.log(
        '🚀 Iniciando verificación de acceso...',
        name: 'RepartidorController',
      );

      // Verificar autenticación
      if (!_apiClient.isAuthenticated) {
        developer.log('❌ Sin autenticación', name: 'RepartidorController');
        return false;
      }

      // Verificar rol cacheado
      final rolCacheado = _apiClient.userRole;
      developer.log(
        '👤 Rol cacheado: $rolCacheado',
        name: 'RepartidorController',
      );

      if (rolCacheado != null &&
          rolCacheado.toUpperCase() != ApiConfig.rolRepartidor) {
        _setError('Acceso denegado: Rol incorrecto ($rolCacheado)');
        return false;
      }

      // Verificar con el servidor (opcional, para validación adicional)
      try {
        final info = await _apiClient.get(ApiConfig.infoRol);
        final rolServidor = info['rol'] as String?;

        if (rolServidor?.toUpperCase() != ApiConfig.rolRepartidor) {
          _setError('Acceso denegado: Rol incorrecto ($rolServidor)');
          return false;
        }
      } catch (e) {
        developer.log(
          '⚠️ No se pudo verificar con servidor, usando rol cacheado',
          name: 'RepartidorController',
          error: e,
        );

        if (rolCacheado?.toUpperCase() != ApiConfig.rolRepartidor) {
          _setError('Acceso denegado');
          return false;
        }
      }

      developer.log(
        '✅ Acceso verificado - Cargando datos...',
        name: 'RepartidorController',
      );

      await cargarDatos();
      return true;
    } catch (e, stackTrace) {
      developer.log(
        '❌ Error en verificación',
        name: 'RepartidorController',
        error: e,
        stackTrace: stackTrace,
      );

      _setError('Error al verificar acceso');
      _setLoading(false);

      return !(e is ApiException && e.isAuthError);
    }
  }

  // ============================================
  // ✅ CARGAR DATOS
  // ============================================

  /// Carga el perfil y estadísticas del repartidor
  Future<void> cargarDatos({bool forzarRecarga = true}) async {
    try {
      developer.log(
        '📥 Cargando perfil y estadísticas...',
        name: 'RepartidorController',
      );

      // Cargar en paralelo
      final results = await Future.wait([
        _repartidorService.obtenerPerfil(forzarRecarga: forzarRecarga),
        _repartidorService.obtenerEstadisticas(forzarRecarga: forzarRecarga),
      ]);

      _perfil = results[0] as PerfilRepartidorModel;
      _estadisticas = results[1] as EstadisticasRepartidorModel;
      _setError(null);
      _setLoading(false);

      developer.log(
        '✅ Datos cargados correctamente',
        name: 'RepartidorController',
      );
      developer.log('   👤 Nombre: ${_perfil!.nombreCompleto}');
      developer.log('   📊 Entregas: ${_perfil!.entregasCompletadas}');
      developer.log('   ⭐ Rating: ${_perfil!.calificacionPromedio}');
      developer.log('   🚦 Estado: ${_perfil!.estado.nombre}');
    } on ApiException catch (e) {
      developer.log(
        '❌ API Exception: ${e.message}',
        name: 'RepartidorController',
      );

      _setError(e.getUserFriendlyMessage());
      _setLoading(false);

      if (e.isAuthError) {
        rethrow; // Propagar para que la UI maneje el logout
      }
    } catch (e, stackTrace) {
      developer.log(
        '❌ Error cargando datos',
        name: 'RepartidorController',
        error: e,
        stackTrace: stackTrace,
      );

      _setError('Error al cargar información');
      _setLoading(false);
    }
  }

  // ============================================
  // ✅ CAMBIAR ESTADO (DISPONIBILIDAD)
  // ============================================

  /// Cambia el estado de disponibilidad del repartidor
  /// Retorna true si el cambio fue exitoso
  Future<bool> cambiarEstado(EstadoRepartidor nuevoEstado) async {
    try {
      developer.log(
        '🔄 Cambiando estado a: ${nuevoEstado.nombre}',
        name: 'RepartidorController',
      );

      final resultado = await _repartidorService.cambiarEstado(nuevoEstado);

      // Actualizar perfil local
      _perfil = _perfil?.copyWith(estado: nuevoEstado);
      notifyListeners();

      developer.log(
        '✅ Estado cambiado: ${resultado.estadoAnterior.nombre} → ${resultado.estadoNuevo.nombre}',
        name: 'RepartidorController',
      );

      return true;
    } on ApiException catch (e) {
      developer.log(
        '❌ Error cambiando estado: ${e.message}',
        name: 'RepartidorController',
      );
      _setError(e.getUserFriendlyMessage());
      return false;
    } catch (e) {
      developer.log(
        '❌ Error inesperado cambiando estado',
        name: 'RepartidorController',
        error: e,
      );
      _setError('Error al cambiar estado');
      return false;
    }
  }

  // ============================================
  // ✅ CERRAR SESIÓN
  // ============================================

  /// Cierra la sesión del usuario
  Future<void> cerrarSesion() async {
    try {
      await _authService.logout();
      _limpiarEstado();
    } catch (e) {
      developer.log(
        '❌ Error cerrando sesión',
        name: 'RepartidorController',
        error: e,
      );
    }
  }

  // ============================================
  // HELPERS PRIVADOS
  // ============================================

  void _setLoading(bool value) {
    _loading = value;
    notifyListeners();
  }

  void _setError(String? value) {
    _error = value;
    notifyListeners();
  }

  void _limpiarEstado() {
    _perfil = null;
    _estadisticas = null;
    _error = null;
    _loading = false;
    notifyListeners();
  }

  // ============================================
  // UTILIDADES
  // ============================================

  /// Obtiene el icono correspondiente al estado
  IconData getIconoEstado(EstadoRepartidor estado) {
    switch (estado) {
      case EstadoRepartidor.disponible:
        return Icons.check_circle;
      case EstadoRepartidor.ocupado:
        return Icons.delivery_dining;
      case EstadoRepartidor.fueraServicio:
        return Icons.pause_circle;
    }
  }

  /// Obtiene el color correspondiente al estado
  Color getColorEstado(EstadoRepartidor estado) {
    switch (estado) {
      case EstadoRepartidor.disponible:
        return const Color(0xFF4CAF50); // Verde
      case EstadoRepartidor.ocupado:
        return const Color(0xFF2196F3); // Azul
      case EstadoRepartidor.fueraServicio:
        return Colors.grey[700]!;
    }
  }

  @override
  void dispose() {
    _limpiarEstado();
    super.dispose();
  }
}
