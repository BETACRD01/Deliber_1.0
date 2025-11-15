// lib/screens/delivery/controllers/perfil_repartidor_controller.dart

import 'dart:io';
import 'package:flutter/material.dart';
import '../../../services/repartidor_service.dart';
import '../../../models/repartidor.dart';
import '../../../apis/helpers/api_exception.dart';
import 'dart:developer' as developer;

/// 🎯 Controller para la pantalla de perfil del repartidor
/// Maneja la lógica de actualización de foto y teléfono
class PerfilRepartidorController extends ChangeNotifier {
  // ============================================
  // SERVICIO
  // ============================================
  final RepartidorService _service;

  // ============================================
  // ESTADO
  // ============================================
  PerfilRepartidorModel? _perfil;
  EstadisticasRepartidorModel? _estadisticas;
  bool _loading = false;
  bool _subiendoFoto = false;
  String? _error;

  // ============================================
  // GETTERS
  // ============================================
  PerfilRepartidorModel? get perfil => _perfil;
  EstadisticasRepartidorModel? get estadisticas => _estadisticas;
  bool get loading => _loading;
  bool get subiendoFoto => _subiendoFoto;
  String? get error => _error;

  // ============================================
  // CONSTRUCTOR
  // ============================================
  PerfilRepartidorController({RepartidorService? service})
    : _service = service ?? RepartidorService();

  // ============================================
  // 📥 CARGAR PERFIL
  // ============================================

  /// Carga el perfil y estadísticas del repartidor
  Future<void> cargarPerfil({bool forzarRecarga = true}) async {
    _setLoading(true);
    _setError(null);

    try {
      developer.log('📥 Cargando perfil...', name: 'PerfilController');

      // Cargar en paralelo
      final results = await Future.wait([
        _service.obtenerPerfil(forzarRecarga: forzarRecarga),
        _service.obtenerEstadisticas(forzarRecarga: forzarRecarga),
      ]);

      _perfil = results[0] as PerfilRepartidorModel;
      _estadisticas = results[1] as EstadisticasRepartidorModel;

      developer.log('✅ Perfil cargado', name: 'PerfilController');
      _setLoading(false);
    } on ApiException catch (e) {
      developer.log('❌ Error API: ${e.message}', name: 'PerfilController');
      _setError(e.getUserFriendlyMessage());
      _setLoading(false);
    } catch (e, stackTrace) {
      developer.log(
        '❌ Error inesperado',
        name: 'PerfilController',
        error: e,
        stackTrace: stackTrace,
      );
      _setError('Error al cargar perfil');
      _setLoading(false);
    }
  }

  // ============================================
  // 📸 ACTUALIZAR FOTO DE PERFIL
  // ============================================

  /// Actualiza la foto de perfil del repartidor
  Future<bool> actualizarFotoPerfil(File foto) async {
    _setSubiendoFoto(true);
    _setError(null);

    try {
      developer.log('📸 Subiendo foto...', name: 'PerfilController');

      // Validar tamaño del archivo
      final fileSize = await foto.length();
      final fileSizeInMB = fileSize / (1024 * 1024);

      if (fileSizeInMB > 5) {
        throw Exception('La imagen es muy grande (máx 5MB)');
      }

      // Actualizar perfil con la nueva foto
      final perfilActualizado = await _service.actualizarPerfil(
        fotoPerfil: foto,
      );

      _perfil = perfilActualizado;

      developer.log('✅ Foto actualizada', name: 'PerfilController');
      _setSubiendoFoto(false);
      return true;
    } on ApiException catch (e) {
      developer.log(
        '❌ Error API subiendo foto: ${e.message}',
        name: 'PerfilController',
      );
      _setError(e.getUserFriendlyMessage());
      _setSubiendoFoto(false);
      return false;
    } catch (e, stackTrace) {
      developer.log(
        '❌ Error subiendo foto',
        name: 'PerfilController',
        error: e,
        stackTrace: stackTrace,
      );
      _setError('Error al subir foto: ${e.toString()}');
      _setSubiendoFoto(false);
      return false;
    }
  }

  // ============================================
  // 🗑️ ELIMINAR FOTO DE PERFIL
  // ============================================

  /// Elimina la foto de perfil del repartidor
  Future<bool> eliminarFotoPerfil() async {
    _setSubiendoFoto(true);
    _setError(null);

    try {
      developer.log('🗑️ Eliminando foto...', name: 'PerfilController');

      // Llamar al servicio para eliminar la foto
      final perfilActualizado = await _service.eliminarFotoPerfil();

      _perfil = perfilActualizado;

      developer.log('✅ Foto eliminada', name: 'PerfilController');
      _setSubiendoFoto(false);
      return true;
    } on ApiException catch (e) {
      developer.log(
        '❌ Error API eliminando foto: ${e.message}',
        name: 'PerfilController',
      );
      _setError(e.getUserFriendlyMessage());
      _setSubiendoFoto(false);
      return false;
    } catch (e, stackTrace) {
      developer.log(
        '❌ Error eliminando foto',
        name: 'PerfilController',
        error: e,
        stackTrace: stackTrace,
      );
      _setError('Error al eliminar foto: ${e.toString()}');
      _setSubiendoFoto(false);
      return false;
    }
  }

  // ============================================
  // 📞 ACTUALIZAR TELÉFONO
  // ============================================

  /// Actualiza el teléfono del repartidor
  Future<bool> actualizarTelefono(String telefono) async {
    _setLoading(true);
    _setError(null);

    try {
      developer.log('📞 Actualizando teléfono...', name: 'PerfilController');

      // Validar formato de teléfono
      if (telefono.isEmpty || telefono.length < 7) {
        throw Exception('Teléfono inválido');
      }

      // Actualizar perfil con el nuevo teléfono
      final perfilActualizado = await _service.actualizarPerfil(
        telefono: telefono,
      );

      _perfil = perfilActualizado;

      developer.log('✅ Teléfono actualizado', name: 'PerfilController');
      _setLoading(false);
      return true;
    } on ApiException catch (e) {
      developer.log(
        '❌ Error API actualizando teléfono: ${e.message}',
        name: 'PerfilController',
      );
      _setError(e.getUserFriendlyMessage());
      _setLoading(false);
      return false;
    } catch (e, stackTrace) {
      developer.log(
        '❌ Error actualizando teléfono',
        name: 'PerfilController',
        error: e,
        stackTrace: stackTrace,
      );
      _setError('Error al actualizar teléfono: ${e.toString()}');
      _setLoading(false);
      return false;
    }
  }

  // ============================================
  // 🔄 ACTUALIZAR FOTO Y TELÉFONO JUNTOS
  // ============================================

  /// Actualiza foto y teléfono en una sola petición
  Future<bool> actualizarPerfilCompleto({File? foto, String? telefono}) async {
    if (foto == null && telefono == null) {
      _setError('No hay cambios para guardar');
      return false;
    }

    _setLoading(true);
    _setError(null);

    try {
      developer.log(
        '🔄 Actualizando perfil completo...',
        name: 'PerfilController',
      );

      final perfilActualizado = await _service.actualizarPerfil(
        fotoPerfil: foto,
        telefono: telefono,
      );

      _perfil = perfilActualizado;

      developer.log('✅ Perfil actualizado', name: 'PerfilController');
      _setLoading(false);
      return true;
    } on ApiException catch (e) {
      developer.log('❌ Error API: ${e.message}', name: 'PerfilController');
      _setError(e.getUserFriendlyMessage());
      _setLoading(false);
      return false;
    } catch (e, stackTrace) {
      developer.log(
        '❌ Error actualizando perfil',
        name: 'PerfilController',
        error: e,
        stackTrace: stackTrace,
      );
      _setError('Error al actualizar perfil');
      _setLoading(false);
      return false;
    }
  }

  // ============================================
  // HELPERS PRIVADOS
  // ============================================

  void _setLoading(bool value) {
    _loading = value;
    notifyListeners();
  }

  void _setSubiendoFoto(bool value) {
    _subiendoFoto = value;
    notifyListeners();
  }

  void _setError(String? value) {
    _error = value;
    notifyListeners();
  }

  // ============================================
  // LIMPIEZA
  // ============================================

  @override
  void dispose() {
    _perfil = null;
    _estadisticas = null;
    _error = null;
    super.dispose();
  }
}
