// lib/models/solicitud_cambio_rol.dart

import 'package:flutter/material.dart';

/// Modelo para solicitudes de cambio de rol
/// Usuario → PROVEEDOR o REPARTIDOR
class SolicitudCambioRol {
  // ════════════════════════════════════════════════════════════════════════
  // CAMPOS PRINCIPALES
  // ════════════════════════════════════════════════════════════════════════

  /// ID único de la solicitud (UUID)
  final String id;

  /// Email del usuario que solicita
  final String usuarioEmail;

  /// Nombre completo del usuario (opcional)
  final String? usuarioNombre;

  /// Rol solicitado: "PROVEEDOR" o "REPARTIDOR"
  final String rolSolicitado;

  /// Motivo de la solicitud (10-500 caracteres)
  final String motivo;

  /// Estado: "PENDIENTE", "ACEPTADA", "RECHAZADA"
  final String estado;

  /// Fecha de creación de la solicitud
  final DateTime creadoEn;

  /// Fecha de respuesta del admin (si ya fue procesada)
  final DateTime? respondidoEn;

  /// Email del admin que respondió (si aplica)
  final String? adminEmail;

  /// Motivo de la respuesta del admin (aceptación o rechazo)
  final String? motivoRespuesta;

  /// Días que lleva pendiente (calculado en backend)
  final int? diasPendiente;

  // ════════════════════════════════════════════════════════════════════════
  // DATOS ESPECÍFICOS DE PROVEEDOR
  // ════════════════════════════════════════════════════════════════════════

  /// RUC del negocio (13 dígitos, solo para PROVEEDOR)
  final String? ruc;

  /// Nombre comercial del negocio
  final String? nombreComercial;

  /// Tipo de negocio: "restaurante", "farmacia", "supermercado", "tienda", "otro"
  final String? tipoNegocio;

  /// Descripción detallada del negocio
  final String? descripcionNegocio;

  /// Horario de apertura (formato "HH:mm")
  final String? horarioApertura;

  /// Horario de cierre (formato "HH:mm")
  final String? horarioCierre;

  // ════════════════════════════════════════════════════════════════════════
  // DATOS ESPECÍFICOS DE REPARTIDOR
  // ════════════════════════════════════════════════════════════════════════

  /// Cédula de identidad (10-20 dígitos, solo para REPARTIDOR)
  final String? cedulaIdentidad;

  /// Tipo de vehículo: "bicicleta", "moto", "auto", "camion", "otro"
  final String? tipoVehiculo;

  /// Zona de cobertura (ej: "Centro, Sur, Norte")
  final String? zonaCobertura;

  /// Disponibilidad horaria (JSON con días y horarios)
  final Map<String, dynamic>? disponibilidad;

  // ════════════════════════════════════════════════════════════════════════
  // CONSTRUCTOR
  // ════════════════════════════════════════════════════════════════════════

  SolicitudCambioRol({
    required this.id,
    required this.usuarioEmail,
    this.usuarioNombre,
    required this.rolSolicitado,
    required this.motivo,
    required this.estado,
    required this.creadoEn,
    this.respondidoEn,
    this.adminEmail,
    this.motivoRespuesta,
    this.diasPendiente,
    // Proveedor
    this.ruc,
    this.nombreComercial,
    this.tipoNegocio,
    this.descripcionNegocio,
    this.horarioApertura,
    this.horarioCierre,
    // Repartidor
    this.cedulaIdentidad,
    this.tipoVehiculo,
    this.zonaCobertura,
    this.disponibilidad,
  });

  // ════════════════════════════════════════════════════════════════════════
  // FACTORY: DESDE JSON (Backend Django)
  // ════════════════════════════════════════════════════════════════════════

  factory SolicitudCambioRol.fromJson(Map<String, dynamic> json) {
    return SolicitudCambioRol(
      id: json['id'] as String,
      usuarioEmail: json['usuario_email'] as String,
      usuarioNombre: json['usuario_nombre'] as String?,
      rolSolicitado: json['rol_solicitado'] as String,
      motivo: json['motivo'] as String,
      estado: json['estado'] as String,
      creadoEn: DateTime.parse(json['creado_en'] as String),
      respondidoEn: json['respondido_en'] != null
          ? DateTime.parse(json['respondido_en'] as String)
          : null,
      adminEmail: json['admin_email'] as String?,
      motivoRespuesta: json['motivo_respuesta'] as String?,
      diasPendiente: json['dias_pendiente'] as int?,
      // Proveedor
      ruc: json['ruc'] as String?,
      nombreComercial: json['nombre_comercial'] as String?,
      tipoNegocio: json['tipo_negocio'] as String?,
      descripcionNegocio: json['descripcion_negocio'] as String?,
      horarioApertura: json['horario_apertura'] as String?,
      horarioCierre: json['horario_cierre'] as String?,
      // Repartidor
      cedulaIdentidad: json['cedula_identidad'] as String?,
      tipoVehiculo: json['tipo_vehiculo'] as String?,
      zonaCobertura: json['zona_cobertura'] as String?,
      disponibilidad: json['disponibilidad'] as Map<String, dynamic>?,
    );
  }

  // ════════════════════════════════════════════════════════════════════════
  // TO JSON (Para enviar al backend)
  // ════════════════════════════════════════════════════════════════════════

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'usuario_email': usuarioEmail,
      if (usuarioNombre != null) 'usuario_nombre': usuarioNombre,
      'rol_solicitado': rolSolicitado,
      'motivo': motivo,
      'estado': estado,
      'creado_en': creadoEn.toIso8601String(),
      if (respondidoEn != null)
        'respondido_en': respondidoEn!.toIso8601String(),
      if (adminEmail != null) 'admin_email': adminEmail,
      if (motivoRespuesta != null) 'motivo_respuesta': motivoRespuesta,
      if (diasPendiente != null) 'dias_pendiente': diasPendiente,
      // Proveedor
      if (ruc != null) 'ruc': ruc,
      if (nombreComercial != null) 'nombre_comercial': nombreComercial,
      if (tipoNegocio != null) 'tipo_negocio': tipoNegocio,
      if (descripcionNegocio != null) 'descripcion_negocio': descripcionNegocio,
      if (horarioApertura != null) 'horario_apertura': horarioApertura,
      if (horarioCierre != null) 'horario_cierre': horarioCierre,
      // Repartidor
      if (cedulaIdentidad != null) 'cedula_identidad': cedulaIdentidad,
      if (tipoVehiculo != null) 'tipo_vehiculo': tipoVehiculo,
      if (zonaCobertura != null) 'zona_cobertura': zonaCobertura,
      if (disponibilidad != null) 'disponibilidad': disponibilidad,
    };
  }

  // ════════════════════════════════════════════════════════════════════════
  // PROPIEDADES COMPUTADAS
  // ════════════════════════════════════════════════════════════════════════

  /// ✅ Si la solicitud está PENDIENTE
  bool get estaPendiente => estado == 'PENDIENTE';

  /// ✅ Si la solicitud fue ACEPTADA
  bool get fueAceptada => estado == 'ACEPTADA';

  /// ✅ Si la solicitud fue RECHAZADA
  bool get fueRechazada => estado == 'RECHAZADA';

  /// ✅ Si es solicitud de PROVEEDOR
  bool get esProveedor => rolSolicitado == 'PROVEEDOR';

  /// ✅ Si es solicitud de REPARTIDOR
  bool get esRepartidor => rolSolicitado == 'REPARTIDOR';

  /// 🎨 Color del badge según estado
  Color get colorEstado {
    switch (estado) {
      case 'PENDIENTE':
        return Colors.orange;
      case 'ACEPTADA':
        return Colors.green;
      case 'RECHAZADA':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  /// 🎨 Icono del badge según estado
  IconData get iconoEstado {
    switch (estado) {
      case 'PENDIENTE':
        return Icons.hourglass_empty;
      case 'ACEPTADA':
        return Icons.check_circle;
      case 'RECHAZADA':
        return Icons.cancel;
      default:
        return Icons.help_outline;
    }
  }

  /// 🎨 Texto legible del estado
  String get estadoTexto {
    switch (estado) {
      case 'PENDIENTE':
        return 'Pendiente de Revisión';
      case 'ACEPTADA':
        return 'Aceptada';
      case 'RECHAZADA':
        return 'Rechazada';
      default:
        return estado;
    }
  }

  /// 🎨 Icono según el rol solicitado
  IconData get iconoRol {
    switch (rolSolicitado) {
      case 'PROVEEDOR':
        return Icons.store;
      case 'REPARTIDOR':
        return Icons.delivery_dining;
      default:
        return Icons.person;
    }
  }

  /// 🎨 Texto legible del rol
  String get rolTexto {
    switch (rolSolicitado) {
      case 'PROVEEDOR':
        return 'Proveedor';
      case 'REPARTIDOR':
        return 'Repartidor';
      default:
        return rolSolicitado;
    }
  }

  /// 🎨 Texto legible del tipo de negocio
  String? get tipoNegocioTexto {
    if (tipoNegocio == null) return null;

    switch (tipoNegocio) {
      case 'restaurante':
        return 'Restaurante';
      case 'farmacia':
        return 'Farmacia';
      case 'supermercado':
        return 'Supermercado';
      case 'tienda':
        return 'Tienda';
      case 'otro':
        return 'Otro';
      default:
        return tipoNegocio;
    }
  }

  /// 🎨 Texto legible del tipo de vehículo
  String? get tipoVehiculoTexto {
    if (tipoVehiculo == null) return null;

    switch (tipoVehiculo) {
      case 'bicicleta':
        return 'Bicicleta';
      case 'moto':
        return 'Moto';
      case 'auto':
        return 'Auto';
      case 'camion':
        return 'Camión';
      case 'otro':
        return 'Otro';
      default:
        return tipoVehiculo;
    }
  }

  /// 📅 Fecha formateada de creación (ej: "15 Nov 2025, 14:30")
  String get fechaCreacionFormateada {
    final meses = [
      'Ene',
      'Feb',
      'Mar',
      'Abr',
      'May',
      'Jun',
      'Jul',
      'Ago',
      'Sep',
      'Oct',
      'Nov',
      'Dic',
    ];

    return '${creadoEn.day} ${meses[creadoEn.month - 1]} ${creadoEn.year}, '
        '${creadoEn.hour.toString().padLeft(2, '0')}:'
        '${creadoEn.minute.toString().padLeft(2, '0')}';
  }

  /// 📅 Fecha formateada de respuesta
  String? get fechaRespuestaFormateada {
    if (respondidoEn == null) return null;

    final meses = [
      'Ene',
      'Feb',
      'Mar',
      'Abr',
      'May',
      'Jun',
      'Jul',
      'Ago',
      'Sep',
      'Oct',
      'Nov',
      'Dic',
    ];

    return '${respondidoEn!.day} ${meses[respondidoEn!.month - 1]} ${respondidoEn!.year}, '
        '${respondidoEn!.hour.toString().padLeft(2, '0')}:'
        '${respondidoEn!.minute.toString().padLeft(2, '0')}';
  }

  /// ⏱️ Texto de días pendientes
  String? get diasPendienteTexto {
    if (diasPendiente == null) return null;

    if (diasPendiente == 0) return 'Hoy';
    if (diasPendiente == 1) return '1 día';
    return '$diasPendiente días';
  }

  // ════════════════════════════════════════════════════════════════════════
  // COPYWIDTH (Para actualizaciones inmutables)
  // ════════════════════════════════════════════════════════════════════════

  SolicitudCambioRol copyWith({
    String? id,
    String? usuarioEmail,
    String? usuarioNombre,
    String? rolSolicitado,
    String? motivo,
    String? estado,
    DateTime? creadoEn,
    DateTime? respondidoEn,
    String? adminEmail,
    String? motivoRespuesta,
    int? diasPendiente,
    // Proveedor
    String? ruc,
    String? nombreComercial,
    String? tipoNegocio,
    String? descripcionNegocio,
    String? horarioApertura,
    String? horarioCierre,
    // Repartidor
    String? cedulaIdentidad,
    String? tipoVehiculo,
    String? zonaCobertura,
    Map<String, dynamic>? disponibilidad,
  }) {
    return SolicitudCambioRol(
      id: id ?? this.id,
      usuarioEmail: usuarioEmail ?? this.usuarioEmail,
      usuarioNombre: usuarioNombre ?? this.usuarioNombre,
      rolSolicitado: rolSolicitado ?? this.rolSolicitado,
      motivo: motivo ?? this.motivo,
      estado: estado ?? this.estado,
      creadoEn: creadoEn ?? this.creadoEn,
      respondidoEn: respondidoEn ?? this.respondidoEn,
      adminEmail: adminEmail ?? this.adminEmail,
      motivoRespuesta: motivoRespuesta ?? this.motivoRespuesta,
      diasPendiente: diasPendiente ?? this.diasPendiente,
      // Proveedor
      ruc: ruc ?? this.ruc,
      nombreComercial: nombreComercial ?? this.nombreComercial,
      tipoNegocio: tipoNegocio ?? this.tipoNegocio,
      descripcionNegocio: descripcionNegocio ?? this.descripcionNegocio,
      horarioApertura: horarioApertura ?? this.horarioApertura,
      horarioCierre: horarioCierre ?? this.horarioCierre,
      // Repartidor
      cedulaIdentidad: cedulaIdentidad ?? this.cedulaIdentidad,
      tipoVehiculo: tipoVehiculo ?? this.tipoVehiculo,
      zonaCobertura: zonaCobertura ?? this.zonaCobertura,
      disponibilidad: disponibilidad ?? this.disponibilidad,
    );
  }

  // ════════════════════════════════════════════════════════════════════════
  // EQUALS Y HASHCODE (Para comparaciones)
  // ════════════════════════════════════════════════════════════════════════

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;

    return other is SolicitudCambioRol &&
        other.id == id &&
        other.usuarioEmail == usuarioEmail &&
        other.rolSolicitado == rolSolicitado &&
        other.estado == estado;
  }

  @override
  int get hashCode {
    return id.hashCode ^
        usuarioEmail.hashCode ^
        rolSolicitado.hashCode ^
        estado.hashCode;
  }

  // ════════════════════════════════════════════════════════════════════════
  // TO STRING (Para debugging)
  // ════════════════════════════════════════════════════════════════════════

  @override
  String toString() {
    return 'SolicitudCambioRol('
        'id: $id, '
        'usuario: $usuarioEmail, '
        'rol: $rolSolicitado, '
        'estado: $estado, '
        'creado: $fechaCreacionFormateada'
        ')';
  }
}

// ════════════════════════════════════════════════════════════════════════
// EXTENSIÓN: LISTA DE SOLICITUDES
// ════════════════════════════════════════════════════════════════════════

extension SolicitudesListExtension on List<SolicitudCambioRol> {
  /// Filtrar solo pendientes
  List<SolicitudCambioRol> get pendientes =>
      where((s) => s.estaPendiente).toList();

  /// Filtrar solo aceptadas
  List<SolicitudCambioRol> get aceptadas =>
      where((s) => s.fueAceptada).toList();

  /// Filtrar solo rechazadas
  List<SolicitudCambioRol> get rechazadas =>
      where((s) => s.fueRechazada).toList();

  /// Filtrar por rol
  List<SolicitudCambioRol> porRol(String rol) =>
      where((s) => s.rolSolicitado == rol).toList();

  /// Ordenar por fecha (más recientes primero)
  List<SolicitudCambioRol> ordenarPorFecha() {
    final sorted = List<SolicitudCambioRol>.from(this);
    sorted.sort((a, b) => b.creadoEn.compareTo(a.creadoEn));
    return sorted;
  }
}

// ════════════════════════════════════════════════════════════════════════
// ENUMS AUXILIARES
// ════════════════════════════════════════════════════════════════════════

/// Estados posibles de una solicitud
enum EstadoSolicitud {
  pendiente('PENDIENTE', 'Pendiente'),
  aceptada('ACEPTADA', 'Aceptada'),
  rechazada('RECHAZADA', 'Rechazada');

  final String value;
  final String label;

  const EstadoSolicitud(this.value, this.label);

  static EstadoSolicitud fromValue(String value) {
    return EstadoSolicitud.values.firstWhere(
      (e) => e.value == value,
      orElse: () => EstadoSolicitud.pendiente,
    );
  }
}

/// Roles disponibles para solicitar
enum RolSolicitable {
  proveedor('PROVEEDOR', 'Proveedor', Icons.store),
  repartidor('REPARTIDOR', 'Repartidor', Icons.delivery_dining);

  final String value;
  final String label;
  final IconData icon;

  const RolSolicitable(this.value, this.label, this.icon);

  static RolSolicitable fromValue(String value) {
    return RolSolicitable.values.firstWhere(
      (e) => e.value == value,
      orElse: () => RolSolicitable.proveedor,
    );
  }
}

/// Tipos de negocio para proveedores
enum TipoNegocio {
  restaurante('restaurante', 'Restaurante', Icons.restaurant),
  farmacia('farmacia', 'Farmacia', Icons.local_pharmacy),
  supermercado('supermercado', 'Supermercado', Icons.shopping_cart),
  tienda('tienda', 'Tienda', Icons.store),
  otro('otro', 'Otro', Icons.category);

  final String value;
  final String label;
  final IconData icon;

  const TipoNegocio(this.value, this.label, this.icon);

  static TipoNegocio fromValue(String value) {
    return TipoNegocio.values.firstWhere(
      (e) => e.value == value,
      orElse: () => TipoNegocio.otro,
    );
  }
}

/// Tipos de vehículo para repartidores
enum TipoVehiculo {
  bicicleta('bicicleta', 'Bicicleta', Icons.pedal_bike),
  moto('moto', 'Moto', Icons.two_wheeler),
  auto('auto', 'Auto', Icons.directions_car),
  camion('camion', 'Camión', Icons.local_shipping),
  otro('otro', 'Otro', Icons.commute);

  final String value;
  final String label;
  final IconData icon;

  const TipoVehiculo(this.value, this.label, this.icon);

  static TipoVehiculo fromValue(String value) {
    return TipoVehiculo.values.firstWhere(
      (e) => e.value == value,
      orElse: () => TipoVehiculo.otro,
    );
  }
}
