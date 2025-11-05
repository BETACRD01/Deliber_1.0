// lib/models/repartidor.dart

import 'package:flutter/material.dart';
import '../config/api_config.dart';

// ══════════════════════════════════════════════════════════════════════════════
// 🚚 ENUMS Y CONSTANTES
// ══════════════════════════════════════════════════════════════════════════════

/// Estados posibles del repartidor
enum EstadoRepartidor {
  disponible,
  ocupado,
  fueraServicio;

  String get valor {
    switch (this) {
      case EstadoRepartidor.disponible:
        return 'disponible';
      case EstadoRepartidor.ocupado:
        return 'ocupado';
      case EstadoRepartidor.fueraServicio:
        return 'fuera_servicio';
    }
  }

  String get nombre {
    switch (this) {
      case EstadoRepartidor.disponible:
        return 'Disponible';
      case EstadoRepartidor.ocupado:
        return 'Ocupado';
      case EstadoRepartidor.fueraServicio:
        return 'Fuera de Servicio';
    }
  }

  Color get color {
    switch (this) {
      case EstadoRepartidor.disponible:
        return Colors.green;
      case EstadoRepartidor.ocupado:
        return Colors.blue;
      case EstadoRepartidor.fueraServicio:
        return Colors.red;
    }
  }

  IconData get icono {
    switch (this) {
      case EstadoRepartidor.disponible:
        return Icons.check_circle;
      case EstadoRepartidor.ocupado:
        return Icons.delivery_dining;
      case EstadoRepartidor.fueraServicio:
        return Icons.pause_circle;
    }
  }

  static EstadoRepartidor fromString(String value) {
    switch (value.toLowerCase()) {
      case 'disponible':
        return EstadoRepartidor.disponible;
      case 'ocupado':
        return EstadoRepartidor.ocupado;
      case 'fuera_servicio':
      case 'fuera servicio':
        return EstadoRepartidor.fueraServicio;
      default:
        return EstadoRepartidor.fueraServicio;
    }
  }
}

/// Tipos de vehículo
enum TipoVehiculo {
  motocicleta,
  bicicleta,
  automovil,
  camioneta,
  otro;

  String get valor {
    switch (this) {
      case TipoVehiculo.motocicleta:
        return 'motocicleta';
      case TipoVehiculo.bicicleta:
        return 'bicicleta';
      case TipoVehiculo.automovil:
        return 'automovil';
      case TipoVehiculo.camioneta:
        return 'camioneta';
      case TipoVehiculo.otro:
        return 'otro';
    }
  }

  String get nombre {
    switch (this) {
      case TipoVehiculo.motocicleta:
        return 'Motocicleta';
      case TipoVehiculo.bicicleta:
        return 'Bicicleta';
      case TipoVehiculo.automovil:
        return 'Automóvil';
      case TipoVehiculo.camioneta:
        return 'Camioneta';
      case TipoVehiculo.otro:
        return 'Otro';
    }
  }

  IconData get icono {
    switch (this) {
      case TipoVehiculo.motocicleta:
        return Icons.two_wheeler;
      case TipoVehiculo.bicicleta:
        return Icons.pedal_bike;
      case TipoVehiculo.automovil:
        return Icons.directions_car;
      case TipoVehiculo.camioneta:
        return Icons.local_shipping;
      case TipoVehiculo.otro:
        return Icons.help_outline;
    }
  }

  static TipoVehiculo fromString(String value) {
    switch (value.toLowerCase()) {
      case 'motocicleta':
        return TipoVehiculo.motocicleta;
      case 'bicicleta':
        return TipoVehiculo.bicicleta;
      case 'automovil':
      case 'automóvil':
        return TipoVehiculo.automovil;
      case 'camioneta':
        return TipoVehiculo.camioneta;
      default:
        return TipoVehiculo.otro;
    }
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// 👤 PERFIL DEL REPARTIDOR
// ══════════════════════════════════════════════════════════════════════════════

class PerfilRepartidorModel {
  final int id;
  final String nombreCompleto;
  final String email;
  final String? fotoPerfil;
  final String cedula;
  final String telefono;
  final EstadoRepartidor estado;
  final String estadoDisplay;
  final bool verificado;
  final bool activo;
  final double? latitud;
  final double? longitud;
  final DateTime? ultimaLocalizacion;
  final int entregasCompletadas;
  final double calificacionPromedio;
  final int totalCalificaciones;
  final List<VehiculoRepartidorModel> vehiculos;
  final List<CalificacionRepartidorModel> calificacionesRecientes;
  final DateTime creadoEn;
  final DateTime actualizadoEn;

  PerfilRepartidorModel({
    required this.id,
    required this.nombreCompleto,
    required this.email,
    this.fotoPerfil,
    required this.cedula,
    required this.telefono,
    required this.estado,
    required this.estadoDisplay,
    required this.verificado,
    required this.activo,
    this.latitud,
    this.longitud,
    this.ultimaLocalizacion,
    required this.entregasCompletadas,
    required this.calificacionPromedio,
    required this.totalCalificaciones,
    required this.vehiculos,
    required this.calificacionesRecientes,
    required this.creadoEn,
    required this.actualizadoEn,
  });

  factory PerfilRepartidorModel.fromJson(Map<String, dynamic> json) {
    double? parseDouble(dynamic value) {
      if (value == null) return null;
      if (value is num) return value.toDouble();
      if (value is String) return double.tryParse(value);
      return null;
    }

    int parseInt(dynamic value) {
      if (value is int) return value;
      if (value is String) return int.tryParse(value) ?? 0;
      if (value is double) return value.toInt();
      return 0;
    }

    return PerfilRepartidorModel(
      id: parseInt(json['id']),
      nombreCompleto: json['nombre_completo'] ?? '',
      email: json['email'] ?? '',
      fotoPerfil: json['foto_perfil'],
      cedula: json['cedula'] ?? '',
      telefono: json['telefono'] ?? '',
      estado: EstadoRepartidor.fromString(json['estado'] ?? 'fuera_servicio'),
      estadoDisplay: json['estado_display'] ?? '',
      verificado: json['verificado'] == true || json['verificado'] == 'true',
      activo: json['activo'] == true || json['activo'] == 'true',
      latitud: parseDouble(json['latitud']),
      longitud: parseDouble(json['longitud']),
      ultimaLocalizacion: json['ultima_localizacion'] != null
          ? DateTime.tryParse(json['ultima_localizacion'])
          : null,
      entregasCompletadas: parseInt(json['entregas_completadas']),
      calificacionPromedio: parseDouble(json['calificacion_promedio']) ?? 0.0,
      totalCalificaciones: parseInt(json['total_calificaciones']),
      vehiculos: (json['vehiculos'] is List)
          ? (json['vehiculos'] as List)
                .map(
                  (v) => VehiculoRepartidorModel.fromJson(
                    v as Map<String, dynamic>,
                  ),
                )
                .toList()
          : [],
      calificacionesRecientes: (json['calificaciones_recientes'] is List)
          ? (json['calificaciones_recientes'] as List)
                .map(
                  (c) => CalificacionRepartidorModel.fromJson(
                    c as Map<String, dynamic>,
                  ),
                )
                .toList()
          : [],
      creadoEn: DateTime.tryParse(json['creado_en'] ?? '') ?? DateTime.now(),
      actualizadoEn:
          DateTime.tryParse(json['actualizado_en'] ?? '') ?? DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'nombre_completo': nombreCompleto,
      'email': email,
      'foto_perfil': fotoPerfil,
      'cedula': cedula,
      'telefono': telefono,
      'estado': estado.valor,
      'estado_display': estadoDisplay,
      'verificado': verificado,
      'activo': activo,
      'latitud': latitud,
      'longitud': longitud,
      'ultima_localizacion': ultimaLocalizacion?.toIso8601String(),
      'entregas_completadas': entregasCompletadas,
      'calificacion_promedio': calificacionPromedio,
      'total_calificaciones': totalCalificaciones,
      'vehiculos': vehiculos.map((v) => v.toJson()).toList(),
      'calificaciones_recientes': calificacionesRecientes
          .map((c) => c.toJson())
          .toList(),
      'creado_en': creadoEn.toIso8601String(),
      'actualizado_en': actualizadoEn.toIso8601String(),
    };
  }

  /// URL completa de la foto de perfil
  String? get fotoPerfilUrl {
    if (fotoPerfil == null || fotoPerfil!.isEmpty) return null;
    if (fotoPerfil!.startsWith('http')) return fotoPerfil;
    return '${ApiConfig.baseUrl}$fotoPerfil';
  }

  /// ¿Tiene ubicación registrada?
  bool get tieneUbicacion => latitud != null && longitud != null;

  /// Vehículo activo actual
  VehiculoRepartidorModel? get vehiculoActivo {
    try {
      return vehiculos.firstWhere((v) => v.activo);
    } catch (e) {
      return null;
    }
  }

  /// ¿Puede recibir pedidos?
  bool get puedeRecibirPedidos {
    return verificado && activo && estado == EstadoRepartidor.disponible;
  }

  /// Nivel de experiencia basado en entregas
  String get nivelExperiencia {
    if (entregasCompletadas < 10) return 'Principiante';
    if (entregasCompletadas < 50) return 'Intermedio';
    if (entregasCompletadas < 200) return 'Experimentado';
    return 'Experto';
  }

  PerfilRepartidorModel copyWith({
    int? id,
    String? nombreCompleto,
    String? email,
    String? fotoPerfil,
    String? cedula,
    String? telefono,
    EstadoRepartidor? estado,
    String? estadoDisplay,
    bool? verificado,
    bool? activo,
    double? latitud,
    double? longitud,
    DateTime? ultimaLocalizacion,
    int? entregasCompletadas,
    double? calificacionPromedio,
    int? totalCalificaciones,
    List<VehiculoRepartidorModel>? vehiculos,
    List<CalificacionRepartidorModel>? calificacionesRecientes,
    DateTime? creadoEn,
    DateTime? actualizadoEn,
  }) {
    return PerfilRepartidorModel(
      id: id ?? this.id,
      nombreCompleto: nombreCompleto ?? this.nombreCompleto,
      email: email ?? this.email,
      fotoPerfil: fotoPerfil ?? this.fotoPerfil,
      cedula: cedula ?? this.cedula,
      telefono: telefono ?? this.telefono,
      estado: estado ?? this.estado,
      estadoDisplay: estadoDisplay ?? this.estadoDisplay,
      verificado: verificado ?? this.verificado,
      activo: activo ?? this.activo,
      latitud: latitud ?? this.latitud,
      longitud: longitud ?? this.longitud,
      ultimaLocalizacion: ultimaLocalizacion ?? this.ultimaLocalizacion,
      entregasCompletadas: entregasCompletadas ?? this.entregasCompletadas,
      calificacionPromedio: calificacionPromedio ?? this.calificacionPromedio,
      totalCalificaciones: totalCalificaciones ?? this.totalCalificaciones,
      vehiculos: vehiculos ?? this.vehiculos,
      calificacionesRecientes:
          calificacionesRecientes ?? this.calificacionesRecientes,
      creadoEn: creadoEn ?? this.creadoEn,
      actualizadoEn: actualizadoEn ?? this.actualizadoEn,
    );
  }

  @override
  String toString() =>
      'PerfilRepartidor(id: $id, nombre: $nombreCompleto, estado: ${estado.nombre})';
}

// ══════════════════════════════════════════════════════════════════════════════
// 🚗 VEHÍCULO DEL REPARTIDOR
// ══════════════════════════════════════════════════════════════════════════════

class VehiculoRepartidorModel {
  final int id;
  final TipoVehiculo tipo;
  final String tipoDisplay;
  final String? placa;
  final bool activo;
  final String? licenciaFoto;
  final DateTime creadoEn;

  VehiculoRepartidorModel({
    required this.id,
    required this.tipo,
    required this.tipoDisplay,
    this.placa,
    required this.activo,
    this.licenciaFoto,
    required this.creadoEn,
  });

  factory VehiculoRepartidorModel.fromJson(Map<String, dynamic> json) {
    return VehiculoRepartidorModel(
      id: json['id'] as int,
      tipo: TipoVehiculo.fromString(json['tipo'] as String),
      tipoDisplay: json['tipo_display'] as String,
      placa: json['placa'] as String?,
      activo: json['activo'] as bool,
      licenciaFoto: json['licencia_foto'] as String?,
      creadoEn: DateTime.parse(json['creado_en'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'tipo': tipo.valor,
      'tipo_display': tipoDisplay,
      'placa': placa,
      'activo': activo,
      'licencia_foto': licenciaFoto,
      'creado_en': creadoEn.toIso8601String(),
    };
  }

  /// JSON para crear/actualizar (sin campos readonly)
  Map<String, dynamic> toCreateJson() {
    return {
      'tipo': tipo.valor,
      if (placa != null && placa!.isNotEmpty) 'placa': placa,
      'activo': activo,
    };
  }

  /// URL completa de la licencia
  String? get licenciaFotoUrl {
    if (licenciaFoto == null || licenciaFoto!.isEmpty) return null;
    if (licenciaFoto!.startsWith('http')) return licenciaFoto;
    return '${ApiConfig.baseUrl}$licenciaFoto';
  }

  VehiculoRepartidorModel copyWith({
    int? id,
    TipoVehiculo? tipo,
    String? tipoDisplay,
    String? placa,
    bool? activo,
    String? licenciaFoto,
    DateTime? creadoEn,
  }) {
    return VehiculoRepartidorModel(
      id: id ?? this.id,
      tipo: tipo ?? this.tipo,
      tipoDisplay: tipoDisplay ?? this.tipoDisplay,
      placa: placa ?? this.placa,
      activo: activo ?? this.activo,
      licenciaFoto: licenciaFoto ?? this.licenciaFoto,
      creadoEn: creadoEn ?? this.creadoEn,
    );
  }

  @override
  String toString() =>
      'Vehiculo(id: $id, tipo: ${tipo.nombre}, placa: ${placa ?? "N/A"})';
}

// ══════════════════════════════════════════════════════════════════════════════
// 📊 ESTADÍSTICAS DEL REPARTIDOR
// ══════════════════════════════════════════════════════════════════════════════

class EstadisticasRepartidorModel {
  final int entregasCompletadas;
  final double calificacionPromedio;
  final int totalCalificaciones;
  final int calificaciones5Estrellas;
  final int calificaciones4Estrellas;
  final int calificaciones3Estrellas;
  final int calificaciones2Estrellas;
  final int calificaciones1Estrella;
  final double porcentaje5Estrellas;
  final EstadoRepartidor estadoActual;
  final bool verificado;
  final bool activo;

  EstadisticasRepartidorModel({
    required this.entregasCompletadas,
    required this.calificacionPromedio,
    required this.totalCalificaciones,
    required this.calificaciones5Estrellas,
    required this.calificaciones4Estrellas,
    required this.calificaciones3Estrellas,
    required this.calificaciones2Estrellas,
    required this.calificaciones1Estrella,
    required this.porcentaje5Estrellas,
    required this.estadoActual,
    required this.verificado,
    required this.activo,
  });

  factory EstadisticasRepartidorModel.fromJson(Map<String, dynamic> json) {
    final desglose = json['desglose_calificaciones'] as Map<String, dynamic>;

    return EstadisticasRepartidorModel(
      entregasCompletadas: json['entregas_completadas'] as int,
      calificacionPromedio: (json['calificacion_promedio'] as num).toDouble(),
      totalCalificaciones: json['total_calificaciones'] as int,
      calificaciones5Estrellas: desglose['5_estrellas'] as int,
      calificaciones4Estrellas: desglose['4_estrellas'] as int,
      calificaciones3Estrellas: desglose['3_estrellas'] as int,
      calificaciones2Estrellas: desglose['2_estrellas'] as int,
      calificaciones1Estrella: desglose['1_estrella'] as int,
      porcentaje5Estrellas: (json['porcentaje_5_estrellas'] as num).toDouble(),
      estadoActual: EstadoRepartidor.fromString(
        json['estado_actual'] as String,
      ),
      verificado: json['verificado'] as bool,
      activo: json['activo'] as bool,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'entregas_completadas': entregasCompletadas,
      'calificacion_promedio': calificacionPromedio,
      'total_calificaciones': totalCalificaciones,
      'desglose_calificaciones': {
        '5_estrellas': calificaciones5Estrellas,
        '4_estrellas': calificaciones4Estrellas,
        '3_estrellas': calificaciones3Estrellas,
        '2_estrellas': calificaciones2Estrellas,
        '1_estrella': calificaciones1Estrella,
      },
      'porcentaje_5_estrellas': porcentaje5Estrellas,
      'estado_actual': estadoActual.valor,
      'verificado': verificado,
      'activo': activo,
    };
  }

  @override
  String toString() =>
      'Estadisticas(entregas: $entregasCompletadas, rating: $calificacionPromedio)';
}

// ══════════════════════════════════════════════════════════════════════════════
// 📜 HISTORIAL DE ESTADO
// ══════════════════════════════════════════════════════════════════════════════

class EstadoLogModel {
  final int id;
  final EstadoRepartidor estadoAnterior;
  final String estadoAnteriorDisplay;
  final EstadoRepartidor estadoNuevo;
  final String estadoNuevoDisplay;
  final String? motivo;
  final DateTime timestamp;
  final String timestampLocal;

  EstadoLogModel({
    required this.id,
    required this.estadoAnterior,
    required this.estadoAnteriorDisplay,
    required this.estadoNuevo,
    required this.estadoNuevoDisplay,
    this.motivo,
    required this.timestamp,
    required this.timestampLocal,
  });

  factory EstadoLogModel.fromJson(Map<String, dynamic> json) {
    return EstadoLogModel(
      id: json['id'] as int,
      estadoAnterior: EstadoRepartidor.fromString(
        json['estado_anterior'] as String,
      ),
      estadoAnteriorDisplay: json['estado_anterior_display'] as String,
      estadoNuevo: EstadoRepartidor.fromString(json['estado_nuevo'] as String),
      estadoNuevoDisplay: json['estado_nuevo_display'] as String,
      motivo: json['motivo'] as String?,
      timestamp: DateTime.parse(json['timestamp'] as String),
      timestampLocal: json['timestamp_local'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'estado_anterior': estadoAnterior.valor,
      'estado_anterior_display': estadoAnteriorDisplay,
      'estado_nuevo': estadoNuevo.valor,
      'estado_nuevo_display': estadoNuevoDisplay,
      'motivo': motivo,
      'timestamp': timestamp.toIso8601String(),
      'timestamp_local': timestampLocal,
    };
  }

  @override
  String toString() =>
      'EstadoLog(${estadoAnterior.nombre} → ${estadoNuevo.nombre})';
}

// ══════════════════════════════════════════════════════════════════════════════
// 📍 HISTORIAL DE UBICACIÓN
// ══════════════════════════════════════════════════════════════════════════════

class UbicacionHistorialModel {
  final int id;
  final double latitud;
  final double longitud;
  final DateTime timestamp;

  UbicacionHistorialModel({
    required this.id,
    required this.latitud,
    required this.longitud,
    required this.timestamp,
  });

  factory UbicacionHistorialModel.fromJson(Map<String, dynamic> json) {
    return UbicacionHistorialModel(
      id: json['id'] as int,
      latitud: (json['latitud'] as num).toDouble(),
      longitud: (json['longitud'] as num).toDouble(),
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'latitud': latitud,
      'longitud': longitud,
      'timestamp': timestamp.toIso8601String(),
    };
  }

  @override
  String toString() => 'UbicacionHistorial(lat: $latitud, lon: $longitud)';
}

// ══════════════════════════════════════════════════════════════════════════════
// ⭐ CALIFICACIÓN RECIBIDA
// ══════════════════════════════════════════════════════════════════════════════

class CalificacionRepartidorModel {
  final int id;
  final String clienteNombre;
  final String clienteEmail;
  final double puntuacion;
  final String? comentario;
  final String pedidoId;
  final DateTime creadoEn;

  CalificacionRepartidorModel({
    required this.id,
    required this.clienteNombre,
    required this.clienteEmail,
    required this.puntuacion,
    this.comentario,
    required this.pedidoId,
    required this.creadoEn,
  });

  factory CalificacionRepartidorModel.fromJson(Map<String, dynamic> json) {
    return CalificacionRepartidorModel(
      id: json['id'] as int,
      clienteNombre: json['cliente_nombre'] as String,
      clienteEmail: json['cliente_email'] as String,
      puntuacion: (json['puntuacion'] as num).toDouble(),
      comentario: json['comentario'] as String?,
      pedidoId: json['pedido_id'].toString(),
      creadoEn: DateTime.parse(json['creado_en'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'cliente_nombre': clienteNombre,
      'cliente_email': clienteEmail,
      'puntuacion': puntuacion,
      'comentario': comentario,
      'pedido_id': pedidoId,
      'creado_en': creadoEn.toIso8601String(),
    };
  }

  /// ¿Es una calificación positiva? (4-5 estrellas)
  bool get esPositiva => puntuacion >= 4.0;

  /// ¿Es una calificación negativa? (1-2 estrellas)
  bool get esNegativa => puntuacion <= 2.0;

  @override
  String toString() => 'Calificacion($puntuacion⭐ por $clienteNombre)';
}

// ══════════════════════════════════════════════════════════════════════════════
// 📦 RESPUESTAS DE API (WRAPPERS)
// ══════════════════════════════════════════════════════════════════════════════

/// Respuesta de GET /api/repartidores/perfil/
class PerfilRepartidorResponse {
  final PerfilRepartidorModel perfil;

  PerfilRepartidorResponse({required this.perfil});

  factory PerfilRepartidorResponse.fromJson(Map<String, dynamic> json) {
    return PerfilRepartidorResponse(
      perfil: PerfilRepartidorModel.fromJson(json),
    );
  }
}

/// Respuesta de GET /api/repartidores/perfil/estadisticas/
class EstadisticasRepartidorResponse {
  final EstadisticasRepartidorModel estadisticas;

  EstadisticasRepartidorResponse({required this.estadisticas});

  factory EstadisticasRepartidorResponse.fromJson(Map<String, dynamic> json) {
    return EstadisticasRepartidorResponse(
      estadisticas: EstadisticasRepartidorModel.fromJson(json),
    );
  }
}

/// Respuesta de PATCH /api/repartidores/estado/
class CambioEstadoResponse {
  final String mensaje;
  final EstadoRepartidor estadoAnterior;
  final EstadoRepartidor estadoNuevo;

  CambioEstadoResponse({
    required this.mensaje,
    required this.estadoAnterior,
    required this.estadoNuevo,
  });

  factory CambioEstadoResponse.fromJson(Map<String, dynamic> json) {
    return CambioEstadoResponse(
      mensaje: json['mensaje'] as String,
      estadoAnterior: EstadoRepartidor.fromString(
        json['estado_anterior'] as String,
      ),
      estadoNuevo: EstadoRepartidor.fromString(json['estado_nuevo'] as String),
    );
  }
}

/// Respuesta de PATCH /api/repartidores/ubicacion/
class UbicacionActualizadaResponse {
  final String mensaje;
  final double latitud;
  final double longitud;
  final DateTime timestamp;

  UbicacionActualizadaResponse({
    required this.mensaje,
    required this.latitud,
    required this.longitud,
    required this.timestamp,
  });

  factory UbicacionActualizadaResponse.fromJson(Map<String, dynamic> json) {
    return UbicacionActualizadaResponse(
      mensaje: json['mensaje'] as String,
      latitud: (json['latitud'] as num).toDouble(),
      longitud: (json['longitud'] as num).toDouble(),
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }
}

/// Respuesta de GET /api/repartidores/vehiculos/
class VehiculosResponse {
  final int total;
  final List<VehiculoRepartidorModel> vehiculos;

  VehiculosResponse({required this.total, required this.vehiculos});

  factory VehiculosResponse.fromJson(Map<String, dynamic> json) {
    return VehiculosResponse(
      total: json['total'] as int,
      vehiculos: (json['vehiculos'] as List)
          .map(
            (v) => VehiculoRepartidorModel.fromJson(v as Map<String, dynamic>),
          )
          .toList(),
    );
  }
}
