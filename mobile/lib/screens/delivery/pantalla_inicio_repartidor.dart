// lib/screens/delivery/pantalla_inicio_repartidor.dart

import 'package:flutter/material.dart';
import '../../config/rutas.dart';
import '../../models/repartidor.dart';
import '../../widgets/mapa_pedidos_widget.dart/mapa_pedidos_widget.dart';
import 'controllers/repartidor_controller.dart';
import 'widgets/repartidor_drawer.dart';
import 'widgets/lista_vacia_widget.dart';

/// ✅ REFACTORIZADA: Pantalla principal para REPARTIDORES
/// UI limpia que delega toda la lógica al controller
class PantallaInicioRepartidor extends StatefulWidget {
  const PantallaInicioRepartidor({super.key});

  @override
  State<PantallaInicioRepartidor> createState() =>
      _PantallaInicioRepartidorState();
}

class _PantallaInicioRepartidorState extends State<PantallaInicioRepartidor>
    with SingleTickerProviderStateMixin {
  // ============================================
  // CONTROLLER Y TABS
  // ============================================
  late final RepartidorController _controller;
  late final TabController _tabController;

  // ============================================
  // COLORES
  // ============================================
  static const Color _naranja = Color(0xFFFF9800);
  static const Color _naranjaOscuro = Color(0xFFF57C00);
  static const Color _verde = Color(0xFF4CAF50);
  static const Color _rojo = Color(0xFFF44336);

  // ============================================
  // CICLO DE VIDA
  // ============================================

  @override
  void initState() {
    super.initState();
    _controller = RepartidorController();
    _tabController = TabController(length: 3, vsync: this);
    _inicializar();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _controller.dispose();
    super.dispose();
  }

  // ============================================
  // INICIALIZACIÓN
  // ============================================

  Future<void> _inicializar() async {
    final accesoValido = await _controller.verificarAccesoYCargarDatos();

    if (!mounted) return;

    if (!accesoValido) {
      _manejarAccesoDenegado();
    }
  }

  void _manejarAccesoDenegado() {
    final error = _controller.error;
    final rolIncorrecto = error?.contains('Rol incorrecto') ?? false;

    if (rolIncorrecto) {
      _mostrarDialogoAccesoDenegado();
    } else {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        Rutas.irAYLimpiar(context, Rutas.login);
      });
    }
  }

  Future<void> _mostrarDialogoAccesoDenegado() async {
    await showDialog(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => PopScope(
        canPop: false,
        child: AlertDialog(
          title: Row(
            children: [
              Icon(Icons.block, color: _rojo),
              const SizedBox(width: 12),
              const Text('Acceso Denegado'),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Esta sección es exclusiva para repartidores.',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),
              Text(_controller.error ?? ''),
              const SizedBox(height: 8),
              const Text(
                'Serás redirigido a tu pantalla correspondiente.',
                style: TextStyle(color: Colors.grey),
              ),
            ],
          ),
          actions: [
            ElevatedButton(
              onPressed: () => Navigator.pop(dialogContext),
              style: ElevatedButton.styleFrom(backgroundColor: _naranja),
              child: const Text('Entendido'),
            ),
          ],
        ),
      ),
    );

    if (mounted) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        Rutas.irAYLimpiar(context, Rutas.router);
      });
    }
  }

  // ============================================
  // ACCIONES
  // ============================================

  void _abrirMapaPedidos() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const MapaPedidosScreen()),
    );
  }

  Future<void> _cambiarDisponibilidad() async {
    final nuevoEstado = _controller.estaDisponible
        ? EstadoRepartidor.fueraServicio
        : EstadoRepartidor.disponible;

    final exito = await _controller.cambiarEstado(nuevoEstado);

    if (!mounted) return;

    if (exito) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              Icon(
                _controller.getIconoEstado(nuevoEstado),
                color: Colors.white,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text('Estado actualizado: ${nuevoEstado.nombre}'),
              ),
            ],
          ),
          backgroundColor: _controller.getColorEstado(nuevoEstado),
          behavior: SnackBarBehavior.floating,
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(_controller.error ?? 'Error al cambiar estado'),
          backgroundColor: _rojo,
        ),
      );
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
      await _controller.cerrarSesion();
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
    return ListenableBuilder(
      listenable: _controller,
      builder: (context, child) {
        return Scaffold(
          appBar: _buildAppBar(),
          drawer: _buildDrawer(),
          body: _buildBody(),
        );
      },
    );
  }

  // ============================================
  // APP BAR
  // ============================================

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      title: const Text('Dashboard Repartidor'),
      elevation: 0,
      flexibleSpace: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [_naranja, _naranjaOscuro],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
      ),
      actions: [
        IconButton(
          icon: const Icon(Icons.map),
          onPressed: _abrirMapaPedidos,
          tooltip: 'Ver mapa de pedidos',
        ),
        Padding(
          padding: const EdgeInsets.only(right: 8),
          child: Center(
            child: Row(
              children: [
                Icon(
                  _controller.getIconoEstado(_controller.estadoActual),
                  color: _controller.estaDisponible ? _verde : Colors.grey[300],
                  size: 20,
                ),
                const SizedBox(width: 4),
                Text(
                  _controller.estadoActual.nombre,
                  style: const TextStyle(fontSize: 12),
                ),
              ],
            ),
          ),
        ),
        IconButton(
          icon: const Icon(Icons.refresh),
          onPressed: () => _controller.cargarDatos(),
          tooltip: 'Actualizar',
        ),
      ],
      bottom: TabBar(
        controller: _tabController,
        indicatorColor: Colors.white,
        tabs: const [
          Tab(text: 'Pendientes', icon: Icon(Icons.list_alt, size: 20)),
          Tab(text: 'En Curso', icon: Icon(Icons.delivery_dining, size: 20)),
          Tab(text: 'Historial', icon: Icon(Icons.history, size: 20)),
        ],
      ),
    );
  }

  // ============================================
  // DRAWER
  // ============================================

  Widget _buildDrawer() {
    return RepartidorDrawer(
      perfil: _controller.perfil,
      estaDisponible: _controller.estaDisponible,
      onCambiarDisponibilidad: _cambiarDisponibilidad,
      onAbrirMapa: _abrirMapaPedidos,
      onCerrarSesion: _cerrarSesion,
    );
  }

  // ============================================
  // BODY
  // ============================================

  Widget _buildBody() {
    if (_controller.loading) {
      return _buildCargando();
    }

    if (_controller.error != null && _controller.perfil == null) {
      return _buildError();
    }

    return Column(
      children: [
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: [
              _buildPedidosPendientes(),
              _buildPedidosEnCurso(),
              _buildHistorial(),
            ],
          ),
        ),
      ],
    );
  }

  // ============================================
  // ESTADOS DE CARGA Y ERROR
  // ============================================

  Widget _buildCargando() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(color: _naranja),
          const SizedBox(height: 16),
          Text('Cargando datos...', style: TextStyle(color: Colors.grey[600])),
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
              _controller.error!,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16, color: Colors.grey[700]),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _inicializar,
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _naranja,
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

  // ============================================
  // TABS DE CONTENIDO
  // ============================================

  Widget _buildPedidosPendientes() {
    return ListaVaciaWidget(
      icono: Icons.inbox,
      mensaje: 'No hay pedidos pendientes',
      submensaje: 'Los nuevos pedidos aparecerán aquí',
      accionBoton: ElevatedButton.icon(
        onPressed: _abrirMapaPedidos,
        icon: const Icon(Icons.map),
        label: const Text('Ver Mapa de Pedidos'),
        style: ElevatedButton.styleFrom(
          backgroundColor: _naranja,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        ),
      ),
    );
  }

  Widget _buildPedidosEnCurso() {
    return ListaVaciaWidget(
      icono: Icons.delivery_dining,
      mensaje: 'No tienes entregas en curso',
      submensaje: 'Acepta un pedido para comenzar',
      accionBoton: ElevatedButton.icon(
        onPressed: _abrirMapaPedidos,
        icon: const Icon(Icons.map),
        label: const Text('Buscar Pedidos Cercanos'),
        style: ElevatedButton.styleFrom(
          backgroundColor: _verde,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        ),
      ),
    );
  }

  Widget _buildHistorial() {
    final entregas = _controller.totalEntregas;

    return ListaVaciaWidget(
      icono: Icons.history,
      mensaje: entregas > 0
          ? 'Has completado $entregas entregas'
          : 'Historial vacío',
      submensaje: entregas > 0
          ? '¡Excelente trabajo!'
          : 'Tus entregas completadas aparecerán aquí',
    );
  }
}
