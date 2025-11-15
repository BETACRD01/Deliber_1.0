// lib/screens/supplier/widgets/supplier_stats_header.dart

import 'package:flutter/material.dart';

/// Header con estadísticas principales del proveedor
/// Muestra productos, pedidos pendientes y ventas del día
class SupplierStatsHeader extends StatelessWidget {
  final int productos;
  final int pendientes;
  final double ventasHoy;

  const SupplierStatsHeader({
    super.key,
    required this.productos,
    required this.pendientes,
    required this.ventasHoy,
  });

  // ============================================
  // COLORES
  // ============================================
  static const Color _azul = Color(0xFF2196F3);
  static const Color _verde = Color(0xFF4CAF50);
  static const Color _naranja = Color(0xFFFF9800);
  static const Color _morado = Color(0xFF9C27B0);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [_azul.withValues(alpha: 0.03), Colors.white],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: _buildEstadistica(
              icon: Icons.inventory_2_outlined,
              label: 'Productos',
              value: '$productos',
              color: _morado,
              gradient: [_morado.withValues(alpha: 0.8), _morado],
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _buildEstadistica(
              icon: Icons.pending_actions_outlined,
              label: 'Pendientes',
              value: '$pendientes',
              color: _naranja,
              gradient: [_naranja.withValues(alpha: 0.8), _naranja],
              showBadge: pendientes > 0,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _buildEstadistica(
              icon: Icons.attach_money,
              label: 'Ventas Hoy',
              value: '\$${ventasHoy.toStringAsFixed(2)}',
              color: _verde,
              gradient: [_verde.withValues(alpha: 0.8), _verde],
              isAmount: true,
            ),
          ),
        ],
      ),
    );
  }

  // ============================================
  // ESTADÍSTICA INDIVIDUAL
  // ============================================

  Widget _buildEstadistica({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
    required List<Color> gradient,
    bool showBadge = false,
    bool isAmount = false,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: color.withValues(alpha: 0.15),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          // Icono con gradiente
          Stack(
            clipBehavior: Clip.none,
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: gradient,
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(14),
                  boxShadow: [
                    BoxShadow(
                      color: color.withValues(alpha: 0.3),
                      blurRadius: 8,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: Icon(icon, color: Colors.white, size: 26),
              ),
              // Badge de notificación
              if (showBadge)
                Positioned(
                  top: -4,
                  right: -4,
                  child: Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: Colors.red,
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 2),
                    ),
                    child: const SizedBox(width: 6, height: 6),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 14),
          // Valor
          Text(
            value,
            style: TextStyle(
              fontSize: isAmount ? 16 : 22,
              fontWeight: FontWeight.bold,
              color: color,
              letterSpacing: -0.5,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 6),
          // Label
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              color: Colors.grey[600],
              fontWeight: FontWeight.w500,
            ),
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}
