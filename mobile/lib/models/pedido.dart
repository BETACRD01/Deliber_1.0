/// Modelo para pedidos disponibles en el mapa
class PedidoDisponible {
  final int id;
  final String clienteNombre;
  final String direccionEntrega;
  final double latitud;
  final double longitud;
  final double distanciaKm;
  final int tiempoEstimadoMin;
  final double montoTotal;
  final DateTime? creadoEn;

  PedidoDisponible({
    required this.id,
    required this.clienteNombre,
    required this.direccionEntrega,
    required this.latitud,
    required this.longitud,
    required this.distanciaKm,
    required this.tiempoEstimadoMin,
    required this.montoTotal,
    this.creadoEn,
  });

  /// Factory para crear desde JSON del backend
  factory PedidoDisponible.fromJson(Map<String, dynamic> json) {
    return PedidoDisponible(
      id: json['id'] as int,
      clienteNombre: json['cliente_nombre'] as String? ?? 'Cliente',
      direccionEntrega: json['direccion_entrega'] as String? ?? 'Sin dirección',
      latitud: (json['latitud'] as num).toDouble(),
      longitud: (json['longitud'] as num).toDouble(),
      distanciaKm: (json['distancia_km'] as num).toDouble(),
      tiempoEstimadoMin: json['tiempo_estimado_min'] as int? ?? 0,
      montoTotal: (json['monto_total'] as num).toDouble(),
      creadoEn: json['creado_en'] != null
          ? DateTime.parse(json['creado_en'] as String)
          : null,
    );
  }

  /// Convierte a JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'cliente_nombre': clienteNombre,
      'direccion_entrega': direccionEntrega,
      'latitud': latitud,
      'longitud': longitud,
      'distancia_km': distanciaKm,
      'tiempo_estimado_min': tiempoEstimadoMin,
      'monto_total': montoTotal,
      'creado_en': creadoEn?.toIso8601String(),
    };
  }

  /// Copia con modificaciones
  PedidoDisponible copyWith({
    int? id,
    String? clienteNombre,
    String? direccionEntrega,
    double? latitud,
    double? longitud,
    double? distanciaKm,
    int? tiempoEstimadoMin,
    double? montoTotal,
    DateTime? creadoEn,
  }) {
    return PedidoDisponible(
      id: id ?? this.id,
      clienteNombre: clienteNombre ?? this.clienteNombre,
      direccionEntrega: direccionEntrega ?? this.direccionEntrega,
      latitud: latitud ?? this.latitud,
      longitud: longitud ?? this.longitud,
      distanciaKm: distanciaKm ?? this.distanciaKm,
      tiempoEstimadoMin: tiempoEstimadoMin ?? this.tiempoEstimadoMin,
      montoTotal: montoTotal ?? this.montoTotal,
      creadoEn: creadoEn ?? this.creadoEn,
    );
  }

  @override
  String toString() {
    return 'PedidoDisponible(id: $id, cliente: $clienteNombre, distancia: ${distanciaKm}km, monto: \$$montoTotal)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is PedidoDisponible && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;
}

/// Respuesta completa del endpoint de pedidos disponibles
class PedidosDisponiblesResponse {
  final UbicacionRepartidor repartidorUbicacion;
  final double radioKm;
  final int totalPedidos;
  final List<PedidoDisponible> pedidos;

  PedidosDisponiblesResponse({
    required this.repartidorUbicacion,
    required this.radioKm,
    required this.totalPedidos,
    required this.pedidos,
  });

  factory PedidosDisponiblesResponse.fromJson(Map<String, dynamic> json) {
    return PedidosDisponiblesResponse(
      repartidorUbicacion: UbicacionRepartidor.fromJson(
        json['repartidor_ubicacion'] as Map<String, dynamic>,
      ),
      radioKm: (json['radio_km'] as num).toDouble(),
      totalPedidos: json['total_pedidos'] as int,
      pedidos: (json['pedidos'] as List<dynamic>)
          .map((p) => PedidoDisponible.fromJson(p as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'repartidor_ubicacion': repartidorUbicacion.toJson(),
      'radio_km': radioKm,
      'total_pedidos': totalPedidos,
      'pedidos': pedidos.map((p) => p.toJson()).toList(),
    };
  }
}

/// Ubicación del repartidor
class UbicacionRepartidor {
  final double latitud;
  final double longitud;

  UbicacionRepartidor({required this.latitud, required this.longitud});

  factory UbicacionRepartidor.fromJson(Map<String, dynamic> json) {
    return UbicacionRepartidor(
      latitud: (json['latitud'] as num).toDouble(),
      longitud: (json['longitud'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {'latitud': latitud, 'longitud': longitud};
  }
}
