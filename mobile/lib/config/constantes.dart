// lib/config/constantes.dart

import '../config/api_config.dart';
import 'dart:developer' as developer;

// ══════════════════════════════════════════════════════════════════════════════
// 🌍 CONSTANTES GLOBALES JP EXPRESS
// ══════════════════════════════════════════════════════════════════════════════

class JPConstantes {
  // Prevenir instanciación
  JPConstantes._();

  // ────────────────────────────────────────────────────────────────────────────
  // 🎨 INFORMACIÓN DE LA APP
  // ────────────────────────────────────────────────────────────────────────────

  static const String appName = 'JP Express';
  static const String appVersion = '1.0.0';
  static const String appSlogan = '¡Tu delivery favorito!';

  // ────────────────────────────────────────────────────────────────────────────
  // 🖼️ IMÁGENES Y ASSETS
  // ────────────────────────────────────────────────────────────────────────────

  /// Avatar por defecto cuando el usuario no tiene foto
  static String get defaultAvatarUrl => 'https://via.placeholder.com/150';

  /// Logo de la app
  static const String logoPath = 'assets/images/logo.png';

  /// Placeholder de productos
  static const String productPlaceholder = 'assets/images/product_placeholder.png';

  // ────────────────────────────────────────────────────────────────────────────
  // 📏 LÍMITES Y VALIDACIONES
  // ────────────────────────────────────────────────────────────────────────────

  /// Tamaño máximo de imágenes (5 MB)
  static const int maxImageSizeMB = 5;
  static const int maxImageSizeBytes = maxImageSizeMB * 1024 * 1024;

  /// Extensiones de imagen permitidas
  static const List<String> allowedImageExtensions = [
    'jpg',
    'jpeg',
    'png',
    'webp',
  ];

  /// Extensiones de comprobante permitidas (incluye PDF)
  static const List<String> allowedComprobanteExtensions = [
    'jpg',
    'jpeg',
    'png',
    'pdf',
  ];

  /// Longitud mínima de alias (direcciones, métodos de pago)
  static const int minAliasLength = 3;
  static const int maxAliasLength = 50;

  /// Longitud máxima de observaciones
  static const int maxObservacionesLength = 100;

  /// Longitud mínima de dirección
  static const int minDireccionLength = 10;

  // ────────────────────────────────────────────────────────────────────────────
  // 🗺️ COORDENADAS ECUADOR
  // ────────────────────────────────────────────────────────────────────────────

  /// Rango de latitud válido para Ecuador
  static const double latitudMinEcuador = -5.0;
  static const double latitudMaxEcuador = 2.0;

  /// Rango de longitud válido para Ecuador
  static const double longitudMinEcuador = -92.0;
  static const double longitudMaxEcuador = -75.0;

  /// Coordenadas por defecto (Quito)
  static const double latitudDefaultQuito = -0.1807;
  static const double longitudDefaultQuito = -78.4678;

  // ────────────────────────────────────────────────────────────────────────────
  // 🎯 PEDIDOS Y RIFAS
  // ────────────────────────────────────────────────────────────────────────────

  /// Pedidos necesarios para ser cliente VIP
  static const int pedidosParaVIP = 10;

  /// Pedidos necesarios para participar en rifa mensual
  static const int pedidosParaRifa = 3;

  /// Calificación mínima
  static const double calificacionMin = 0.0;

  /// Calificación máxima
  static const double calificacionMax = 5.0;

  // ────────────────────────────────────────────────────────────────────────────
  // ⏱️ TIMEOUTS Y DELAYS
  // ────────────────────────────────────────────────────────────────────────────

  /// Duración de snackbars
  static const Duration snackbarDuration = Duration(seconds: 3);

  /// Duración de snackbars de error (más largo)
  static const Duration snackbarErrorDuration = Duration(seconds: 5);

  /// Delay para búsqueda (debounce)
  static const Duration searchDebounce = Duration(milliseconds: 500);

  /// Timeout para cargar imágenes
  static const Duration imageLoadTimeout = Duration(seconds: 10);

  // ────────────────────────────────────────────────────────────────────────────
  // 💬 MENSAJES COMUNES
  // ────────────────────────────────────────────────────────────────────────────

  static const String msgCargando = 'Cargando...';
  static const String msgGuardando = 'Guardando...';
  static const String msgActualizando = 'Actualizando...';
  static const String msgEliminando = 'Eliminando...';

  static const String msgExito = 'Operación exitosa';
  static const String msgError = 'Ocurrió un error';
  static const String msgSinConexion = 'Sin conexión a internet';
  static const String msgTimeout = 'La operación tardó demasiado';

  static const String msgConfirmarEliminar = '¿Estás seguro de eliminar este elemento?';
  static const String msgCancelar = 'Cancelar';
  static const String msgConfirmar = 'Confirmar';
  static const String msgAceptar = 'Aceptar';

  // ────────────────────────────────────────────────────────────────────────────
  // 🎨 ANIMACIONES
  // ────────────────────────────────────────────────────────────────────────────

  /// Duración estándar de animaciones
  static const Duration animationDuration = Duration(milliseconds: 300);

  /// Duración de animaciones rápidas
  static const Duration animationDurationFast = Duration(milliseconds: 150);

  /// Duración de animaciones lentas
  static const Duration animationDurationSlow = Duration(milliseconds: 500);

  // ────────────────────────────────────────────────────────────────────────────
  // 📱 RESPONSIVE
  // ────────────────────────────────────────────────────────────────────────────

  /// Ancho máximo para tablet
  static const double maxWidthTablet = 768.0;

  /// Ancho máximo para desktop
  static const double maxWidthDesktop = 1200.0;

  /// Padding horizontal estándar
  static const double paddingHorizontal = 16.0;

  /// Padding vertical estándar
  static const double paddingVertical = 16.0;
}

// ══════════════════════════════════════════════════════════════════════════════
// ✅ VALIDADORES
// ══════════════════════════════════════════════════════════════════════════════

class JPValidadores {
  // Prevenir instanciación
  JPValidadores._();

  /// Valida si una coordenada está dentro de Ecuador
  static bool coordenadaValidaEcuador(double lat, double lon) {
    return (lat >= JPConstantes.latitudMinEcuador &&
            lat <= JPConstantes.latitudMaxEcuador) &&
        (lon >= JPConstantes.longitudMinEcuador &&
            lon <= JPConstantes.longitudMaxEcuador);
  }

  /// Valida si las coordenadas NO son (0, 0)
  static bool coordenadasNoNulas(double lat, double lon) {
    return !(lat == 0.0 && lon == 0.0);
  }

  /// Valida alias (direcciones, métodos de pago)
  static String? validarAlias(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'El nombre no puede estar vacío';
    }

    final trimmed = value.trim();

    if (trimmed.length < JPConstantes.minAliasLength) {
      return 'Debe tener al menos ${JPConstantes.minAliasLength} caracteres';
    }

    if (trimmed.length > JPConstantes.maxAliasLength) {
      return 'No puede exceder ${JPConstantes.maxAliasLength} caracteres';
    }

    return null;
  }

  /// Valida dirección
  static String? validarDireccion(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'La dirección no puede estar vacía';
    }

    final trimmed = value.trim();

    if (trimmed.length < JPConstantes.minDireccionLength) {
      return 'Debe tener al menos ${JPConstantes.minDireccionLength} caracteres';
    }

    return null;
  }

  /// Valida observaciones
  static String? validarObservaciones(String? value) {
    if (value == null || value.trim().isEmpty) {
      return null; // Las observaciones son opcionales
    }

    final trimmed = value.trim();

    if (trimmed.length > JPConstantes.maxObservacionesLength) {
      return 'No puede exceder ${JPConstantes.maxObservacionesLength} caracteres';
    }

    return null;
  }

  /// Valida extensión de archivo
  static bool extensionValida(String filename, List<String> allowedExtensions) {
    final extension = filename.split('.').last.toLowerCase();
    return allowedExtensions.contains(extension);
  }

  /// Valida tamaño de archivo
  static bool tamanoValido(int sizeBytes) {
    return sizeBytes <= JPConstantes.maxImageSizeBytes;
  }

  /// Formatea tamaño de archivo a string legible
  static String formatearTamano(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// 🎨 HELPERS DE UI
// ══════════════════════════════════════════════════════════════════════════════

class JPHelpers {
  // Prevenir instanciación
  JPHelpers._();

  /// Construye URL completa de imagen desde el backend
  static String construirUrlImagen(String? path) {
    if (path == null || path.isEmpty) {
      return JPConstantes.defaultAvatarUrl;
    }

    // Si ya es una URL completa
    if (path.startsWith('http')) {
      return path;
    }

    // Si es una ruta relativa, construir con baseUrl
    return '${ApiConfig.baseUrl}$path';
  }

  /// Formatea fecha a string legible
  static String formatearFecha(DateTime fecha) {
    return '${fecha.day}/${fecha.month}/${fecha.year}';
  }

  /// Formatea fecha con hora
  static String formatearFechaHora(DateTime fecha) {
    return '${formatearFecha(fecha)} ${fecha.hour}:${fecha.minute.toString().padLeft(2, '0')}';
  }

  /// Calcula tiempo transcurrido desde una fecha
  static String tiempoTranscurrido(DateTime fecha) {
    final ahora = DateTime.now();
    final diferencia = ahora.difference(fecha);

    if (diferencia.inSeconds < 60) {
      return 'Hace ${diferencia.inSeconds}s';
    } else if (diferencia.inMinutes < 60) {
      return 'Hace ${diferencia.inMinutes}m';
    } else if (diferencia.inHours < 24) {
      return 'Hace ${diferencia.inHours}h';
    } else if (diferencia.inDays < 7) {
      return 'Hace ${diferencia.inDays}d';
    } else if (diferencia.inDays < 30) {
      return 'Hace ${(diferencia.inDays / 7).floor()}sem';
    } else if (diferencia.inDays < 365) {
      return 'Hace ${(diferencia.inDays / 30).floor()}mes';
    } else {
      return 'Hace ${(diferencia.inDays / 365).floor()}a';
    }
  }

  /// Obtiene saludo según hora del día
  static String obtenerSaludo() {
    final hora = DateTime.now().hour;

    if (hora < 12) {
      return 'Buenos días';
    } else if (hora < 18) {
      return 'Buenas tardes';
    } else {
      return 'Buenas noches';
    }
  }

  /// Trunca texto con ellipsis
  static String truncar(String texto, int maxLength) {
    if (texto.length <= maxLength) return texto;
    return '${texto.substring(0, maxLength)}...';
  }

  /// Determina si es dispositivo pequeño
  static bool esDispositivoPequeno(double width) {
    return width < JPConstantes.maxWidthTablet;
  }

  /// Determina si es tablet
  static bool esTablet(double width) {
    return width >= JPConstantes.maxWidthTablet &&
        width < JPConstantes.maxWidthDesktop;
  }

  /// Determina si es desktop
  static bool esDesktop(double width) {
    return width >= JPConstantes.maxWidthDesktop;
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// 🗺️ REGIONES DE ECUADOR
// ══════════════════════════════════════════════════════════════════════════════

enum RegionEcuador {
  costa,
  sierra,
  oriente,
  galapagos,
  desconocida,
}

class JPRegiones {
  // Prevenir instanciación
  JPRegiones._();

  /// Detecta la región de Ecuador según coordenadas
  static RegionEcuador detectarRegion(double lat, double lon) {
    // Costa: -3.5 a 2.0 lat, -81 a -75 lon
    if (lat >= -3.5 && lat <= 2.0 && lon >= -81.0 && lon <= -75.0) {
      return RegionEcuador.costa;
    }

    // Sierra: -4.5 a 1.5 lat, -79.5 a -77 lon
    if (lat >= -4.5 && lat <= 1.5 && lon >= -79.5 && lon <= -77.0) {
      return RegionEcuador.sierra;
    }

    // Oriente: -5 a 0.5 lat, -78 a -75 lon
    if (lat >= -5.0 && lat <= 0.5 && lon >= -78.0 && lon <= -75.0) {
      return RegionEcuador.oriente;
    }

    // Galápagos: -1.5 a 1.5 lat, -92 a -89 lon
    if (lat >= -1.5 && lat <= 1.5 && lon >= -92.0 && lon <= -89.0) {
      return RegionEcuador.galapagos;
    }

    return RegionEcuador.desconocida;
  }

  /// Obtiene nombre legible de la región
  static String nombreRegion(RegionEcuador region) {
    switch (region) {
      case RegionEcuador.costa:
        return 'Costa';
      case RegionEcuador.sierra:
        return 'Sierra';
      case RegionEcuador.oriente:
        return 'Oriente';
      case RegionEcuador.galapagos:
        return 'Galápagos';
      case RegionEcuador.desconocida:
        return 'Región desconocida';
    }
  }

  /// Obtiene emoji de la región
  static String emojiRegion(RegionEcuador region) {
    switch (region) {
      case RegionEcuador.costa:
        return '🏖️';
      case RegionEcuador.sierra:
        return '🏔️';
      case RegionEcuador.oriente:
        return '🌳';
      case RegionEcuador.galapagos:
        return '🐢';
      case RegionEcuador.desconocida:
        return '❓';
    }
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// 📊 TIPOS DE DATOS
// ══════════════════════════════════════════════════════════════════════════════

/// Tipo de dirección
enum TipoDireccion {
  casa,
  trabajo,
  otro,
}

extension TipoDireccionExtension on TipoDireccion {
  String get nombre {
    switch (this) {
      case TipoDireccion.casa:
        return 'Casa';
      case TipoDireccion.trabajo:
        return 'Trabajo';
      case TipoDireccion.otro:
        return 'Otro';
    }
  }

  String get icono {
    switch (this) {
      case TipoDireccion.casa:
        return '🏠';
      case TipoDireccion.trabajo:
        return '💼';
      case TipoDireccion.otro:
        return '📍';
    }
  }

  String get valor {
    switch (this) {
      case TipoDireccion.casa:
        return 'casa';
      case TipoDireccion.trabajo:
        return 'trabajo';
      case TipoDireccion.otro:
        return 'otro';
    }
  }

  static TipoDireccion fromString(String value) {
    switch (value.toLowerCase()) {
      case 'casa':
        return TipoDireccion.casa;
      case 'trabajo':
        return TipoDireccion.trabajo;
      default:
        return TipoDireccion.otro;
    }
  }
}

/// Tipo de método de pago
enum TipoMetodoPago {
  efectivo,
  transferencia,
  tarjeta,
}

extension TipoMetodoPagoExtension on TipoMetodoPago {
  String get nombre {
    switch (this) {
      case TipoMetodoPago.efectivo:
        return 'Efectivo';
      case TipoMetodoPago.transferencia:
        return 'Transferencia';
      case TipoMetodoPago.tarjeta:
        return 'Tarjeta';
    }
  }

  String get icono {
    switch (this) {
      case TipoMetodoPago.efectivo:
        return '💵';
      case TipoMetodoPago.transferencia:
        return '🏦';
      case TipoMetodoPago.tarjeta:
        return '💳';
    }
  }

  String get descripcion {
    switch (this) {
      case TipoMetodoPago.efectivo:
        return 'Pago al recibir el pedido';
      case TipoMetodoPago.transferencia:
        return 'Requiere comprobante';
      case TipoMetodoPago.tarjeta:
        return 'Pago con tarjeta';
    }
  }

  bool get requiereComprobante {
    return this == TipoMetodoPago.transferencia;
  }

  String get valor {
    switch (this) {
      case TipoMetodoPago.efectivo:
        return 'efectivo';
      case TipoMetodoPago.transferencia:
        return 'transferencia';
      case TipoMetodoPago.tarjeta:
        return 'tarjeta';
    }
  }

  static TipoMetodoPago fromString(String value) {
    switch (value.toLowerCase()) {
      case 'efectivo':
        return TipoMetodoPago.efectivo;
      case 'transferencia':
        return TipoMetodoPago.transferencia;
      case 'tarjeta':
        return TipoMetodoPago.tarjeta;
      default:
        return TipoMetodoPago.efectivo;
    }
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// 🎯 CONFIGURACIÓN DE CARACTERÍSTICAS
// ══════════════════════════════════════════════════════════════════════════════

class JPFeatures {
  // Prevenir instanciación
  JPFeatures._();

  /// ¿Habilitar modo debug?
  static const bool debugMode = true;

  /// ¿Mostrar logs detallados?
  static const bool verboseLogs = true;

  /// ¿Habilitar animaciones?
  static const bool enableAnimations = true;

  /// ¿Habilitar sistema de rifas?
  static const bool enableRifas = true;

  /// ¿Habilitar notificaciones push?
  static const bool enablePushNotifications = true;

  /// ¿Habilitar geolocalización?
  static const bool enableGeolocation = true;

  /// ¿Habilitar modo offline?
  static const bool enableOfflineMode = false;

  /// ¿Habilitar analytics?
  static const bool enableAnalytics = false;

  /// ¿Habilitar crash reporting?
  static const bool enableCrashReporting = false;
}

// ══════════════════════════════════════════════════════════════════════════════
// 📱 LINKS Y CONTACTO
// ══════════════════════════════════════════════════════════════════════════════

class JPContacto {
  // Prevenir instanciación
  JPContacto._();

  /// Teléfono de soporte
  static const String telefonoSoporte = '+593 99 999 9999';

  /// Email de soporte
  static const String emailSoporte = 'soporte@jpexpress.com';

  /// WhatsApp
  static const String whatsapp = '+593999999999';

  /// Facebook
  static const String facebook = 'https://facebook.com/jpexpress';

  /// Instagram
  static const String instagram = 'https://instagram.com/jpexpress';

  /// Twitter
  static const String twitter = 'https://twitter.com/jpexpress';

  /// Sitio web
  static const String sitioWeb = 'https://jpexpress.com';

  /// Términos y condiciones
  static const String terminosUrl = 'https://jpexpress.com/terminos';

  /// Política de privacidad
  static const String privacidadUrl = 'https://jpexpress.com/privacidad';
}

// ══════════════════════════════════════════════════════════════════════════════
// 🔧 DEBUG HELPERS
// ══════════════════════════════════════════════════════════════════════════════

class JPDebug {
  // Prevenir instanciación
  JPDebug._();

  /// Imprime mensaje de debug si está habilitado
  static void log(String message, {String? tag}) {
    if (JPFeatures.debugMode) {
      final tagStr = tag != null ? '[$tag] ' : '';
      developer.log('🔵 JP Express $tagStr$message', name: 'JPDebug');
    }
  }

  /// Imprime error
  static void error(String message, {Object? error, StackTrace? stackTrace}) {
    if (JPFeatures.debugMode) {
      developer.log(
        '🔴 JP Express ERROR: $message',
        name: 'JPDebug',
        error: error,
        stackTrace: stackTrace,
      );
    }
  }

  /// Imprime advertencia
  static void warning(String message) {
    if (JPFeatures.debugMode) {
      developer.log('🟡 JP Express WARNING: $message', name: 'JPDebug');
    }
  }

  /// Imprime éxito
  static void success(String message) {
    if (JPFeatures.debugMode) {
      developer.log('🟢 JP Express SUCCESS: $message', name: 'JPDebug');
    }
  }

  /// Imprime información
  static void info(String message) {
    if (JPFeatures.debugMode && JPFeatures.verboseLogs) {
      developer.log('ℹ️ JP Express INFO: $message', name: 'JPDebug');
    }
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// 🎨 EJEMPLOS DE USO
// ══════════════════════════════════════════════════════════════════════════════

/*

EJEMPLOS DE USO DE CONSTANTES:

1. Validar coordenadas:
   ```dart
   if (JPValidadores.coordenadaValidaEcuador(lat, lon)) {
     JPDebug.log('Coordenadas válidas para Ecuador');
   }
   ```

2. Validar alias:
   ```dart
   final error = JPValidadores.validarAlias(textoIngresado);
   if (error != null) {
     mostrarError(error);
   }
   ```

3. Construir URL de imagen:
   ```dart
   final url = JPHelpers.construirUrlImagen(perfil.fotoPerfil);
   Image.network(url);
   ```

4. Formatear fecha:
   ```dart
   final fecha = JPHelpers.formatearFecha(DateTime.now());
   Text(fecha);
   ```

5. Detectar región:
   ```dart
   final region = JPRegiones.detectarRegion(lat, lon);
   final nombre = JPRegiones.nombreRegion(region);
   final emoji = JPRegiones.emojiRegion(region);
   ```

6. Usar enums:
   ```dart
   final tipo = TipoDireccion.casa;
   Text(tipo.nombre); // "Casa"
   Text(tipo.icono); // "🏠"
   ```

7. Debug logs:
   ```dart
   JPDebug.log('Usuario inició sesión', tag: 'Auth');
   JPDebug.error('Error al cargar datos', error: e);
   JPDebug.success('Perfil actualizado');
   ```

8. Features flags:
   ```dart
   if (JPFeatures.enableRifas) {
     mostrarSeccionRifas();
   }
   ```

9. Contacto:
   ```dart
   launchUrl(Uri.parse('tel:${JPContacto.telefonoSoporte}'));
   launchUrl(Uri.parse('mailto:${JPContacto.emailSoporte}'));
   ```

10. Responsive:
    ```dart
    final width = MediaQuery.of(context).size.width;
    if (JPHelpers.esDispositivoPequeno(width)) {
      return LayoutMovil();
    } else if (JPHelpers.esTablet(width)) {
      return LayoutTablet();
    } else {
      return LayoutDesktop();
    }
    ```

*/
