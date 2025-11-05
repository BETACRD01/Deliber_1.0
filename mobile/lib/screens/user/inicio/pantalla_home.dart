// lib/screens/user/inicio/pantalla_home.dart

import 'package:flutter/material.dart';
import '../../../theme/jp_theme.dart';

// ══════════════════════════════════════════════════════════════════════════════
// 🏠 PANTALLA HOME - JP EXPRESS
// ══════════════════════════════════════════════════════════════════════════════

class PantallaHome extends StatelessWidget {
  const PantallaHome({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: CustomScrollView(
        slivers: [
          // AppBar con gradiente
          _buildSliverAppBar(context),

          // Contenido
          SliverToBoxAdapter(
            child: Column(
              children: [
                const SizedBox(height: 16),

                // Banner de bienvenida
                _buildBannerBienvenida(context),
                const SizedBox(height: 24),

                // Categorías
                _buildSeccionCategorias(context),
                const SizedBox(height: 24),

                // Promociones del día
                _buildSeccionPromociones(context),
                const SizedBox(height: 24),

                // Productos destacados
                _buildSeccionDestacados(context),
                const SizedBox(height: 24),

                // Estadísticas rápidas
                _buildEstadisticasRapidas(context),
                const SizedBox(height: 32),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ────────────────────────────────────────────────────────────────────────────
  // 🎨 SLIVER APP BAR CON GRADIENTE
  // ────────────────────────────────────────────────────────────────────────────

  Widget _buildSliverAppBar(BuildContext context) {
    return SliverAppBar(
      expandedHeight: 120,
      floating: false,
      pinned: true,
      flexibleSpace: Container(
        decoration: const BoxDecoration(gradient: JPColors.primaryGradient),
        child: FlexibleSpaceBar(
          title: const Text(
            '🚀 JP Express',
            style: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 20,
              color: Colors.white,
            ),
          ),
          centerTitle: false,
          titlePadding: const EdgeInsets.only(left: 16, bottom: 16),
          background: SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 50),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Spacer(),
                  // Badge de notificaciones
                  Stack(
                    children: [
                      IconButton(
                        icon: const Icon(
                          Icons.notifications_outlined,
                          color: Colors.white,
                        ),
                        onPressed: () {},
                      ),
                      Positioned(
                        right: 8,
                        top: 8,
                        child: Container(
                          padding: const EdgeInsets.all(4),
                          decoration: const BoxDecoration(
                            color: JPColors.secondary,
                            shape: BoxShape.circle,
                          ),
                          child: const Text(
                            '3',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  // ────────────────────────────────────────────────────────────────────────────
  // 🎉 BANNER DE BIENVENIDA - ✅ CORREGIDO OVERFLOW
  // ────────────────────────────────────────────────────────────────────────────

  Widget _buildBannerBienvenida(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Container(
        height: 160,
        decoration: BoxDecoration(
          gradient: JPColors.secondaryGradient,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: JPColors.secondary.withValues(alpha: 0.3),
              blurRadius: 20,
              offset: const Offset(0, 10),
            ),
          ],
        ),
        child: Stack(
          children: [
            // Patrón decorativo
            Positioned.fill(
              child: CustomPaint(painter: _CirclePatternPainter()),
            ),
            // Contenido - ✅ FIX: Envolver en SingleChildScrollView
            SingleChildScrollView(
              physics:
                  const NeverScrollableScrollPhysics(), // Solo para overflow
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisAlignment: MainAxisAlignment.center,
                        mainAxisSize: MainAxisSize.min, // ✅ IMPORTANTE
                        children: [
                          const Text(
                            '¡Hola Usuario! 👋',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 24,
                              fontWeight: FontWeight.bold,
                            ),
                            maxLines: 1, // ✅ Limitar líneas
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 6), // ✅ Reducir de 8 a 6
                          Text(
                            '¿Qué se te antoja hoy?',
                            style: TextStyle(
                              color: Colors.white.withValues(alpha: 0.9),
                              fontSize: 16,
                            ),
                            maxLines: 1, // ✅ Limitar líneas
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 10), // ✅ Reducir de 12 a 10
                          ElevatedButton(
                            onPressed: () {},
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.white,
                              foregroundColor: JPColors.secondary,
                              padding: const EdgeInsets.symmetric(
                                horizontal: 20, // ✅ Reducir de 24 a 20
                                vertical: 10, // ✅ Reducir de 12 a 10
                              ),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(30),
                              ),
                            ),
                            child: const Text(
                              'Ver Menú',
                              style: TextStyle(fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const Icon(
                      Icons.delivery_dining,
                      size: 80,
                      color: Colors.white54,
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ────────────────────────────────────────────────────────────────────────────
  // 🍕 SECCIÓN DE CATEGORÍAS
  // ────────────────────────────────────────────────────────────────────────────

  Widget _buildSeccionCategorias(BuildContext context) {
    final categorias = [
      _CategoriaData(Icons.fastfood, 'Comida', JPColors.error),
      _CategoriaData(Icons.local_drink, 'Bebidas', JPColors.info),
      _CategoriaData(Icons.cake, 'Postres', JPColors.accent),
      _CategoriaData(Icons.local_pizza, 'Pizza', JPColors.warning),
      _CategoriaData(Icons.restaurant, 'Snacks', JPColors.success),
      _CategoriaData(Icons.icecream, 'Helados', JPColors.primary),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            children: [
              Text('🎯 Categorías', style: JPTextStyles.h3),
              Spacer(),
              Text('Ver todo', style: TextStyle(color: JPColors.primary)),
            ],
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          height: 110,
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            scrollDirection: Axis.horizontal,
            itemCount: categorias.length,
            itemBuilder: (context, index) {
              final categoria = categorias[index];
              return _CategoriaCard(categoria: categoria);
            },
          ),
        ),
      ],
    );
  }

  // ────────────────────────────────────────────────────────────────────────────
  // 🔥 SECCIÓN DE PROMOCIONES
  // ────────────────────────────────────────────────────────────────────────────

  Widget _buildSeccionPromociones(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            children: [
              Text('🔥 Promociones del Día', style: JPTextStyles.h3),
              Spacer(),
              JPBadge(label: '50% OFF', color: JPColors.error),
            ],
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          height: 180,
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            scrollDirection: Axis.horizontal,
            itemCount: 3,
            itemBuilder: (context, index) {
              return _PromocionCard(
                titulo: 'Combo ${index + 1}',
                descuento: '${(index + 1) * 20}% OFF',
                precio: '\$${(12.99 - index * 2).toStringAsFixed(2)}',
              );
            },
          ),
        ),
      ],
    );
  }

  // ────────────────────────────────────────────────────────────────────────────
  // ⭐ SECCIÓN DE DESTACADOS
  // ────────────────────────────────────────────────────────────────────────────

  Widget _buildSeccionDestacados(BuildContext context) {
    final productos = [
      _ProductoData(
        'Hamburguesa Clásica',
        'Carne, queso, lechuga',
        12.99,
        4.5,
        120,
      ),
      _ProductoData('Pizza Familiar', '8 porciones de queso', 18.99, 4.8, 85),
      _ProductoData('Papas Premium', 'Con queso cheddar', 6.99, 4.3, 200),
      _ProductoData('Refresco Grande', 'Bebida 1L fría', 3.50, 4.0, 150),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 16),
          child: Text('⭐ Destacados', style: JPTextStyles.h3),
        ),
        const SizedBox(height: 12),
        ListView.separated(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: productos.length,
          separatorBuilder: (_, __) => const SizedBox(height: 12),
          itemBuilder: (context, index) {
            return _ProductoCard(producto: productos[index]);
          },
        ),
      ],
    );
  }

  // ────────────────────────────────────────────────────────────────────────────
  // 📊 ESTADÍSTICAS RÁPIDAS
  // ────────────────────────────────────────────────────────────────────────────

  Widget _buildEstadisticasRapidas(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          Expanded(
            child: _buildStatCard(
              icon: Icons.shopping_bag,
              label: 'Pedidos',
              value: '24',
              color: JPColors.primary,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _buildStatCard(
              icon: Icons.star,
              label: 'Puntos',
              value: '1.2K',
              color: JPColors.accent,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _buildStatCard(
              icon: Icons.local_offer,
              label: 'Cupones',
              value: '5',
              color: JPColors.secondary,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 32),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          Text(
            label,
            style: JPTextStyles.small.copyWith(color: JPColors.textSecondary),
          ),
        ],
      ),
    );
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// 📦 WIDGETS PERSONALIZADOS
// ══════════════════════════════════════════════════════════════════════════════

// ────────────────────────────────────────────────────────────────────────────
// Card de Categoría
// ────────────────────────────────────────────────────────────────────────────

class _CategoriaData {
  final IconData icon;
  final String nombre;
  final Color color;

  _CategoriaData(this.icon, this.nombre, this.color);
}

class _CategoriaCard extends StatelessWidget {
  final _CategoriaData categoria;

  const _CategoriaCard({required this.categoria});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 90,
      margin: const EdgeInsets.only(right: 12),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () {},
          borderRadius: BorderRadius.circular(16),
          child: Container(
            decoration: BoxDecoration(
              color: categoria.color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: categoria.color.withValues(alpha: 0.3),
                width: 2,
              ),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(categoria.icon, size: 36, color: categoria.color),
                const SizedBox(height: 8),
                Text(
                  categoria.nombre,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: categoria.color,
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Card de Promoción
// ────────────────────────────────────────────────────────────────────────────

class _PromocionCard extends StatelessWidget {
  final String titulo;
  final String descuento;
  final String precio;

  const _PromocionCard({
    required this.titulo,
    required this.descuento,
    required this.precio,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 160,
      margin: const EdgeInsets.only(right: 12),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [JPColors.error, JPColors.warning],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: JPColors.error.withValues(alpha: 0.3),
            blurRadius: 12,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () {},
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    descuento,
                    style: const TextStyle(
                      color: JPColors.error,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
                const Spacer(),
                Text(
                  titulo,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  precio,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Card de Producto
// ────────────────────────────────────────────────────────────────────────────

class _ProductoData {
  final String nombre;
  final String descripcion;
  final double precio;
  final double rating;
  final int ventas;

  _ProductoData(
    this.nombre,
    this.descripcion,
    this.precio,
    this.rating,
    this.ventas,
  );
}

class _ProductoCard extends StatelessWidget {
  final _ProductoData producto;

  const _ProductoCard({required this.producto});

  @override
  Widget build(BuildContext context) {
    return JPCard(
      padding: const EdgeInsets.all(12),
      onTap: () {},
      child: Row(
        children: [
          // Imagen del producto
          Hero(
            tag: 'producto_${producto.nombre}',
            child: Container(
              width: 90,
              height: 90,
              decoration: BoxDecoration(
                gradient: JPColors.primaryGradient,
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.fastfood, size: 48, color: Colors.white),
            ),
          ),
          const SizedBox(width: 12),
          // Información del producto
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  producto.nombre,
                  style: JPTextStyles.body.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Text(
                  producto.descripcion,
                  style: JPTextStyles.caption,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    const Icon(Icons.star, size: 16, color: JPColors.accent),
                    const SizedBox(width: 4),
                    Text(
                      '${producto.rating}',
                      style: JPTextStyles.small.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      '${producto.ventas} ventas',
                      style: JPTextStyles.small.copyWith(
                        color: JPColors.textSecondary,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  '\$${producto.precio.toStringAsFixed(2)}',
                  style: JPTextStyles.h3.copyWith(color: JPColors.primary),
                ),
              ],
            ),
          ),
          // Botón de agregar
          Container(
            decoration: BoxDecoration(
              color: JPColors.secondary,
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: JPColors.secondary.withValues(alpha: 0.3),
                  blurRadius: 8,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: IconButton(
              onPressed: () {},
              icon: const Icon(Icons.add_shopping_cart, color: Colors.white),
              tooltip: 'Agregar al carrito',
            ),
          ),
        ],
      ),
    );
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Painter de Patrón Circular
// ────────────────────────────────────────────────────────────────────────────

class _CirclePatternPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withValues(alpha: 0.1)
      ..style = PaintingStyle.fill;

    // Círculos decorativos
    canvas.drawCircle(Offset(size.width * 0.8, size.height * 0.2), 40, paint);
    canvas.drawCircle(Offset(size.width * 0.9, size.height * 0.7), 30, paint);
    canvas.drawCircle(Offset(size.width * 0.7, size.height * 0.9), 25, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
