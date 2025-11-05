// lib/services/ubicacion_service.dart

import 'dart:async';
import 'dart:developer' as developer;
import 'package:geolocator/geolocator.dart';
import 'repartidor_service.dart';
import '../apis/helpers/api_exception.dart';

/// Servicio de Ubicación para Repartidores
/// ✅ REFACTORIZADO: Ahora usa RepartidorService en lugar de UsuariosApi
/// ✅ Compatible con Geolocator 12.x
/// ✅ Modos: Periódico y Tiempo Real
/// ✅ Sin lógica de UI
class UbicacionService {
  // ══════════════════════════════════════════════════════════════════════════
  // SINGLETON
  // ══════════════════════════════════════════════════════════════════════════

  static final UbicacionService _instance = UbicacionService._internal();
  factory UbicacionService() => _instance;
  UbicacionService._internal();

  // ══════════════════════════════════════════════════════════════════════════
  // SERVICIOS
  // ══════════════════════════════════════════════════════════════════════════

  final _repartidorService = RepartidorService();

  // ══════════════════════════════════════════════════════════════════════════
  // ESTADO
  // ══════════════════════════════════════════════════════════════════════════

  Timer? _timer;
  StreamSubscription<Position>? _streamSubscription;
  Position? _ultimaUbicacion;
  bool _estaActivo = false;
  ModoUbicacion _modoActual = ModoUbicacion.ninguno;

  // ══════════════════════════════════════════════════════════════════════════
  // CONFIGURACIÓN
  // ══════════════════════════════════════════════════════════════════════════

  /// Intervalo para modo periódico (default: 30 segundos)
  Duration intervaloPeriodico = const Duration(seconds: 30);

  /// Distancia mínima en metros para actualizar en modo tiempo real (default: 5m)
  int distanciaMinima = 5;

  /// Precisión deseada
  LocationAccuracy precision = LocationAccuracy.high;

  // ══════════════════════════════════════════════════════════════════════════
  // CALLBACKS (opcionales para notificar a la UI)
  // ══════════════════════════════════════════════════════════════════════════

  /// Callback cuando se actualiza la ubicación exitosamente
  Function(Position)? onUbicacionActualizada;

  /// Callback cuando ocurre un error
  Function(String)? onError;

  /// Callback cuando cambia el estado del servicio
  Function(bool)? onEstadoCambiado;

  // ══════════════════════════════════════════════════════════════════════════
  // GETTERS PÚBLICOS
  // ══════════════════════════════════════════════════════════════════════════

  /// ¿El servicio está enviando ubicación?
  bool get estaActivo => _estaActivo;

  /// Modo actual de envío
  ModoUbicacion get modoActual => _modoActual;

  /// Última ubicación obtenida
  Position? get ultimaUbicacion => _ultimaUbicacion;

  /// ¿Tiene permisos de ubicación?
  Future<bool> get tienePermisos async => await _verificarPermisos();

  // ══════════════════════════════════════════════════════════════════════════
  // LOGGING
  // ══════════════════════════════════════════════════════════════════════════

  void _log(String message, {Object? error, StackTrace? stackTrace}) {
    developer.log(
      message,
      name: 'UbicacionService',
      error: error,
      stackTrace: stackTrace,
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // ✅ VALIDACIÓN DE AUTENTICACIÓN
  // ══════════════════════════════════════════════════════════════════════════

  /// Verifica que el usuario esté autenticado antes de enviar ubicación
  Future<bool> _verificarAutenticacion() async {
    try {
      _log('🔍 Verificando autenticación...');

      // Cargar tokens si no están en memoria
      await _repartidorService.client.loadTokens();

      final isAuth = _repartidorService.client.isAuthenticated;
      final token = _repartidorService.client.accessToken;

      _log('   isAuthenticated: $isAuth');
      _log('   Token presente: ${token != null}');

      if (!isAuth) {
        _log('❌ No autenticado - no se puede enviar ubicación');
        onError?.call('No estás autenticado');
        return false;
      }

      if (token != null) {
        _log('✅ Autenticación verificada');
        _log('   Token: ${token.substring(0, 20)}...');
      }

      return true;
    } catch (e, stackTrace) {
      _log(
        '❌ Error verificando autenticación',
        error: e,
        stackTrace: stackTrace,
      );
      return false;
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🔐 VERIFICACIÓN Y SOLICITUD DE PERMISOS
  // ══════════════════════════════════════════════════════════════════════════

  /// Verifica si los servicios de ubicación están habilitados
  Future<bool> _verificarServiciosActivos() async {
    try {
      final serviceEnabled = await Geolocator.isLocationServiceEnabled();

      if (!serviceEnabled) {
        _log('⚠️ Servicios de ubicación desactivados');
        onError?.call('Los servicios de ubicación están desactivados');
        return false;
      }

      return true;
    } catch (e, stackTrace) {
      _log('❌ Error verificando servicios', error: e, stackTrace: stackTrace);
      return false;
    }
  }

  /// Verifica y solicita permisos de ubicación
  Future<bool> _verificarPermisos() async {
    try {
      LocationPermission permission = await Geolocator.checkPermission();

      if (permission == LocationPermission.denied) {
        _log('⚠️ Permisos denegados, solicitando...');
        permission = await Geolocator.requestPermission();
      }

      if (permission == LocationPermission.deniedForever) {
        _log('❌ Permisos bloqueados permanentemente');
        onError?.call(
          'Los permisos de ubicación están bloqueados. '
          'Por favor, actívalos en la configuración.',
        );
        return false;
      }

      if (permission == LocationPermission.denied) {
        _log('❌ Permisos denegados por el usuario');
        onError?.call('Se requieren permisos de ubicación para continuar.');
        return false;
      }

      _log('✅ Permisos de ubicación concedidos');
      return true;
    } catch (e, stackTrace) {
      _log('❌ Error verificando permisos', error: e, stackTrace: stackTrace);
      return false;
    }
  }

  /// Solicita permisos y verifica servicios (método público)
  Future<bool> solicitarPermisos() async {
    final serviciosOk = await _verificarServiciosActivos();
    if (!serviciosOk) return false;

    return await _verificarPermisos();
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📍 OBTENER UBICACIÓN ACTUAL (UNA VEZ)
  // ══════════════════════════════════════════════════════════════════════════

  /// Obtiene la ubicación actual sin enviarla al servidor
  Future<Position?> obtenerUbicacionActual() async {
    try {
      if (!await solicitarPermisos()) {
        return null;
      }

      _log('📍 Obteniendo ubicación actual...');

      final position =
          await Geolocator.getCurrentPosition(
            desiredAccuracy: precision,
          ).timeout(
            const Duration(seconds: 10),
            onTimeout: () {
              throw TimeoutException('Timeout obteniendo ubicación');
            },
          );

      _ultimaUbicacion = position;

      _log(
        '✅ Ubicación obtenida: (${position.latitude}, ${position.longitude})',
      );

      return position;
    } catch (e, stackTrace) {
      _log('❌ Error obteniendo ubicación', error: e, stackTrace: stackTrace);
      onError?.call('Error al obtener ubicación: $e');
      return null;
    }
  }

  /// Obtiene la ubicación actual Y la envía al servidor
  Future<Position?> obtenerYEnviarUbicacion() async {
    try {
      _log('🎯 Iniciando obtención y envío de ubicación...');

      final position = await obtenerUbicacionActual();

      if (position == null) {
        _log('❌ No se pudo obtener ubicación');
        return null;
      }

      _log('📤 Enviando ubicación al servidor...');
      await _enviarUbicacionAlServidor(position);
      _log('✅ Ubicación enviada exitosamente');

      return position;
    } catch (e, stackTrace) {
      _log(
        '❌ Error obteniendo y enviando ubicación',
        error: e,
        stackTrace: stackTrace,
      );
      return null;
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🔄 MODO 1: ENVÍO PERIÓDICO
  // ══════════════════════════════════════════════════════════════════════════

  /// Inicia el envío periódico de ubicación
  /// Se ejecuta cada [intervalo] (default: 30 segundos)
  Future<bool> iniciarEnvioPeriodico({Duration? intervalo}) async {
    try {
      _log('═══════════════════════════════════════════════════════════════');
      _log('🚀 INICIANDO ENVÍO PERIÓDICO DE UBICACIÓN');
      _log('═══════════════════════════════════════════════════════════════');

      // ✅ Verificar autenticación PRIMERO
      if (!await _verificarAutenticacion()) {
        _log('❌ No se puede iniciar - usuario no autenticado');
        return false;
      }

      // Verificar permisos
      if (!await solicitarPermisos()) {
        _log('❌ No se concedieron permisos');
        return false;
      }

      // Detener cualquier modo activo
      detener();

      // Configurar intervalo
      if (intervalo != null) {
        intervaloPeriodico = intervalo;
      }

      _log('⚙️ Configuración:');
      _log('   Intervalo: ${intervaloPeriodico.inSeconds}s');
      _log('   Precisión: ${precision.name}');

      // Enviar ubicación inmediatamente
      _log('📍 Enviando ubicación inicial...');
      await obtenerYEnviarUbicacion();

      // Iniciar timer
      _timer = Timer.periodic(intervaloPeriodico, (_) async {
        await _enviarUbicacionPeriodica();
      });

      _estaActivo = true;
      _modoActual = ModoUbicacion.periodico;
      onEstadoCambiado?.call(true);

      _log('═══════════════════════════════════════════════════════════════');
      _log('✅ ENVÍO PERIÓDICO INICIADO CORRECTAMENTE');
      _log('═══════════════════════════════════════════════════════════════');
      return true;
    } catch (e, stackTrace) {
      _log(
        '❌ Error iniciando envío periódico',
        error: e,
        stackTrace: stackTrace,
      );
      onError?.call('Error al iniciar envío periódico: $e');
      return false;
    }
  }

  /// Envía ubicación de forma periódica (método privado)
  Future<void> _enviarUbicacionPeriodica() async {
    try {
      _log('⏰ [TIMER] Ejecutando envío periódico...');

      final position =
          await Geolocator.getCurrentPosition(
            desiredAccuracy: precision,
          ).timeout(
            const Duration(seconds: 10),
            onTimeout: () {
              throw TimeoutException('Timeout en ubicación periódica');
            },
          );

      _ultimaUbicacion = position;

      await _enviarUbicacionAlServidor(position);

      _log(
        '✅ [PERIÓDICO] Ubicación enviada: '
        '(${position.latitude.toStringAsFixed(5)}, '
        '${position.longitude.toStringAsFixed(5)})',
      );
    } catch (e, stackTrace) {
      _log('❌ Error en envío periódico', error: e, stackTrace: stackTrace);
      onError?.call('Error al enviar ubicación: $e');
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🌐 MODO 2: TIEMPO REAL (STREAM)
  // ══════════════════════════════════════════════════════════════════════════

  /// Inicia el rastreo en tiempo real con stream
  Future<bool> iniciarRastreoTiempoReal({
    int? distanciaMinima,
    LocationAccuracy? precision,
  }) async {
    try {
      _log('═══════════════════════════════════════════════════════════════');
      _log('🚀 INICIANDO RASTREO EN TIEMPO REAL');
      _log('═══════════════════════════════════════════════════════════════');

      // ✅ Verificar autenticación PRIMERO
      if (!await _verificarAutenticacion()) {
        _log('❌ No se puede iniciar - usuario no autenticado');
        return false;
      }

      // Verificar permisos
      if (!await solicitarPermisos()) {
        _log('❌ No se concedieron permisos');
        return false;
      }

      // Detener cualquier modo activo
      detener();

      // Configurar parámetros
      if (distanciaMinima != null) {
        this.distanciaMinima = distanciaMinima;
      }

      if (precision != null) {
        this.precision = precision;
      }

      _log('⚙️ Configuración:');
      _log('   Distancia mínima: ${this.distanciaMinima}m');
      _log('   Precisión: ${this.precision.name}');

      // Configurar settings
      final settings = LocationSettings(
        accuracy: this.precision,
        distanceFilter: this.distanciaMinima,
      );

      // Iniciar stream
      _streamSubscription =
          Geolocator.getPositionStream(locationSettings: settings).listen(
            _onNuevaUbicacionTiempoReal,
            onError: _onErrorTiempoReal,
            cancelOnError: false,
          );

      _estaActivo = true;
      _modoActual = ModoUbicacion.tiempoReal;
      onEstadoCambiado?.call(true);

      _log('═══════════════════════════════════════════════════════════════');
      _log('✅ RASTREO EN TIEMPO REAL INICIADO CORRECTAMENTE');
      _log('═══════════════════════════════════════════════════════════════');
      return true;
    } catch (e, stackTrace) {
      _log(
        '❌ Error iniciando rastreo tiempo real',
        error: e,
        stackTrace: stackTrace,
      );
      onError?.call('Error al iniciar rastreo: $e');
      return false;
    }
  }

  /// Callback cuando llega nueva ubicación en tiempo real
  void _onNuevaUbicacionTiempoReal(Position position) async {
    try {
      _ultimaUbicacion = position;

      await _enviarUbicacionAlServidor(position);

      _log(
        '📡 [TIEMPO REAL] Ubicación enviada: '
        '(${position.latitude.toStringAsFixed(5)}, '
        '${position.longitude.toStringAsFixed(5)})',
      );
    } catch (e, stackTrace) {
      _log(
        '❌ Error procesando ubicación tiempo real',
        error: e,
        stackTrace: stackTrace,
      );
      onError?.call('Error al procesar ubicación: $e');
    }
  }

  /// Callback cuando ocurre un error en el stream
  void _onErrorTiempoReal(Object error, StackTrace stackTrace) {
    _log(
      '❌ Error en stream de ubicación',
      error: error,
      stackTrace: stackTrace,
    );
    onError?.call('Error en rastreo: $error');
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📤 ENVÍO AL SERVIDOR (MÉTODO PRIVADO CENTRAL)
  // ══════════════════════════════════════════════════════════════════════════

  /// Envía la ubicación al servidor usando RepartidorService
  Future<void> _enviarUbicacionAlServidor(Position position) async {
    try {
      _log('───────────────────────────────────────────────────────────────');
      _log('📤 ENVIANDO UBICACIÓN AL SERVIDOR');
      _log('───────────────────────────────────────────────────────────────');
      _log('📍 Coordenadas:');
      _log('   Latitud: ${position.latitude}');
      _log('   Longitud: ${position.longitude}');
      _log('   Precisión: ${position.accuracy}m');
      _log('   Timestamp: ${position.timestamp}');

      // ✅ Verificar autenticación antes de cada envío
      if (!await _verificarAutenticacion()) {
        _log('⚠️ Omitiendo envío - no autenticado');
        return;
      }

      _log('📡 Llamando a RepartidorService.actualizarUbicacion()...');

      final response = await _repartidorService.actualizarUbicacion(
        latitud: position.latitude,
        longitud: position.longitude,
      );

      _log('✅ Respuesta del servidor recibida:');
      _log('   Timestamp: ${response.timestamp}');
      _log('   Latitud: ${response.latitud}');
      _log('   Longitud: ${response.longitud}');
      _log('───────────────────────────────────────────────────────────────');
      _log('✅ UBICACIÓN ENVIADA EXITOSAMENTE');
      _log('───────────────────────────────────────────────────────────────');

      // Notificar éxito
      onUbicacionActualizada?.call(position);
    } on ApiException catch (e) {
      _log('❌ Error API enviando ubicación: ${e.message}');
      _log('   Status Code: ${e.statusCode}');
      _log('   Errors: ${e.errors}');

      // ✅ Si es 401, detener el servicio
      if (e.statusCode == 401) {
        _log('🛑 Token inválido - deteniendo servicio de ubicación');
        detener();
        onError?.call('Sesión expirada - por favor inicia sesión nuevamente');
      } else {
        onError?.call('Error al enviar ubicación: ${e.message}');
      }

      rethrow;
    } catch (e, stackTrace) {
      _log(
        '❌ Error enviando ubicación al servidor',
        error: e,
        stackTrace: stackTrace,
      );
      onError?.call('Error al enviar ubicación');
      rethrow;
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🛑 DETENER ENVÍO
  // ══════════════════════════════════════════════════════════════════════════

  /// Detiene el envío de ubicación (ambos modos)
  void detener() {
    _log('🛑 Deteniendo servicio de ubicación...');

    _timer?.cancel();
    _timer = null;

    _streamSubscription?.cancel();
    _streamSubscription = null;

    final modoAnterior = _modoActual;
    _estaActivo = false;
    _modoActual = ModoUbicacion.ninguno;

    onEstadoCambiado?.call(false);

    _log('✅ Servicio detenido (modo anterior: ${modoAnterior.nombre})');
  }

  /// Pausa temporalmente el envío (puede reanudarse)
  void pausar() {
    if (!_estaActivo) {
      _log('⚠️ El servicio ya está detenido');
      return;
    }

    _log('⏸️ Pausando envío de ubicación...');

    _timer?.cancel();
    _streamSubscription?.pause();

    _estaActivo = false;
    onEstadoCambiado?.call(false);

    _log('✅ Servicio pausado');
  }

  /// Reanuda el envío después de pausar
  void reanudar() {
    if (_estaActivo) {
      _log('⚠️ El servicio ya está activo');
      return;
    }

    _log('▶️ Reanudando envío de ubicación...');

    if (_modoActual == ModoUbicacion.periodico && _timer == null) {
      // Reiniciar timer
      _timer = Timer.periodic(intervaloPeriodico, (_) async {
        await _enviarUbicacionPeriodica();
      });
    }

    if (_modoActual == ModoUbicacion.tiempoReal &&
        _streamSubscription != null) {
      _streamSubscription!.resume();
    }

    _estaActivo = true;
    onEstadoCambiado?.call(true);

    _log('✅ Servicio reanudado');
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🔧 CONFIGURACIÓN Y UTILIDADES
  // ══════════════════════════════════════════════════════════════════════════

  /// Cambia el intervalo del modo periódico (solo si está activo)
  void cambiarIntervalo(Duration nuevoIntervalo) {
    intervaloPeriodico = nuevoIntervalo;
    _log('⚙️ Intervalo actualizado: ${nuevoIntervalo.inSeconds}s');

    // Si está activo en modo periódico, reiniciar
    if (_estaActivo && _modoActual == ModoUbicacion.periodico) {
      _log('🔄 Reiniciando con nuevo intervalo...');
      iniciarEnvioPeriodico(intervalo: nuevoIntervalo);
    }
  }

  /// Cambia la distancia mínima del modo tiempo real
  void cambiarDistanciaMinima(int nuevaDistancia) {
    distanciaMinima = nuevaDistancia;
    _log('⚙️ Distancia mínima actualizada: ${nuevaDistancia}m');

    // Si está activo en modo tiempo real, reiniciar
    if (_estaActivo && _modoActual == ModoUbicacion.tiempoReal) {
      _log('🔄 Reiniciando con nueva distancia...');
      iniciarRastreoTiempoReal(distanciaMinima: nuevaDistancia);
    }
  }

  /// Cambia la precisión de ubicación
  void cambiarPrecision(LocationAccuracy nuevaPrecision) {
    precision = nuevaPrecision;
    _log('⚙️ Precisión actualizada: ${nuevaPrecision.name}');
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📊 INFORMACIÓN Y ESTADO
  // ══════════════════════════════════════════════════════════════════════════

  /// Imprime el estado actual del servicio (para debugging)
  void imprimirEstado() {
    _log('═══════════════════════════════════════════════════════════════');
    _log('📍 ESTADO DEL SERVICIO DE UBICACIÓN');
    _log('═══════════════════════════════════════════════════════════════');
    _log('🔄 Activo: $_estaActivo');
    _log('🎯 Modo: ${_modoActual.nombre}');

    if (_ultimaUbicacion != null) {
      _log('📍 Última ubicación:');
      _log('   Lat: ${_ultimaUbicacion!.latitude.toStringAsFixed(6)}');
      _log('   Lon: ${_ultimaUbicacion!.longitude.toStringAsFixed(6)}');
      _log('   Precisión: ${_ultimaUbicacion!.accuracy}m');
      _log('   Hora: ${_ultimaUbicacion!.timestamp}');
    } else {
      _log('📍 Sin ubicación registrada');
    }

    _log('⚙️ Configuración:');
    _log('   Intervalo periódico: ${intervaloPeriodico.inSeconds}s');
    _log('   Distancia mínima: ${distanciaMinima}m');
    _log('   Precisión: ${precision.name}');

    _log('═══════════════════════════════════════════════════════════════');
  }

  /// Obtiene un resumen del estado como Map
  Map<String, dynamic> obtenerEstadoResumen() {
    return {
      'activo': _estaActivo,
      'modo': _modoActual.nombre,
      'tiene_ubicacion': _ultimaUbicacion != null,
      'ultima_actualizacion': _ultimaUbicacion?.timestamp.toIso8601String(),
      'config': {
        'intervalo_segundos': intervaloPeriodico.inSeconds,
        'distancia_minima': distanciaMinima,
        'precision': precision.name,
      },
    };
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🧹 LIMPIEZA
  // ══════════════════════════════════════════════════════════════════════════

  /// Limpia todos los recursos (llamar al cerrar la app)
  void dispose() {
    _log('🧹 Limpiando UbicacionService...');
    detener();
    onUbicacionActualizada = null;
    onError = null;
    onEstadoCambiado = null;
    _ultimaUbicacion = null;
    _log('✅ UbicacionService limpiado');
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// 📦 ENUM: MODO DE UBICACIÓN
// ══════════════════════════════════════════════════════════════════════════════

enum ModoUbicacion {
  ninguno,
  periodico,
  tiempoReal;

  String get nombre {
    switch (this) {
      case ModoUbicacion.ninguno:
        return 'Ninguno';
      case ModoUbicacion.periodico:
        return 'Periódico';
      case ModoUbicacion.tiempoReal:
        return 'Tiempo Real';
    }
  }
}
