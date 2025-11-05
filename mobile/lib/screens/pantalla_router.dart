// lib/screens/pantalla_router.dart

import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../apis/helpers/api_exception.dart';
import './user/pantalla_inicio.dart';
import './supplier/pantalla_inicio_proveedor.dart';
import './delivery/pantalla_inicio_repartidor.dart';
import './auth/pantalla_login.dart';

/// 🎯 Router inteligente que redirige según el rol del usuario
class PantallaRouter extends StatefulWidget {
  const PantallaRouter({super.key});

  @override
  State<PantallaRouter> createState() => _PantallaRouterState();
}

class _PantallaRouterState extends State<PantallaRouter> {
  final _api = AuthService();
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _verificarRol();
  }

  Future<void> _verificarRol() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      // Obtener perfil del usuario autenticado
      final perfil = await _api.getPerfil();
      final usuario = perfil['usuario'];
      final rol = usuario['rol'] as String?;

      debugPrint('🎭 Rol detectado: $rol');

      if (!mounted) return;

      // Redirigir según el rol
      Widget destino;
      switch (rol?.toUpperCase()) {
        case 'PROVEEDOR':
          destino = const PantallaInicioProveedor();
          break;
        case 'REPARTIDOR':
          destino = const PantallaInicioRepartidor();
          break;
        case 'USUARIO':
        default:
          destino = const PantallaInicio();
          break;
      }

      // Navegar sin animación
      Navigator.pushReplacement(
        context,
        PageRouteBuilder(
          pageBuilder: (context, animation, secondaryAnimation) => destino,
          transitionDuration: Duration.zero,
        ),
      );
    } on ApiException catch (e) {
      debugPrint('❌ ApiException: ${e.message}');

      if (mounted) {
        if (e.isAuthError) {
          // Token inválido o expirado - ir a login
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (_) => const PantallaLogin()),
          );
        } else {
          setState(() => _error = e.message);
        }
      }
    } catch (e) {
      debugPrint('❌ Error inesperado: $e');
      if (mounted) {
        setState(() => _error = 'Error al verificar sesión');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(color: Theme.of(context).primaryColor),
              const SizedBox(height: 16),
              const Text(
                'Verificando sesión...',
                style: TextStyle(fontSize: 14, color: Colors.grey),
              ),
            ],
          ),
        ),
      );
    }

    if (_error != null) {
      return Scaffold(
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, size: 64, color: Colors.red),
                const SizedBox(height: 16),
                Text(
                  _error!,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 16),
                ),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: _verificarRol,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Reintentar'),
                ),
                const SizedBox(height: 12),
                TextButton(
                  onPressed: () {
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(builder: (_) => const PantallaLogin()),
                    );
                  },
                  child: const Text('Volver al Login'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    // Mientras se decide, mostrar pantalla vacía
    return const Scaffold(body: Center(child: CircularProgressIndicator()));
  }
}
