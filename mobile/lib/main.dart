// lib/main.dart

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:provider/provider.dart';
// Configuración baseF
import './config/rutas.dart';
import './config/api_config.dart';
import './services/servicio_notificacion.dart';
import './services/ubicacion_service.dart';
import './services/auth_service.dart';
import './apis/subapis/http_client.dart';
// Providers
import './providers/proveedor_roles.dart';
// Controllers
import './screens/supplier/controllers/supplier_controller.dart';

// ============================================
// 🔔 HANDLER PARA NOTIFICACIONES EN BACKGROUND
// ============================================
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  debugPrint('🔨 Notificación recibida en background');
  debugPrint('  Título: ${message.notification?.title}');
  debugPrint('  Mensaje: ${message.notification?.body}');
  debugPrint('  Data: ${message.data}');
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // ============================================
  // PASO 1: Inicializar Firebase
  // ============================================
  try {
    debugPrint('🔥 Inicializando Firebase...');
    await Firebase.initializeApp();
    debugPrint('✅ Firebase inicializado');
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
  } catch (e) {
    debugPrint('❌ Error inicializando Firebase: $e');
  }

  // ============================================
  // PASO 2: Inicializar detección de red
  // ============================================
  try {
    debugPrint('🌐 Inicializando detección de red...');
    await ApiConfig.initialize();
    debugPrint('✅ Detección de red completada');
  } catch (e) {
    debugPrint('⚠️ Error detectando red: $e');
  }

  // ============================================
  // ✅ PASO 3: Cargar tokens UNA SOLA VEZ
  // ============================================
  final apiClient = ApiClient();

  try {
    debugPrint('🔑 Cargando tokens desde storage...');
    await apiClient.loadTokens();
    debugPrint('✅ Tokens cargados correctamente');
  } catch (e) {
    debugPrint('⚠️ Error cargando tokens: $e');
  }

  final hasToken = apiClient.isAuthenticated;
  debugPrint('🔍 Usuario autenticado: $hasToken');

  if (hasToken && apiClient.accessToken != null) {
    debugPrint('✅ Token válido en memoria');
    debugPrint('   Token: ${apiClient.accessToken!.substring(0, 20)}...');

    if (apiClient.tokenExpiry != null) {
      final remaining = apiClient.tokenExpiry!.difference(DateTime.now());
      if (remaining.isNegative) {
        debugPrint(
          '⚠️ Token EXPIRADO hace ${remaining.abs().inMinutes} minutos',
        );
      } else {
        debugPrint('⏰ Token expira en ${remaining.inMinutes} minutos');
      }
    }
  }

  // ============================================
  // ✅ PASO 4: Inicializar servicios (SOLO SI AUTENTICADO)
  // ============================================
  if (hasToken && apiClient.accessToken != null) {
    // 4.1: Inicializar notificaciones
    try {
      debugPrint('📱 Inicializando servicio de notificaciones...');
      final notificationService = NotificationService();
      await notificationService.initialize();
      debugPrint('✅ Notificaciones inicializadas');
    } catch (e) {
      debugPrint('⚠️ Error inicializando notificaciones: $e');
    }

    // ✅ 4.2: SOLO INICIAR UBICACIÓN PARA REPARTIDORES
    debugPrint('🔍 Verificando si debe iniciar servicio de ubicación...');

    // Verificar el rol del usuario
    final authService = AuthService();
    final rolUsuario = authService.getRolCacheado()?.toUpperCase();

    debugPrint('👤 Rol del usuario: $rolUsuario');

    if (rolUsuario == 'REPARTIDOR') {
      debugPrint(
        '✅ Usuario es REPARTIDOR - Iniciando servicio de ubicación...',
      );

      // DELAY AUMENTADO: 5 segundos
      Future.delayed(const Duration(seconds: 5), () async {
        try {
          debugPrint(
            '╔═══════════════════════════════════════════════════════════╗',
          );
          debugPrint(
            '║ 🚀 INICIANDO SERVICIO DE UBICACIÓN PARA REPARTIDOR        ║',
          );
          debugPrint(
            '╚═══════════════════════════════════════════════════════════╝',
          );

          final ubicacionService = UbicacionService();

          // Verificar nuevamente autenticación antes de iniciar
          if (!apiClient.isAuthenticated) {
            debugPrint('⚠️ Token no válido, cancelando inicio de ubicación');
            return;
          }

          final exito = await ubicacionService.iniciarEnvioPeriodico(
            intervalo: const Duration(seconds: 30),
          );

          if (exito) {
            debugPrint(
              '╔═══════════════════════════════════════════════════════════╗',
            );
            debugPrint(
              '║ ✅ SERVICIO DE UBICACIÓN INICIADO CORRECTAMENTE           ║',
            );
            debugPrint(
              '║    Modo: Periódico                                        ║',
            );
            debugPrint(
              '║    Intervalo: 30 segundos                                 ║',
            );
            debugPrint(
              '╚═══════════════════════════════════════════════════════════╝',
            );
          } else {
            debugPrint(
              '╔═══════════════════════════════════════════════════════════╗',
            );
            debugPrint(
              '║ ❌ NO SE PUDO INICIAR SERVICIO DE UBICACIÓN              ║',
            );
            debugPrint(
              '║    Razón: Fallo en inicialización                         ║',
            );
            debugPrint(
              '╚═══════════════════════════════════════════════════════════╝',
            );
          }
        } catch (e, stackTrace) {
          debugPrint(
            '╔═══════════════════════════════════════════════════════════╗',
          );
          debugPrint(
            '║ ❌ ERROR INICIANDO SERVICIO DE UBICACIÓN                   ║',
          );
          debugPrint('║    Error: $e');
          debugPrint(
            '╚═══════════════════════════════════════════════════════════╝',
          );
          debugPrint('Stack trace: $stackTrace');
        }
      });
    } else if (rolUsuario == 'PROVEEDOR') {
      debugPrint('🏪 Usuario es PROVEEDOR - No requiere servicio de ubicación');
    } else if (rolUsuario == 'USUARIO') {
      debugPrint(
        '👤 Usuario es USUARIO regular - No requiere servicio de ubicación',
      );
    } else if (rolUsuario == 'ADMINISTRADOR') {
      debugPrint(
        '👨‍💼 Usuario es ADMINISTRADOR - No requiere servicio de ubicación',
      );
    } else {
      debugPrint('⚠️ Rol desconocido o no definido: $rolUsuario');
    }
  } else {
    debugPrint('ℹ️ Usuario no autenticado - servicios no iniciados');
    debugPrint('   Los servicios se iniciarán después del login');
  }

  // ============================================
  // PASO 5: Determinar ruta inicial
  // ============================================
  String initialRoute = hasToken ? Rutas.router : Rutas.login;
  debugPrint('═══════════════════════════════════════════════════════════');
  debugPrint('🗺️ INICIANDO APLICACIÓN');
  debugPrint('   Ruta inicial: $initialRoute');
  debugPrint('   Autenticado: $hasToken');
  debugPrint('═══════════════════════════════════════════════════════════');

  runApp(MyApp(initialRoute: initialRoute));
}

/// Widget raíz principal
class MyApp extends StatelessWidget {
  final String initialRoute;
  const MyApp({super.key, this.initialRoute = Rutas.login});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // ✅ SUPPLIER CONTROLLER - disponible globalmente
        ChangeNotifierProvider(create: (_) => SupplierController()),

        // ✅ PROVEEDOR DE ROLES - gestión de roles múltiples
        ChangeNotifierProvider(create: (_) => ProveedorRoles()..inicializar()),
      ],
      child: MaterialApp(
        title: 'JP Express',
        debugShowCheckedModeBanner: false,

        // ============================================
        // LOCALIZACIÓN EN ESPAÑOL
        // ============================================
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: const [Locale('es', 'ES'), Locale('en', 'US')],
        locale: const Locale('es', 'ES'),

        // ============================================
        // TEMA GLOBAL
        // ============================================
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF4FC3F7)),
          useMaterial3: true,
          appBarTheme: const AppBarTheme(
            centerTitle: true,
            elevation: 0,
            foregroundColor: Colors.white,
          ),
          cardTheme: CardThemeData(
            elevation: 2,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
          inputDecorationTheme: InputDecorationTheme(
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
            filled: true,
            fillColor: Colors.white,
          ),
          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              elevation: 0,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
          snackBarTheme: SnackBarThemeData(
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
          ),
        ),

        // ============================================
        // RUTAS CENTRALIZADAS
        // ============================================
        initialRoute: initialRoute,
        routes: Rutas.obtenerRutas(),

        onUnknownRoute: (settings) {
          return MaterialPageRoute(
            builder: (context) => PantallaRutaNoEncontrada(
              nombreRuta: settings.name ?? 'desconocida',
            ),
          );
        },

        navigatorObservers: [RouteLogger()],
      ),
    );
  }
}

// ============================================
// PANTALLA DE RUTA NO ENCONTRADA
// ============================================
class PantallaRutaNoEncontrada extends StatelessWidget {
  final String nombreRuta;
  const PantallaRutaNoEncontrada({super.key, required this.nombreRuta});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Error de Navegación'),
        backgroundColor: Colors.red,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 80, color: Colors.red),
              const SizedBox(height: 24),
              Text(
                'La ruta "$nombreRuta" no existe',
                style: const TextStyle(fontSize: 18),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () {
                  Navigator.pushNamedAndRemoveUntil(
                    context,
                    Rutas.login,
                    (route) => false,
                  );
                },
                child: const Text('Volver al inicio'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ============================================
// OBSERVADOR DE RUTAS (DEBUG)
// ============================================
class RouteLogger extends NavigatorObserver {
  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) {
    debugPrint('>>> PUSH: ${route.settings.name}');
  }

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) {
    debugPrint('<<< POP: ${previousRoute?.settings.name}');
  }

  @override
  void didReplace({Route<dynamic>? newRoute, Route<dynamic>? oldRoute}) {
    debugPrint(
      '<<>> REPLACE: ${oldRoute?.settings.name} → ${newRoute?.settings.name}',
    );
  }
}
