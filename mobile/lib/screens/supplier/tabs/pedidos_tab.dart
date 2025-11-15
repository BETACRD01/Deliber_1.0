// lib/screens/supplier/tabs/pedidos_tab.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../controllers/supplier_controller.dart';

/// Tab de pedidos pendientes del proveedor
class PedidosTab extends StatelessWidget {
  const PedidosTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<SupplierController>(
      builder: (context, controller, child) {
        // Si no está verificado, mostrar mensaje
        if (!controller.verificado) {
          return _buildSinVerificar();
        }

        // Si no hay pedidos pendientes
        if (controller.pedidosPendientes.isEmpty) {
          return _buildVacio();
        }

        // Lista de pedidos
        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: controller.pedidosPendientes.length,
          itemBuilder: (context, index) {
            final pedido = controller.pedidosPendientes[index];
            return _buildPedidoCard(pedido);
          },
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
              'Tu cuenta debe ser verificada para poder recibir pedidos.',
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

  Widget _buildVacio() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.shopping_cart_outlined,
              size: 80,
              color: Colors.grey[300],
            ),
            const SizedBox(height: 24),
            const Text(
              'Sin pedidos pendientes',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Text(
              '¡Excelente! No tienes pedidos pendientes por procesar.',
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

  Widget _buildPedidoCard(Map<String, dynamic> pedido) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Pedido #${pedido['id'] ?? '000'}',
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFF9800).withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Text(
                    'PENDIENTE',
                    style: TextStyle(
                      color: Color(0xFFFF9800),
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              'Total: \$${pedido['total'] ?? '0.00'}',
              style: const TextStyle(
                color: Color(0xFF4CAF50),
                fontWeight: FontWeight.w600,
                fontSize: 16,
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Icon(Icons.access_time, size: 14, color: Colors.grey[600]),
                const SizedBox(width: 4),
                Text(
                  pedido['fecha'] ?? 'Hace unos minutos',
                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
