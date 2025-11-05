// lib/services/api_exception.dart

/// Excepción personalizada para errores de API
class ApiException implements Exception {
  final int statusCode;
  final String message;
  final Map<String, dynamic> errors;
  final Map<String, dynamic>? details;
  final StackTrace? stackTrace;

  ApiException({
    required this.statusCode,
    required this.message,
    required this.errors,
    this.details,
    this.stackTrace,
  });

  @override
  String toString() {
    final buffer = StringBuffer();
    buffer.writeln('ApiException: $message');
    buffer.writeln('Status Code: $statusCode');

    if (errors.isNotEmpty) {
      buffer.writeln('Errors: $errors');
    }

    if (details != null && details!.isNotEmpty) {
      buffer.writeln('Details: $details');
    }

    if (stackTrace != null) {
      buffer.writeln('\nStack Trace:');
      buffer.writeln(stackTrace.toString());
    }

    return buffer.toString();
  }

  /// Convierte la excepción a JSON para logging
  Map<String, dynamic> toJson() {
    return {
      'statusCode': statusCode,
      'message': message,
      'errors': errors,
      'details': details,
      'stackTrace': stackTrace?.toString(),
      'timestamp': DateTime.now().toIso8601String(),
    };
  }

  // ============================================
  // GETTERS ÚTILES
  // ============================================

  /// Es un error de autenticación (401)
  bool get isAuthError => statusCode == 401;

  /// Es un error de red (sin conexión)
  bool get isNetworkError => statusCode == 0;

  /// Es un error del servidor (5xx)
  bool get isServerError => statusCode >= 500;

  /// Es un error de rate limiting (429)
  bool get isRateLimitError => statusCode == 429;

  /// La cuenta está bloqueada
  bool get isCuentaBloqueada =>
      details?['bloqueado'] == true || errors['bloqueado'] == true;

  /// Es un error de validación (400)
  bool get isValidationError => statusCode == 400;

  /// Es un error de permisos (403)
  bool get isForbiddenError => statusCode == 403;

  /// Es un error de recurso no encontrado (404)
  bool get isNotFoundError => statusCode == 404;

  // ============================================
  // GETTERS DE DETALLES
  // ============================================

  /// Intentos restantes antes del bloqueo
  int? get intentosRestantes => details?['intentos_restantes'];

  /// Segundos a esperar antes de reintentar
  int? get retryAfter => details?['retry_after'];

  /// Tipo de rate limit aplicado
  String? get tipoRateLimit => details?['tipo'];

  /// Mensaje de advertencia
  String? get mensajeAdvertencia => details?['mensaje_advertencia'];

  /// Fecha/hora hasta cuando está bloqueado
  String? get bloqueadoHasta => details?['bloqueado_hasta'];

  // ============================================
  // MÉTODOS ÚTILES
  // ============================================

  /// Obtiene el primer error de un campo específico
  String? getFieldError(String fieldName) {
    if (errors.containsKey(fieldName)) {
      final error = errors[fieldName];
      if (error is List && error.isNotEmpty) {
        return error[0].toString();
      } else if (error is String) {
        return error;
      }
    }
    return null;
  }

  /// Obtiene todos los errores de campos como lista
  List<String> getAllFieldErrors() {
    final fieldErrors = <String>[];

    errors.forEach((key, value) {
      if (key == 'non_field_errors') return;

      if (value is List && value.isNotEmpty) {
        fieldErrors.add('$key: ${value[0]}');
      } else if (value is String) {
        fieldErrors.add('$key: $value');
      }
    });

    return fieldErrors;
  }

  /// Obtiene un mensaje de error legible para el usuario
  String getUserFriendlyMessage() {
    // Errores específicos primero
    if (isNetworkError) {
      return 'Sin conexión a internet. Por favor verifica tu conexión.';
    }

    if (isServerError) {
      return 'Error en el servidor. Por favor intenta más tarde.';
    }

    if (isRateLimitError) {
      if (retryAfter != null) {
        return 'Demasiados intentos. Espera ${_formatSeconds(retryAfter!)} antes de reintentar.';
      }
      return 'Demasiados intentos. Por favor espera un momento.';
    }

    if (isCuentaBloqueada) {
      if (bloqueadoHasta != null) {
        return 'Tu cuenta está bloqueada hasta $bloqueadoHasta';
      }
      return 'Tu cuenta ha sido bloqueada temporalmente.';
    }

    // Retornar el mensaje principal
    return message;
  }

  /// Formatea segundos a texto legible
  String _formatSeconds(int segundos) {
    if (segundos < 60) {
      return '$segundos ${segundos == 1 ? "segundo" : "segundos"}';
    }

    final minutos = segundos ~/ 60;
    final segs = segundos % 60;

    if (segs == 0) {
      return '$minutos ${minutos == 1 ? "minuto" : "minutos"}';
    }

    return '$minutos ${minutos == 1 ? "minuto" : "minutos"} y $segs ${segs == 1 ? "segundo" : "segundos"}';
  }

  /// Determina si el error es recuperable (puede reintentar)
  bool get isRecoverable {
    return isNetworkError ||
        isRateLimitError ||
        statusCode == 503 || // Service Unavailable
        statusCode == 504; // Gateway Timeout
  }

  /// Crea una copia con valores actualizados
  ApiException copyWith({
    int? statusCode,
    String? message,
    Map<String, dynamic>? errors,
    Map<String, dynamic>? details,
    StackTrace? stackTrace,
  }) {
    return ApiException(
      statusCode: statusCode ?? this.statusCode,
      message: message ?? this.message,
      errors: errors ?? this.errors,
      details: details ?? this.details,
      stackTrace: stackTrace ?? this.stackTrace,
    );
  }
}
