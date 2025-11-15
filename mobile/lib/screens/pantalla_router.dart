// lib/screens/pantalla_router.dart

import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import './user/pantalla_inicio.dart';
import './supplier/pantalla_inicio_proveedor.dart';
import './delivery/pantalla_inicio_repartidor.dart';
import './admin/pantalla_dashboard.dart';

/// 🎯 Router inteligente que redirige según el rol del usuario
/// ✅ OPTIMIZADO: Usa rol cacheado, no hace petición al backend
class PantallaRouter extends StatefulWidget {
  const PantallaRouter({super.key});

  @override
  State<PantallaRouter> createState() => _PantallaRouterState();
}

class _PantallaRouterState extends State<PantallaRouter> {
  final _authService = AuthService();
  String? _error;

  @override
  void initState() {
    super.initState();
    _rutearSegunRol();
  }

  Future<void> _rutearSegunRol() async {
    try {
      debugPrint('═══════════════════════════════════════════════════════');
      debugPrint('🎯 ROUTER: Determinando ruta según rol...');
      debugPrint('═══════════════════════════════════════════════════════');

      // ✅ OPTIMIZADO: Obtener rol desde caché (no hace petición HTTP)
      final rol = _authService.getRolCacheado()?.toUpperCase();
      debugPrint('👤 Rol cacheado detectado: ${rol ?? "NULL"}');

      // Si no hay rol, verificar autenticación
      if (rol == null || rol.isEmpty) {
        debugPrint('❌ No hay rol cacheado');

        // Verificar si hay tokens guardados
        final isAuthenticated = _authService.isAuthenticated;
        debugPrint('🔐 Autenticado: $isAuthenticated');

        if (!isAuthenticated) {
          debugPrint('❌ No autenticado - Redirigiendo a login');
          if (mounted) {
            Navigator.pushReplacementNamed(context, '/login');
          }
          return;
        }

        // Si hay tokens pero no rol, cargar tokens y reintentar
        debugPrint('🔄 Tokens presentes pero sin rol - Cargando...');
        await _authService.loadTokens();

        final rolDespuesCarga = _authService.getRolCacheado()?.toUpperCase();
        if (rolDespuesCarga == null) {
          debugPrint('❌ No se pudo obtener rol - Redirigiendo a login');
          if (mounted) {
            Navigator.pushReplacementNamed(context, '/login');
          }
          return;
        }

        // Continuar con el rol cargado
        await _navegarSegunRol(rolDespuesCarga);
      } else {
        // Ya tenemos el rol, navegar directamente
        await _navegarSegunRol(rol);
      }

      debugPrint('═══════════════════════════════════════════════════════');
    } catch (e, stackTrace) {
      debugPrint('❌ Error en router: $e');
      debugPrint('StackTrace: $stackTrace');

      if (mounted) {
        setState(() {
          _error = 'Error al determinar ruta de inicio';
        });
      }
    }
  }

  Future<void> _navegarSegunRol(String rol) async {
    // Pequeño delay para evitar parpadeo de UI
    await Future.delayed(const Duration(milliseconds: 200));

    if (!mounted) return;

    Widget destino;
    String nombreRuta;

    switch (rol) {
      case 'USUARIO':
        debugPrint('🏠 Navegando a pantalla de USUARIO');
        destino = const PantallaInicio();
        nombreRuta = 'PantallaInicio (Usuario)';
        break;

      case 'REPARTIDOR':
        debugPrint('🚚 Navegando a pantalla de REPARTIDOR');
        destino = const PantallaInicioRepartidor();
        nombreRuta = 'PantallaInicioRepartidor';
        break;

      case 'PROVEEDOR':
        debugPrint('🏪 Navegando a pantalla de PROVEEDOR');
        destino = const PantallaInicioProveedor();
        nombreRuta = 'PantallaInicioProveedor';
        break;

      case 'ADMINISTRADOR':
        debugPrint('👨‍💼 Navegando a pantalla de ADMINISTRADOR');
        destino = const PantallaDashboard();
        nombreRuta = 'PantallaDashboard (Admin)';
        break;

      default:
        debugPrint('⚠️ Rol desconocido: $rol - Redirigiendo a login');
        Navigator.pushReplacementNamed(context, '/login');
        return;
    }

    debugPrint('✅ Navegando a: $nombreRuta');

    // Navegar sin animación para transición suave
    Navigator.pushReplacement(
      context,
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) => destino,
        transitionDuration: Duration.zero,
        reverseTransitionDuration: Duration.zero,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    // Mostrar error si algo salió mal
    if (_error != null) {
      return Scaffold(
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, size: 64, color: Colors.red),
                const SizedBox(height: 24),
                Text(
                  _error!,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 16),
                ),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: () {
                    setState(() {
                      _error = null;
                    });
                    _rutearSegunRol();
                  },
                  icon: const Icon(Icons.refresh),
                  label: const Text('Reintentar'),
                ),
                const SizedBox(height: 12),
                TextButton(
                  onPressed: () {
                    Navigator.pushReplacementNamed(context, '/login');
                  },
                  child: const Text('Volver al Login'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    // Pantalla de carga mientras se determina la ruta
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Logo o indicador de carga
            SizedBox(
              width: 60,
              height: 60,
              child: CircularProgressIndicator(
                strokeWidth: 3,
                valueColor: AlwaysStoppedAnimation<Color>(
                  Theme.of(context).primaryColor,
                ),
              ),
            ),
            const SizedBox(height: 24),
            Text(
              'Verificando sesión...',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Por favor espera',
              style: TextStyle(fontSize: 13, color: Colors.grey[400]),
            ),
          ],
        ),
      ),
    );
  }
}
