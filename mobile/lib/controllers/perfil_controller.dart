// lib/screens/user/perfil/perfil_controller.dart

import 'package:flutter/material.dart';
import '../models/usuario.dart';
import '../services/usuarios_service.dart';
import '../apis/helpers/api_exception.dart';
import 'dart:developer' as developer;

/// 🎮 CONTROLADOR DE PERFIL
/// Maneja toda la lógica de negocio y estado de la pantalla de perfil
/// Separado de la UI para mejor mantenimiento
/// ✅ CORRECCIÓN: Gestión mejorada de direcciones y caché
class PerfilController extends ChangeNotifier {
  // ══════════════════════════════════════════════════════════════════════════
  // 📦 DEPENDENCIAS
  // ══════════════════════════════════════════════════════════════════════════

  final UsuarioService _usuarioService = UsuarioService();

  // ══════════════════════════════════════════════════════════════════════════
  // 📊 ESTADO DE DATOS
  // ══════════════════════════════════════════════════════════════════════════

  PerfilModel? _perfil;
  List<DireccionModel>? _direcciones;
  EstadisticasModel? _estadisticas;

  // ══════════════════════════════════════════════════════════════════════════
  // 🔄 ESTADO DE CARGA Y ERRORES
  // ══════════════════════════════════════════════════════════════════════════

  bool _isLoading = false;
  bool _isLoadingPerfil = false;
  bool _isLoadingDirecciones = false;
  bool _isLoadingEstadisticas = false;

  String? _error;
  String? _errorPerfil;
  String? _errorDirecciones;
  String? _errorEstadisticas;

  // ══════════════════════════════════════════════════════════════════════════
  // 📖 GETTERS PÚBLICOS
  // ══════════════════════════════════════════════════════════════════════════

  PerfilModel? get perfil => _perfil;
  List<DireccionModel>? get direcciones => _direcciones;
  EstadisticasModel? get estadisticas => _estadisticas;

  bool get isLoading => _isLoading;
  bool get isLoadingPerfil => _isLoadingPerfil;
  bool get isLoadingDirecciones => _isLoadingDirecciones;
  bool get isLoadingEstadisticas => _isLoadingEstadisticas;

  String? get error => _error;
  String? get errorPerfil => _errorPerfil;
  String? get errorDirecciones => _errorDirecciones;
  String? get errorEstadisticas => _errorEstadisticas;

  bool get tieneError => _error != null;
  bool get tieneDatos => _perfil != null;
  bool get tieneDirecciones => _direcciones != null && _direcciones!.isNotEmpty;

  // ══════════════════════════════════════════════════════════════════════════
  // 🔧 LOGGING
  // ══════════════════════════════════════════════════════════════════════════

  void _log(String message, {Object? error, StackTrace? stackTrace}) {
    developer.log(
      message,
      name: 'PerfilController',
      error: error,
      stackTrace: stackTrace,
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📥 CARGA INICIAL COMPLETA
  // ══════════════════════════════════════════════════════════════════════════

  /// Carga todos los datos del perfil de una vez
  /// ✅ MEJORADO: Logs más detallados
  Future<void> cargarDatosCompletos({bool forzarRecarga = false}) async {
    if (_isLoading) {
      _log('⚠️ Ya hay una carga en progreso, ignorando...');
      return;
    }

    _log('═══════════════════════════════════════════════════════════════');
    _log('🚀 Iniciando carga completa de perfil...');
    _log('   forzarRecarga: $forzarRecarga');
    _log('═══════════════════════════════════════════════════════════════');

    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      // ✅ NO usar Future.wait para que los errores no bloqueen todo
      // Cargar uno por uno y continuar aunque falle alguno
      await _cargarPerfil(forzarRecarga: forzarRecarga);
      await _cargarDirecciones(forzarRecarga: forzarRecarga);
      await _cargarEstadisticas(forzarRecarga: forzarRecarga);

      _log('═══════════════════════════════════════════════════════════════');
      _log('✅ Carga completa finalizada');
      _log('   Perfil: ${_perfil != null ? "✅" : "❌"}');
      _log('   Direcciones: ${_direcciones?.length ?? 0}');
      _log('   Estadísticas: ${_estadisticas != null ? "✅" : "❌"}');
      _log('═══════════════════════════════════════════════════════════════');

      // Solo mostrar error general si TODO falló
      if (_perfil == null &&
          _estadisticas == null &&
          (_direcciones == null || _direcciones!.isEmpty)) {
        _error = 'No se pudo cargar ningún dato del perfil';
      } else {
        _error = null;
      }
    } catch (e, stackTrace) {
      _log('❌ Error en carga completa', error: e, stackTrace: stackTrace);
      _error = 'Error al cargar los datos del perfil';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 👤 CARGA DE PERFIL
  // ══════════════════════════════════════════════════════════════════════════

  Future<void> _cargarPerfil({bool forzarRecarga = false}) async {
    _isLoadingPerfil = true;
    _errorPerfil = null;
    notifyListeners();

    try {
      _log('📥 Cargando perfil... (forzar: $forzarRecarga)');
      _perfil = await _usuarioService.obtenerPerfil(
        forzarRecarga: forzarRecarga,
      );

      // 🔍 DEBUG: Verificar si el perfil está cargado
      if (_perfil != null) {
        _log('✅ Perfil cargado exitosamente');
        _log('   👤 Nombre: ${_perfil!.usuarioNombre}');
        _log('   📧 Email: ${_perfil!.usuarioEmail}');
        _log('   📱 Teléfono: ${_perfil!.telefono ?? "Sin teléfono"}');
        _log('   🖼️ Foto: ${_perfil!.fotoPerfilUrl ?? "Sin foto"}');
      } else {
        _log('⚠️ PERFIL ES NULL después de cargar');
      }
    } on ApiException catch (e) {
      _log('❌ Error API cargando perfil: ${e.message}');
      _errorPerfil = e.getUserFriendlyMessage();
    } catch (e, stackTrace) {
      _log(
        '❌ Error inesperado cargando perfil',
        error: e,
        stackTrace: stackTrace,
      );
      _errorPerfil = 'Error al cargar el perfil';
    } finally {
      _isLoadingPerfil = false;
      notifyListeners();
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📍 CARGA DE DIRECCIONES - ✅ COMPLETAMENTE CORREGIDO
  // ══════════════════════════════════════════════════════════════════════════

  /// ✅ CORRECCIÓN CRÍTICA: Limpia caché del servicio antes de recargar
  Future<void> _cargarDirecciones({bool forzarRecarga = false}) async {
    _isLoadingDirecciones = true;
    _errorDirecciones = null;

    _log('───────────────────────────────────────────────────────────────');
    _log('📍 CARGANDO DIRECCIONES');
    _log('   forzarRecarga: $forzarRecarga');
    _log(
      '   direcciones actuales en controlador: ${_direcciones?.length ?? "null"}',
    );

    // ✅ CRÍTICO: Si se fuerza recarga, limpiar caché del servicio PRIMERO
    if (forzarRecarga) {
      _log('🧹 Limpiando caché del servicio antes de recargar...');
      _usuarioService.limpiarCacheDirecciones();

      // ✅ También limpiar el estado local del controlador
      _direcciones = null;
      _log('🧹 Caché local del controlador también limpiado');
    }

    notifyListeners();

    try {
      _log('📥 Llamando a usuarioService.listarDirecciones()...');

      _direcciones = await _usuarioService.listarDirecciones(
        forzarRecarga: forzarRecarga,
      );

      _log('✅ Direcciones cargadas en controlador: ${_direcciones!.length}');

      // ✅ Log detallado de cada dirección
      if (_direcciones!.isNotEmpty) {
        _log('📋 Lista de direcciones:');
        for (var i = 0; i < _direcciones!.length; i++) {
          final dir = _direcciones![i];
          _log('   [$i] ${dir.etiqueta}: "${dir.direccion}"');
          _log('       Predeterminada: ${dir.esPredeterminada}');
          _log('       ID: ${dir.id}');
        }
      } else {
        _log('ℹ️ No hay direcciones guardadas');
      }
    } on ApiException catch (e) {
      _log('❌ Error API cargando direcciones: ${e.message}');
      _errorDirecciones = e.getUserFriendlyMessage();
      _direcciones = []; // Lista vacía en caso de error
    } catch (e, stackTrace) {
      _log(
        '❌ Error inesperado cargando direcciones',
        error: e,
        stackTrace: stackTrace,
      );
      _errorDirecciones = 'Error al cargar las direcciones';
      _direcciones = [];
    } finally {
      _isLoadingDirecciones = false;
      _log('───────────────────────────────────────────────────────────────');
      notifyListeners();
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📊 CARGA DE ESTADÍSTICAS
  // ══════════════════════════════════════════════════════════════════════════

  Future<void> _cargarEstadisticas({bool forzarRecarga = false}) async {
    _isLoadingEstadisticas = true;
    _errorEstadisticas = null;
    notifyListeners();

    try {
      _log('📥 Cargando estadísticas... (forzar: $forzarRecarga)');
      _estadisticas = await _usuarioService.obtenerEstadisticas(
        forzarRecarga: forzarRecarga,
      );
      _log('✅ Estadísticas cargadas: ${_estadisticas!.totalPedidos} pedidos');
    } on ApiException catch (e) {
      _log('❌ Error API cargando estadísticas: ${e.message}');
      _errorEstadisticas = e.getUserFriendlyMessage();
    } catch (e, stackTrace) {
      _log(
        '❌ Error inesperado cargando estadísticas',
        error: e,
        stackTrace: stackTrace,
      );
      _errorEstadisticas = 'Error al cargar las estadísticas';
    } finally {
      _isLoadingEstadisticas = false;
      notifyListeners();
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🔄 RECARGAS INDIVIDUALES - ✅ CORREGIDAS
  // ══════════════════════════════════════════════════════════════════════════

  /// Recarga solo el perfil
  Future<void> recargarPerfil() async {
    _log('🔄 Recargando perfil (forzado)...');
    await _cargarPerfil(forzarRecarga: true);
  }

  /// Recarga solo las direcciones
  /// ✅ CORRECCIÓN CRÍTICA: Ahora fuerza recarga correctamente
  Future<void> recargarDirecciones() async {
    _log('═══════════════════════════════════════════════════════════════');
    _log('🔄 RECARGANDO DIRECCIONES (FORZADO)');
    _log('═══════════════════════════════════════════════════════════════');

    // ✅ CRÍTICO: Limpiar caché del servicio ANTES de recargar
    _usuarioService.limpiarCacheDirecciones();
    _log('🧹 Caché del servicio limpiado');

    // ✅ Llamar con forzarRecarga=true
    await _cargarDirecciones(forzarRecarga: true);

    _log('═══════════════════════════════════════════════════════════════');
    _log('✅ RECARGA COMPLETADA');
    _log('   Direcciones en memoria: ${_direcciones?.length ?? 0}');
    _log('═══════════════════════════════════════════════════════════════');
  }

  /// Recarga solo las estadísticas
  Future<void> recargarEstadisticas() async {
    _log('🔄 Recargando estadísticas (forzado)...');
    await _cargarEstadisticas(forzarRecarga: true);
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🔔 ACTUALIZAR NOTIFICACIONES
  // ══════════════════════════════════════════════════════════════════════════

  /// Actualiza las preferencias de notificaciones del usuario
  Future<bool> actualizarNotificaciones({
    bool? notificacionesPedido,
    bool? notificacionesPromociones,
  }) async {
    try {
      _log('🔔 Actualizando notificaciones...');

      final datos = <String, dynamic>{};
      if (notificacionesPedido != null) {
        datos['notificaciones_pedido'] = notificacionesPedido;
      }
      if (notificacionesPromociones != null) {
        datos['notificaciones_promociones'] = notificacionesPromociones;
      }

      // Llamar al servicio para actualizar
      await _usuarioService.actualizarPerfil(datos);

      // Actualizar perfil local
      if (_perfil != null) {
        _perfil = _perfil!.copyWith(
          notificacionesPedido:
              notificacionesPedido ?? _perfil!.notificacionesPedido,
          notificacionesPromociones:
              notificacionesPromociones ?? _perfil!.notificacionesPromociones,
        );
      }

      _log('✅ Notificaciones actualizadas');
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _log('❌ Error actualizando notificaciones: ${e.message}');
      return false;
    } catch (e, stackTrace) {
      _log('❌ Error inesperado', error: e, stackTrace: stackTrace);
      return false;
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🗑️ ELIMINAR DIRECCIÓN - ✅ MEJORADO
  // ══════════════════════════════════════════════════════════════════════════

  /// ✅ MEJORADO: Ahora limpia caché y actualiza lista local correctamente
  Future<bool> eliminarDireccion(String direccionId) async {
    try {
      _log('🗑️ Eliminando dirección $direccionId...');

      // Llamar al servicio (que ya limpia su caché interno)
      await _usuarioService.eliminarDireccion(direccionId);

      // ✅ Actualizar lista local inmediatamente
      if (_direcciones != null) {
        _direcciones!.removeWhere((d) => d.id == direccionId);
        _log('✅ Dirección eliminada de la lista local');
        _log('   Direcciones restantes: ${_direcciones!.length}');
      }

      _log('✅ Dirección eliminada exitosamente');
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _log('❌ Error eliminando dirección: ${e.message}');
      _errorDirecciones = e.getUserFriendlyMessage();
      notifyListeners();
      return false;
    } catch (e, stackTrace) {
      _log(
        '❌ Error inesperado eliminando dirección',
        error: e,
        stackTrace: stackTrace,
      );
      _errorDirecciones = 'Error al eliminar la dirección';
      notifyListeners();
      return false;
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🔄 ACTUALIZAR DIRECCIÓN PREDETERMINADA - ✅ MEJORADO
  // ══════════════════════════════════════════════════════════════════════════

  /// ✅ MEJORADO: Actualiza correctamente la lista local
  Future<bool> establecerDireccionPredeterminada(String direccionId) async {
    try {
      _log('⭐ Estableciendo dirección $direccionId como predeterminada...');

      // Llamar al servicio
      await _usuarioService.actualizarDireccion(direccionId, {
        'es_predeterminada': true,
      });

      // ✅ Actualizar lista local
      if (_direcciones != null) {
        _log('🔄 Actualizando lista local de direcciones...');

        for (var i = 0; i < _direcciones!.length; i++) {
          final direccion = _direcciones![i];

          if (direccion.id == direccionId) {
            // Marcar esta como predeterminada
            _direcciones![i] = direccion.copyWith(esPredeterminada: true);
            _log('   ✓ ${direccion.etiqueta} marcada como predeterminada');
          } else if (direccion.esPredeterminada) {
            // Desmarcar otras predeterminadas
            _direcciones![i] = direccion.copyWith(esPredeterminada: false);
            _log('   - ${direccion.etiqueta} desmarcada');
          }
        }
      }

      _log('✅ Dirección predeterminada actualizada');
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _log('❌ Error actualizando dirección predeterminada: ${e.message}');
      _errorDirecciones = e.getUserFriendlyMessage();
      notifyListeners();
      return false;
    } catch (e, stackTrace) {
      _log('❌ Error inesperado', error: e, stackTrace: stackTrace);
      _errorDirecciones = 'Error al actualizar la dirección';
      notifyListeners();
      return false;
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🧹 LIMPIEZA
  // ══════════════════════════════════════════════════════════════════════════

  /// Limpia todos los datos (útil al cerrar sesión)
  void limpiar() {
    _log('🧹 Limpiando datos del controlador...');
    _perfil = null;
    _direcciones = null;
    _estadisticas = null;
    _error = null;
    _errorPerfil = null;
    _errorDirecciones = null;
    _errorEstadisticas = null;
    _isLoading = false;
    _isLoadingPerfil = false;
    _isLoadingDirecciones = false;
    _isLoadingEstadisticas = false;
    notifyListeners();
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🔍 HELPERS DE VALIDACIÓN
  // ══════════════════════════════════════════════════════════════════════════

  /// Verifica si el perfil está completo (tiene teléfono y fecha de nacimiento)
  bool get perfilCompleto {
    if (_perfil == null) return false;
    return _perfil!.tieneTelefono && _perfil!.fechaNacimiento != null;
  }

  /// Obtiene el porcentaje de completitud del perfil
  int get porcentajeCompletitud {
    if (_perfil == null) return 0;

    int completados = 0;
    const int total = 4;

    // Email y nombre siempre están (requeridos en registro)
    completados += 2;

    if (_perfil!.tieneTelefono) completados++;
    if (_perfil!.fechaNacimiento != null) completados++;

    return ((completados / total) * 100).round();
  }

  /// Obtiene el mensaje de completitud
  String get mensajeCompletitud {
    final porcentaje = porcentajeCompletitud;

    if (porcentaje == 100) {
      return '¡Perfil completo!';
    } else if (porcentaje >= 75) {
      return 'Casi listo, completa tu perfil';
    } else if (porcentaje >= 50) {
      return 'Completa tu perfil para mejor experiencia';
    } else {
      return 'Completa tu información personal';
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📊 ESTADÍSTICAS COMPUTADAS
  // ══════════════════════════════════════════════════════════════════════════

  /// Obtiene el progreso para la rifa (0.0 a 1.0)
  double get progresoRifa {
    if (_estadisticas == null) return 0.0;
    return _estadisticas!.progresoRifa;
  }

  /// Obtiene el mensaje de la rifa
  String get mensajeRifa {
    if (_estadisticas == null) return 'Cargando...';
    return _estadisticas!.mensajeRifa;
  }

  /// Verifica si puede participar en la rifa
  bool get puedeParticiparRifa {
    if (_estadisticas == null) return false;
    return _estadisticas!.puedeParticiparRifa;
  }

  /// Obtiene el nivel del cliente
  String get nivelCliente {
    if (_estadisticas == null) return '🆕 Cliente Nuevo';
    return _estadisticas!.nivelCliente;
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🔧 DEBUG
  // ══════════════════════════════════════════════════════════════════════════

  /// ✅ MEJORADO: Logs más detallados
  void imprimirEstado() {
    _log('═══════════════════════════════════════════════════════════════');
    _log('📊 ESTADO DEL CONTROLADOR DE PERFIL');
    _log('═══════════════════════════════════════════════════════════════');
    _log('🔄 Estados de carga:');
    _log('   General: $_isLoading');
    _log('   Perfil: $_isLoadingPerfil');
    _log('   Direcciones: $_isLoadingDirecciones');
    _log('   Estadísticas: $_isLoadingEstadisticas');
    _log('───────────────────────────────────────────────────────────────');
    _log('📦 Datos cargados:');
    _log(
      '   Perfil: ${_perfil != null ? "✅ ${_perfil!.usuarioNombre}" : "❌ null"}',
    );
    _log(
      '   Direcciones: ${_direcciones != null ? "✅ ${_direcciones!.length}" : "❌ null"}',
    );
    if (_direcciones != null && _direcciones!.isNotEmpty) {
      for (var dir in _direcciones!) {
        _log('      - ${dir.etiqueta}: ${dir.direccion}');
      }
    }
    _log(
      '   Estadísticas: ${_estadisticas != null ? "✅ ${_estadisticas!.totalPedidos} pedidos" : "❌ null"}',
    );
    _log('───────────────────────────────────────────────────────────────');
    _log('❌ Errores:');
    _log('   General: ${_error ?? "Sin errores"}');
    _log('   Perfil: ${_errorPerfil ?? "Sin errores"}');
    _log('   Direcciones: ${_errorDirecciones ?? "Sin errores"}');
    _log('   Estadísticas: ${_errorEstadisticas ?? "Sin errores"}');
    _log('═══════════════════════════════════════════════════════════════');
  }
}
