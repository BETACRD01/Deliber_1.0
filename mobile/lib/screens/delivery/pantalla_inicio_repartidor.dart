// lib/screens/delivery/pantalla_inicio_repartidor.dart

import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import '../../services/repartidor_service.dart';
import '../../config/rutas.dart';
import '../../config/api_config.dart';
import '../../apis/subapis/http_client.dart';
import '../../apis/helpers/api_exception.dart';
import '../../widgets/mapa_pedidos_widget.dart/mapa_pedidos_widget.dart';
import '../../models/repartidor.dart';
import 'dart:developer' as developer;

/// ✅ ACTUALIZADO: Pantalla principal para REPARTIDORES con DATOS REALES
/// Consume RepartidorService para mostrar perfil, estadísticas y estado
class PantallaInicioRepartidor extends StatefulWidget {
  const PantallaInicioRepartidor({super.key});

  @override
  State<PantallaInicioRepartidor> createState() =>
      _PantallaInicioRepartidorState();
}

class _PantallaInicioRepartidorState extends State<PantallaInicioRepartidor>
    with SingleTickerProviderStateMixin {
  // ============================================
  // SERVICIOS Y CONTROLADORES
  // ============================================
  final _authService = AuthService();
  final _repartidorService = RepartidorService();
  final _apiClient = ApiClient();
  late TabController _tabController;

  // ============================================
  // ESTADO - CON MODELOS REALES
  // ============================================
  PerfilRepartidorModel? _perfil;
  EstadisticasRepartidorModel? _estadisticas;
  bool _loading = true;
  String? _error;

  // ============================================
  // COLORES
  // ============================================
  static const Color _naranja = Color(0xFFFF9800);
  static const Color _naranjaOscuro = Color(0xFFF57C00);
  static const Color _verde = Color(0xFF4CAF50);
  static const Color _azul = Color(0xFF2196F3);
  static const Color _rojo = Color(0xFFF44336);

  // ============================================
  // CICLO DE VIDA
  // ============================================

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _verificarAccesoYCargarDatos();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  // ============================================
  // ✅ VERIFICACIÓN DE ACCESO
  // ============================================

  Future<void> _verificarAccesoYCargarDatos() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      developer.log(
        '🚀 Iniciando verificación de acceso...',
        name: 'InicioRepartidor',
      );

      await _apiClient.loadTokens();

      if (!_apiClient.isAuthenticated) {
        developer.log(
          '❌ Sin autenticación - Redirigiendo a login',
          name: 'InicioRepartidor',
        );
        if (mounted) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            Rutas.irAYLimpiar(context, Rutas.login);
          });
        }
        return;
      }

      final rolCacheado = _apiClient.userRole;
      developer.log('👤 Rol cacheado: $rolCacheado', name: 'InicioRepartidor');

      if (rolCacheado != null &&
          rolCacheado.toUpperCase() != ApiConfig.rolRepartidor) {
        await _mostrarDialogoAccesoDenegadoYRedirigir(rolCacheado);
        return;
      }

      try {
        final info = await _apiClient.get(ApiConfig.infoRol);
        final rolServidor = info['rol'] as String?;

        if (rolServidor?.toUpperCase() != ApiConfig.rolRepartidor) {
          await _mostrarDialogoAccesoDenegadoYRedirigir(rolServidor);
          return;
        }
      } catch (e) {
        if (rolCacheado?.toUpperCase() != ApiConfig.rolRepartidor) {
          await _mostrarDialogoAccesoDenegadoYRedirigir(rolCacheado);
          return;
        }
      }

      developer.log(
        '✅ Acceso verificado - Cargando datos...',
        name: 'InicioRepartidor',
      );
      await _cargarDatos();
    } catch (e, stackTrace) {
      developer.log(
        '❌ Error en verificación',
        name: 'InicioRepartidor',
        error: e,
        stackTrace: stackTrace,
      );

      if (mounted) {
        setState(() {
          _error = 'Error al verificar acceso';
          _loading = false;
        });

        if (e is ApiException && e.isAuthError) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            Rutas.irAYLimpiar(context, Rutas.login);
          });
        }
      }
    }
  }

  Future<void> _mostrarDialogoAccesoDenegadoYRedirigir(String? rol) async {
    if (!mounted) return;

    final navigatorContext = context;

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
              if (rol != null) ...[
                Text('Tu rol actual: $rol'),
                const SizedBox(height: 8),
              ],
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
        Rutas.irAYLimpiar(navigatorContext, Rutas.router);
      });
    }
  }

  // ============================================
  // ✅ CARGAR DATOS REALES
  // ============================================

  Future<void> _cargarDatos() async {
    try {
      developer.log(
        '📥 Cargando perfil y estadísticas...',
        name: 'InicioRepartidor',
      );

      // Cargar perfil y estadísticas en paralelo
      final results = await Future.wait([
        _repartidorService.obtenerPerfil(forzarRecarga: true),
        _repartidorService.obtenerEstadisticas(forzarRecarga: true),
      ]);

      if (mounted) {
        setState(() {
          _perfil = results[0] as PerfilRepartidorModel;
          _estadisticas = results[1] as EstadisticasRepartidorModel;
          _loading = false;
        });

        developer.log(
          '✅ Datos cargados correctamente',
          name: 'InicioRepartidor',
        );
        developer.log(
          '   👤 Nombre: ${_perfil!.nombreCompleto}',
          name: 'InicioRepartidor',
        );
        developer.log(
          '   📊 Entregas: ${_perfil!.entregasCompletadas}',
          name: 'InicioRepartidor',
        );
        developer.log(
          '   ⭐ Rating: ${_perfil!.calificacionPromedio}',
          name: 'InicioRepartidor',
        );
        developer.log(
          '   🚦 Estado: ${_perfil!.estado.nombre}',
          name: 'InicioRepartidor',
        );
      }
    } on ApiException catch (e) {
      developer.log('❌ API Exception: ${e.message}', name: 'InicioRepartidor');

      if (mounted) {
        setState(() {
          _error = e.getUserFriendlyMessage();
          _loading = false;
        });

        if (e.isAuthError) {
          Rutas.irAYLimpiar(context, Rutas.login);
        }
      }
    } catch (e, stackTrace) {
      developer.log(
        '❌ Error cargando datos',
        name: 'InicioRepartidor',
        error: e,
        stackTrace: stackTrace,
      );

      if (mounted) {
        setState(() {
          _error = 'Error al cargar información';
          _loading = false;
        });
      }
    }
  }

  // ============================================
  // ✅ CAMBIAR ESTADO (DISPONIBILIDAD)
  // ============================================

  Future<void> _cambiarEstado(EstadoRepartidor nuevoEstado) async {
    try {
      developer.log(
        '🔄 Cambiando estado a: ${nuevoEstado.nombre}',
        name: 'InicioRepartidor',
      );

      final resultado = await _repartidorService.cambiarEstado(nuevoEstado);

      if (mounted) {
        // Actualizar perfil local
        setState(() {
          _perfil = _perfil?.copyWith(estado: nuevoEstado);
        });

        // Mostrar notificación
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                Icon(_getIconoEstado(nuevoEstado), color: Colors.white),
                const SizedBox(width: 12),
                Expanded(
                  child: Text('Estado actualizado: ${nuevoEstado.nombre}'),
                ),
              ],
            ),
            backgroundColor: _getColorEstado(nuevoEstado),
            behavior: SnackBarBehavior.floating,
          ),
        );

        developer.log(
          '✅ Estado cambiado: ${resultado.estadoAnterior.nombre} → ${resultado.estadoNuevo.nombre}',
          name: 'InicioRepartidor',
        );
      }
    } on ApiException catch (e) {
      developer.log(
        '❌ Error cambiando estado: ${e.message}',
        name: 'InicioRepartidor',
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.getUserFriendlyMessage()),
            backgroundColor: _rojo,
          ),
        );
      }
    } catch (e) {
      developer.log(
        '❌ Error inesperado cambiando estado',
        name: 'InicioRepartidor',
        error: e,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error al cambiar estado: ${e.toString()}'),
            backgroundColor: _rojo,
          ),
        );
      }
    }
  }

  IconData _getIconoEstado(EstadoRepartidor estado) {
    switch (estado) {
      case EstadoRepartidor.disponible:
        return Icons.check_circle;
      case EstadoRepartidor.ocupado:
        return Icons.delivery_dining;
      case EstadoRepartidor.fueraServicio:
        return Icons.pause_circle;
    }
  }

  Color _getColorEstado(EstadoRepartidor estado) {
    switch (estado) {
      case EstadoRepartidor.disponible:
        return _verde;
      case EstadoRepartidor.ocupado:
        return _azul;
      case EstadoRepartidor.fueraServicio:
        return Colors.grey[700]!;
    }
  }

  void _abrirMapaPedidos() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const MapaPedidosScreen()),
    );
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
      await _authService.logout();
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
      floatingActionButton: _buildFAB(),
    );
  }

  // ============================================
  // APP BAR
  // ============================================

  PreferredSizeWidget _buildAppBar() {
    final estado = _perfil?.estado ?? EstadoRepartidor.fueraServicio;

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
                  _getIconoEstado(estado),
                  color: estado == EstadoRepartidor.disponible
                      ? _verde
                      : Colors.grey[300],
                  size: 20,
                ),
                const SizedBox(width: 4),
                Text(estado.nombre, style: const TextStyle(fontSize: 12)),
              ],
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
    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          _buildDrawerHeader(),
          _buildDisponibilidadTile(),
          const Divider(),
          ListTile(
            leading: Icon(Icons.map, color: _naranja),
            title: const Text('Mapa de Pedidos'),
            subtitle: const Text('Ver pedidos cercanos'),
            trailing: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: _verde,
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Text(
                'ACTIVO',
                style: TextStyle(
                  fontSize: 10,
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            onTap: () {
              Navigator.pop(context);
              _abrirMapaPedidos();
            },
          ),
          const Divider(),
          ListTile(
            leading: Icon(Icons.person, color: _naranja),
            title: const Text('Mi Perfil'),
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a perfil
            },
          ),
          ListTile(
            leading: Icon(Icons.history, color: _azul),
            title: const Text('Historial Completo'),
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a historial
            },
          ),
          ListTile(
            leading: Icon(Icons.attach_money, color: _verde),
            title: const Text('Mis Ganancias'),
            subtitle: Text('\$${(_perfil?.entregasCompletadas ?? 0) * 5.0}'),
            onTap: () {
              Navigator.pop(context);
              // TODO: Navegar a ganancias
            },
          ),
          ListTile(
            leading: Icon(Icons.settings, color: Colors.grey[700]),
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
    final fotoPerfil = _perfil?.fotoPerfil;
    final nombre = _perfil?.nombreCompleto ?? 'Cargando...';
    final email = _perfil?.email ?? '';

    return UserAccountsDrawerHeader(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [_naranja, _naranjaOscuro],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      currentAccountPicture: CircleAvatar(
        backgroundColor: Colors.white,
        backgroundImage: fotoPerfil != null ? NetworkImage(fotoPerfil) : null,
        child: fotoPerfil == null
            ? Icon(Icons.delivery_dining, size: 40, color: _naranja)
            : null,
      ),
      accountName: Text(
        nombre,
        style: const TextStyle(fontWeight: FontWeight.bold),
      ),
      accountEmail: Text(email),
    );
  }

  Widget _buildDisponibilidadTile() {
    final estado = _perfil?.estado ?? EstadoRepartidor.fueraServicio;
    final estaDisponible = estado == EstadoRepartidor.disponible;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: estaDisponible ? _verde.withOpacity(0.1) : Colors.grey[100],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: estaDisponible ? _verde : Colors.grey[300]!,
          width: 2,
        ),
      ),
      child: SwitchListTile(
        value: estaDisponible,
        onChanged: (value) {
          _cambiarEstado(
            value
                ? EstadoRepartidor.disponible
                : EstadoRepartidor.fueraServicio,
          );
        },
        activeThumbColor: _verde,
        activeTrackColor: _verde.withOpacity(0.4),
        secondary: Icon(
          estaDisponible ? Icons.check_circle : Icons.pause_circle,
          color: estaDisponible ? _verde : Colors.grey,
        ),
        title: Text(
          estado.nombre,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: estaDisponible ? _verde : Colors.grey[700],
          ),
        ),
        subtitle: Text(
          estaDisponible
              ? 'Recibirás notificaciones de pedidos'
              : 'No recibirás pedidos nuevos',
          style: TextStyle(fontSize: 12, color: Colors.grey[600]),
        ),
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
  // ✅ ESTADÍSTICAS HEADER CON DATOS REALES
  // ============================================

  Widget _buildEstadisticasHeader() {
    final entregas = _perfil?.entregasCompletadas ?? 0;
    final rating = _perfil?.calificacionPromedio ?? 0.0;
    final gananciasEstimadas =
        entregas * 5.0; // $5 por entrega (ajustar según tu lógica)

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [_naranja.withOpacity(0.1), Colors.white],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: Column(
        children: [
          Row(
            children: [
              _buildEstadistica(
                'Entregas',
                '$entregas',
                Icons.delivery_dining,
                _azul,
              ),
              const SizedBox(width: 12),
              _buildEstadistica(
                'Rating',
                rating.toStringAsFixed(1),
                Icons.star,
                Colors.amber,
              ),
              const SizedBox(width: 12),
              _buildEstadistica(
                'Ganancias',
                '\$${gananciasEstimadas.toStringAsFixed(2)}',
                Icons.attach_money,
                _verde,
              ),
            ],
          ),
          if (_estadisticas != null) ...[
            const SizedBox(height: 12),
            _buildDetallesEstadisticas(),
          ],
        ],
      ),
    );
  }

  Widget _buildDetallesEstadisticas() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.1),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildMiniEstadistica(
            '⭐⭐⭐⭐⭐',
            '${_estadisticas!.calificaciones5Estrellas}',
            Colors.amber,
          ),
          _buildMiniEstadistica(
            'Total',
            '${_estadisticas!.totalCalificaciones}',
            _azul,
          ),
          _buildMiniEstadistica(
            'Promedio',
            '${(_estadisticas!.calificaciones5Estrellas / (_estadisticas!.totalCalificaciones == 0 ? 1 : _estadisticas!.totalCalificaciones) * 100).toStringAsFixed(0)}%',
            _verde,
          ),
        ],
      ),
    );
  }

  Widget _buildMiniEstadistica(String label, String value, Color color) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        const SizedBox(height: 4),
        Text(label, style: TextStyle(fontSize: 10, color: Colors.grey[600])),
      ],
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
              color: Colors.grey.withOpacity(0.1),
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
    return _buildListaVacia(
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
    return _buildListaVacia(
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
    final entregas = _perfil?.entregasCompletadas ?? 0;

    return _buildListaVacia(
      icono: Icons.history,
      mensaje: entregas > 0
          ? 'Has completado $entregas entregas'
          : 'Historial vacío',
      submensaje: entregas > 0
          ? '¡Excelente trabajo!'
          : 'Tus entregas completadas aparecerán aquí',
    );
  }

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
            Icon(Icons.error_outline, size: 64, color: _rojo.withOpacity(0.5)),
            const SizedBox(height: 16),
            Text(
              _error!,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16, color: Colors.grey[700]),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _verificarAccesoYCargarDatos,
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

  Widget _buildListaVacia({
    required IconData icono,
    required String mensaje,
    required String submensaje,
    Widget? accionBoton,
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
            if (accionBoton != null) ...[
              const SizedBox(height: 24),
              accionBoton,
            ],
          ],
        ),
      ),
    );
  }

  Widget? _buildFAB() {
    final estado = _perfil?.estado ?? EstadoRepartidor.fueraServicio;

    if (estado != EstadoRepartidor.disponible) {
      return FloatingActionButton.extended(
        onPressed: () => _cambiarEstado(EstadoRepartidor.disponible),
        backgroundColor: _verde,
        icon: const Icon(Icons.check_circle),
        label: const Text('Activar Disponibilidad'),
      );
    }
    return FloatingActionButton.extended(
      onPressed: _abrirMapaPedidos,
      backgroundColor: _naranja,
      icon: const Icon(Icons.map),
      label: const Text('Ver Mapa'),
      heroTag: 'mapa_fab',
    );
  }
}
