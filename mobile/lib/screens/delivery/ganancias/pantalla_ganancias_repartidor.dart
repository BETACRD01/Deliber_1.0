import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

/// 💵 Pantalla de Ganancias del Repartidor
/// Muestra resumen de ingresos, historial de entregas y estadísticas
class PantallaGananciasRepartidor extends StatefulWidget {
  const PantallaGananciasRepartidor({super.key});

  @override
  State<PantallaGananciasRepartidor> createState() =>
      _PantallaGananciasRepartidorState();
}

class _PantallaGananciasRepartidorState
    extends State<PantallaGananciasRepartidor> {
  // ==========================================================
  // COLORES BASE
  // ==========================================================
  static const Color _naranja = Color(0xFFFF9800);
  static const Color _verde = Color(0xFF4CAF50);
  static const Color _grisFondo = Color(0xFFF5F5F5);

  // ==========================================================
  // DATOS SIMULADOS (puedes conectarlo con Firestore o API)
  // ==========================================================
  double gananciasTotales = 256.75;
  double gananciasSemana = 48.20;
  double gananciasHoy = 12.50;

  final List<Map<String, dynamic>> entregas = [
    {
      'fecha': DateTime(2025, 11, 5, 14, 30),
      'monto': 6.5,
      'cliente': 'Juan Pérez',
      'direccion': 'Av. Tena y Amazonas',
    },
    {
      'fecha': DateTime(2025, 11, 5, 16, 45),
      'monto': 6.0,
      'cliente': 'María Gómez',
      'direccion': 'Barrio El Progreso',
    },
    {
      'fecha': DateTime(2025, 11, 4, 12, 20),
      'monto': 7.0,
      'cliente': 'Carlos Quishpe',
      'direccion': 'Parque Central',
    },
    {
      'fecha': DateTime(2025, 11, 3, 19, 10),
      'monto': 8.0,
      'cliente': 'Ana López',
      'direccion': 'Av. del Ejército',
    },
  ];

  // ==========================================================
  // CONSTRUCCIÓN DE UI
  // ==========================================================
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _grisFondo,
      appBar: AppBar(
        title: const Text('Mis Ganancias'),
        backgroundColor: _naranja,
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildResumenGeneral(),
          const SizedBox(height: 16),
          _buildEstadisticasSemanal(),
          const SizedBox(height: 16),
          _buildListaEntregas(),
        ],
      ),
    );
  }

  // ==========================================================
  // RESUMEN GENERAL
  // ==========================================================
  Widget _buildResumenGeneral() {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [_naranja, _verde],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const Text(
            'Resumen General',
            style: TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 18,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            '\$${gananciasTotales.toStringAsFixed(2)}',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 36,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Ganancia total acumulada',
            style: TextStyle(color: Colors.white70, fontSize: 14),
          ),
        ],
      ),
    );
  }

  // ==========================================================
  // ESTADÍSTICAS SEMANALES
  // ==========================================================
  Widget _buildEstadisticasSemanal() {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Estadísticas recientes',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildEstadisticaItem('Hoy', gananciasHoy, Icons.today),
                _buildEstadisticaItem(
                  'Semana',
                  gananciasSemana,
                  Icons.bar_chart,
                ),
                _buildEstadisticaItem(
                  'Total',
                  gananciasTotales,
                  Icons.attach_money,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEstadisticaItem(String titulo, double valor, IconData icono) {
    return Column(
      children: [
        Icon(icono, color: _naranja, size: 28),
        const SizedBox(height: 6),
        Text(
          '\$${valor.toStringAsFixed(2)}',
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        Text(titulo, style: TextStyle(color: Colors.grey[600])),
      ],
    );
  }

  // ==========================================================
  // LISTA DE ENTREGAS
  // ==========================================================
  Widget _buildListaEntregas() {
    if (entregas.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: const [
              Icon(Icons.inbox, size: 60, color: Colors.grey),
              SizedBox(height: 12),
              Text(
                'No hay entregas registradas',
                style: TextStyle(color: Colors.grey),
              ),
            ],
          ),
        ),
      );
    }

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.all(12),
            child: Text(
              'Historial de Entregas',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
          ),
          const Divider(height: 1),
          // ✅ Eliminado .toList() innecesario
          ...entregas.map((e) => _buildEntregaItem(e)),
        ],
      ),
    );
  }

  Widget _buildEntregaItem(Map<String, dynamic> e) {
    final fecha = DateFormat('dd/MM/yyyy hh:mm a').format(e['fecha']);
    return ListTile(
      leading: const Icon(Icons.delivery_dining, color: _verde),
      title: Text('${e['cliente']} - \$${e['monto']}'),
      subtitle: Text('${e['direccion']}\n$fecha'),
      isThreeLine: true,
      // ✅ Corregido: Color con MaterialColor válido
      trailing: Icon(Icons.check_circle, color: Colors.green.shade400),
    );
  }
}
