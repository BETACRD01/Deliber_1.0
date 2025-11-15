// lib/screens/supplier/tabs/estadisticas_tab.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../controllers/supplier_controller.dart';

/// Tab de estadísticas del proveedor
class EstadisticasTab extends StatelessWidget {
  const EstadisticasTab({super.key});

  static const Color _azul = Color(0xFF2196F3);
  static const Color _verde = Color(0xFF4CAF50);
  static const Color _naranja = Color(0xFFFF9800);
  static const Color _morado = Color(0xFF9C27B0);

  @override
  Widget build(BuildContext context) {
    return Consumer<SupplierController>(
      builder: (context, controller, child) {
        if (!controller.verificado) {
          return _buildSinVerificar();
        }

        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _buildSeccion('Ventas'),
            const SizedBox(height: 8),
            _buildEstadisticaCard(
              icon: Icons.today,
              label: 'Ventas Hoy',
              value: '\$${controller.ventasHoy.toStringAsFixed(2)}',
              color: _verde,
            ),
            const SizedBox(height: 12),
            _buildEstadisticaCard(
              icon: Icons.calendar_month,
              label: 'Ventas del Mes',
              value: '\$${controller.ventasMes.toStringAsFixed(2)}',
              color: _azul,
            ),
            const SizedBox(height: 24),
            _buildSeccion('Pedidos'),
            const SizedBox(height: 8),
            _buildEstadisticaCard(
              icon: Icons.check_circle_outline,
              label: 'Pedidos Completados',
              value: '${controller.pedidosCompletados}',
              color: _verde,
            ),
            const SizedBox(height: 12),
            _buildEstadisticaCard(
              icon: Icons.pending_actions,
              label: 'Pedidos Pendientes',
              value: '${controller.pedidosPendientesCount}',
              color: _naranja,
            ),
            const SizedBox(height: 24),
            _buildSeccion('Valoración'),
            const SizedBox(height: 8),
            _buildEstadisticaCard(
              icon: Icons.star,
              label: 'Valoración Promedio',
              value: controller.valoracionPromedio > 0
                  ? '${controller.valoracionPromedio.toStringAsFixed(1)} ⭐'
                  : 'Sin valoraciones',
              color: _morado,
            ),
            const SizedBox(height: 12),
            _buildEstadisticaCard(
              icon: Icons.rate_review,
              label: 'Total de Reseñas',
              value: '${controller.totalResenas}',
              color: _azul,
            ),
          ],
        );
      },
    );
  }

  Widget _buildSinVerificar() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.verified_user_outlined,
              size: 80,
              color: Colors.orange[300],
            ),
            const SizedBox(height: 24),
            const Text(
              'Cuenta sin verificar',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Text(
              'Las estadísticas estarán disponibles una vez que tu cuenta sea verificada.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 15,
                color: Colors.grey[600],
                height: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSeccion(String titulo) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Text(
        titulo.toUpperCase(),
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.bold,
          color: Colors.grey[600],
          letterSpacing: 1.2,
        ),
      ),
    );
  }

  Widget _buildEstadisticaCard({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: color.withValues(alpha: 0.1),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color, size: 28),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                ),
                const SizedBox(height: 4),
                Text(
                  value,
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
