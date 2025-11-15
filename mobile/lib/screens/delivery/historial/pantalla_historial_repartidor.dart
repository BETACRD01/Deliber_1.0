// lib/screens/delivery/historial/pantalla_historial_repartidor.dart

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

/// 📜 Pantalla de Historial del Repartidor
/// Muestra todas las entregas realizadas con detalles y estado
class PantallaHistorialRepartidor extends StatefulWidget {
  const PantallaHistorialRepartidor({super.key});

  @override
  State<PantallaHistorialRepartidor> createState() =>
      _PantallaHistorialRepartidorState();
}

class _PantallaHistorialRepartidorState
    extends State<PantallaHistorialRepartidor> {
  // ==========================================================
  // COLORES BASE
  // ==========================================================
  static const Color _naranja = Color(0xFFFF9800);
  static const Color _verde = Color(0xFF4CAF50);
  static const Color _rojo = Color(0xFFF44336);
  static const Color _grisFondo = Color(0xFFF5F5F5);

  // ==========================================================
  // DATOS DE EJEMPLO (simulados)
  // ==========================================================
  final List<Map<String, dynamic>> _historial = [
    {
      'fecha': DateTime(2025, 11, 6, 10, 15),
      'cliente': 'Carlos Quishpe',
      'direccion': 'Av. Amazonas y Sucre',
      'monto': 7.50,
      'estado': 'Entregado',
    },
    {
      'fecha': DateTime(2025, 11, 5, 18, 40),
      'cliente': 'María López',
      'direccion': 'Barrio El Paraíso',
      'monto': 6.00,
      'estado': 'Cancelado',
    },
    {
      'fecha': DateTime(2025, 11, 4, 12, 30),
      'cliente': 'Juan Pérez',
      'direccion': 'Calle Bolívar y Vargas Torres',
      'monto': 8.00,
      'estado': 'Entregado',
    },
    {
      'fecha': DateTime(2025, 11, 3, 20, 00),
      'cliente': 'Lucía Aguinda',
      'direccion': 'Av. del Ejército',
      'monto': 5.75,
      'estado': 'En curso',
    },
  ];

  String _busqueda = '';

  @override
  Widget build(BuildContext context) {
    final historialFiltrado = _historial.where((pedido) {
      final texto = _busqueda.toLowerCase();
      return pedido['cliente'].toLowerCase().contains(texto) ||
          pedido['direccion'].toLowerCase().contains(texto) ||
          pedido['estado'].toLowerCase().contains(texto);
    }).toList();

    final totalEntregas = _historial
        .where((p) => p['estado'] == 'Entregado')
        .length;
    final totalCanceladas = _historial
        .where((p) => p['estado'] == 'Cancelado')
        .length;

    return Scaffold(
      backgroundColor: _grisFondo,
      appBar: AppBar(
        title: const Text('Historial de Entregas'),
        backgroundColor: _naranja,
        elevation: 0,
      ),
      body: Column(
        children: [
          _buildResumen(totalEntregas, totalCanceladas),
          _buildBuscador(),
          Expanded(
            child: historialFiltrado.isEmpty
                ? _buildListaVacia()
                : ListView.builder(
                    itemCount: historialFiltrado.length,
                    padding: const EdgeInsets.all(8),
                    itemBuilder: (context, index) =>
                        _buildItem(historialFiltrado[index]),
                  ),
          ),
        ],
      ),
    );
  }

  // ==========================================================
  // RESUMEN SUPERIOR
  // ==========================================================
  Widget _buildResumen(int entregadas, int canceladas) {
    return Container(
      margin: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [_naranja, _verde],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildResumenItem(
            'Entregadas',
            entregadas,
            Icons.check_circle,
            _verde,
          ),
          _buildResumenItem('Canceladas', canceladas, Icons.cancel, _rojo),
          _buildResumenItem(
            'Total',
            _historial.length,
            Icons.list_alt,
            Colors.white,
          ),
        ],
      ),
    );
  }

  Widget _buildResumenItem(
    String titulo,
    int valor,
    IconData icono,
    Color color,
  ) {
    return Column(
      children: [
        Icon(
          icono,
          color: color == Colors.white ? Colors.white : color,
          size: 28,
        ),
        const SizedBox(height: 4),
        Text(
          '$valor',
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
        ),
        Text(
          titulo,
          style: const TextStyle(color: Colors.white70, fontSize: 13),
        ),
      ],
    );
  }

  // ==========================================================
  // BUSCADOR
  // ==========================================================
  Widget _buildBuscador() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: TextField(
        decoration: InputDecoration(
          prefixIcon: const Icon(Icons.search),
          hintText: 'Buscar por cliente, dirección o estado...',
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(30),
            borderSide: BorderSide.none,
          ),
        ),
        onChanged: (valor) => setState(() => _busqueda = valor),
      ),
    );
  }

  // ==========================================================
  // LISTA DE PEDIDOS
  // ==========================================================
  Widget _buildItem(Map<String, dynamic> pedido) {
    final fecha = DateFormat('dd/MM/yyyy hh:mm a').format(pedido['fecha']);
    final estado = pedido['estado'];
    final colorEstado = _getColorEstado(estado);
    final iconoEstado = _getIconoEstado(estado);

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 8),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      elevation: 2,
      child: ListTile(
        leading: Icon(iconoEstado, color: colorEstado, size: 30),
        title: Text(pedido['cliente']),
        subtitle: Text('${pedido['direccion']}\n$fecha'),
        isThreeLine: true,
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              '\$${pedido['monto'].toStringAsFixed(2)}',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
            ),
            const SizedBox(height: 4),
            Text(estado, style: TextStyle(color: colorEstado, fontSize: 13)),
          ],
        ),
      ),
    );
  }

  Color _getColorEstado(String estado) {
    switch (estado) {
      case 'Entregado':
        return _verde;
      case 'Cancelado':
        return _rojo;
      case 'En curso':
        return _naranja;
      default:
        return Colors.grey;
    }
  }

  IconData _getIconoEstado(String estado) {
    switch (estado) {
      case 'Entregado':
        return Icons.check_circle;
      case 'Cancelado':
        return Icons.cancel;
      case 'En curso':
        return Icons.delivery_dining;
      default:
        return Icons.help_outline;
    }
  }

  // ==========================================================
  // LISTA VACÍA
  // ==========================================================
  Widget _buildListaVacia() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: const [
            Icon(Icons.inbox, size: 64, color: Colors.grey),
            SizedBox(height: 12),
            Text(
              'No se encontraron pedidos',
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}
