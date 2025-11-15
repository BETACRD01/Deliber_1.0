// lib/screens/supplier/pantalla_inicio_proveedor.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../config/rutas.dart';
import 'controllers/supplier_controller.dart';
import 'widgets/supplier_drawer.dart';
import 'widgets/supplier_stats_header.dart';
import 'tabs/productos_tab.dart';
import 'tabs/pedidos_tab.dart';
import 'tabs/estadisticas_tab.dart';

/// Pantalla principal para PROVEEDORES
/// Dashboard con productos, pedidos pendientes y estadísticas
class PantallaInicioProveedor extends StatefulWidget {
  const PantallaInicioProveedor({super.key});

  @override
  State<PantallaInicioProveedor> createState() =>
      _PantallaInicioProveedorState();
}

class _PantallaInicioProveedorState extends State<PantallaInicioProveedor>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  // ============================================
  // CONSTANTES
  // ============================================

  static const Color _azul = Color(0xFF2196F3);
  static const Color _azulOscuro = Color(0xFF1976D2);
  static const Color _verde = Color(0xFF4CAF50);
  static const Color _naranja = Color(0xFFFF9800);
  static const Color _rojo = Color(0xFFF44336);

  // ============================================
  // CICLO DE VIDA
  // ============================================

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);

    // Cargar datos después del primer frame
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        context.read<SupplierController>().cargarDatos();
      }
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  // ============================================
  // MÉTODOS - ACCIONES
  // ============================================

  Future<void> _cerrarSesion() async {
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Row(
          children: [
            const Icon(Icons.logout, color: _rojo),
            const SizedBox(width: 12),
            const Text('Cerrar Sesión'),
          ],
        ),
        content: const Text('¿Estás seguro que deseas cerrar sesión?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: _rojo,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: const Text('Cerrar Sesión'),
          ),
        ],
      ),
    );

    if (confirmar == true && mounted) {
      final controller = context.read<SupplierController>();
      final success = await controller.cerrarSesion();

      if (success && mounted) {
        Rutas.irAYLimpiar(context, Rutas.login);
      }
    }
  }

  void _agregarProducto() {
    final controller = context.read<SupplierController>();

    if (!controller.verificado) {
      _mostrarMensaje(
        'Necesitas verificar tu cuenta para agregar productos',
        tipo: _TipoMensaje.advertencia,
      );
      return;
    }

    // TODO: Navegar a pantalla de agregar producto
    _mostrarMensaje('Funcionalidad próximamente');
  }

  void _mostrarMensaje(
    String mensaje, {
    _TipoMensaje tipo = _TipoMensaje.info,
  }) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(mensaje),
        backgroundColor: _getColorMensaje(tipo),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        margin: const EdgeInsets.all(16),
      ),
    );
  }

  // ============================================
  // MÉTODOS - BUILD UI
  // ============================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: _buildAppBar(),
      drawer: SupplierDrawer(onCerrarSesion: _cerrarSesion),
      body: Consumer<SupplierController>(
        builder: (context, controller, child) {
          if (controller.loading) {
            return _buildCargando();
          }

          if (controller.rolIncorrecto) {
            return _buildAccesoDenegado(controller.error ?? 'Acceso denegado');
          }

          if (controller.error != null) {
            return _buildError(controller.error!);
          }

          return _buildContenido(controller);
        },
      ),
      floatingActionButton: _buildFAB(),
    );
  }

  // ============================================
  // APP BAR
  // ============================================

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      title: const Text(
        'Dashboard Proveedor',
        style: TextStyle(fontWeight: FontWeight.bold),
      ),
      elevation: 0,
      flexibleSpace: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [_azul, _azulOscuro],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
      ),
      actions: [
        // Indicador de verificación
        Consumer<SupplierController>(
          builder: (context, controller, child) {
            if (controller.verificado) return const SizedBox.shrink();

            return Padding(
              padding: const EdgeInsets.only(right: 8),
              child: Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: _naranja.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: _naranja, width: 1.5),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.warning_amber,
                        color: _naranja,
                        size: 16,
                      ),
                      const SizedBox(width: 4),
                      const Text(
                        'Sin verificar',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
        IconButton(
          icon: const Icon(Icons.refresh),
          onPressed: () => context.read<SupplierController>().refrescar(),
          tooltip: 'Actualizar',
        ),
      ],
      bottom: TabBar(
        controller: _tabController,
        indicatorColor: Colors.white,
        indicatorWeight: 3,
        tabs: const [
          Tab(
            text: 'Productos',
            icon: Icon(Icons.inventory_2_outlined, size: 22),
          ),
          Tab(
            text: 'Pedidos',
            icon: Icon(Icons.shopping_cart_outlined, size: 22),
          ),
          Tab(
            text: 'Estadísticas',
            icon: Icon(Icons.analytics_outlined, size: 22),
          ),
        ],
      ),
    );
  }

  // ============================================
  // BODY - CONTENIDO PRINCIPAL
  // ============================================

  Widget _buildContenido(SupplierController controller) {
    return Column(
      children: [
        SupplierStatsHeader(
          productos: controller.totalProductos,
          pendientes: controller.pedidosPendientesCount,
          ventasHoy: controller.ventasHoy,
        ),
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: const [ProductosTab(), PedidosTab(), EstadisticasTab()],
          ),
        ),
      ],
    );
  }

  // ============================================
  // BODY - ESTADOS
  // ============================================

  Widget _buildCargando() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(color: _azul, strokeWidth: 3),
          const SizedBox(height: 24),
          Text(
            'Cargando información...',
            style: TextStyle(color: Colors.grey[600], fontSize: 16),
          ),
        ],
      ),
    );
  }

  Widget _buildAccesoDenegado(String mensaje) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: _naranja.withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(Icons.block, size: 64, color: _naranja),
            ),
            const SizedBox(height: 24),
            Text(
              'Acceso Denegado',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.grey[800],
              ),
            ),
            const SizedBox(height: 12),
            Text(
              mensaje,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16, color: Colors.grey[600]),
            ),
            const SizedBox(height: 8),
            Text(
              'Esta pantalla es exclusiva para proveedores.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, color: Colors.grey[500]),
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: () => Rutas.irAYLimpiar(context, Rutas.router),
              icon: const Icon(Icons.home),
              label: const Text('Volver al Inicio'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _azul,
                padding: const EdgeInsets.symmetric(
                  horizontal: 32,
                  vertical: 16,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
            const SizedBox(height: 12),
            TextButton(
              onPressed: _cerrarSesion,
              child: const Text(
                'Cerrar Sesión',
                style: TextStyle(color: _rojo),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildError(String mensaje) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: _rojo.withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(Icons.error_outline, size: 64, color: _rojo),
            ),
            const SizedBox(height: 24),
            Text(
              'Oops!',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.grey[800],
              ),
            ),
            const SizedBox(height: 12),
            Text(
              mensaje,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16, color: Colors.grey[600]),
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: () => context.read<SupplierController>().refrescar(),
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _azul,
                padding: const EdgeInsets.symmetric(
                  horizontal: 32,
                  vertical: 16,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================
  // FAB
  // ============================================

  Widget? _buildFAB() {
    return Consumer<SupplierController>(
      builder: (context, controller, child) {
        if (controller.rolIncorrecto || controller.loading) {
          return const SizedBox.shrink();
        }

        if (!controller.verificado) {
          return const SizedBox.shrink();
        }

        return FloatingActionButton.extended(
          onPressed: _agregarProducto,
          backgroundColor: _verde,
          icon: const Icon(Icons.add_circle_outline),
          label: const Text(
            'Nuevo Producto',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          elevation: 4,
        );
      },
    );
  }

  // ============================================
  // UTILIDADES
  // ============================================

  Color _getColorMensaje(_TipoMensaje tipo) {
    return switch (tipo) {
      _TipoMensaje.exito => _verde,
      _TipoMensaje.error => _rojo,
      _TipoMensaje.advertencia => _naranja,
      _TipoMensaje.info => _azul,
    };
  }
}

// ============================================
// ENUMS
// ============================================

enum _TipoMensaje { exito, error, advertencia, info }
