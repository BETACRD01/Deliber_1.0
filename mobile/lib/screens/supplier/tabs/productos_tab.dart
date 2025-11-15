// lib/screens/supplier/tabs/productos_tab.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../controllers/supplier_controller.dart';

/// Tab de productos del proveedor
class ProductosTab extends StatelessWidget {
  const ProductosTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<SupplierController>(
      builder: (context, controller, child) {
        // Si no está verificado, mostrar mensaje
        if (!controller.verificado) {
          return _buildSinVerificar();
        }

        // Si no hay productos
        if (controller.productos.isEmpty) {
          return _buildVacio();
        }

        // Lista de productos
        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: controller.productos.length,
          itemBuilder: (context, index) {
            final producto = controller.productos[index];
            return _buildProductoCard(producto);
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
              'Tu cuenta debe ser verificada por el administrador antes de poder agregar productos.',
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
            Icon(Icons.inventory_2_outlined, size: 80, color: Colors.grey[300]),
            const SizedBox(height: 24),
            const Text(
              'Sin productos',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Text(
              'Aún no has agregado productos a tu catálogo.\nPresiona el botón + para comenzar.',
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

  Widget _buildProductoCard(Map<String, dynamic> producto) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        contentPadding: const EdgeInsets.all(12),
        leading: Container(
          width: 60,
          height: 60,
          decoration: BoxDecoration(
            color: Colors.grey[200],
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(Icons.image, color: Colors.grey[400]),
        ),
        title: Text(
          producto['nombre'] ?? 'Producto',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Text(
          '\$${producto['precio'] ?? '0.00'}',
          style: const TextStyle(
            color: Color(0xFF4CAF50),
            fontWeight: FontWeight.w600,
          ),
        ),
        trailing: Icon(
          Icons.arrow_forward_ios,
          size: 16,
          color: Colors.grey[400],
        ),
      ),
    );
  }
}
