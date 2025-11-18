// lib/screens/delivery/widgets/estadisticas_header.dart

import 'package:flutter/material.dart';
import '../../../models/repartidor.dart';

/// 📊 Widget reutilizable para mostrar estadísticas del repartidor
/// Muestra entregas, rating, ganancias y detalles de calificaciones
class EstadisticasHeader extends StatelessWidget {
  final int entregas;
  final double rating;
  final double gananciasEstimadas;
  final EstadisticasRepartidorModel? estadisticas;

  // Colores
  static const Color _naranja = Color(0xFFFF9800);
  static const Color _verde = Color(0xFF4CAF50);
  static const Color _azul = Color(0xFF2196F3);

  const EstadisticasHeader({
    super.key,
    required this.entregas,
    required this.rating,
    required this.gananciasEstimadas,
    this.estadisticas,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [_naranja.withValues(alpha: 0.1), Colors.white],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: Column(
        children: [
          _buildEstadisticasPrincipales(),
          if (estadisticas != null) ...[
            const SizedBox(height: 12),
            _buildDetallesEstadisticas(),
          ],
        ],
      ),
    );
  }

  // ============================================
  // ESTADÍSTICAS PRINCIPALES
  // ============================================

  Widget _buildEstadisticasPrincipales() {
    return Row(
      children: [
        _buildEstadistica(
          'Entregas',
          '$entregas',
          Icons.delivery_dining,
          _azul,
        ),
        const SizedBox(width: 12),
        _buildEstadistica(
          'Rating',
          rating.toStringAsFixed(1),
          Icons.star,
          Colors.amber,
        ),
        const SizedBox(width: 12),
        _buildEstadistica(
          'Ganancias',
          '\$${gananciasEstimadas.toStringAsFixed(2)}',
          Icons.attach_money,
          _verde,
        ),
      ],
    );
  }

  Widget _buildEstadistica(
    String titulo,
    String valor,
    IconData icono,
    Color color,
  ) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.grey.withValues(alpha: 0.1),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          children: [
            Icon(icono, color: color, size: 24),
            const SizedBox(height: 8),
            Text(
              valor,
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              titulo,
              style: TextStyle(fontSize: 11, color: Colors.grey[600]),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================
  // DETALLES DE ESTADÍSTICAS
  // ============================================

  Widget _buildDetallesEstadisticas() {
    if (estadisticas == null) return const SizedBox.shrink();

    final totalCalificaciones = estadisticas!.totalCalificaciones;
    final calificaciones5 = estadisticas!.calificaciones5Estrellas;
    final porcentaje5Estrellas = totalCalificaciones > 0
        ? (calificaciones5 / totalCalificaciones * 100)
        : 0.0;

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withValues(alpha: 0.1),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildMiniEstadistica('⭐⭐⭐⭐⭐', '$calificaciones5', Colors.amber),
          _buildMiniEstadistica('Total', '$totalCalificaciones', _azul),
          _buildMiniEstadistica(
            'Promedio',
            '${porcentaje5Estrellas.toStringAsFixed(0)}%',
            _verde,
          ),
        ],
      ),
    );
  }

  Widget _buildMiniEstadistica(String label, String value, Color color) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        const SizedBox(height: 4),
        Text(label, style: TextStyle(fontSize: 10, color: Colors.grey[600])),
      ],
    );
  }
}
