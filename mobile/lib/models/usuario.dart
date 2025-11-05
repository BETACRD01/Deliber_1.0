import 'package:flutter/material.dart';
import '../config/api_config.dart';

// ══════════════════════════════════════════════════════════════════════════════
// 👤 MODELO: PERFIL DE USUARIO
// ══════════════════════════════════════════════════════════════════════════════

class PerfilModel {
  final int id;
  final String usuarioEmail;
  final String usuarioNombre;
  final String? fotoPerfil;
  final String? telefono;
  final DateTime? fechaNacimiento;
  final int? edad;
  final double calificacion;
  final int totalResenas;
  final int totalPedidos;
  final bool esClienteFrecuente;
  final bool tieneTelefono;
  final bool puedeParticiparRifa;
  final bool notificacionesPedido;
  final bool notificacionesPromociones;
  final bool puedeRecibirNotificaciones;
  final DateTime creadoEn;
  final DateTime actualizadoEn;

  PerfilModel({
    required this.id,
    required this.usuarioEmail,
    required this.usuarioNombre,
    this.fotoPerfil,
    this.telefono,
    this.fechaNacimiento,
    this.edad,
    required this.calificacion,
    required this.totalResenas,
    required this.totalPedidos,
    required this.esClienteFrecuente,
    required this.tieneTelefono,
    required this.puedeParticiparRifa,
    required this.notificacionesPedido,
    required this.notificacionesPromociones,
    required this.puedeRecibirNotificaciones,
    required this.creadoEn,
    required this.actualizadoEn,
  });

  factory PerfilModel.fromJson(Map<String, dynamic> json) {
    return PerfilModel(
      id: json['id'] as int,
      usuarioEmail: json['usuario_email'] as String,
      usuarioNombre: json['usuario_nombre'] as String,
      fotoPerfil: json['foto_perfil'] as String?,
      telefono: json['telefono'] as String?,
      fechaNacimiento: json['fecha_nacimiento'] != null
          ? DateTime.parse(json['fecha_nacimiento'] as String)
          : null,
      edad: json['edad'] as int?,
      calificacion: (json['calificacion'] as num).toDouble(),
      totalResenas: json['total_resenas'] as int,
      totalPedidos: json['total_pedidos'] as int,
      esClienteFrecuente: json['es_cliente_frecuente'] as bool,
      tieneTelefono: json['tiene_telefono'] as bool,
      puedeParticiparRifa: json['puede_participar_rifa'] as bool,
      notificacionesPedido: json['notificaciones_pedido'] as bool,
      notificacionesPromociones: json['notificaciones_promociones'] as bool,
      puedeRecibirNotificaciones:
          json['puede_recibir_notificaciones'] as bool? ?? false,
      creadoEn: DateTime.parse(json['creado_en'] as String),
      actualizadoEn: DateTime.parse(json['actualizado_en'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'usuario_email': usuarioEmail,
      'usuario_nombre': usuarioNombre,
      'foto_perfil': fotoPerfil,
      'telefono': telefono,
      'fecha_nacimiento': fechaNacimiento?.toIso8601String(),
      'edad': edad,
      'calificacion': calificacion,
      'total_resenas': totalResenas,
      'total_pedidos': totalPedidos,
      'es_cliente_frecuente': esClienteFrecuente,
      'tiene_telefono': tieneTelefono,
      'puede_participar_rifa': puedeParticiparRifa,
      'notificaciones_pedido': notificacionesPedido,
      'notificaciones_promociones': notificacionesPromociones,
      'puede_recibir_notificaciones': puedeRecibirNotificaciones,
      'creado_en': creadoEn.toIso8601String(),
      'actualizado_en': actualizadoEn.toIso8601String(),
    };
  }

  PerfilModel copyWith({
    int? id,
    String? usuarioEmail,
    String? usuarioNombre,
    String? fotoPerfil,
    String? telefono,
    DateTime? fechaNacimiento,
    int? edad,
    double? calificacion,
    int? totalResenas,
    int? totalPedidos,
    bool? esClienteFrecuente,
    bool? tieneTelefono,
    bool? puedeParticiparRifa,
    bool? notificacionesPedido,
    bool? notificacionesPromociones,
    bool? puedeRecibirNotificaciones,
    DateTime? creadoEn,
    DateTime? actualizadoEn,
  }) {
    return PerfilModel(
      id: id ?? this.id,
      usuarioEmail: usuarioEmail ?? this.usuarioEmail,
      usuarioNombre: usuarioNombre ?? this.usuarioNombre,
      fotoPerfil: fotoPerfil ?? this.fotoPerfil,
      telefono: telefono ?? this.telefono,
      fechaNacimiento: fechaNacimiento ?? this.fechaNacimiento,
      edad: edad ?? this.edad,
      calificacion: calificacion ?? this.calificacion,
      totalResenas: totalResenas ?? this.totalResenas,
      totalPedidos: totalPedidos ?? this.totalPedidos,
      esClienteFrecuente: esClienteFrecuente ?? this.esClienteFrecuente,
      tieneTelefono: tieneTelefono ?? this.tieneTelefono,
      puedeParticiparRifa: puedeParticiparRifa ?? this.puedeParticiparRifa,
      notificacionesPedido: notificacionesPedido ?? this.notificacionesPedido,
      notificacionesPromociones:
          notificacionesPromociones ?? this.notificacionesPromociones,
      puedeRecibirNotificaciones:
          puedeRecibirNotificaciones ?? this.puedeRecibirNotificaciones,
      creadoEn: creadoEn ?? this.creadoEn,
      actualizadoEn: actualizadoEn ?? this.actualizadoEn,
    );
  }

  String? get fotoPerfilUrl {
    if (fotoPerfil == null || fotoPerfil!.isEmpty) return null;
    if (fotoPerfil!.startsWith('http')) return fotoPerfil;
    if (fotoPerfil!.startsWith('/media/')) {
      return '${ApiConfig.baseUrl}$fotoPerfil';
    }
    return '${ApiConfig.baseUrl}/media/$fotoPerfil';
  }

  @override
  String toString() =>
      'PerfilModel(id: $id, email: $usuarioEmail, nombre: $usuarioNombre)';
}

// ══════════════════════════════════════════════════════════════════════════════
// 📍 MODELO: DIRECCIÓN FAVORITA
// ══════════════════════════════════════════════════════════════════════════════

class DireccionModel {
  final String id;
  final String tipo;
  final String tipoDisplay;
  final String etiqueta;
  final String direccion;
  final String? referencia;
  final double latitud;
  final double longitud;
  final String? ciudad;
  final bool esPredeterminada;
  final bool activa;
  final int vecesUsada;
  final DateTime? ultimoUso;
  final String direccionCompleta;
  final DateTime createdAt;
  final DateTime updatedAt;

  DireccionModel({
    required this.id,
    required this.tipo,
    required this.tipoDisplay,
    required this.etiqueta,
    required this.direccion,
    this.referencia,
    required this.latitud,
    required this.longitud,
    this.ciudad,
    required this.esPredeterminada,
    required this.activa,
    required this.vecesUsada,
    this.ultimoUso,
    required this.direccionCompleta,
    required this.createdAt,
    required this.updatedAt,
  });

  // ──────────────────────────────────────────────────────────────────────────
  // FROM JSON (sin cambios)
  // ──────────────────────────────────────────────────────────────────────────

  factory DireccionModel.fromJson(Map<String, dynamic> json) {
    String safeString(dynamic v) => v is String ? v : '';
    double safeDouble(dynamic v) => (v is num) ? v.toDouble() : 0.0;
    bool safeBool(dynamic v) => v is bool ? v : false;
    int safeInt(dynamic v) => v is int ? v : 0;

    DateTime parseDate(dynamic v) {
      if (v is String && v.isNotEmpty) {
        return DateTime.tryParse(v) ?? DateTime.now();
      }
      return DateTime.now();
    }

    return DireccionModel(
      id: safeString(json['id']),
      tipo: safeString(json['tipo']),
      tipoDisplay: safeString(json['tipo_display']),
      etiqueta: safeString(json['etiqueta']),
      direccion: safeString(json['direccion']),
      referencia: json['referencia'] is String ? json['referencia'] : null,
      latitud: safeDouble(json['latitud']),
      longitud: safeDouble(json['longitud']),
      ciudad: json['ciudad'] is String ? json['ciudad'] : null,
      esPredeterminada: safeBool(json['es_predeterminada']),
      activa: safeBool(json['activa']),
      vecesUsada: safeInt(json['veces_usada']),
      ultimoUso: json['ultimo_uso'] != null
          ? DateTime.tryParse(json['ultimo_uso']) ?? DateTime.now()
          : null,
      direccionCompleta: safeString(json['direccion_completa']),
      createdAt: parseDate(json['created_at']),
      updatedAt: parseDate(json['updated_at']),
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // TO JSON COMPLETO (sin cambios)
  // ──────────────────────────────────────────────────────────────────────────

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'tipo': tipo,
      'tipo_display': tipoDisplay,
      'etiqueta': etiqueta,
      'direccion': direccion,
      'referencia': referencia,
      'latitud': latitud,
      'longitud': longitud,
      'ciudad': ciudad,
      'es_predeterminada': esPredeterminada,
      'activa': activa,
      'veces_usada': vecesUsada,
      'ultimo_uso': ultimoUso?.toIso8601String(),
      'direccion_completa': direccionCompleta,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  // ──────────────────────────────────────────────────────────────────────────
  // ✅ TO CREATE JSON - CORREGIDO (solo incluye campos con valor)
  // ──────────────────────────────────────────────────────────────────────────

  /// Convierte el modelo a JSON para crear/actualizar en el backend
  /// ✅ CORREGIDO: Solo incluye campos opcionales si tienen valor real
  ///
  /// - Si `etiqueta` está vacía, NO se envía (el backend la genera)
  /// - Si `referencia` está vacía, NO se envía
  /// - Si `ciudad` está vacía, NO se envía
  Map<String, dynamic> toCreateJson() {
    // ✅ Campos obligatorios siempre presentes
    final data = <String, dynamic>{
      'tipo': tipo,
      'direccion': direccion,
      'latitud': latitud,
      'longitud': longitud,
      'es_predeterminada': esPredeterminada,
    };

    // ✅ Campos opcionales: solo agregar si tienen valor real

    // Etiqueta: solo si NO está vacía
    if (etiqueta.isNotEmpty) {
      data['etiqueta'] = etiqueta;
    }

    // Referencia: solo si NO es null y NO está vacía
    if (referencia != null && referencia!.isNotEmpty) {
      data['referencia'] = referencia;
    }

    // Ciudad: solo si NO es null y NO está vacía
    if (ciudad != null && ciudad!.isNotEmpty) {
      data['ciudad'] = ciudad;
    }

    return data;
  }

  // ──────────────────────────────────────────────────────────────────────────
  // COPY WITH (sin cambios)
  // ──────────────────────────────────────────────────────────────────────────

  DireccionModel copyWith({
    String? id,
    String? tipo,
    String? tipoDisplay,
    String? etiqueta,
    String? direccion,
    String? referencia,
    double? latitud,
    double? longitud,
    String? ciudad,
    bool? esPredeterminada,
    bool? activa,
    int? vecesUsada,
    DateTime? ultimoUso,
    String? direccionCompleta,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return DireccionModel(
      id: id ?? this.id,
      tipo: tipo ?? this.tipo,
      tipoDisplay: tipoDisplay ?? this.tipoDisplay,
      etiqueta: etiqueta ?? this.etiqueta,
      direccion: direccion ?? this.direccion,
      referencia: referencia ?? this.referencia,
      latitud: latitud ?? this.latitud,
      longitud: longitud ?? this.longitud,
      ciudad: ciudad ?? this.ciudad,
      esPredeterminada: esPredeterminada ?? this.esPredeterminada,
      activa: activa ?? this.activa,
      vecesUsada: vecesUsada ?? this.vecesUsada,
      ultimoUso: ultimoUso ?? this.ultimoUso,
      direccionCompleta: direccionCompleta ?? this.direccionCompleta,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // HELPERS (sin cambios)
  // ──────────────────────────────────────────────────────────────────────────

  String get iconoTipo {
    switch (tipo) {
      case 'casa':
        return '🏠';
      case 'trabajo':
        return '💼';
      default:
        return '📍';
    }
  }

  @override
  String toString() =>
      'DireccionModel(id: $id, etiqueta: $etiqueta, tipo: $tipo)';
}
// ══════════════════════════════════════════════════════════════════════════════
// 💳 MODELO: MÉTODO DE PAGO (ACTUALIZADO CON COMPROBANTES)
// ══════════════════════════════════════════════════════════════════════════════

class MetodoPagoModel {
  final String id;
  final String tipo;
  final String tipoDisplay;
  final String alias;

  // ✅ NUEVOS CAMPOS PARA COMPROBANTES Y OBSERVACIONES
  final String? comprobantePago; // URL de la imagen del comprobante
  final String? observaciones; // Notas sobre el pago (máx. 100 chars)
  final bool tieneComprobante; // ¿Tiene comprobante subido?
  final bool requiereVerificacion; // ¿Requiere verificación manual?

  final bool esPredeterminado;
  final bool activo;
  final DateTime createdAt;
  final DateTime updatedAt;

  MetodoPagoModel({
    required this.id,
    required this.tipo,
    required this.tipoDisplay,
    required this.alias,
    this.comprobantePago,
    this.observaciones,
    required this.tieneComprobante,
    required this.requiereVerificacion,
    required this.esPredeterminado,
    required this.activo,
    required this.createdAt,
    required this.updatedAt,
  });

  // ──────────────────────────────────────────────────────────────────────────
  // FROM JSON (ACTUALIZADO)
  // ──────────────────────────────────────────────────────────────────────────

  factory MetodoPagoModel.fromJson(Map<String, dynamic> json) {
    return MetodoPagoModel(
      id: json['id'] as String,
      tipo: json['tipo'] as String,
      tipoDisplay: json['tipo_display'] as String,
      alias: json['alias'] as String,

      // ✅ PARSEAR NUEVOS CAMPOS
      comprobantePago: json['comprobante_pago'] as String?,
      observaciones: json['observaciones'] as String?,
      tieneComprobante: json['tiene_comprobante'] as bool? ?? false,
      requiereVerificacion: json['requiere_verificacion'] as bool? ?? false,

      esPredeterminado: json['es_predeterminado'] as bool,
      activo: json['activo'] as bool,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // TO JSON (ACTUALIZADO)
  // ──────────────────────────────────────────────────────────────────────────

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'tipo': tipo,
      'tipo_display': tipoDisplay,
      'alias': alias,
      'comprobante_pago': comprobantePago,
      'observaciones': observaciones,
      'tiene_comprobante': tieneComprobante,
      'requiere_verificacion': requiereVerificacion,
      'es_predeterminado': esPredeterminado,
      'activo': activo,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  // ──────────────────────────────────────────────────────────────────────────
  // TO JSON PARA CREAR/ACTUALIZAR (sin campos readonly)
  // ──────────────────────────────────────────────────────────────────────────

  Map<String, dynamic> toCreateJson() {
    return {
      'tipo': tipo,
      'alias': alias,
      // ✅ INCLUIR OBSERVACIONES SI EXISTEN
      if (observaciones != null && observaciones!.isNotEmpty)
        'observaciones': observaciones,
      'es_predeterminado': esPredeterminado,
      // NOTA: comprobante_pago se envía como archivo multipart, no como JSON
    };
  }

  // ──────────────────────────────────────────────────────────────────────────
  // COPY WITH (ACTUALIZADO)
  // ──────────────────────────────────────────────────────────────────────────

  MetodoPagoModel copyWith({
    String? id,
    String? tipo,
    String? tipoDisplay,
    String? alias,
    String? comprobantePago,
    String? observaciones,
    bool? tieneComprobante,
    bool? requiereVerificacion,
    bool? esPredeterminado,
    bool? activo,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return MetodoPagoModel(
      id: id ?? this.id,
      tipo: tipo ?? this.tipo,
      tipoDisplay: tipoDisplay ?? this.tipoDisplay,
      alias: alias ?? this.alias,
      comprobantePago: comprobantePago ?? this.comprobantePago,
      observaciones: observaciones ?? this.observaciones,
      tieneComprobante: tieneComprobante ?? this.tieneComprobante,
      requiereVerificacion: requiereVerificacion ?? this.requiereVerificacion,
      esPredeterminado: esPredeterminado ?? this.esPredeterminado,
      activo: activo ?? this.activo,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // HELPERS (MEJORADOS CON NUEVOS CAMPOS)
  // ──────────────────────────────────────────────────────────────────────────

  /// Icono según tipo de pago
  String get iconoTipo {
    switch (tipo) {
      case 'efectivo':
        return '💵';
      case 'transferencia':
        return '🏦';
      case 'tarjeta':
        return '💳';
      default:
        return '💰';
    }
  }

  /// URL completa del comprobante para mostrar en Image.network()
  /// Nota: Debes importar ApiConfig para construir la URL completa
  String? get urlComprobante {
    if (comprobantePago == null || comprobantePago!.isEmpty) return null;

    // Si ya es una URL completa (http/https), retornarla tal cual
    if (comprobantePago!.startsWith('http')) {
      return comprobantePago;
    }

    // Si es una ruta relativa, construir URL completa
    // Descomenta y ajusta según tu ApiConfig:
    // return '${ApiConfig.baseUrl}$comprobantePago';

    // Por ahora, retornar tal cual (ajustar según necesites)
    return comprobantePago;
  }

  /// ¿Es un método de pago válido y listo para usar?
  bool get esValido {
    // Efectivo siempre es válido
    if (tipo == 'efectivo') return true;

    // Transferencia requiere comprobante
    if (tipo == 'transferencia') return tieneComprobante;

    // Tarjeta (futuro)
    if (tipo == 'tarjeta') return true;

    return true;
  }

  /// Mensaje descriptivo del estado del comprobante
  String get mensajeComprobante {
    if (tipo == 'efectivo') {
      return 'No requiere comprobante';
    }

    if (tipo == 'transferencia') {
      if (tieneComprobante) {
        return requiereVerificacion
            ? '⏳ Pendiente de verificación'
            : '✅ Comprobante verificado';
      }
      return '❌ Falta subir comprobante';
    }

    if (tipo == 'tarjeta') {
      return '💳 Pago con tarjeta';
    }

    return '-';
  }

  /// Color del estado del comprobante (para UI)
  Color get colorEstado {
    if (tipo == 'efectivo') return Colors.grey;

    if (tipo == 'transferencia') {
      if (tieneComprobante) {
        return requiereVerificacion ? Colors.orange : Colors.green;
      }
      return Colors.red;
    }

    if (tipo == 'tarjeta') return Colors.blue;

    return Colors.grey;
  }

  /// Icono del estado del comprobante
  IconData get iconoEstado {
    if (tipo == 'efectivo') return Icons.attach_money;

    if (tipo == 'transferencia') {
      if (tieneComprobante) {
        return requiereVerificacion ? Icons.pending : Icons.check_circle;
      }
      return Icons.error;
    }

    if (tipo == 'tarjeta') return Icons.credit_card;

    return Icons.help_outline;
  }

  /// ¿Puede ser usado para pagar ahora?
  bool get puedeUsarse {
    if (!activo) return false;

    // Efectivo siempre disponible
    if (tipo == 'efectivo') return true;

    // Transferencia: requiere comprobante verificado
    if (tipo == 'transferencia') {
      return tieneComprobante && !requiereVerificacion;
    }

    // Tarjeta: siempre disponible si está activa
    if (tipo == 'tarjeta') return true;

    return false;
  }

  /// Descripción completa del método de pago
  String get descripcionCompleta {
    final buffer = StringBuffer();
    buffer.write('$tipoDisplay - $alias');

    if (observaciones != null && observaciones!.isNotEmpty) {
      buffer.write(' ($observaciones)');
    }

    if (!puedeUsarse) {
      buffer.write(' [No disponible]');
    }

    return buffer.toString();
  }

  /// ¿Tiene problemas reportados?
  bool get tieneProblemas {
    return observaciones != null && observaciones!.isNotEmpty;
  }

  @override
  String toString() {
    return 'MetodoPagoModel(id: $id, alias: $alias, tipo: $tipo, comprobante: ${tieneComprobante ? 'Sí' : 'No'})';
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// 📊 MODELO: ESTADÍSTICAS DE USUARIO
// ══════════════════════════════════════════════════════════════════════════════

class EstadisticasModel {
  final int totalPedidos;
  final int pedidosMesActual;
  final double calificacion;
  final int totalResenas;
  final bool esClienteFrecuente;
  final bool puedeParticiparRifa;
  final int totalDirecciones;
  final int totalMetodosPago;

  EstadisticasModel({
    required this.totalPedidos,
    required this.pedidosMesActual,
    required this.calificacion,
    required this.totalResenas,
    required this.esClienteFrecuente,
    required this.puedeParticiparRifa,
    required this.totalDirecciones,
    required this.totalMetodosPago,
  });

  // ──────────────────────────────────────────────────────────────────────────
  // FROM JSON
  // ──────────────────────────────────────────────────────────────────────────

  factory EstadisticasModel.fromJson(Map<String, dynamic> json) {
    return EstadisticasModel(
      totalPedidos: json['total_pedidos'] as int,
      pedidosMesActual: json['pedidos_mes_actual'] as int,
      calificacion: (json['calificacion'] as num).toDouble(),
      totalResenas: json['total_resenas'] as int,
      esClienteFrecuente: json['es_cliente_frecuente'] as bool,
      puedeParticiparRifa: json['puede_participar_rifa'] as bool,
      totalDirecciones: json['total_direcciones'] as int,
      totalMetodosPago: json['total_metodos_pago'] as int,
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // TO JSON
  // ──────────────────────────────────────────────────────────────────────────

  Map<String, dynamic> toJson() {
    return {
      'total_pedidos': totalPedidos,
      'pedidos_mes_actual': pedidosMesActual,
      'calificacion': calificacion,
      'total_resenas': totalResenas,
      'es_cliente_frecuente': esClienteFrecuente,
      'puede_participar_rifa': puedeParticiparRifa,
      'total_direcciones': totalDirecciones,
      'total_metodos_pago': totalMetodosPago,
    };
  }

  // ──────────────────────────────────────────────────────────────────────────
  // HELPERS
  // ──────────────────────────────────────────────────────────────────────────

  String get nivelCliente {
    if (esClienteFrecuente) return '🌟 Cliente VIP';
    if (totalPedidos >= 5) return '⭐ Cliente Regular';
    return '🆕 Cliente Nuevo';
  }

  double get progresoRifa {
    if (pedidosMesActual >= 3) return 1.0;
    return pedidosMesActual / 3.0;
  }

  String get mensajeRifa {
    if (puedeParticiparRifa) {
      return '🎉 ¡Participas en la rifa!';
    }
    final faltantes = 3 - pedidosMesActual;
    return 'Te faltan $faltantes pedido${faltantes == 1 ? '' : 's'} para la rifa';
  }

  @override
  String toString() {
    return 'EstadisticasModel(pedidos: $totalPedidos, calificación: $calificacion)';
  }
}
