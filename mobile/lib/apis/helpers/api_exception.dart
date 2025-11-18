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
    Map<String, dynamic>? errors,
    this.details,
    this.stackTrace,
  }) : errors = errors ?? {};

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

  bool get isAuthError => statusCode == 401;
  bool get isNetworkError => statusCode == 0;
  bool get isServerError => statusCode >= 500;
  bool get isRateLimitError => statusCode == 429;

  bool get isCuentaBloqueada =>
      details?['bloqueado'] == true || errors['bloqueado'] == true;

  bool get isValidationError => statusCode == 400;
  bool get isForbiddenError => statusCode == 403;
  bool get isNotFoundError => statusCode == 404;

  int? get intentosRestantes => details?['intentos_restantes'];
  int? get retryAfter => details?['retry_after'];
  String? get tipoRateLimit => details?['tipo'];
  String? get mensajeAdvertencia => details?['mensaje_advertencia'];
  String? get bloqueadoHasta => details?['bloqueado_hasta'];

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

  String getUserFriendlyMessage() {
    if (isNetworkError) {
      return 'Sin conexión a internet. Verifique su red.';
    }

    if (isServerError) {
      return 'Error del servidor. Intente más tarde.';
    }

    if (isRateLimitError) {
      if (retryAfter != null) {
        return 'Demasiados intentos. Espera ${_formatSeconds(retryAfter!)}.';
      }
      return 'Demasiados intentos. Intente más tarde.';
    }

    if (isCuentaBloqueada) {
      if (bloqueadoHasta != null) {
        return 'Tu cuenta está bloqueada hasta $bloqueadoHasta';
      }
      return 'Tu cuenta ha sido bloqueada temporalmente.';
    }

    return message;
  }

  String _formatSeconds(int segundos) {
    if (segundos < 60) {
      return '$segundos segundos';
    }

    final minutos = segundos ~/ 60;
    final segs = segundos % 60;

    if (segs == 0) {
      return '$minutos minutos';
    }

    return '$minutos minutos y $segs segundos';
  }

  bool get isRecoverable {
    return isNetworkError ||
        isRateLimitError ||
        statusCode == 503 ||
        statusCode == 504;
  }

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
