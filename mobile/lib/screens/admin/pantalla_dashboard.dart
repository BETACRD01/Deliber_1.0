// lib/screens/admin/pantalla_dashboard.dart

import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import '../../config/rutas.dart';
import '../../apis/helpers/api_exception.dart';

/// Pantalla principal para ADMINISTRADORES
/// Dashboard completo con gestión de usuarios, proveedores, repartidores y estadísticas
class PantallaDashboard extends StatefulWidget {
  const PantallaDashboard({super.key});

  @override
  State<PantallaDashboard> createState() => _PantallaDashboardState();
}

class _PantallaDashboardState extends State<PantallaDashboard>
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
  String? _error;

  // Estadísticas generales
  int _totalUsuarios = 0;
  int _totalProveedores = 0;
  int _totalRepartidores = 0;
  int _proveedoresPendientes = 0;
  double _ventasTotales = 0.0;
  int _pedidosActivos = 0;

  // ============================================
  // COLORES
  // ============================================
  static const Color _morado = Color(0xFF9C27B0);
  static const Color _moradoOscuro = Color(0xFF7B1FA2);
  static const Color _verde = Color(0xFF4CAF50);
  static const Color _azul = Color(0xFF2196F3);
  static const Color _naranja = Color(0xFFFF9800);
  static const Color _rojo = Color(0xFFF44336);
  static const Color _gris = Color(0xFF757575);

  // ============================================
  // CICLO DE VIDA
  // ============================================

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
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
          _loading = false;
        });

        // Cargar estadísticas y datos (implementar cuando tengas los endpoints)
        // await _cargarEstadisticas();
        // await _cargarProveedoresPendientes();
        // await _cargarActividadReciente();

        // Datos de ejemplo (eliminar cuando tengas datos reales)
        _simularDatos();
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

  void _simularDatos() {
    setState(() {
      _totalUsuarios = 150;
      _totalProveedores = 25;
      _totalRepartidores = 15;
      _proveedoresPendientes = 5;
      _ventasTotales = 15750.50;
      _pedidosActivos = 12;
    });
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
    );
  }

  // ============================================
  // APP BAR
  // ============================================

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      title: const Text('Panel de Administración'),
      elevation: 0,
      flexibleSpace: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [_morado, _moradoOscuro],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
      ),
      actions: [
        // Notificaciones
        Stack(
          children: [
            IconButton(
              icon: const Icon(Icons.notifications),
              onPressed: () {
                // TODO: Ver notificaciones
              },
            ),
            if (_proveedoresPendientes > 0)
              Positioned(
                right: 8,
                top: 8,
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: _rojo,
                    shape: BoxShape.circle,
                  ),
                  constraints: const BoxConstraints(
                    minWidth: 16,
                    minHeight: 16,
                  ),
                  child: Text(
                    '$_proveedoresPendientes',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
              ),
          ],
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
        isScrollable: true,
        tabs: const [
          Tab(text: 'Resumen', icon: Icon(Icons.dashboard, size: 20)),
          Tab(text: 'Usuarios', icon: Icon(Icons.people, size: 20)),
          Tab(text: 'Proveedores', icon: Icon(Icons.store, size: 20)),
          Tab(text: 'Actividad', icon: Icon(Icons.history, size: 20)),
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
          const Divider(),
          ListTile(
            leading: Icon(Icons.dashboard, color: _morado),
            title: const Text('Dashboard'),
            selected: true,
            onTap: () => Navigator.pop(context),
          ),
          ListTile(
            leading: Icon(Icons.people, color: _azul),
            title: const Text('Gestión de Usuarios'),
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a usuarios
            },
          ),
          ListTile(
            leading: Icon(Icons.store, color: _verde),
            title: const Text('Proveedores'),
            trailing: _proveedoresPendientes > 0
                ? Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: _naranja,
                      shape: BoxShape.circle,
                    ),
                    child: Text(
                      '$_proveedoresPendientes',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  )
                : null,
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a proveedores
            },
          ),
          ListTile(
            leading: Icon(Icons.delivery_dining, color: _naranja),
            title: const Text('Repartidores'),
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a repartidores
            },
          ),
          ListTile(
            leading: Icon(Icons.analytics, color: Colors.purple[700]),
            title: const Text('Reportes y Estadísticas'),
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a reportes
            },
          ),
          ListTile(
            leading: Icon(Icons.shopping_cart, color: _azul),
            title: const Text('Gestión de Pedidos'),
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a pedidos
            },
          ),
          ListTile(
            leading: Icon(Icons.inventory, color: _verde),
            title: const Text('Productos'),
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a productos
            },
          ),
          const Divider(),
          ListTile(
            leading: Icon(Icons.settings, color: _gris),
            title: const Text('Configuración'),
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a configuración
            },
          ),
          ListTile(
            leading: Icon(Icons.support_agent, color: Colors.blue[700]),
            title: const Text('Soporte'),
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a soporte
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
          colors: [_morado, _moradoOscuro],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      currentAccountPicture: CircleAvatar(
        backgroundColor: Colors.white,
        child: Icon(Icons.admin_panel_settings, size: 40, color: _morado),
      ),
      accountName: Text(
        '${_usuario?['nombre'] ?? ''} ${_usuario?['apellido'] ?? ''}',
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
              color: Colors.white.withValues(alpha: 0.3),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Text(
              'ADMINISTRADOR',
              style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
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

    return TabBarView(
      controller: _tabController,
      children: [
        _buildResumen(),
        _buildUsuarios(),
        _buildProveedores(),
        _buildActividad(),
      ],
    );
  }

  // ============================================
  // TAB: RESUMEN
  // ============================================

  Widget _buildResumen() {
    return RefreshIndicator(
      onRefresh: _cargarDatos,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Estadísticas principales
            _buildSeccionTitulo('Estadísticas Generales'),
            const SizedBox(height: 12),
            _buildGridEstadisticas(),

            const SizedBox(height: 24),

            // Proveedores pendientes
            if (_proveedoresPendientes > 0) ...[
              _buildSeccionTitulo('Acciones Pendientes'),
              const SizedBox(height: 12),
              _buildAlertaProveedoresPendientes(),
              const SizedBox(height: 24),
            ],

            // Gráficos y actividad reciente
            _buildSeccionTitulo('Actividad Reciente'),
            const SizedBox(height: 12),
            _buildActividadRecienteCard(),
          ],
        ),
      ),
    );
  }

  Widget _buildSeccionTitulo(String titulo) {
    return Text(
      titulo,
      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
    );
  }

  Widget _buildGridEstadisticas() {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.5,
      children: [
        _buildCardEstadistica(
          'Usuarios Totales',
          _totalUsuarios.toString(),
          Icons.people,
          _azul,
          '+12 este mes',
        ),
        _buildCardEstadistica(
          'Proveedores',
          _totalProveedores.toString(),
          Icons.store,
          _verde,
          '$_proveedoresPendientes pendientes',
        ),
        _buildCardEstadistica(
          'Repartidores',
          _totalRepartidores.toString(),
          Icons.delivery_dining,
          _naranja,
          '${_totalRepartidores - 2} activos',
        ),
        _buildCardEstadistica(
          'Ventas Totales',
          '\$${_ventasTotales.toStringAsFixed(2)}',
          Icons.attach_money,
          _verde,
          '+8% vs mes anterior',
        ),
        _buildCardEstadistica(
          'Pedidos Activos',
          _pedidosActivos.toString(),
          Icons.shopping_cart,
          _morado,
          'En proceso',
        ),
        _buildCardEstadistica(
          'Ingresos Hoy',
          '\$1,250.00',
          Icons.trending_up,
          Colors.teal,
          '+15% vs ayer',
        ),
      ],
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
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(icono, color: color, size: 24),
                ),
              ],
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
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
                  titulo,
                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                ),
                const SizedBox(height: 4),
                Text(
                  subtitulo,
                  style: TextStyle(fontSize: 10, color: Colors.grey[500]),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAlertaProveedoresPendientes() {
    return Card(
      elevation: 2,
      color: _naranja.withValues(alpha: 0.1),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: _naranja, width: 2),
      ),
      child: InkWell(
        onTap: () {
          _tabController.animateTo(2); // Ir a tab de proveedores
        },
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: _naranja,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.warning_amber,
                  color: Colors.white,
                  size: 32,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '$_proveedoresPendientes proveedores pendientes de verificación',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Toca aquí para revisar y aprobar',
                      style: TextStyle(fontSize: 13),
                    ),
                  ],
                ),
              ),
              Icon(Icons.arrow_forward_ios, color: _naranja),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildActividadRecienteCard() {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Últimas Acciones',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            _buildItemActividad(
              'Nuevo usuario registrado',
              'Juan Pérez se registró como usuario',
              Icons.person_add,
              _azul,
              'Hace 5 min',
            ),
            const Divider(),
            _buildItemActividad(
              'Proveedor verificado',
              'Restaurante "La Casa" fue aprobado',
              Icons.check_circle,
              _verde,
              'Hace 1 hora',
            ),
            const Divider(),
            _buildItemActividad(
              'Pedido completado',
              'Pedido #1234 entregado exitosamente',
              Icons.delivery_dining,
              _naranja,
              'Hace 2 horas',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildItemActividad(
    String titulo,
    String descripcion,
    IconData icono,
    Color color,
    String tiempo,
  ) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icono, color: color, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  titulo,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  descripcion,
                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                ),
              ],
            ),
          ),
          Text(tiempo, style: TextStyle(fontSize: 11, color: Colors.grey[500])),
        ],
      ),
    );
  }

  // ============================================
  // TAB: USUARIOS
  // ============================================

  Widget _buildUsuarios() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.people, size: 80, color: Colors.grey[300]),
            const SizedBox(height: 16),
            Text(
              'Gestión de Usuarios',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.grey[700],
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Aquí podrás ver y gestionar todos los usuarios',
              style: TextStyle(fontSize: 14, color: Colors.grey[500]),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () {
                // TODO: Implementar vista de usuarios
              },
              icon: const Icon(Icons.add),
              label: const Text('Agregar Usuario'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _azul,
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 12,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================
  // TAB: PROVEEDORES
  // ============================================

  Widget _buildProveedores() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.store, size: 80, color: Colors.grey[300]),
            const SizedBox(height: 16),
            Text(
              'Gestión de Proveedores',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.grey[700],
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Verifica y gestiona los proveedores de la plataforma',
              style: TextStyle(fontSize: 14, color: Colors.grey[500]),
              textAlign: TextAlign.center,
            ),
            if (_proveedoresPendientes > 0) ...[
              const SizedBox(height: 24),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: _naranja.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: _naranja, width: 2),
                ),
                child: Column(
                  children: [
                    Icon(Icons.pending_actions, color: _naranja, size: 48),
                    const SizedBox(height: 12),
                    Text(
                      '$_proveedoresPendientes proveedores esperando verificación',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  // ============================================
  // TAB: ACTIVIDAD
  // ============================================

  Widget _buildActividad() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.history, size: 80, color: Colors.grey[300]),
            const SizedBox(height: 16),
            Text(
              'Registro de Actividad',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.grey[700],
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Historial completo de acciones en la plataforma',
              style: TextStyle(fontSize: 14, color: Colors.grey[500]),
              textAlign: TextAlign.center,
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
          CircularProgressIndicator(color: _morado),
          const SizedBox(height: 16),
          Text(
            'Cargando dashboard...',
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
                backgroundColor: _morado,
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
}
