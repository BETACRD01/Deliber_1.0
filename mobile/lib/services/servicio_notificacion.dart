// servicio_notificacion.dart (ACTUALIZADO)
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter/material.dart';
import '../apis/usuarios_api.dart'; // ✅ NUEVO: Importar API

class NotificationService {
  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();
  final UsuariosApi _usuariosApi = UsuariosApi(); // ✅ NUEVO

  Future<void> initialize() async {
    // 1. Pedir permisos
    NotificationSettings settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: false,
    );

    debugPrint('📱 Permisos de notificación: ${settings.authorizationStatus}');

    // 2. Configurar notificaciones locales
    const AndroidInitializationSettings androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');

    const InitializationSettings initSettings = InitializationSettings(
      android: androidSettings,
    );

    await _localNotifications.initialize(
      initSettings,
      onDidReceiveNotificationResponse: (details) {
        debugPrint('📌 Notificación tocada: ${details.payload}');
      },
    );

    // 3. Obtener token FCM
    String? token = await _messaging.getToken();
    if (token != null) {
      debugPrint('🔑 Token FCM: ${token.substring(0, 30)}...');

      // ✅ NUEVO: Enviar token al backend
      await _enviarTokenAlBackend(token);

      // ✅ NUEVO: Escuchar cuando el token se refresca
      _messaging.onTokenRefresh.listen((nuevoToken) {
        debugPrint('🔄 Token FCM refrescado');
        _enviarTokenAlBackend(nuevoToken);
      });
    } else {
      debugPrint('⚠️ No se pudo obtener el token FCM');
    }

    // 4. Escuchar mensajes en foreground
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      debugPrint('📬 Mensaje recibido en foreground');
      if (message.notification != null) {
        _showLocalNotification(message);
      }
    });

    // 5. Manejar clic en notificación (app cerrada/background)
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      debugPrint('🖱️ Notificación abierta: ${message.messageId}');
      // Navegar a pantalla específica si es necesario
    });
  }

  // ✅ NUEVO: Envía el token FCM al backend
  Future<void> _enviarTokenAlBackend(String token) async {
    try {
      final response = await _usuariosApi.registrarFCMToken(token);

      if (response['success'] == true || response.containsKey('message')) {
        debugPrint('✅ Token FCM enviado al backend exitosamente');
      } else {
        debugPrint('⚠️ Respuesta inesperada del backend: $response');
      }
    } catch (e) {
      debugPrint('❌ Error enviando token al backend: $e');
      // No lanzamos error para no bloquear la inicialización
    }
  }

  Future<void> _showLocalNotification(RemoteMessage message) async {
    const AndroidNotificationDetails androidDetails =
        AndroidNotificationDetails(
          'high_importance_channel',
          'Notificaciones Importantes',
          channelDescription: 'Canal para notificaciones de alta prioridad',
          importance: Importance.high,
          priority: Priority.high,
          showWhen: true,
        );

    const NotificationDetails notificationDetails = NotificationDetails(
      android: androidDetails,
    );

    await _localNotifications.show(
      message.hashCode,
      message.notification?.title ?? 'Sin título',
      message.notification?.body ?? 'Sin mensaje',
      notificationDetails,
      payload: message.data.toString(),
    );
  }

  Future<String?> getToken() async {
    return await _messaging.getToken();
  }

  // ✅ NUEVO: Eliminar token al cerrar sesión
  Future<void> eliminarToken() async {
    try {
      await _usuariosApi.eliminarFCMToken();
      await _messaging.deleteToken();
      debugPrint('✅ Token FCM eliminado del backend y dispositivo');
    } catch (e) {
      debugPrint('❌ Error eliminando token: $e');
    }
  }
}
