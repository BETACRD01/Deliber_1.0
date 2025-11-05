// lib/screens/supplier/pantalla_inicio_proveedor.dart

import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import '../../config/rutas.dart';
import '../../apis/helpers/api_exception.dart';

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
  // ============================================
  // SERVICIOS Y CONTROLADORES
  // ============================================
  final _api = AuthService();
  late TabController _tabController;

  // ============================================
  // ESTADO
  // ============================================
  Map<String, dynamic>? _usuario;
  bool _loading = true;
  bool _verificado = false;
  String? _error;

  // Datos simulados (reemplazar con datos reales de la API)
  final List<Map<String, dynamic>> _productos = [];
  final List<Map<String, dynamic>> _pedidosPendientes = [];

  // ============================================
  // COLORES
  // ============================================
  static const Color _azul = Color(0xFF2196F3);
  static const Color _azulOscuro = Color(0xFF1976D2);
  static const Color _verde = Color(0xFF4CAF50);
  static const Color _naranja = Color(0xFFFF9800);
  static const Color _rojo = Color(0xFFF44336);
  static const Color _gris = Color(0xFF757575);

  // ============================================
  // CICLO DE VIDA
  // ============================================

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _cargarDatos();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  // ============================================
  // MÉTODOS DE DATOS
  // ============================================

  Future<void> _cargarDatos() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final perfil = await _api.getPerfil();

      if (mounted) {
        setState(() {
          _usuario = perfil['usuario'];
          _verificado = _usuario?['verificado'] ?? false;
          _loading = false;
        });

        // Cargar productos y pedidos (implementar cuando tengas los endpoints)
        // await _cargarProductos();
        // await _cargarPedidos();
      }
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          _error = e.message;
          _loading = false;
        });

        if (e.isAuthError) {
          Rutas.irAYLimpiar(context, Rutas.login);
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Error al cargar información';
          _loading = false;
        });
      }
    }
  }

  Future<void> _cerrarSesion() async {
    final confirmar = await Rutas.mostrarDialogo<bool>(
      context,
      AlertDialog(
        title: const Text('Cerrar Sesión'),
        content: const Text('¿Estás seguro que deseas cerrar sesión?'),
        actions: [
          TextButton(
            onPressed: () => Rutas.volver(context, false),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () => Rutas.volver(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: _rojo),
            child: const Text('Cerrar Sesión'),
          ),
        ],
      ),
    );

    if (confirmar == true) {
      await _api.logout();
      if (mounted) {
        Rutas.irAYLimpiar(context, Rutas.login);
      }
    }
  }

  // ============================================
  // UI - BUILD PRINCIPAL
  // ============================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: _buildAppBar(),
      drawer: _buildDrawer(),
      body: _loading ? _buildCargando() : _buildContenido(),
      floatingActionButton: _verificado ? _buildFAB() : null,
    );
  }

  // ============================================
  // APP BAR
  // ============================================

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      title: const Text('Dashboard Proveedor'),
      elevation: 0,
      flexibleSpace: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [_azul, _azulOscuro],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
      ),
      actions: [
        // Indicador de verificación
        if (!_verificado)
          Padding(
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
                    Icon(Icons.warning_amber, color: _naranja, size: 16),
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
          ),
        IconButton(
          icon: const Icon(Icons.refresh),
          onPressed: _cargarDatos,
          tooltip: 'Actualizar',
        ),
      ],
      bottom: TabBar(
        controller: _tabController,
        indicatorColor: Colors.white,
        tabs: const [
          Tab(text: 'Productos', icon: Icon(Icons.inventory, size: 20)),
          Tab(text: 'Pedidos', icon: Icon(Icons.shopping_cart, size: 20)),
          Tab(text: 'Estadísticas', icon: Icon(Icons.analytics, size: 20)),
        ],
      ),
    );
  }

  // ============================================
  // DRAWER
  // ============================================

  Widget _buildDrawer() {
    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          _buildDrawerHeader(),
          if (!_verificado) _buildAlertaVerificacion(),
          const Divider(),
          ListTile(
            leading: Icon(Icons.store, color: _azul),
            title: const Text('Mi Negocio'),
            subtitle: Text(_usuario?['nombre_negocio'] ?? ''),
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a detalles del negocio
            },
          ),
          ListTile(
            leading: Icon(Icons.inventory_2, color: _verde),
            title: const Text('Gestionar Productos'),
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a productos
            },
          ),
          ListTile(
            leading: Icon(Icons.attach_money, color: Colors.green[700]),
            title: const Text('Ventas y Reportes'),
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a reportes
            },
          ),
          ListTile(
            leading: Icon(Icons.local_offer, color: _naranja),
            title: const Text('Promociones'),
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a promociones
            },
          ),
          ListTile(
            leading: Icon(Icons.person, color: _azul),
            title: const Text('Mi Perfil'),
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a perfil
            },
          ),
          ListTile(
            leading: Icon(Icons.settings, color: _gris),
            title: const Text('Configuración'),
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a configuración
            },
          ),
          ListTile(
            leading: Icon(Icons.help_outline, color: Colors.blue[700]),
            title: const Text('Ayuda y Soporte'),
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a ayuda
            },
          ),
          const Divider(),
          ListTile(
            leading: Icon(Icons.logout, color: _rojo),
            title: const Text('Cerrar Sesión'),
            onTap: _cerrarSesion,
          ),
        ],
      ),
    );
  }

  Widget _buildDrawerHeader() {
    return UserAccountsDrawerHeader(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [_azul, _azulOscuro],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      currentAccountPicture: CircleAvatar(
        backgroundColor: Colors.white,
        child: Icon(Icons.store, size: 40, color: _azul),
      ),
      accountName: Text(
        _usuario?['nombre_negocio'] ?? 'Nombre del Negocio',
        style: const TextStyle(fontWeight: FontWeight.bold),
      ),
      accountEmail: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(_usuario?['email'] ?? ''),
          const SizedBox(height: 4),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: _verificado ? _verde : _naranja,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              _verificado ? '✓ Verificado' : '⚠ Sin verificar',
              style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAlertaVerificacion() {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _naranja.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _naranja, width: 2),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Icon(Icons.warning_amber, color: _naranja, size: 32),
              const SizedBox(width: 12),
              const Expanded(
                child: Text(
                  'Cuenta sin verificar',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          const Text(
            'Tu cuenta está pendiente de verificación por el administrador. '
            'Mientras tanto, puedes explorar la plataforma con funcionalidad limitada.',
            style: TextStyle(fontSize: 13),
          ),
          const SizedBox(height: 12),
          ElevatedButton.icon(
            onPressed: () {
              // TODO: Mostrar información sobre verificación
            },
            icon: const Icon(Icons.info_outline, size: 18),
            label: const Text('Más información'),
            style: ElevatedButton.styleFrom(
              backgroundColor: _naranja,
              foregroundColor: Colors.white,
              minimumSize: const Size(double.infinity, 36),
            ),
          ),
        ],
      ),
    );
  }

  // ============================================
  // CONTENIDO PRINCIPAL
  // ============================================

  Widget _buildContenido() {
    if (_error != null) {
      return _buildError();
    }

    return Column(
      children: [
        _buildEstadisticasHeader(),
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: [
              _buildProductos(),
              _buildPedidos(),
              _buildEstadisticas(),
            ],
          ),
        ),
      ],
    );
  }

  // ============================================
  // ESTADÍSTICAS HEADER
  // ============================================

  Widget _buildEstadisticasHeader() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [_azul.withValues(alpha: 0.1), Colors.white],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: Row(
        children: [
          _buildEstadistica('Productos', '0', Icons.inventory, _azul),
          const SizedBox(width: 12),
          _buildEstadistica('Pendientes', '0', Icons.pending, _naranja),
          const SizedBox(width: 12),
          _buildEstadistica('Ventas Hoy', '\$0.00', Icons.attach_money, _verde),
        ],
      ),
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
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  // ============================================
  // TABS DE CONTENIDO
  // ============================================

  Widget _buildProductos() {
    if (!_verificado) {
      return _buildMensajeVerificacion(
        'Gestión de productos no disponible',
        'Necesitas que tu cuenta sea verificada para poder agregar y gestionar productos.',
      );
    }

    if (_productos.isEmpty) {
      return _buildListaVacia(
        icono: Icons.inventory_2,
        mensaje: 'No tienes productos registrados',
        submensaje: 'Comienza agregando tus primeros productos',
        botonTexto: 'Agregar Producto',
        botonAccion: () {
          // TODO: Navegar a agregar producto
        },
      );
    }

    return RefreshIndicator(
      onRefresh: _cargarDatos,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _productos.length,
        itemBuilder: (context, index) {
          final producto = _productos[index];
          return _buildCardProducto(producto);
        },
      ),
    );
  }

  Widget _buildPedidos() {
    if (!_verificado) {
      return _buildMensajeVerificacion(
        'Gestión de pedidos no disponible',
        'Necesitas verificación para recibir y gestionar pedidos.',
      );
    }

    if (_pedidosPendientes.isEmpty) {
      return _buildListaVacia(
        icono: Icons.shopping_cart,
        mensaje: 'No hay pedidos pendientes',
        submensaje: 'Los pedidos de tus clientes aparecerán aquí',
      );
    }

    return RefreshIndicator(
      onRefresh: _cargarDatos,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _pedidosPendientes.length,
        itemBuilder: (context, index) {
          final pedido = _pedidosPendientes[index];
          return _buildCardPedido(pedido);
        },
      ),
    );
  }

  Widget _buildEstadisticas() {
    if (!_verificado) {
      return _buildMensajeVerificacion(
        'Estadísticas no disponibles',
        'Las estadísticas de ventas estarán disponibles una vez verificada tu cuenta.',
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          _buildCardEstadistica(
            'Ventas del Mes',
            '\$0.00',
            Icons.trending_up,
            _verde,
            '+0%',
          ),
          const SizedBox(height: 16),
          _buildCardEstadistica(
            'Pedidos Completados',
            '0',
            Icons.check_circle,
            _azul,
            'este mes',
          ),
          const SizedBox(height: 16),
          _buildCardEstadistica(
            'Valoración Promedio',
            '0.0',
            Icons.star,
            _naranja,
            '0 reseñas',
          ),
          const SizedBox(height: 16),
          _buildCardEstadistica(
            'Productos Activos',
            '0',
            Icons.inventory,
            _azulOscuro,
            'publicados',
          ),
        ],
      ),
    );
  }

  // ============================================
  // CARDS
  // ============================================

  Widget _buildCardProducto(Map<String, dynamic> producto) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: () {
          // TODO: Ver detalles del producto
        },
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  color: Colors.grey[200],
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(Icons.image, size: 40, color: Colors.grey[400]),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      producto['nombre'] ?? 'Producto',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      producto['categoria'] ?? 'Categoría',
                      style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '\$${producto['precio'] ?? '0.00'}',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: _verde,
                      ),
                    ),
                  ],
                ),
              ),
              Column(
                children: [
                  IconButton(
                    icon: Icon(Icons.edit, color: _azul),
                    onPressed: () {
                      // TODO: Editar producto
                    },
                  ),
                  IconButton(
                    icon: Icon(Icons.delete, color: _rojo),
                    onPressed: () {
                      // TODO: Eliminar producto
                    },
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCardPedido(Map<String, dynamic> pedido) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: () {
          // TODO: Ver detalles del pedido
        },
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: _azul.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(Icons.shopping_bag, color: _azul, size: 24),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Pedido #${pedido['id']}',
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          pedido['cliente'] ?? 'Cliente',
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  ),
                  Chip(
                    label: Text(
                      pedido['estado'] ?? 'Pendiente',
                      style: const TextStyle(fontSize: 11, color: Colors.white),
                    ),
                    backgroundColor: _naranja,
                    padding: EdgeInsets.zero,
                  ),
                ],
              ),
              const Divider(height: 24),
              Row(
                children: [
                  Icon(Icons.shopping_cart, size: 18, color: Colors.grey[600]),
                  const SizedBox(width: 8),
                  Text(
                    '${pedido['cantidad'] ?? 0} productos',
                    style: const TextStyle(fontSize: 13),
                  ),
                  const Spacer(),
                  Text(
                    '\$${pedido['total'] ?? '0.00'}',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: _verde,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () {
                        // TODO: Rechazar pedido
                      },
                      icon: const Icon(Icons.close, size: 18),
                      label: const Text('Rechazar'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: _rojo,
                        side: BorderSide(color: _rojo),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton.icon(
                      onPressed: () {
                        // TODO: Aceptar pedido
                      },
                      icon: const Icon(Icons.check, size: 18),
                      label: const Text('Aceptar'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: _verde,
                        foregroundColor: Colors.white,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCardEstadistica(
    String titulo,
    String valor,
    IconData icono,
    Color color,
    String subtitulo,
  ) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icono, color: color, size: 32),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    titulo,
                    style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    valor,
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: color,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitulo,
                    style: TextStyle(fontSize: 12, color: Colors.grey[500]),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================
  // ESTADOS
  // ============================================

  Widget _buildCargando() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(color: _azul),
          const SizedBox(height: 16),
          Text(
            'Cargando información...',
            style: TextStyle(color: Colors.grey[600]),
          ),
        ],
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: _rojo.withValues(alpha: 0.5),
            ),
            const SizedBox(height: 16),
            Text(
              _error!,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16, color: Colors.grey[700]),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _cargarDatos,
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _azul,
                padding: const EdgeInsets.symmetric(
                  horizontal: 32,
                  vertical: 12,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildListaVacia({
    required IconData icono,
    required String mensaje,
    required String submensaje,
    String? botonTexto,
    VoidCallback? botonAccion,
  }) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icono, size: 80, color: Colors.grey[300]),
            const SizedBox(height: 16),
            Text(
              mensaje,
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.grey[700],
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              submensaje,
              style: TextStyle(fontSize: 14, color: Colors.grey[500]),
              textAlign: TextAlign.center,
            ),
            if (botonTexto != null && botonAccion != null) ...[
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: botonAccion,
                icon: const Icon(Icons.add),
                label: Text(botonTexto),
                style: ElevatedButton.styleFrom(
                  backgroundColor: _azul,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 12,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildMensajeVerificacion(String titulo, String mensaje) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.verified_user, size: 80, color: _naranja),
            const SizedBox(height: 24),
            Text(
              titulo,
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.grey[800],
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: _naranja.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: _naranja, width: 2),
              ),
              child: Column(
                children: [
                  Icon(Icons.info_outline, color: _naranja, size: 48),
                  const SizedBox(height: 16),
                  Text(
                    mensaje,
                    style: TextStyle(fontSize: 14, color: Colors.grey[700]),
                    textAlign: TextAlign.center,
                  ),
                ],
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
    return FloatingActionButton.extended(
      onPressed: () {
        // TODO: Agregar nuevo producto
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Funcionalidad de agregar producto próximamente'),
          ),
        );
      },
      backgroundColor: _azul,
      icon: const Icon(Icons.add),
      label: const Text('Agregar Producto'),
    );
  }
}
