// lib/screens/supplier/widgets/supplier_drawer.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../providers/proveedor_roles.dart';
import '../../../config/rutas.dart';
import '../controllers/supplier_controller.dart';
import '../perfil/perfil_proveedor_panel.dart';

/// Drawer (Menú lateral) para la pantalla del proveedor
class SupplierDrawer extends StatelessWidget {
  final VoidCallback onCerrarSesion;

  const SupplierDrawer({super.key, required this.onCerrarSesion});

  // ============================================
  // COLORES
  // ============================================
  static const Color _azul = Color(0xFF2196F3);
  static const Color _azulOscuro = Color(0xFF1976D2);
  static const Color _verde = Color(0xFF4CAF50);
  static const Color _naranja = Color(0xFFFF9800);
  static const Color _rojo = Color(0xFFF44336);
  static const Color _gris = Color(0xFF757575);
  static const Color _morado = Color(0xFF9C27B0);

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [Colors.white, _azul.withValues(alpha: 0.02)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            _buildDrawerHeader(context),
            Consumer<SupplierController>(
              builder: (context, controller, child) {
                if (!controller.verificado) {
                  return _buildAlertaVerificacion(context);
                }
                return const SizedBox.shrink();
              },
            ),

            // ✅ SELECTOR DE ROLES (SI TIENE MÚLTIPLES ROLES)
            Consumer<ProveedorRoles>(
              builder: (context, proveedorRoles, child) {
                if (!proveedorRoles.tieneMultiplesRoles) {
                  return const SizedBox.shrink();
                }

                return _buildSelectorRoles(context, proveedorRoles);
              },
            ),

            const SizedBox(height: 8),
            _buildSeccion('MI NEGOCIO'),
            _buildMenuItem(
              context,
              icon: Icons.store_outlined,
              title: 'Mi Negocio',
              subtitle: 'Información y configuración',
              color: _azul,
              onTap: () {
                Navigator.pop(context);
                // TODO: Navegar a detalles del negocio
              },
            ),
            _buildMenuItem(
              context,
              icon: Icons.verified_outlined,
              title: 'Verificación',
              subtitle: 'Estado y documentos',
              color: _verde,
              onTap: () {
                Navigator.pop(context);
                // TODO: Navegar a verificación
              },
            ),
            const Divider(height: 32),
            _buildSeccion('GESTIÓN'),
            _buildMenuItem(
              context,
              icon: Icons.inventory_2_outlined,
              title: 'Productos',
              subtitle: 'Gestionar inventario',
              color: _morado,
              onTap: () {
                Navigator.pop(context);
                // TODO: Navegar a productos
              },
            ),
            _buildMenuItem(
              context,
              icon: Icons.shopping_cart_outlined,
              title: 'Pedidos',
              subtitle: 'Gestionar órdenes',
              color: _naranja,
              badge: _buildBadge(context),
              onTap: () {
                Navigator.pop(context);
                // TODO: Navegar a pedidos
              },
            ),
            _buildMenuItem(
              context,
              icon: Icons.local_offer_outlined,
              title: 'Promociones',
              subtitle: 'Crear ofertas especiales',
              color: _rojo,
              onTap: () {
                Navigator.pop(context);
                // TODO: Navegar a promociones
              },
            ),
            const Divider(height: 32),
            _buildSeccion('REPORTES'),
            _buildMenuItem(
              context,
              icon: Icons.analytics_outlined,
              title: 'Estadísticas',
              subtitle: 'Análisis de ventas',
              color: Colors.green[700]!,
              onTap: () {
                Navigator.pop(context);
                // TODO: Navegar a estadísticas
              },
            ),
            _buildMenuItem(
              context,
              icon: Icons.receipt_long_outlined,
              title: 'Reportes',
              subtitle: 'Historial y facturación',
              color: _gris,
              onTap: () {
                Navigator.pop(context);
                // TODO: Navegar a reportes
              },
            ),
            const Divider(height: 32),
            _buildSeccion('CUENTA'),
            _buildMenuItem(
              context,
              icon: Icons.person_outline,
              title: 'Mi Perfil',
              subtitle: 'Datos personales',
              color: _azul,
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const PerfilProveedorEditable(),
                  ),
                );
              },
            ),
            _buildMenuItem(
              context,
              icon: Icons.settings_outlined,
              title: 'Configuración',
              subtitle: 'Preferencias y ajustes',
              color: _gris,
              onTap: () {
                Navigator.pop(context);
                // TODO: Navegar a configuración
              },
            ),
            _buildMenuItem(
              context,
              icon: Icons.help_outline,
              title: 'Ayuda y Soporte',
              subtitle: 'Asistencia técnica',
              color: Colors.blue[700]!,
              onTap: () {
                Navigator.pop(context);
                // TODO: Navegar a ayuda
              },
            ),
            const Divider(height: 32),
            _buildMenuItem(
              context,
              icon: Icons.logout,
              title: 'Cerrar Sesión',
              subtitle: 'Salir de la aplicación',
              color: _rojo,
              onTap: onCerrarSesion,
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  // ============================================
  // DRAWER HEADER
  // ============================================

  Widget _buildDrawerHeader(BuildContext context) {
    return Consumer<SupplierController>(
      builder: (context, controller, child) {
        return Container(
          padding: const EdgeInsets.only(
            top: 40,
            bottom: 24,
            left: 16,
            right: 16,
          ),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [_azul, _azulOscuro],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.2),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Icon(Icons.store, size: 32, color: _azul),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          controller.nombreNegocio,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 4),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 10,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: controller.verificado ? _verde : _naranja,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                controller.verificado
                                    ? Icons.check_circle
                                    : Icons.warning_amber,
                                size: 14,
                                color: Colors.white,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                controller.verificado
                                    ? 'Verificado'
                                    : 'Sin verificar',
                                style: const TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.email_outlined,
                      size: 16,
                      color: Colors.white.withValues(alpha: 0.9),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        controller.email,
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.9),
                          fontSize: 13,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  // ============================================
  // ALERTA VERIFICACIÓN
  // ============================================

  Widget _buildAlertaVerificacion(BuildContext context) {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            _naranja.withValues(alpha: 0.1),
            _naranja.withValues(alpha: 0.05),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _naranja, width: 2),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: _naranja,
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.warning_amber,
                  color: Colors.white,
                  size: 24,
                ),
              ),
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
            style: TextStyle(fontSize: 13, height: 1.4),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: () {
                Navigator.pop(context);
                // TODO: Mostrar información sobre verificación
              },
              icon: const Icon(Icons.info_outline, size: 18),
              label: const Text('Más información'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _naranja,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
          ),
        ],
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
            _azul.withValues(alpha: 0.1),
            _morado.withValues(alpha: 0.1),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _azul.withValues(alpha: 0.3), width: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(color: _azul, shape: BoxShape.circle),
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
        return _morado;
      default:
        return _gris;
    }
  }

  // ============================================
  // SECCIÓN
  // ============================================

  Widget _buildSeccion(String titulo) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
      child: Text(
        titulo,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.bold,
          color: Colors.grey[600],
          letterSpacing: 1.2,
        ),
      ),
    );
  }

  // ============================================
  // MENU ITEM
  // ============================================

  Widget _buildMenuItem(
    BuildContext context, {
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
    Widget? badge,
  }) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, color: color, size: 24),
        ),
        title: Row(
          children: [
            Expanded(
              child: Text(
                title,
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 15,
                ),
              ),
            ),
            if (badge != null) badge,
          ],
        ),
        subtitle: Text(
          subtitle,
          style: TextStyle(fontSize: 12, color: Colors.grey[600]),
        ),
        onTap: onTap,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      ),
    );
  }

  // ============================================
  // BADGE
  // ============================================

  Widget? _buildBadge(BuildContext context) {
    return Consumer<SupplierController>(
      builder: (context, controller, child) {
        final count = controller.pedidosPendientesCount;
        if (count == 0) return const SizedBox.shrink();

        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: _naranja,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            '$count',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 11,
              fontWeight: FontWeight.bold,
            ),
          ),
        );
      },
    );
  }
}
