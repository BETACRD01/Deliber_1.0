import 'package:flutter/material.dart';

class PantallaMisPedidos extends StatefulWidget {
  const PantallaMisPedidos({super.key});

  @override
  State<PantallaMisPedidos> createState() => _PantallaMisPedidosState();
}

class _PantallaMisPedidosState extends State<PantallaMisPedidos> {
  // Datos de ejemplo
  final List<Map<String, dynamic>> _pedidos = [
    {
      'id': '#001',
      'fecha': '15 Oct 2025',
      'estado': 'Entregado',
      'total': 25.50,
      'items': 3,
      'color': Colors.green,
    },
    {
      'id': '#002',
      'fecha': '14 Oct 2025',
      'estado': 'En camino',
      'total': 18.75,
      'items': 2,
      'color': Colors.blue,
    },
    {
      'id': '#003',
      'fecha': '13 Oct 2025',
      'estado': 'Preparando',
      'total': 32.00,
      'items': 4,
      'color': Colors.orange,
    },
    {
      'id': '#004',
      'fecha': '12 Oct 2025',
      'estado': 'Entregado',
      'total': 15.25,
      'items': 2,
      'color': Colors.green,
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mis Pedidos'), elevation: 0),
      body: _pedidos.isEmpty ? _buildSinPedidos() : _buildListaPedidos(),
    );
  }

  Widget _buildSinPedidos() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.shopping_bag_outlined, size: 100, color: Colors.grey[400]),
          const SizedBox(height: 24),
          Text(
            'No tienes pedidos',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Colors.grey[700],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Tus pedidos aparecerán aquí',
            style: TextStyle(fontSize: 14, color: Colors.grey[500]),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () {
              // Navegar a la pantalla de inicio
            },
            icon: const Icon(Icons.shopping_cart),
            label: const Text('Comenzar a comprar'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildListaPedidos() {
    return ListView.builder(
      padding: const EdgeInsets.all(16.0),
      itemCount: _pedidos.length,
      itemBuilder: (context, index) {
        final pedido = _pedidos[index];
        return _buildTarjetaPedido(pedido);
      },
    );
  }

  Widget _buildTarjetaPedido(Map<String, dynamic> pedido) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        onTap: () {
          _mostrarDetallePedido(pedido);
        },
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Encabezado del pedido
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Pedido ${pedido['id']}',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: pedido['color'].withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      pedido['estado'],
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: pedido['color'],
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // Información del pedido
              Row(
                children: [
                  Icon(Icons.calendar_today, size: 16, color: Colors.grey[600]),
                  const SizedBox(width: 8),
                  Text(
                    pedido['fecha'],
                    style: TextStyle(fontSize: 14, color: Colors.grey[600]),
                  ),
                  const SizedBox(width: 16),
                  Icon(
                    Icons.shopping_basket,
                    size: 16,
                    color: Colors.grey[600],
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '${pedido['items']} items',
                    style: TextStyle(fontSize: 14, color: Colors.grey[600]),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // Divider
              Divider(color: Colors.grey[300]),
              const SizedBox(height: 12),

              // Total y acciones
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Total',
                        style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                      ),
                      Text(
                        '\$${pedido['total'].toStringAsFixed(2)}',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Theme.of(context).primaryColor,
                        ),
                      ),
                    ],
                  ),
                  Row(
                    children: [
                      if (pedido['estado'] == 'En camino')
                        OutlinedButton.icon(
                          onPressed: () {},
                          icon: const Icon(Icons.location_on, size: 16),
                          label: const Text('Rastrear'),
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 16,
                              vertical: 8,
                            ),
                          ),
                        ),
                      if (pedido['estado'] == 'Entregado')
                        TextButton(
                          onPressed: () {},
                          child: const Text('Volver a pedir'),
                        ),
                    ],
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _mostrarDetallePedido(Map<String, dynamic> pedido) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return Container(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Detalle del Pedido ${pedido['id']}',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.close),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              _buildDetalleItem('Estado', pedido['estado']),
              _buildDetalleItem('Fecha', pedido['fecha']),
              _buildDetalleItem('Items', '${pedido['items']} productos'),
              _buildDetalleItem(
                'Total',
                '\$${pedido['total'].toStringAsFixed(2)}',
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Cerrar'),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildDetalleItem(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontSize: 14, color: Colors.grey[600])),
          Text(
            value,
            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }
}
