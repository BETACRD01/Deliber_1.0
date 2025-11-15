// lib/models/proveedor_model.dart

import 'dart:developer' as developer;

/// Modelo de Proveedor basado en ProveedorSerializer de Django
/// Incluye datos del usuario vinculado y campos calculados
/// ✅ MEJORADO: Defensas contra valores null y tipos incorrectos
/// ✅ ACTUALIZADO: Métodos para editar contacto (admin)
class ProveedorModel {
  // ════════════════════════════════════════════════════════════════════════
  // IDENTIFICACIÓN
  // ════════════════════════════════════════════════════════════════════════
  final int id;
  final int? userId;

  // ════════════════════════════════════════════════════════════════════════
  // INFORMACIÓN BÁSICA
  // ════════════════════════════════════════════════════════════════════════
  final String nombre;
  final String ruc;
  final String tipoProveedor;
  final String? descripcion;

  // ════════════════════════════════════════════════════════════════════════
  // ✅ DATOS DEL USUARIO VINCULADO (READ-ONLY)
  // ════════════════════════════════════════════════════════════════════════
  final String? emailUsuario;
  final String? celularUsuario;
  final String? nombreCompleto;
  final bool verificado;

  // ════════════════════════════════════════════════════════════════════════
  // ⚠️ CAMPOS DEPRECADOS (Mantener por compatibilidad)
  // ════════════════════════════════════════════════════════════════════════
  final String? email;
  final String? telefono;

  // ════════════════════════════════════════════════════════════════════════
  // UBICACIÓN
  // ════════════════════════════════════════════════════════════════════════
  final String? direccion;
  final String? ciudad;
  final double? latitud;
  final double? longitud;

  // ════════════════════════════════════════════════════════════════════════
  // CONFIGURACIÓN
  // ════════════════════════════════════════════════════════════════════════
  final bool activo;
  final double comisionPorcentaje;

  // ════════════════════════════════════════════════════════════════════════
  // HORARIOS
  // ════════════════════════════════════════════════════════════════════════
  final String? horarioApertura;
  final String? horarioCierre;
  final bool? estaAbierto;

  // ════════════════════════════════════════════════════════════════════════
  // MULTIMEDIA
  // ════════════════════════════════════════════════════════════════════════
  final String? logo;
  final String? logoUrl;

  // ════════════════════════════════════════════════════════════════════════
  // AUDITORÍA
  // ════════════════════════════════════════════════════════════════════════
  final DateTime createdAt;
  final DateTime updatedAt;

  // ════════════════════════════════════════════════════════════════════════
  // METADATA (Opcional, de to_representation)
  // ════════════════════════════════════════════════════════════════════════
  final String? warning;

  // ════════════════════════════════════════════════════════════════════════
  // CONSTRUCTOR
  // ════════════════════════════════════════════════════════════════════════
  ProveedorModel({
    required this.id,
    this.userId,
    required this.nombre,
    required this.ruc,
    required this.tipoProveedor,
    this.descripcion,
    this.emailUsuario,
    this.celularUsuario,
    this.nombreCompleto,
    required this.verificado,
    this.email,
    this.telefono,
    this.direccion,
    this.ciudad,
    this.latitud,
    this.longitud,
    required this.activo,
    required this.comisionPorcentaje,
    this.horarioApertura,
    this.horarioCierre,
    this.estaAbierto,
    this.logo,
    this.logoUrl,
    required this.createdAt,
    required this.updatedAt,
    this.warning,
  });

  // ════════════════════════════════════════════════════════════════════════
  // FROM JSON (Deserialización desde API) - ✅ CON DEFENSAS
  // ════════════════════════════════════════════════════════════════════════
  factory ProveedorModel.fromJson(Map<String, dynamic> json) {
    try {
      developer.log(
        '📝 Parseando ProveedorModel desde JSON',
        name: 'ProveedorModel',
      );

      // ✅ DEFENSA: Validar campo requerido 'id'
      final id = json['id'];
      if (id == null) {
        throw FormatException('❌ Campo requerido "id" es null');
      }

      final idInt = _toInt(id);
      if (idInt == null) {
        throw FormatException('❌ Campo "id" no puede convertirse a int: $id');
      }

      final nombre = _toString(json['nombre']) ?? 'Sin nombre';
      final ruc = _toString(json['ruc']) ?? 'N/A';
      final tipoProveedor = _toString(json['tipo_proveedor']) ?? 'otro';

      return ProveedorModel(
        // Identificación
        id: idInt,
        userId: _toInt(json['user_id']),

        // Información básica
        nombre: nombre,
        ruc: ruc,
        tipoProveedor: tipoProveedor,
        descripcion: _toString(json['descripcion']),

        // ✅ Datos del usuario vinculado
        emailUsuario: _toString(json['email_usuario']),
        celularUsuario: _toString(json['celular_usuario']),
        nombreCompleto: _toString(json['nombre_completo']),
        verificado: _toBool(json['verificado']) ?? false,

        // ⚠️ Campos deprecados
        email: _toString(json['email']),
        telefono: _toString(json['telefono']),

        // Ubicación
        direccion: _toString(json['direccion']),
        ciudad: _toString(json['ciudad']),
        latitud: _parseDouble(json['latitud']),
        longitud: _parseDouble(json['longitud']),

        // Configuración
        activo: _toBool(json['activo']) ?? true,
        comisionPorcentaje: _parseDouble(json['comision_porcentaje']) ?? 10.0,

        // Horarios
        horarioApertura: _toString(json['horario_apertura']),
        horarioCierre: _toString(json['horario_cierre']),
        estaAbierto: _toBool(json['esta_abierto']),

        // Multimedia
        logo: _toString(json['logo']),
        logoUrl: _toString(json['logo_url']),

        // Auditoría
        createdAt: _parseDateTime(json['created_at']) ?? DateTime.now(),
        updatedAt: _parseDateTime(json['updated_at']) ?? DateTime.now(),

        // Metadata
        warning: _toString(json['_warning']),
      );
    } catch (e, stackTrace) {
      developer.log(
        '❌ Error parseando ProveedorModel: $e',
        name: 'ProveedorModel',
        error: e,
        stackTrace: stackTrace,
      );
      developer.log('📄 JSON recibido completo: $json', name: 'ProveedorModel');
      rethrow;
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // TO JSON (Serialización para enviar a API)
  // ════════════════════════════════════════════════════════════════════════
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'nombre': nombre,
      'ruc': ruc,
      'tipo_proveedor': tipoProveedor,
      'descripcion': descripcion,
      'direccion': direccion,
      'ciudad': ciudad,
      'latitud': latitud,
      'longitud': longitud,
      'activo': activo,
      'comision_porcentaje': comisionPorcentaje,
      'horario_apertura': horarioApertura,
      'horario_cierre': horarioCierre,
      'logo': logo,
    };
  }

  // ════════════════════════════════════════════════════════════════════════
  // TO JSON ACTUALIZAR (Solo campos editables)
  // ════════════════════════════════════════════════════════════════════════
  Map<String, dynamic> toJsonUpdate() {
    final data = <String, dynamic>{};

    data['nombre'] = nombre;
    data['tipo_proveedor'] = tipoProveedor;
    data['ruc'] = ruc;
    data['telefono'] = telefono;

    if (descripcion != null) data['descripcion'] = descripcion;
    if (direccion != null) data['direccion'] = direccion;
    if (ciudad != null) data['ciudad'] = ciudad;
    if (horarioApertura != null) data['horario_apertura'] = horarioApertura;
    if (horarioCierre != null) data['horario_cierre'] = horarioCierre;
    if (latitud != null) data['latitud'] = latitud;
    if (longitud != null) data['longitud'] = longitud;

    return data;
  }

  // ════════════════════════════════════════════════════════════════════════
  // ✅ TO JSON EDITAR CONTACTO (Admin - NUEVO)
  // ════════════════════════════════════════════════════════════════════════
  /// Serializa solo los campos de contacto del usuario vinculado
  /// Usado por: PATCH /api/admin/proveedores/{id}/editar_contacto/
  Map<String, dynamic> toJsonEditarContacto({
    String? email,
    String? firstName,
    String? lastName,
  }) {
    final data = <String, dynamic>{};

    if (email != null) data['email'] = email;
    if (firstName != null) data['first_name'] = firstName;
    if (lastName != null) data['last_name'] = lastName;

    return data;
  }

  // ════════════════════════════════════════════════════════════════════════
  // COPY WITH
  // ════════════════════════════════════════════════════════════════════════
  ProveedorModel copyWith({
    int? id,
    int? userId,
    String? nombre,
    String? ruc,
    String? tipoProveedor,
    String? descripcion,
    String? emailUsuario,
    String? celularUsuario,
    String? nombreCompleto,
    bool? verificado,
    String? email,
    String? telefono,
    String? direccion,
    String? ciudad,
    double? latitud,
    double? longitud,
    bool? activo,
    double? comisionPorcentaje,
    String? horarioApertura,
    String? horarioCierre,
    bool? estaAbierto,
    String? logo,
    String? logoUrl,
    DateTime? createdAt,
    DateTime? updatedAt,
    String? warning,
  }) {
    return ProveedorModel(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      nombre: nombre ?? this.nombre,
      ruc: ruc ?? this.ruc,
      tipoProveedor: tipoProveedor ?? this.tipoProveedor,
      descripcion: descripcion ?? this.descripcion,
      emailUsuario: emailUsuario ?? this.emailUsuario,
      celularUsuario: celularUsuario ?? this.celularUsuario,
      nombreCompleto: nombreCompleto ?? this.nombreCompleto,
      verificado: verificado ?? this.verificado,
      email: email ?? this.email,
      telefono: telefono ?? this.telefono,
      direccion: direccion ?? this.direccion,
      ciudad: ciudad ?? this.ciudad,
      latitud: latitud ?? this.latitud,
      longitud: longitud ?? this.longitud,
      activo: activo ?? this.activo,
      comisionPorcentaje: comisionPorcentaje ?? this.comisionPorcentaje,
      horarioApertura: horarioApertura ?? this.horarioApertura,
      horarioCierre: horarioCierre ?? this.horarioCierre,
      estaAbierto: estaAbierto ?? this.estaAbierto,
      logo: logo ?? this.logo,
      logoUrl: logoUrl ?? this.logoUrl,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      warning: warning ?? this.warning,
    );
  }

  // ════════════════════════════════════════════════════════════════════════
  // GETTERS ÚTILES
  // ════════════════════════════════════════════════════════════════════════

  String? get emailActual => emailUsuario ?? email;
  String? get celularActual => celularUsuario ?? telefono;
  bool get tieneUsuarioVinculado => userId != null;

  bool get estaSincronizado {
    if (!tieneUsuarioVinculado) return true;
    return emailUsuario == email && celularUsuario == telefono;
  }

  String get tipoProveedorDisplay {
    switch (tipoProveedor) {
      case 'restaurante':
        return '🍽️ Restaurante';
      case 'farmacia':
        return '💊 Farmacia';
      case 'supermercado':
        return '🛒 Supermercado';
      case 'tienda':
        return '🏪 Tienda';
      case 'otro':
        return '📦 Otro';
      default:
        return tipoProveedor;
    }
  }

  String get estadoDisplay {
    if (!activo) return '❌ Inactivo';
    if (!verificado) return '⚠️ Sin Verificar';
    return '✅ Activo';
  }

  String? get horarioCompleto {
    if (horarioApertura == null || horarioCierre == null) {
      return null;
    }
    return '$horarioApertura - $horarioCierre';
  }

  String? get logoUrlCompleta => logoUrl ?? logo;

  // ════════════════════════════════════════════════════════════════════════
  // ✅ HELPER METHODS - CONVERSIONES DEFENSIVAS
  // ════════════════════════════════════════════════════════════════════════

  /// Convierte cualquier tipo a int de forma segura
  static int? _toInt(dynamic value) {
    if (value == null) return null;
    if (value is int) return value;
    if (value is double) return value.toInt();
    if (value is String) return int.tryParse(value);
    return null;
  }

  /// Convierte cualquier tipo a String de forma segura
  static String? _toString(dynamic value) {
    if (value == null) return null;
    if (value is String) {
      return value.isEmpty ? null : value;
    }
    return value.toString();
  }

  /// Convierte cualquier tipo a bool de forma segura
  static bool? _toBool(dynamic value) {
    if (value == null) return null;
    if (value is bool) return value;
    if (value is int) return value != 0;
    if (value is String) {
      return value.toLowerCase() == 'true' || value == '1';
    }
    return null;
  }

  /// Convierte double/String/int a double de forma segura
  static double? _parseDouble(dynamic value) {
    if (value == null) return null;
    if (value is double) return value;
    if (value is int) return value.toDouble();
    if (value is String) return double.tryParse(value);
    return null;
  }

  /// Parsea DateTime de forma segura
  static DateTime? _parseDateTime(dynamic value) {
    if (value == null) return null;
    if (value is DateTime) return value;
    if (value is String) {
      try {
        return DateTime.parse(value);
      } catch (e) {
        developer.log(
          '⚠️ Error parseando DateTime: $value',
          name: 'ProveedorModel',
          error: e,
        );
        return null;
      }
    }
    return null;
  }

  // ════════════════════════════════════════════════════════════════════════
  // TO STRING
  // ════════════════════════════════════════════════════════════════════════
  @override
  String toString() {
    return 'ProveedorModel(id: $id, nombre: $nombre, ruc: $ruc, activo: $activo, verificado: $verificado)';
  }

  // ════════════════════════════════════════════════════════════════════════
  // EQUALITY
  // ════════════════════════════════════════════════════════════════════════
  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is ProveedorModel && other.id == id && other.ruc == ruc;
  }

  @override
  int get hashCode => id.hashCode ^ ruc.hashCode;
}

// ════════════════════════════════════════════════════════════════════════
// ✅ MODELO SIMPLIFICADO PARA LISTADOS (ProveedorListSerializer)
// ════════════════════════════════════════════════════════════════════════
class ProveedorListModel {
  final int id;
  final String nombre;
  final String ruc;
  final String tipoProveedor;
  final String? ciudad;
  final bool activo;
  final bool verificado;
  final bool? estaAbierto;
  final String? logo;
  final String? horarioApertura;
  final String? horarioCierre;
  final double comisionPorcentaje;
  final double? latitud;
  final double? longitud;
  final String? email;
  final String? telefono;

  ProveedorListModel({
    required this.id,
    required this.nombre,
    required this.ruc,
    required this.tipoProveedor,
    this.ciudad,
    required this.activo,
    required this.verificado,
    this.estaAbierto,
    this.logo,
    this.horarioApertura,
    this.horarioCierre,
    required this.comisionPorcentaje,
    this.latitud,
    this.longitud,
    this.email,
    this.telefono,
  });

  factory ProveedorListModel.fromJson(Map<String, dynamic> json) {
    try {
      return ProveedorListModel(
        id: ProveedorModel._toInt(json['id']) ?? 0,
        nombre: ProveedorModel._toString(json['nombre']) ?? 'Sin nombre',
        ruc: ProveedorModel._toString(json['ruc']) ?? 'N/A',
        tipoProveedor:
            ProveedorModel._toString(json['tipo_proveedor']) ?? 'otro',
        ciudad: ProveedorModel._toString(json['ciudad']),
        activo: ProveedorModel._toBool(json['activo']) ?? true,
        verificado: ProveedorModel._toBool(json['verificado']) ?? false,
        estaAbierto: ProveedorModel._toBool(json['esta_abierto']),
        logo: ProveedorModel._toString(json['logo']),
        horarioApertura: ProveedorModel._toString(json['horario_apertura']),
        horarioCierre: ProveedorModel._toString(json['horario_cierre']),
        comisionPorcentaje:
            ProveedorModel._parseDouble(json['comision_porcentaje']) ?? 10.0,
        latitud: ProveedorModel._parseDouble(json['latitud']),
        longitud: ProveedorModel._parseDouble(json['longitud']),
        email: ProveedorModel._toString(json['email']),
        telefono: ProveedorModel._toString(json['telefono']),
      );
    } catch (e, stackTrace) {
      developer.log(
        '❌ Error parseando ProveedorListModel: $e',
        name: 'ProveedorListModel',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  String get tipoProveedorDisplay {
    switch (tipoProveedor) {
      case 'restaurante':
        return '🍽️ Restaurante';
      case 'farmacia':
        return '💊 Farmacia';
      case 'supermercado':
        return '🛒 Supermercado';
      case 'tienda':
        return '🏪 Tienda';
      case 'otro':
        return '📦 Otro';
      default:
        return tipoProveedor;
    }
  }

  String get estadoDisplay {
    if (!activo) return '❌ Inactivo';
    if (!verificado) return '⚠️ Sin Verificar';
    return '✅ Activo';
  }

  bool get tieneUbicacion => latitud != null && longitud != null;

  @override
  String toString() {
    return 'ProveedorListModel(id: $id, nombre: $nombre, ruc: $ruc, tipo: $tipoProveedor)';
  }
}
