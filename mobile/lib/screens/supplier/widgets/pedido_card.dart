// lib/screens/supplier/widgets/pedido_card.dart

import 'package:flutter/material.dart';

/// Card para mostrar un pedido pendiente del proveedor
class PedidoCard extends StatelessWidget {
  final Map<String, dynamic> pedido;
  final VoidCallback? onTap;
  final VoidCallback? onAceptar;
  final VoidCallback? onRechazar;

  const PedidoCard({
    super.key,
    required this.pedido,
    this.onTap,
    this.onAceptar,
    this.onRechazar,
  });

  static const Color _verde = Color(0xFF4CAF50);
  static const Color _naranja = Color(0xFFFF9800);
  static const Color _rojo = Color(0xFFF44336);
  static const Color _azul = Color(0xFF2196F3);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildHeader(),
              const SizedBox(height: 12),
              _buildDetalles(),
              const SizedBox(height: 12),
              _buildInfo(),
              if (onAceptar != null || onRechazar != null) ...[
                const SizedBox(height: 16),
                _buildAcciones(),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    final id = pedido['id'] ?? '000';
    final estado = pedido['estado'] ?? 'pendiente';

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          'Pedido #$id',
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        _buildEstadoBadge(estado),
      ],
    );
  }

  Widget _buildEstadoBadge(String estado) {
    Color color;
    String texto;

    switch (estado.toLowerCase()) {
      case 'pendiente':
        color = _naranja;
        texto = 'PENDIENTE';
        break;
      case 'aceptado':
        color = _azul;
        texto = 'ACEPTADO';
        break;
      case 'en_preparacion':
        color = _azul;
        texto = 'EN PREPARACIÓN';
        break;
      case 'completado':
        color = _verde;
        texto = 'COMPLETADO';
        break;
      case 'rechazado':
        color = _rojo;
        texto = 'RECHAZADO';
        break;
      default:
        color = Colors.grey;
        texto = estado.toUpperCase();
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        texto,
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildDetalles() {
    final total = pedido['total'] ?? 0.0;
    final items = pedido['items'] ?? pedido['productos'] ?? [];
    final cantidadItems = items is List ? items.length : 0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Total: \$${_formatPrecio(total)}',
          style: const TextStyle(
            color: _verde,
            fontWeight: FontWeight.w600,
            fontSize: 18,
          ),
        ),
        if (cantidadItems > 0) ...[
          const SizedBox(height: 4),
          Text(
            '$cantidadItems ${cantidadItems == 1 ? "producto" : "productos"}',
            style: TextStyle(fontSize: 13, color: Colors.grey[600]),
          ),
        ],
      ],
    );
  }

  Widget _buildInfo() {
    final fecha = pedido['fecha'] ?? pedido['created_at'];
    final cliente = pedido['cliente'] ?? pedido['usuario'];
    final direccion = pedido['direccion'] ?? pedido['direccion_entrega'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (fecha != null)
          _buildInfoRow(Icons.access_time, _formatFecha(fecha)),
        if (cliente != null) ...[
          const SizedBox(height: 6),
          _buildInfoRow(Icons.person_outline, _getNombreCliente(cliente)),
        ],
        if (direccion != null) ...[
          const SizedBox(height: 6),
          _buildInfoRow(Icons.location_on_outlined, _getDireccion(direccion)),
        ],
      ],
    );
  }

  Widget _buildInfoRow(IconData icon, String texto) {
    return Row(
      children: [
        Icon(icon, size: 14, color: Colors.grey[600]),
        const SizedBox(width: 4),
        Expanded(
          child: Text(
            texto,
            style: TextStyle(fontSize: 12, color: Colors.grey[600]),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }

  Widget _buildAcciones() {
    return Row(
      children: [
        if (onRechazar != null)
          Expanded(
            child: OutlinedButton.icon(
              onPressed: onRechazar,
              icon: const Icon(Icons.close, size: 18),
              label: const Text('Rechazar'),
              style: OutlinedButton.styleFrom(
                foregroundColor: _rojo,
                side: BorderSide(color: _rojo),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
          ),
        if (onRechazar != null && onAceptar != null) const SizedBox(width: 12),
        if (onAceptar != null)
          Expanded(
            child: ElevatedButton.icon(
              onPressed: onAceptar,
              icon: const Icon(Icons.check, size: 18),
              label: const Text('Aceptar'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _verde,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
          ),
      ],
    );
  }

  // Helpers

  String _formatPrecio(dynamic precio) {
    if (precio is String) {
      return precio;
    }
    if (precio is num) {
      return precio.toStringAsFixed(2);
    }
    return '0.00';
  }

  String _formatFecha(dynamic fecha) {
    if (fecha is String) {
      try {
        final date = DateTime.parse(fecha);
        final now = DateTime.now();
        final diff = now.difference(date);

        if (diff.inMinutes < 60) {
          return 'Hace ${diff.inMinutes} min';
        } else if (diff.inHours < 24) {
          return 'Hace ${diff.inHours}h';
        } else {
          return 'Hace ${diff.inDays}d';
        }
      } catch (e) {
        return fecha;
      }
    }
    return 'Hace unos minutos';
  }

  String _getNombreCliente(dynamic cliente) {
    if (cliente is Map) {
      return cliente['nombre'] ??
          cliente['nombre_completo'] ??
          cliente['username'] ??
          'Cliente';
    }
    if (cliente is String) {
      return cliente;
    }
    return 'Cliente';
  }

  String _getDireccion(dynamic direccion) {
    if (direccion is Map) {
      final calle = direccion['calle'] ?? direccion['direccion'] ?? '';
      final ciudad = direccion['ciudad'] ?? '';

      if (calle.isNotEmpty && ciudad.isNotEmpty) {
        return '$calle, $ciudad';
      }
      return calle.isNotEmpty ? calle : ciudad;
    }
    if (direccion is String) {
      return direccion;
    }
    return 'Sin dirección';
  }
}
