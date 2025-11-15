// lib/screens/delivery/widgets/repartidor_drawer.dart

import 'package:flutter/material.dart';
import '../../../models/repartidor.dart';
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
        color: estaDisponible ? _verde.withOpacity(0.1) : Colors.grey[100],
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
            builder: (context) =>
                const PantallaPerfilRepartidor(), // TODO: Navegar Perfil
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
        // TODO: Navegar a historial
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
        // TODO: Navegar a ganancias
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
        // TODO: Navegar a configuración
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
        // TODO: Navegar a ayuda
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
