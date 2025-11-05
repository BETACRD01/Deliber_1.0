// lib/main.dart

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

// Configuración base
import './config/network_initializer.dart';
import './config/rutas.dart';
import 'services/auth_service.dart';
import './services/servicio_notificacion.dart';

// 🚀 NUEVO: Integración de ubicación
import './services/ubicacion_service.dart';

// ============================================
// 🔔 HANDLER PARA NOTIFICACIONES EN BACKGROUND
// ============================================
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  debugPrint('📨 Notificación recibida en background');
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
  // PASO 2: Cargar tokens guardados
  // ============================================
  final authService = AuthService();
  await authService.loadTokens();

  // ============================================
  // PASO 3: Verificar si hay token válido
  // ============================================
  bool hasToken = await authService.hasStoredTokens();
  debugPrint('Token guardado: $hasToken');

  // ============================================
  // PASO 4: Inicializar detección de red
  // ============================================
  await NetworkInitializer.initialize();

  // ============================================
  // PASO 5: Inicializar notificaciones push (si hay token)
  // ============================================
  if (hasToken) {
    try {
      debugPrint('🔔 Inicializando servicio de notificaciones...');
      final notificationService = NotificationService();
      await notificationService.initialize();
      debugPrint('✅ Notificaciones inicializadas');
    } catch (e) {
      debugPrint('⚠️ Error inicializando notificaciones: $e');
    }
  }

  // ============================================
  // 🚀 PASO 6: Iniciar envío de ubicación
  // ============================================
  if (hasToken) {
    try {
      debugPrint('📍 Inicializando servicio de ubicación...');
      final ubicacionService = UbicacionService();
      ubicacionService.iniciarEnvioPeriodico(
        intervalo: const Duration(seconds: 30),
      );
      debugPrint('✅ Envío de ubicación iniciado correctamente');
    } catch (e) {
      debugPrint('⚠️ Error iniciando servicio de ubicación: $e');
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // ✅ PASO 7: Determinar ruta inicial (CORREGIDO)
  // ════════════════════════════════════════════════════════════════════════
  // 🎯 CORRECCIÓN CRÍTICA: Usar Router para detectar rol automáticamente
  // El Router verifica el rol del usuario y redirige a la pantalla correcta:
  //   - USUARIO → /inicio
  //   - REPARTIDOR → /repartidor/home
  //   - PROVEEDOR → /proveedor/home
  // ════════════════════════════════════════════════════════════════════════
  String initialRoute = hasToken ? Rutas.router : Rutas.login;
  debugPrint('Ruta inicial: $initialRoute');

  runApp(MyApp(initialRoute: initialRoute));
}

/// Widget raíz principal
class MyApp extends StatelessWidget {
  final String initialRoute;
  const MyApp({super.key, this.initialRoute = Rutas.login});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
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
