// lib/config/rutas.dart

import 'package:flutter/material.dart';

// ==========================================
// IMPORTACIONES DE PANTALLAS
// ==========================================

// Auth
import '../screens/auth/pantalla_login.dart';
import '../screens/auth/pantalla_registro.dart';
import '../screens/auth/pantalla_recuperar_password.dart';
import '../screens/auth/panel_recuperacion_contraseña/pantalla_verificar_codigo.dart';
import '../screens/auth/panel_recuperacion_contraseña/pantalla_nueva_password.dart';

// Router
import '../screens/pantalla_router.dart';

// User
import '../screens/user/pantalla_inicio.dart';

// Repartidor
import '../screens/delivery/pantalla_inicio_repartidor.dart';

// Proveedor
import '../screens/supplier/pantalla_inicio_proveedor.dart';

// Admin
import '../screens/admin/pantalla_dashboard.dart';

// Test
import '../screens/test_connection_screen.dart';

/// Clase que centraliza todas las rutas de la aplicación
/// Facilita la navegación y hace el código más escalable
class Rutas {
  // ==========================================
  // ✅ NOMBRES DE RUTAS (CONSTANTES)
  // ==========================================

  // Auth
  static const String login = '/login';
  static const String registro = '/registro';
  static const String recuperarPassword = '/recuperar-password';
  static const String verificarCodigo = '/verificar-codigo';
  static const String nuevaPassword = '/nueva-password';

  // Router (redirige según rol)
  static const String router = '/router';

  // User
  static const String inicio = '/inicio';
  static const String perfil = '/perfil';
  static const String configuracion = '/configuracion';

  // Repartidor
  static const String repartidorHome = '/repartidor/home';
  static const String repartidorPedidos = '/repartidor/pedidos';
  static const String repartidorHistorial = '/repartidor/historial';
  static const String perfilRepartidor = '/repartidor/perfil';

  // Proveedor
  static const String proveedorHome = '/proveedor/home';
  static const String proveedorProductos = '/proveedor/productos';
  static const String proveedorPedidos = '/proveedor/pedidos';
  static const String proveedorEstadisticas = '/proveedor/estadisticas';

  // Admin
  static const String adminHome = '/admin/home';
  static const String adminUsuarios = '/admin/usuarios';
  static const String adminReportes = '/admin/reportes';

  // Test
  static const String test = '/test';

  // ==========================================
  // ✅ MAPA DE RUTAS
  // ==========================================

  /// Retorna el mapa de rutas para usar en MaterialApp
  static Map<String, WidgetBuilder> obtenerRutas() {
    return {
      // ============================================
      // AUTH
      // ============================================
      login: (context) => const PantallaLogin(),
      registro: (context) => const PantallaRegistro(),
      recuperarPassword: (context) => const PantallaRecuperarPassword(),
      verificarCodigo: (context) => const PantallaVerificarCodigo(),
      nuevaPassword: (context) => const PantallaNuevaPassword(),

      // ============================================
      // ROUTER (Detecta rol automáticamente)
      // ============================================
      router: (context) => const PantallaRouter(),

      // ============================================
      // USER
      // ============================================
      inicio: (context) => const PantallaInicio(),

      // ============================================
      // REPARTIDOR
      // ============================================
      repartidorHome: (context) => const PantallaInicioRepartidor(),

      // ============================================
      // PROVEEDOR
      // ============================================
      proveedorHome: (context) => const PantallaInicioProveedor(),

      // ============================================
      // ADMIN
      // ============================================
      adminHome: (context) => const PantallaDashboard(),

      // ============================================
      // TEST
      // ============================================
      test: (context) => const TestConnectionScreen(),
    };
  }

  // ==========================================
  // ✅ MÉTODOS DE NAVEGACIÓN SIMPLIFICADOS
  // ==========================================

  /// Navega a una ruta
  static Future<T?> irA<T>(BuildContext context, String ruta) {
    return Navigator.pushNamed<T>(context, ruta);
  }

  /// Navega a una ruta y elimina todas las anteriores
  static Future<T?> irAYLimpiar<T>(BuildContext context, String ruta) {
    return Navigator.pushNamedAndRemoveUntil<T>(
      context,
      ruta,
      (route) => false,
    );
  }

  /// Navega a una ruta y reemplaza la actual
  static Future<T?> reemplazarCon<T>(BuildContext context, String ruta) {
    return Navigator.pushReplacementNamed<T, Object?>(context, ruta);
  }

  /// Vuelve a la pantalla anterior
  static void volver(BuildContext context, [dynamic resultado]) {
    Navigator.pop(context, resultado);
  }

  /// Verifica si puede volver atrás
  static bool puedeVolver(BuildContext context) {
    return Navigator.canPop(context);
  }

  // ==========================================
  // ✅ NAVEGACIÓN INTELIGENTE CON ROUTER
  // ==========================================

  /// Navega al router que detecta automáticamente el rol del usuario
  ///
  /// Úsalo después de login/registro exitoso.
  /// El router verificará el rol y redirigirá a la pantalla correcta.
  static Future<void> irARouter(BuildContext context) {
    return irAYLimpiar(context, router);
  }

  // ==========================================
  // ✅ NAVEGACIÓN POR ROL
  // ==========================================

  /// Navega a la pantalla home según el rol del usuario
  ///
  /// Si no se proporciona el rol, usa [irARouter] para detectarlo automáticamente.
  static Future<void> irAHomePorRol(BuildContext context, [String? rol]) {
    // Si no se pasa el rol, usar el router para detectarlo
    if (rol == null || rol.isEmpty) {
      return irARouter(context);
    }

    String ruta;

    switch (rol.toUpperCase()) {
      case 'ADMINISTRADOR':
        ruta = adminHome;
        break;
      case 'REPARTIDOR':
        ruta = repartidorHome;
        break;
      case 'PROVEEDOR':
        ruta = proveedorHome;
        break;
      case 'USUARIO':
      default:
        ruta = inicio;
        break;
    }

    return irAYLimpiar(context, ruta);
  }

  // ==========================================
  // ✅ RUTAS CON ARGUMENTOS
  // ==========================================

  /// Navega a una ruta pasando argumentos
  static Future<T?> irAConArgumentos<T>(
    BuildContext context,
    String ruta,
    Object argumentos,
  ) {
    return Navigator.pushNamed<T>(context, ruta, arguments: argumentos);
  }

  /// Obtiene los argumentos de la ruta actual
  static T? obtenerArgumentos<T>(BuildContext context) {
    return ModalRoute.of(context)?.settings.arguments as T?;
  }

  // ==========================================
  // ✅ FLUJO DE RECUPERACIÓN DE CONTRASEÑA
  // ==========================================

  /// Inicia el flujo de recuperación de contraseña
  ///
  /// Flujo completo:
  /// 1. /recuperar-password (ingresa email)
  /// 2. /verificar-codigo (ingresa código de 6 dígitos)
  /// 3. /nueva-password (ingresa nueva contraseña)
  /// 4. /login (confirmación y login)

  static Future<void> iniciarRecuperacionPassword(BuildContext context) {
    return irA(context, recuperarPassword);
  }

  /// Navega a verificar código con el email como argumento
  static Future<void> irAVerificarCodigo(BuildContext context, String email) {
    return irAConArgumentos(context, verificarCodigo, {'email': email});
  }

  /// Navega a nueva password con email y código como argumentos
  static Future<void> irANuevaPassword(
    BuildContext context, {
    required String email,
    required String codigo,
  }) {
    return irAConArgumentos(context, nuevaPassword, {
      'email': email,
      'codigo': codigo,
    });
  }

  /// Completa el flujo de recuperación y vuelve al login
  static Future<void> completarRecuperacionPassword(BuildContext context) {
    return irAYLimpiar(context, login);
  }

  // ==========================================
  // ✅ NAVEGACIÓN CON TRANSICIONES PERSONALIZADAS
  // ==========================================

  /// Navega con transición de fade
  static Future<T?> irAConFade<T>(
    BuildContext context,
    Widget pantalla, {
    Duration duracion = const Duration(milliseconds: 300),
  }) {
    return Navigator.push<T>(
      context,
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) => pantalla,
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          return FadeTransition(opacity: animation, child: child);
        },
        transitionDuration: duracion,
      ),
    );
  }

  /// Navega con transición de slide desde abajo
  static Future<T?> irAConSlide<T>(
    BuildContext context,
    Widget pantalla, {
    Duration duracion = const Duration(milliseconds: 300),
  }) {
    return Navigator.push<T>(
      context,
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) => pantalla,
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          const begin = Offset(0.0, 1.0);
          const end = Offset.zero;
          const curve = Curves.easeInOut;

          var tween = Tween(
            begin: begin,
            end: end,
          ).chain(CurveTween(curve: curve));

          return SlideTransition(
            position: animation.drive(tween),
            child: child,
          );
        },
        transitionDuration: duracion,
      ),
    );
  }

  /// Navega con transición de scale
  static Future<T?> irAConScale<T>(
    BuildContext context,
    Widget pantalla, {
    Duration duracion = const Duration(milliseconds: 300),
  }) {
    return Navigator.push<T>(
      context,
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) => pantalla,
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          return ScaleTransition(
            scale: Tween<double>(begin: 0.0, end: 1.0).animate(
              CurvedAnimation(parent: animation, curve: Curves.easeInOut),
            ),
            child: child,
          );
        },
        transitionDuration: duracion,
      ),
    );
  }

  // ==========================================
  // ✅ DIÁLOGOS Y BOTTOM SHEETS
  // ==========================================

  /// Muestra un diálogo modal
  static Future<T?> mostrarDialogo<T>(
    BuildContext context,
    Widget dialogo, {
    bool barrierDismissible = true,
  }) {
    return showDialog<T>(
      context: context,
      barrierDismissible: barrierDismissible,
      builder: (context) => dialogo,
    );
  }

  /// Muestra un bottom sheet modal
  static Future<T?> mostrarBottomSheet<T>(
    BuildContext context,
    Widget contenido, {
    bool isDismissible = true,
    bool enableDrag = true,
  }) {
    return showModalBottomSheet<T>(
      context: context,
      isDismissible: isDismissible,
      enableDrag: enableDrag,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => contenido,
    );
  }

  // ==========================================
  // ✅ VALIDACIÓN DE RUTAS
  // ==========================================

  /// Verifica si una ruta existe
  static bool existeRuta(String ruta) {
    return obtenerRutas().containsKey(ruta);
  }

  /// Obtiene todas las rutas disponibles
  static List<String> obtenerTodasLasRutas() {
    return obtenerRutas().keys.toList();
  }

  // ==========================================
  // ✅ RUTAS PROTEGIDAS
  // ==========================================

  /// Lista de rutas que requieren autenticación
  static const List<String> rutasProtegidas = [
    router, // ✅ El router verifica autenticación
    inicio,
    perfil,
    configuracion,
    repartidorHome,
    repartidorPedidos,
    repartidorHistorial,
    proveedorHome,
    proveedorProductos,
    proveedorPedidos,
    proveedorEstadisticas,
    adminHome,
    adminUsuarios,
    adminReportes,
  ];

  /// Lista de rutas públicas (no requieren autenticación)
  static const List<String> rutasPublicas = [
    login,
    registro,
    recuperarPassword,
    verificarCodigo,
    nuevaPassword,
    test,
  ];

  /// Verifica si una ruta requiere autenticación
  static bool requiereAutenticacion(String ruta) {
    return rutasProtegidas.contains(ruta);
  }

  /// Verifica si una ruta es pública
  static bool esRutaPublica(String ruta) {
    return rutasPublicas.contains(ruta);
  }

  // ==========================================
  // ✅ RUTAS POR ROL
  // ==========================================

  /// Rutas permitidas para usuarios normales
  static const List<String> rutasUsuario = [inicio, perfil, configuracion];

  /// Rutas permitidas para repartidores
  static const List<String> rutasRepartidor = [
    repartidorHome,
    repartidorPedidos,
    repartidorHistorial,
    perfil,
    configuracion,
  ];

  /// Rutas permitidas para proveedores
  static const List<String> rutasProveedor = [
    proveedorHome,
    proveedorProductos,
    proveedorPedidos,
    proveedorEstadisticas,
    perfil,
    configuracion,
  ];

  /// Rutas permitidas para administradores
  static const List<String> rutasAdmin = [
    adminHome,
    adminUsuarios,
    adminReportes,
    perfil,
    configuracion,
  ];

  /// Verifica si un rol tiene permiso para acceder a una ruta
  static bool tienePermiso(String rol, String ruta) {
    switch (rol.toUpperCase()) {
      case 'ADMINISTRADOR':
        return rutasAdmin.contains(ruta);
      case 'REPARTIDOR':
        return rutasRepartidor.contains(ruta);
      case 'PROVEEDOR':
        return rutasProveedor.contains(ruta);
      case 'USUARIO':
        return rutasUsuario.contains(ruta);
      default:
        return false;
    }
  }

  // ==========================================
  // ✅ UTILIDADES PARA DEBUG
  // ==========================================

  /// Imprime todas las rutas registradas (útil para debug)
  static void imprimirRutas() {
    debugPrint('╔════════════════════════════════════════╗');
    debugPrint('║  📍 RUTAS REGISTRADAS EN LA APLICACIÓN  ║');
    debugPrint('╠════════════════════════════════════════╣');

    final rutas = obtenerTodasLasRutas();
    for (var i = 0; i < rutas.length; i++) {
      debugPrint('║ ${i + 1}. ${rutas[i]}');
    }

    debugPrint('╠════════════════════════════════════════╣');
    debugPrint('║ Total de rutas: ${rutas.length}');
    debugPrint('╚════════════════════════════════════════╝');
  }
}
