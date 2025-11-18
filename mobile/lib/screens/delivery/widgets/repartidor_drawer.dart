// lib/screens/delivery/widgets/repartidor_drawer.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../models/repartidor.dart';
import '../../../providers/proveedor_roles.dart';
import '../../../config/rutas.dart';
import '../perfil/pantalla_perfil_repartidor.dart';
import '../soporte/pantalla_ayuda_soporte_repartidor.dart';
import '../configuracion/pantalla_configuracion_repartidor.dart';
import '../ganancias/pantalla_ganancias_repartidor.dart';
import '../historial/pantalla_historial_repartidor.dart';

/// 🎨 Widget del menú lateral (Drawer) para el repartidor
/// Muestra perfil, disponibilidad y opciones de navegación
class RepartidorDrawer extends StatelessWidget {
  final PerfilRepartidorModel? perfil;
  final bool estaDisponible;
  final VoidCallback onCambiarDisponibilidad;
  final VoidCallback onAbrirMapa;
  final VoidCallback onCerrarSesion;

  // Colores
  static const Color _naranja = Color(0xFFFF9800);
  static const Color _naranjaOscuro = Color(0xFFF57C00);
  static const Color _verde = Color(0xFF4CAF50);
  static const Color _azul = Color(0xFF2196F3);
  static const Color _rojo = Color(0xFFF44336);

  const RepartidorDrawer({
    super.key,
    required this.perfil,
    required this.estaDisponible,
    required this.onCambiarDisponibilidad,
    required this.onAbrirMapa,
    required this.onCerrarSesion,
  });

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          _buildDrawerHeader(),
          _buildDisponibilidadTile(),

          // ✅ SELECTOR DE ROLES (SI TIENE MÚLTIPLES ROLES)
          Consumer<ProveedorRoles>(
            builder: (context, proveedorRoles, child) {
              if (!proveedorRoles.tieneMultiplesRoles) {
                return const SizedBox.shrink();
              }

              return _buildSelectorRoles(context, proveedorRoles);
            },
          ),

          const Divider(),
          _buildMapaTile(context),
          const Divider(),
          _buildPerfilTile(context),
          _buildHistorialTile(context),
          _buildGananciasTile(context),
          _buildConfiguracionTile(context),
          _buildAyudaTile(context),
          const Divider(),
          _buildCerrarSesionTile(context),
        ],
      ),
    );
  }

  // ============================================
  // HEADER DEL DRAWER
  // ============================================

  Widget _buildDrawerHeader() {
    final fotoPerfil = perfil?.fotoPerfil;
    final nombre = perfil?.nombreCompleto ?? 'Cargando...';
    final email = perfil?.email ?? '';

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

  // ============================================
  // DISPONIBILIDAD
  // ============================================

  Widget _buildDisponibilidadTile() {
    final estado = perfil?.estado ?? EstadoRepartidor.fueraServicio;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: estaDisponible
            ? _verde.withValues(alpha: 0.1)
            : Colors.grey[100],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: estaDisponible ? _verde : Colors.grey[300]!,
          width: 2,
        ),
      ),
      child: SwitchListTile(
        value: estaDisponible,
        onChanged: (value) => onCambiarDisponibilidad(),
        activeThumbColor: _verde,
        activeTrackColor: _verde.withValues(alpha: 0.4),
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

  // ════════════════════════════════════════════════════════════════════════
  // 🎭 SELECTOR DE ROLES
  // ════════════════════════════════════════════════════════════════════════

  Widget _buildSelectorRoles(
    BuildContext context,
    ProveedorRoles proveedorRoles,
  ) {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            _naranja.withValues(alpha: 0.1),
            _azul.withValues(alpha: 0.1),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _naranja.withValues(alpha: 0.3), width: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: const BoxDecoration(
                  color: _naranja,
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.swap_horiz,
                  color: Colors.white,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Cambiar de Panel',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 15,
                      ),
                    ),
                    SizedBox(height: 2),
                    Text(
                      'Tienes múltiples roles disponibles',
                      style: TextStyle(fontSize: 11, color: Colors.grey),
                    ),
                  ],
                ),
              ),
            ],
          ),

          const SizedBox(height: 12),
          const Divider(height: 1),
          const SizedBox(height: 12),

          // Lista de roles disponibles para cambiar
          ...proveedorRoles.rolesParaCambiar.map((rol) {
            return Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: _buildBotonCambiarRol(context, proveedorRoles, rol),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildBotonCambiarRol(
    BuildContext context,
    ProveedorRoles proveedorRoles,
    String rol,
  ) {
    final icono = _obtenerIconoRol(rol);
    final nombre = _obtenerNombreRol(rol);
    final color = _obtenerColorRol(rol);

    return InkWell(
      onTap: proveedorRoles.isLoading
          ? null
          : () => _confirmarCambioRol(context, proveedorRoles, rol),
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withValues(alpha: 0.3)),
        ),
        child: Row(
          children: [
            Icon(icono, color: color, size: 24),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                'Cambiar a $nombre',
                style: TextStyle(
                  color: color,
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
            ),
            Icon(Icons.arrow_forward_ios, color: color, size: 16),
          ],
        ),
      ),
    );
  }

  // ════════════════════════════════════════════════════════════════════════
  // 🎬 CONFIRMACIÓN DE CAMBIO DE ROL
  // ════════════════════════════════════════════════════════════════════════

  void _confirmarCambioRol(
    BuildContext context,
    ProveedorRoles proveedorRoles,
    String nuevoRol,
  ) {
    final nombre = _obtenerNombreRol(nuevoRol);
    final icono = _obtenerIconoRol(nuevoRol);
    final color = _obtenerColorRol(nuevoRol);

    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Row(
          children: [
            Icon(icono, color: color, size: 28),
            const SizedBox(width: 12),
            const Expanded(child: Text('Cambiar de Panel')),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '¿Deseas cambiar al panel de $nombre?',
              style: const TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Row(
                children: [
                  Icon(Icons.info_outline, color: Colors.blue, size: 20),
                  SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Serás redirigido automáticamente',
                      style: TextStyle(fontSize: 13),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(dialogContext);
              Navigator.pop(context); // Cerrar drawer
              _ejecutarCambioRol(context, proveedorRoles, nuevoRol);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: color,
              foregroundColor: Colors.white,
            ),
            child: const Text('Cambiar'),
          ),
        ],
      ),
    );
  }

  Future<void> _ejecutarCambioRol(
    BuildContext context,
    ProveedorRoles proveedorRoles,
    String nuevoRol,
  ) async {
    // Mostrar loading
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(
        child: Card(
          child: Padding(
            padding: EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 16),
                Text('Cambiando de panel...'),
              ],
            ),
          ),
        ),
      ),
    );

    try {
      final exito = await proveedorRoles.cambiarARol(nuevoRol);

      if (!context.mounted) return;

      // Cerrar loading
      Navigator.pop(context);

      if (exito) {
        // Navegar al panel correspondiente
        await Rutas.irAHomePorRol(context, nuevoRol);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Error al cambiar de rol')),
        );
      }
    } catch (e) {
      if (!context.mounted) return;

      // Cerrar loading
      Navigator.pop(context);

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Error: ${e.toString()}')));
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // 🎨 HELPERS DE UI
  // ════════════════════════════════════════════════════════════════════════

  IconData _obtenerIconoRol(String rol) {
    switch (rol.toUpperCase()) {
      case 'USUARIO':
        return Icons.person;
      case 'PROVEEDOR':
        return Icons.store;
      case 'REPARTIDOR':
        return Icons.delivery_dining;
      case 'ADMINISTRADOR':
        return Icons.admin_panel_settings;
      default:
        return Icons.help_outline;
    }
  }

  String _obtenerNombreRol(String rol) {
    switch (rol.toUpperCase()) {
      case 'USUARIO':
        return 'Usuario';
      case 'PROVEEDOR':
        return 'Proveedor';
      case 'REPARTIDOR':
        return 'Repartidor';
      case 'ADMINISTRADOR':
        return 'Administrador';
      default:
        return rol;
    }
  }

  Color _obtenerColorRol(String rol) {
    switch (rol.toUpperCase()) {
      case 'USUARIO':
        return _azul;
      case 'PROVEEDOR':
        return _verde;
      case 'REPARTIDOR':
        return _naranja;
      case 'ADMINISTRADOR':
        return const Color(0xFF9C27B0); // morado
      default:
        return Colors.grey;
    }
  }

  // ============================================
  // OPCIONES DE MENÚ
  // ============================================

  Widget _buildMapaTile(BuildContext context) {
    return ListTile(
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
        onAbrirMapa();
      },
    );
  }

  Widget _buildPerfilTile(BuildContext context) {
    return ListTile(
      leading: Icon(Icons.person, color: _naranja),
      title: const Text('Mi Perfil'),
      onTap: () {
        Navigator.pop(context);
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => const PantallaPerfilRepartidor(),
          ),
        );
      },
    );
  }

  Widget _buildHistorialTile(BuildContext context) {
    return ListTile(
      leading: Icon(Icons.history, color: _azul),
      title: const Text('Historial Completo'),
      onTap: () {
        Navigator.pop(context);
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => const PantallaHistorialRepartidor(),
          ),
        );
      },
    );
  }

  Widget _buildGananciasTile(BuildContext context) {
    final ganancias = (perfil?.entregasCompletadas ?? 0) * 5.0;

    return ListTile(
      leading: Icon(Icons.attach_money, color: _verde),
      title: const Text('Mis Ganancias'),
      subtitle: Text('\$${ganancias.toStringAsFixed(2)}'),
      onTap: () {
        Navigator.pop(context);
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => const PantallaGananciasRepartidor(),
          ),
        );
      },
    );
  }

  Widget _buildConfiguracionTile(BuildContext context) {
    return ListTile(
      leading: Icon(Icons.settings, color: Colors.grey[700]),
      title: const Text('Configuración'),
      onTap: () {
        Navigator.pop(context);
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => const PantallaConfiguracionRepartidor(),
          ),
        );
      },
    );
  }

  Widget _buildAyudaTile(BuildContext context) {
    return ListTile(
      leading: Icon(Icons.help_outline, color: Colors.blue[700]),
      title: const Text('Ayuda y Soporte'),
      onTap: () {
        Navigator.pop(context);
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => const PantallaAyudaSoporteRepartidor(),
          ),
        );
      },
    );
  }

  Widget _buildCerrarSesionTile(BuildContext context) {
    return ListTile(
      leading: Icon(Icons.logout, color: _rojo),
      title: const Text('Cerrar Sesión'),
      onTap: () {
        Navigator.pop(context);
        onCerrarSesion();
      },
    );
  }
}
