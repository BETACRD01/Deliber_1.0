// lib/screens/supplier/controllers/supplier_controller.dart

import 'dart:io';
import 'package:flutter/material.dart';
import '../../../services/auth_service.dart';
import '../../../services/proveedor_service.dart';
import '../../../models/proveedor.dart';
import '../../../apis/helpers/api_exception.dart';

/// Controller para gestionar la pantalla del proveedor
/// ✅ ACTUALIZADO: Incluye edición de contacto, RUC y tipo de proveedor
class SupplierController extends ChangeNotifier {
  final AuthService _authService;
  final ProveedorService _proveedorService;

  // ============================================
  // ESTADO PRINCIPAL
  // ============================================
  ProveedorModel? _proveedor;
  bool _loading = true;
  String? _error;
  bool _rolIncorrecto = false;

  // Estados secundarios para operaciones
  bool _actualizandoPerfil = false;
  bool _subiendoLogo = false;
  bool _actualizandoContacto = false;

  SupplierController({
    AuthService? authService,
    ProveedorService? proveedorService,
  }) : _authService = authService ?? AuthService(),
       _proveedorService = proveedorService ?? ProveedorService();

  // ============================================
  // GETTERS - ESTADO PRINCIPAL
  // ============================================

  ProveedorModel? get proveedor => _proveedor;
  bool get loading => _loading;
  bool get verificado => _proveedor?.verificado ?? false;
  String? get error => _error;
  bool get rolIncorrecto => _rolIncorrecto;

  // ============================================
  // GETTERS - ESTADOS SECUNDARIOS
  // ============================================

  bool get actualizandoPerfil => _actualizandoPerfil;
  bool get subiendoLogo => _subiendoLogo;
  bool get actualizandoContacto => _actualizandoContacto;

  // ============================================
  // GETTERS - DATOS DEL PROVEEDOR
  // ============================================

  String get nombreNegocio => _proveedor?.nombre ?? '';
  String get email => _proveedor?.emailActual ?? '';
  String get ruc => _proveedor?.ruc ?? '';
  String get ciudad => _proveedor?.ciudad ?? '';
  String get direccion => _proveedor?.direccion ?? '';
  String? get logo => _proveedor?.logoUrlCompleta;
  String get tipoProveedor => _proveedor?.tipoProveedorDisplay ?? '';
  String get telefono => _proveedor?.celularActual ?? '';
  String get nombreCompleto => _proveedor?.nombreCompleto ?? '';

  // Horarios
  String? get horarioApertura => _proveedor?.horarioApertura;
  String? get horarioCierre => _proveedor?.horarioCierre;
  bool get estaAbierto => _proveedor?.estaAbierto ?? false;
  String? get horarioCompleto => _proveedor?.horarioCompleto;

  // Configuración
  bool get activo => _proveedor?.activo ?? false;
  double get comision => _proveedor?.comisionPorcentaje ?? 0.0;

  // Fechas
  DateTime? get fechaCreacion => _proveedor?.createdAt;
  DateTime? get ultimaActualizacion => _proveedor?.updatedAt;

  // ============================================
  // GETTERS - DATOS OPERACIONALES
  // ============================================

  final List<Map<String, dynamic>> _productos = [];
  final List<Map<String, dynamic>> _pedidosPendientes = [];

  List<Map<String, dynamic>> get productos => _productos;
  List<Map<String, dynamic>> get pedidosPendientes => _pedidosPendientes;
  int get totalProductos => _productos.length;
  int get pedidosPendientesCount => _pedidosPendientes.length;

  // Estadísticas
  double get ventasHoy => 0.0;
  double get ventasMes => 0.0;
  int get pedidosCompletados => 0;
  double get valoracionPromedio => 0.0;
  int get totalResenas => 0;

  // ============================================
  // MÉTODOS - CARGAR DATOS INICIALES
  // ============================================

  Future<void> cargarDatos() async {
    _loading = true;
    _error = null;
    _rolIncorrecto = false;
    notifyListeners();

    try {
      final rolUsuario = _authService.getRolCacheado()?.toUpperCase();
      debugPrint('🔍 Validando rol: $rolUsuario');

      if (rolUsuario != 'PROVEEDOR') {
        _rolIncorrecto = true;
        _error = 'Esta pantalla es solo para proveedores';
        _loading = false;
        debugPrint('⚠️ Rol incorrecto: $rolUsuario');
        notifyListeners();
        return;
      }

      debugPrint('📥 Cargando datos del proveedor...');
      _proveedor = await _proveedorService.obtenerMiProveedor();

      debugPrint('✅ Proveedor cargado: ${_proveedor!.nombre}');
      _loading = false;
      _error = null;
    } on ApiException catch (e) {
      _handleApiException(e);
      _loading = false;
    } catch (e, stackTrace) {
      _error = 'Error al cargar información del proveedor';
      _loading = false;
      debugPrint('❌ Error: $e\n$stackTrace');
    }

    notifyListeners();
  }

  // ============================================
  // MÉTODOS - ACTUALIZAR PERFIL (Negocio)
  // ============================================

  /// Actualiza datos del negocio: nombre, RUC, tipo, descripción, ubicación, horarios
  Future<bool> actualizarPerfil(Map<String, dynamic> datos) async {
    // Validar que no esté vacío
    if (datos.isEmpty) {
      _error = 'No hay datos para actualizar';
      notifyListeners();
      return false;
    }

    // Validar campos
    if (!_validarDatosPerfil(datos)) {
      notifyListeners();
      return false;
    }

    _actualizandoPerfil = true;
    _error = null;
    notifyListeners();

    try {
      debugPrint('🏪 Actualizando perfil del negocio...');
      debugPrint('📊 Datos a enviar: $datos');

      _proveedor = await _proveedorService.actualizarMiProveedor(datos);

      debugPrint('✅ Perfil del negocio actualizado');
      _actualizandoPerfil = false;
      _error = null;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _handleApiException(e);
      _actualizandoPerfil = false;
      notifyListeners();
      return false;
    } catch (e, stackTrace) {
      _error = 'Error al actualizar perfil: $e';
      _actualizandoPerfil = false;
      debugPrint('❌ Error: $e\n$stackTrace');
      notifyListeners();
      return false;
    }
  }

  // ============================================
  // MÉTODOS - ACTUALIZAR DATOS DE CONTACTO (✅ NUEVO)
  // ============================================
  /// Usa el endpoint PÚBLICO (no admin)
  Future<bool> actualizarDatosContacto({
    String? email,
    String? firstName,
    String? lastName,
    String? telefono,
  }) async {
    // Validar que al menos un campo esté presente
    if ((email == null || email.isEmpty) &&
        (firstName == null || firstName.isEmpty) &&
        (lastName == null || lastName.isEmpty) &&
        (telefono == null || telefono.isEmpty)) {
      _error = 'Debes proporcionar al menos un dato de contacto';
      notifyListeners();
      return false;
    }

    _actualizandoContacto = true;
    _error = null;
    notifyListeners();

    try {
      debugPrint('👤 Actualizando mis datos de contacto...');
      debugPrint(
        '📊 Email: $email, Nombre: $firstName, Apellido: $lastName, Teléfono: $telefono',
      );

      // ✅ CAMBIO IMPORTANTE: Usar el nuevo método público (NO admin)
      _proveedor = await _proveedorService.editarMiContacto(
        email: email,
        firstName: firstName,
        lastName: lastName,
      );

      // Actualizar teléfono si viene y es diferente
      // (el teléfono se guarda en campos del proveedor, no del usuario)
      if (telefono != null && telefono.isNotEmpty) {
        debugPrint('📱 Actualizando teléfono: $telefono');

        final datosAdicionales = {'telefono': telefono};
        _proveedor = await _proveedorService.actualizarMiProveedor(
          datosAdicionales,
        );
      }

      debugPrint('✅ Datos de contacto actualizados correctamente');
      _actualizandoContacto = false;
      _error = null;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _handleApiException(e);
      _actualizandoContacto = false;
      notifyListeners();
      return false;
    } catch (e, stackTrace) {
      _error = 'Error al actualizar datos de contacto: $e';
      _actualizandoContacto = false;
      debugPrint('❌ Error: $e\n$stackTrace');
      notifyListeners();
      return false;
    }
  }
  // ============================================
  // MÉTODOS - SUBIR LOGO
  // ============================================

  /// Sube el logo/imagen del proveedor
  Future<bool> subirLogo(File logoFile) async {
    // Validar que el archivo existe
    if (!logoFile.existsSync()) {
      _error = 'El archivo no existe';
      notifyListeners();
      return false;
    }

    // Validar tamaño (máximo 5 MB)
    final tamano = logoFile.lengthSync();
    const tamanoMaximo = 5 * 1024 * 1024;

    if (tamano > tamanoMaximo) {
      _error = 'El archivo es demasiado grande (máximo 5 MB)';
      notifyListeners();
      return false;
    }

    _subiendoLogo = true;
    _error = null;
    notifyListeners();

    try {
      debugPrint('🖼️ Subiendo logo...');
      debugPrint('📁 Tamaño: ${(tamano / 1024 / 1024).toStringAsFixed(2)} MB');

      _proveedor = await _proveedorService.subirMiLogo(logoFile);

      debugPrint('✅ Logo subido: ${_proveedor!.logoUrlCompleta}');
      _subiendoLogo = false;
      _error = null;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _handleApiException(e);
      _subiendoLogo = false;
      notifyListeners();
      return false;
    } catch (e, stackTrace) {
      _error = 'Error al subir logo: $e';
      _subiendoLogo = false;
      debugPrint('❌ Error: $e\n$stackTrace');
      notifyListeners();
      return false;
    }
  }

  // ============================================
  // MÉTODOS PRIVADOS - VALIDACIÓN
  // ============================================

  bool _validarDatosPerfil(Map<String, dynamic> datos) {
    final camposValidos = {
      'nombre',
      'descripcion',
      'telefono',
      'direccion',
      'ciudad',
      'horarioApertura',
      'horarioCierre',
      'horario_apertura',
      'horario_cierre',
      'comisionPorcentaje',
      'tipo_proveedor',
      'tipoProveedor',
      'ruc',
    };

    // Validar que todos los campos sean válidos
    for (var key in datos.keys) {
      if (!camposValidos.contains(key)) {
        _error = 'Campo no válido: $key';
        return false;
      }
    }

    // Validar nombre no vacío
    if ((datos['nombre'] as String?)?.isEmpty ?? true) {
      _error = 'El nombre del negocio es requerido';
      return false;
    }

    // Validar RUC si viene en los datos
    if (datos.containsKey('ruc')) {
      final ruc = datos['ruc'] as String?;
      if (ruc != null && ruc.isEmpty) {
        _error = 'El RUC es requerido';
        return false;
      }
      if (ruc != null && ruc.length < 10) {
        _error = 'El RUC debe tener al menos 10 caracteres';
        return false;
      }
    }

    // Validar tipo de proveedor si viene en los datos
    if (datos.containsKey('tipo_proveedor')) {
      final tipo = datos['tipo_proveedor'] as String?;
      if (tipo == null || tipo.isEmpty) {
        _error = 'El tipo de proveedor es requerido';
        return false;
      }
    }

    return true;
  }

  // ============================================
  // MÉTODOS PRIVADOS - MANEJO DE ERRORES
  // ============================================

  void _handleApiException(ApiException e) {
    if (e.statusCode == 404) {
      _rolIncorrecto = true;
      _error = 'No tienes proveedor vinculado';
    } else if (e.statusCode == 401) {
      _error = 'Sesión expirada. Vuelve a iniciar sesión';
    } else if (e.statusCode == 403) {
      _error = 'No tienes permisos para esta acción';
    } else if (e.statusCode == 400) {
      _error = e.message;
    } else {
      _error = e.message;
    }
    debugPrint('❌ ApiException: ${e.message}');
  }

  // ============================================
  // MÉTODOS - UTILIDAD
  // ============================================

  /// Refresca todos los datos del proveedor
  Future<void> refrescar() async {
    await cargarDatos();
  }

  /// Cierra la sesión del usuario
  Future<bool> cerrarSesion() async {
    try {
      debugPrint('🔓 Cerrando sesión...');
      await _authService.logout();
      debugPrint('✅ Sesión cerrada');
      return true;
    } catch (e) {
      debugPrint('❌ Error cerrando sesión: $e');
      _error = 'Error al cerrar sesión';
      notifyListeners();
      return false;
    }
  }
}
