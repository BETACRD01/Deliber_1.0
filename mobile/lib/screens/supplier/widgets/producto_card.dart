// lib/screens/supplier/widgets/producto_card.dart

import 'package:flutter/material.dart';

/// Card para mostrar un producto del proveedor
class ProductoCard extends StatelessWidget {
  final Map<String, dynamic> producto;
  final VoidCallback? onTap;

  const ProductoCard({super.key, required this.producto, this.onTap});

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
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              // Imagen del producto
              _buildImagen(),
              const SizedBox(width: 12),
              // Información del producto
              Expanded(child: _buildInfo()),
              // Icono de acción
              Icon(Icons.arrow_forward_ios, size: 16, color: Colors.grey[400]),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildImagen() {
    final imagen = producto['imagen'] ?? producto['logo'];

    return Container(
      width: 60,
      height: 60,
      decoration: BoxDecoration(
        color: Colors.grey[200],
        borderRadius: BorderRadius.circular(8),
        image: imagen != null
            ? DecorationImage(image: NetworkImage(imagen), fit: BoxFit.cover)
            : null,
      ),
      child: imagen == null
          ? Icon(Icons.image, color: Colors.grey[400], size: 28)
          : null,
    );
  }

  Widget _buildInfo() {
    final nombre = producto['nombre'] ?? 'Producto';
    final precio = producto['precio'] ?? 0.0;
    final stock = producto['stock'] ?? producto['cantidad'];
    final disponible = producto['disponible'] ?? true;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Nombre del producto
        Text(
          nombre,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        const SizedBox(height: 4),
        // Precio
        Text(
          '\$${_formatPrecio(precio)}',
          style: const TextStyle(
            color: Color(0xFF4CAF50),
            fontWeight: FontWeight.w600,
            fontSize: 16,
          ),
        ),
        const SizedBox(height: 4),
        // Stock y disponibilidad
        Row(
          children: [
            if (stock != null) ...[
              Icon(
                Icons.inventory_2_outlined,
                size: 14,
                color: Colors.grey[600],
              ),
              const SizedBox(width: 4),
              Text(
                'Stock: $stock',
                style: TextStyle(fontSize: 12, color: Colors.grey[600]),
              ),
              const SizedBox(width: 12),
            ],
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: disponible
                    ? Color(0xFF4CAF50).withValues(alpha: 0.1)
                    : Colors.red.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                disponible ? 'Disponible' : 'No disponible',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  color: disponible ? const Color(0xFF4CAF50) : Colors.red,
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  String _formatPrecio(dynamic precio) {
    if (precio is String) {
      return precio;
    }
    if (precio is num) {
      return precio.toStringAsFixed(2);
    }
    return '0.00';
  }
}
