// lib/services/api_validators.dart

import '../../config/api_config.dart';

/// Clase con validadores para datos de entrada
class ApiValidators {
  // Prevenir instanciación
  ApiValidators._();

  /// Valida email según RFC 5322 (simplificado)
  static bool esEmailValido(String email) {
    if (email.isEmpty) return false;

    final emailRegex = RegExp(
      r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$",
    );

    return emailRegex.hasMatch(email);
  }

  /// Valida contraseña (debe coincidir con validación del backend)
  static Map<String, dynamic> validarPassword(String password) {
    final errores = <String>[];

    if (password.length < 8) {
      errores.add('Debe tener al menos 8 caracteres');
    }
    if (!password.contains(RegExp(r'[a-zA-Z]'))) {
      errores.add('Debe contener al menos una letra');
    }
    if (!password.contains(RegExp(r'\d'))) {
      errores.add('Debe contener al menos un número');
    }
    if (password.contains(RegExp(r'\s'))) {
      errores.add('No puede contener espacios');
    }

    return {'valida': errores.isEmpty, 'errores': errores};
  }

  /// Valida código de 6 dígitos (o la longitud definida en ApiConfig)
  static bool esCodigoValido(String codigo) {
    if (codigo.length != ApiConfig.codigoLongitud) return false;
    return RegExp(r'^\d{6}$').hasMatch(codigo);
  }

  /// Valida celular ecuatoriano (09XXXXXXXX)
  static bool esCelularValido(String celular) {
    if (celular.length != 10) return false;
    return RegExp(r'^09\d{8}$').hasMatch(celular);
  }

  /// Valida nombre de usuario (sin espacios, alfanumérico, guiones y underscores)
  static bool esUsernameValido(String username) {
    if (username.isEmpty || username.length < 3) return false;
    return RegExp(r'^[a-zA-Z0-9_-]+$').hasMatch(username);
  }

  /// Valida que un string no esté vacío después de trim
  static bool noEstaVacio(String? texto) {
    return texto != null && texto.trim().isNotEmpty;
  }

  /// Valida RUC ecuatoriano (13 dígitos numéricos)
  /// Nota: Solo valida formato; no verifica dígitos verificadores.
  static bool esRucValido(String ruc) {
    if (ruc.length != 13) return false;
    return RegExp(r'^\d{13}$').hasMatch(ruc);
  }

  /// Valida placa vehicular ecuatoriana (XXX-0000 o XXX0000)
  static bool esPlacaValida(String placa) {
    // Normaliza: sin guion y en mayúsculas
    final placaSinGuion = placa.replaceAll('-', '').toUpperCase();
    if (placaSinGuion.length != 7) return false;
    return RegExp(r'^[A-Z]{3}\d{4}$').hasMatch(placaSinGuion);
  }

  /// Valida licencia de conducir ecuatoriana (10 dígitos)
  static bool esLicenciaValida(String licencia) {
    if (licencia.length != 10) return false;
    return RegExp(r'^\d{10}$').hasMatch(licencia);
  }

  /// Valida fecha de nacimiento (debe ser mayor de 18 años)
  static Map<String, dynamic> validarFechaNacimiento(DateTime fecha) {
    final hoy = DateTime.now();
    int edad = hoy.year - fecha.year;

    if (hoy.month < fecha.month ||
        (hoy.month == fecha.month && hoy.day < fecha.day)) {
      edad--;
    }

    return {
      'valida': edad >= 18,
      'edad': edad,
      'mensaje': edad < 18 ? 'Debes ser mayor de 18 años' : null,
    };
  }

  /// Valida formato de fecha YYYY-MM-DD
  static bool esFechaFormatoValido(String fecha) {
    return RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(fecha);
  }

  /// Normaliza email (trim y lowercase)
  static String normalizarEmail(String email) {
    return email.trim().toLowerCase();
  }

  /// Normaliza texto (trim)
  static String normalizarTexto(String texto) {
    return texto.trim();
  }

  /// Normaliza placa (uppercase y sin espacios ni guiones)
  static String normalizarPlaca(String placa) {
    return placa.replaceAll(' ', '').replaceAll('-', '').toUpperCase();
  }
}
