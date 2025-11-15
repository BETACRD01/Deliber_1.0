// lib/services/proveedor_service.dart

import 'dart:io';
import 'dart:developer' as developer;
import '../config/api_config.dart';
import '../models/proveedor.dart';
import '../apis/subapis/http_client.dart';

/// Servicio para gestionar proveedores
/// Consume endpoints de /api/proveedores/ y /api/admin/proveedores/
/// ✅ Incluye métodos tanto para usuario como para admin
class ProveedorService {
  final ApiClient _apiClient = ApiClient();

  void _log(String message, {Object? error, StackTrace? stackTrace}) {
    developer.log(
      message,
      name: 'ProveedorService',
      error: error,
      stackTrace: stackTrace,
    );
  }

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 1: 📋 CRUD BÁSICO (Endpoints públicos)
  // ════════════════════════════════════════════════════════════════════════

  /// GET - Listar todos los proveedores
  /// Soporta filtros: activos, verificados, tipo, ciudad, search
  Future<List<ProveedorListModel>> listarProveedores({
    bool? activos,
    bool? verificados,
    String? tipo,
    String? ciudad,
    String? search,
  }) async {
    try {
      _log('📥 Obteniendo lista de proveedores...');

      final url = ApiConfig.buildProveedoresUrl(
        activos: activos,
        verificados: verificados,
        tipo: tipo,
        ciudad: ciudad,
        search: search,
      );

      final response = await _apiClient.get(url);

      // Puede venir con paginación {count, results}
      final List<dynamic> proveedoresJson;
      if (response.containsKey('results')) {
        proveedoresJson = response['results'] as List<dynamic>;
      } else {
        proveedoresJson = [];
      }

      final proveedores = proveedoresJson
          .map(
            (json) => ProveedorListModel.fromJson(json as Map<String, dynamic>),
          )
          .toList();

      _log('✅ ${proveedores.length} proveedores obtenidos');
      return proveedores;
    } catch (e, stackTrace) {
      _log('❌ Error listando proveedores', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// GET - Obtener detalle de un proveedor
  Future<ProveedorModel> obtenerProveedor(int id) async {
    try {
      _log('📥 Obteniendo proveedor ID: $id');

      final response = await _apiClient.get(ApiConfig.proveedorDetalle(id));
      _log('📄 Response JSON: $response');

      final proveedor = ProveedorModel.fromJson(response);

      _log('✅ Proveedor obtenido: ${proveedor.nombre}');
      return proveedor;
    } catch (e, stackTrace) {
      _log('❌ Error obteniendo proveedor', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// POST - Crear proveedor (solo admin)
  Future<ProveedorModel> crearProveedor(Map<String, dynamic> data) async {
    try {
      _log('📤 Creando proveedor: ${data['nombre']}');

      final response = await _apiClient.post(ApiConfig.proveedores, data);
      _log('📄 Response JSON: $response');

      final proveedor = ProveedorModel.fromJson(response);

      _log('✅ Proveedor creado: ${proveedor.nombre} (ID: ${proveedor.id})');
      return proveedor;
    } catch (e, stackTrace) {
      _log('❌ Error creando proveedor', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// PUT - Actualizar proveedor completo
  Future<ProveedorModel> actualizarProveedor(
    int id,
    Map<String, dynamic> data,
  ) async {
    try {
      _log('📤 Actualizando proveedor ID: $id');
      _log('📊 Datos a enviar: $data');

      final response = await _apiClient.put(
        ApiConfig.proveedorActualizar(id),
        data,
      );
      _log('📄 Response JSON: $response');

      final proveedor = ProveedorModel.fromJson(response);

      _log('✅ Proveedor actualizado: ${proveedor.nombre}');
      return proveedor;
    } catch (e, stackTrace) {
      _log('❌ Error actualizando proveedor', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// PATCH - Actualizar proveedor parcial
  Future<ProveedorModel> actualizarProveedorParcial(
    int id,
    Map<String, dynamic> data,
  ) async {
    try {
      _log('📤 Actualizando parcialmente proveedor ID: $id');
      _log('📊 Datos a enviar: $data');

      final response = await _apiClient.patch(
        ApiConfig.proveedorActualizar(id),
        data,
      );
      _log('📄 Response JSON completo: $response');

      // ✅ Validar que la respuesta contiene datos
      if (response.isEmpty) {
        _log('❌ Respuesta vacía del servidor');
        throw FormatException('Respuesta vacía del servidor en PATCH');
      }

      if (response['id'] == null) {
        _log('⚠️ ADVERTENCIA: Campo "id" ausente en respuesta');
        _log('💡 Estructura recibida: ${response.keys.toList()}');
      }

      final proveedor = ProveedorModel.fromJson(response);

      _log('✅ Proveedor actualizado: ${proveedor.nombre}');
      return proveedor;
    } catch (e, stackTrace) {
      _log(
        '❌ Error actualizando parcialmente proveedor',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// DELETE - Eliminar proveedor (solo admin)
  Future<void> eliminarProveedor(int id) async {
    try {
      _log('🗑️ Eliminando proveedor ID: $id');

      await _apiClient.delete(ApiConfig.proveedorActualizar(id));

      _log('✅ Proveedor eliminado');
    } catch (e, stackTrace) {
      _log('❌ Error eliminando proveedor', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 2: 👤 PERFIL DEL PROVEEDOR AUTENTICADO
  // ════════════════════════════════════════════════════════════════════════

  /// GET - Obtener MI proveedor (usuario con rol PROVEEDOR)
  Future<ProveedorModel> obtenerMiProveedor() async {
    try {
      _log('📥 Obteniendo mi proveedor...');

      final response = await _apiClient.get(ApiConfig.miProveedor);
      _log('📄 Response JSON: $response');

      final proveedor = ProveedorModel.fromJson(response);

      _log('✅ Mi proveedor obtenido: ${proveedor.nombre}');
      return proveedor;
    } catch (e, stackTrace) {
      _log('❌ Error obteniendo mi proveedor', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// PATCH - Actualizar MI proveedor
  Future<ProveedorModel> actualizarMiProveedor(
    Map<String, dynamic> data,
  ) async {
    try {
      _log('📤 Actualizando mi proveedor...');
      _log('📊 Datos a enviar: $data');

      // Primero obtener mi proveedor para tener el ID
      final miProveedor = await obtenerMiProveedor();

      // Luego actualizar
      final response = await _apiClient.patch(
        ApiConfig.proveedorActualizar(miProveedor.id),
        data,
      );
      _log('📄 Response JSON completo: $response');

      // ✅ Validar respuesta
      if (response.isEmpty) {
        _log('❌ Respuesta vacía del servidor');
        throw FormatException('Respuesta vacía en PATCH');
      }

      if (response['id'] == null) {
        _log('⚠️ ADVERTENCIA CRÍTICA: Backend devolvió respuesta incompleta');
        _log('📋 Backend retornó: $response');

        // Como fallback, retornar proveedor con cambios locales
        return miProveedor.copyWith(
          nombre: data['nombre'] as String?,
          descripcion: data['descripcion'] as String?,
          direccion: data['direccion'] as String?,
          ciudad: data['ciudad'] as String?,
        );
      }

      final proveedorActualizado = ProveedorModel.fromJson(response);

      _log('✅ Mi proveedor actualizado: ${proveedorActualizado.nombre}');
      return proveedorActualizado;
    } catch (e, stackTrace) {
      _log(
        '❌ Error actualizando mi proveedor',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 3: 🖼️ SUBIDA DE LOGO
  // ════════════════════════════════════════════════════════════════════════

  /// PATCH - Subir logo del proveedor (multipart/form-data)
  Future<ProveedorModel> subirLogo(int id, File logoFile) async {
    try {
      _log('📤 Subiendo logo para proveedor ID: $id');
      _log('📁 Archivo: ${logoFile.path}');

      final response = await _apiClient.multipart(
        'PATCH',
        ApiConfig.proveedorActualizar(id),
        {},
        {'logo': logoFile},
      );

      _log('📄 Response recibida de multipart: $response');

      // ✅ VALIDACIÓN 1: Respuesta vacía
      if (response.isEmpty) {
        _log('❌ Respuesta vacía del servidor en subida de logo');
        throw FormatException('Respuesta vacía del servidor al subir logo');
      }

      _log('📋 Estructura de respuesta: ${response.keys.toList()}');

      // ✅ VALIDACIÓN 2: Campo "id" ausente
      if (response['id'] == null) {
        _log('⚠️ ADVERTENCIA CRÍTICA: Campo "id" ausente en respuesta de logo');
        _log('📊 Respuesta completa recibida: $response');

        // 🔧 FALLBACK: Obtener datos actualizados del servidor
        _log(
          '🔄 Realizando fallback: obteniendo datos actualizados del servidor...',
        );
        try {
          final proveedorActualizado = await obtenerProveedor(id);
          _log('✅ Logo subido (confirmado por GET posterior)');
          return proveedorActualizado;
        } catch (e) {
          _log(
            '❌ Error en fallback: no se pudo verificar logo subido',
            error: e,
          );
          rethrow;
        }
      }

      _log('✅ Respuesta válida recibida, parseando ProveedorModel...');
      final proveedor = ProveedorModel.fromJson(response);

      _log('✅ Logo subido exitosamente para: ${proveedor.nombre}');
      return proveedor;
    } catch (e, stackTrace) {
      _log('❌ Error subiendo logo', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// PATCH - Subir logo de MI proveedor
  Future<ProveedorModel> subirMiLogo(File logoFile) async {
    try {
      _log('📤 Subiendo mi logo...');
      _log('📁 Archivo: ${logoFile.path}');

      final miProveedor = await obtenerMiProveedor();
      _log('✅ ID de mi proveedor obtenido: ${miProveedor.id}');

      final resultado = await subirLogo(miProveedor.id, logoFile);

      _log('✅ Mi logo subido exitosamente');
      return resultado;
    } catch (e, stackTrace) {
      _log('❌ Error subiendo mi logo', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 4: 🔍 FILTROS Y BÚSQUEDAS
  // ════════════════════════════════════════════════════════════════════════

  /// GET - Proveedores activos
  Future<List<ProveedorListModel>> obtenerProveedoresActivos() async {
    try {
      _log('📥 Obteniendo proveedores activos...');

      final response = await _apiClient.get(ApiConfig.proveedoresActivos);

      final List<dynamic> proveedoresJson;
      if (response.containsKey('results')) {
        proveedoresJson = response['results'] as List<dynamic>;
      } else {
        proveedoresJson = [];
      }

      final proveedores = proveedoresJson
          .map(
            (json) => ProveedorListModel.fromJson(json as Map<String, dynamic>),
          )
          .toList();

      _log('✅ ${proveedores.length} proveedores activos obtenidos');
      return proveedores;
    } catch (e, stackTrace) {
      _log(
        '❌ Error obteniendo proveedores activos',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// GET - Proveedores abiertos ahora
  Future<List<ProveedorListModel>> obtenerProveedoresAbiertos() async {
    try {
      _log('📥 Obteniendo proveedores abiertos...');

      final response = await _apiClient.get(ApiConfig.proveedoresAbiertos);

      final List<dynamic> proveedoresJson;
      if (response.containsKey('results')) {
        proveedoresJson = response['results'] as List<dynamic>;
      } else {
        proveedoresJson = [];
      }

      final proveedores = proveedoresJson
          .map(
            (json) => ProveedorListModel.fromJson(json as Map<String, dynamic>),
          )
          .toList();

      _log('✅ ${proveedores.length} proveedores abiertos obtenidos');
      return proveedores;
    } catch (e, stackTrace) {
      _log(
        '❌ Error obteniendo proveedores abiertos',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// GET - Proveedores por tipo
  Future<List<ProveedorListModel>> obtenerProveedoresPorTipo(
    String tipo,
  ) async {
    try {
      _log('📥 Obteniendo proveedores de tipo: $tipo');

      final url = ApiConfig.proveedoresPorTipoUrl(tipo);
      final response = await _apiClient.get(url);

      final List<dynamic> proveedoresJson;
      if (response.containsKey('results')) {
        proveedoresJson = response['results'] as List<dynamic>;
      } else {
        proveedoresJson = [];
      }

      final proveedores = proveedoresJson
          .map(
            (json) => ProveedorListModel.fromJson(json as Map<String, dynamic>),
          )
          .toList();

      _log('✅ ${proveedores.length} proveedores de tipo $tipo obtenidos');
      return proveedores;
    } catch (e, stackTrace) {
      _log(
        '❌ Error obteniendo proveedores por tipo',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 5: ⚙️ ACCIONES ADMINISTRATIVAS (Endpoints públicos)
  // ════════════════════════════════════════════════════════════════════════

  /// POST - Activar proveedor (solo admin)
  Future<ProveedorModel> activarProveedor(int id) async {
    try {
      _log('📤 Activando proveedor ID: $id');

      final response = await _apiClient.post(
        ApiConfig.proveedorActivar(id),
        {},
      );

      final proveedor = ProveedorModel.fromJson(response['proveedor']);

      _log('✅ Proveedor activado: ${proveedor.nombre}');
      return proveedor;
    } catch (e, stackTrace) {
      _log('❌ Error activando proveedor', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// POST - Desactivar proveedor (solo admin)
  Future<ProveedorModel> desactivarProveedor(int id) async {
    try {
      _log('📤 Desactivando proveedor ID: $id');

      final response = await _apiClient.post(
        ApiConfig.proveedorDesactivar(id),
        {},
      );

      final proveedor = ProveedorModel.fromJson(response['proveedor']);

      _log('✅ Proveedor desactivado: ${proveedor.nombre}');
      return proveedor;
    } catch (e, stackTrace) {
      _log('❌ Error desactivando proveedor', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// POST - Verificar proveedor (solo admin)
  Future<ProveedorModel> verificarProveedor(int id) async {
    try {
      _log('📤 Verificando proveedor ID: $id');

      final response = await _apiClient.post(
        ApiConfig.proveedorVerificar(id),
        {},
      );

      final proveedor = ProveedorModel.fromJson(response['proveedor']);

      _log('✅ Proveedor verificado: ${proveedor.nombre}');
      return proveedor;
    } catch (e, stackTrace) {
      _log('❌ Error verificando proveedor', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 6: 🛡️ ADMIN ENDPOINTS - GESTIÓN COMPLETA
  // ════════════════════════════════════════════════════════════════════════

  /// GET - Listar proveedores (Admin)
  /// Acceso: Solo administrador
  /// Soporta filtros: verificado, activo, tipo_proveedor, search
  Future<List<ProveedorListModel>> listarProveedoresAdmin({
    bool? verificado,
    bool? activo,
    String? tipoProveedor,
    String? search,
  }) async {
    try {
      _log('🛡️ [ADMIN] Listando proveedores...');

      final url = ApiConfig.buildAdminProveedoresUrl(
        verificado: verificado,
        activo: activo,
        tipoProveedor: tipoProveedor,
        search: search,
      );

      final response = await _apiClient.get(url);

      final List<dynamic> proveedoresJson;
      if (response.containsKey('results')) {
        proveedoresJson = response['results'] as List<dynamic>;
      } else {
        proveedoresJson = [];
      }

      final proveedores = proveedoresJson
          .map(
            (json) => ProveedorListModel.fromJson(json as Map<String, dynamic>),
          )
          .toList();

      _log('✅ [ADMIN] ${proveedores.length} proveedores obtenidos');
      return proveedores;
    } catch (e, stackTrace) {
      _log(
        '❌ [ADMIN] Error listando proveedores',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// GET - Obtener proveedor (Admin)
  Future<ProveedorModel> obtenerProveedorAdmin(int id) async {
    try {
      _log('🛡️ [ADMIN] Obteniendo proveedor ID: $id');

      final response = await _apiClient.get(
        ApiConfig.adminProveedorDetalle(id),
      );

      final proveedor = ProveedorModel.fromJson(response);

      _log('✅ [ADMIN] Proveedor obtenido: ${proveedor.nombre}');
      return proveedor;
    } catch (e, stackTrace) {
      _log(
        '❌ [ADMIN] Error obteniendo proveedor',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// PUT - Actualizar proveedor completo (Admin)
  Future<ProveedorModel> actualizarProveedorAdmin(
    int id,
    Map<String, dynamic> data,
  ) async {
    try {
      _log('🛡️ [ADMIN] Actualizando proveedor ID: $id');
      _log('📊 Datos: $data');

      final response = await _apiClient.put(
        ApiConfig.adminProveedorDetalle(id),
        data,
      );

      final proveedor = ProveedorModel.fromJson(response);

      _log('✅ [ADMIN] Proveedor actualizado: ${proveedor.nombre}');
      return proveedor;
    } catch (e, stackTrace) {
      _log(
        '❌ [ADMIN] Error actualizando proveedor',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// PATCH - Actualizar parcialmente (Admin)
  Future<ProveedorModel> actualizarProveedorAdminParcial(
    int id,
    Map<String, dynamic> data,
  ) async {
    try {
      _log('🛡️ [ADMIN] Actualizando parcialmente proveedor ID: $id');
      _log('📊 Datos: $data');

      final response = await _apiClient.patch(
        ApiConfig.adminProveedorDetalle(id),
        data,
      );

      if (response.isEmpty || response['id'] == null) {
        _log(
          '⚠️ [ADMIN] Respuesta incompleta, obteniendo datos actualizados...',
        );
        return await obtenerProveedorAdmin(id);
      }

      final proveedor = ProveedorModel.fromJson(response);

      _log('✅ [ADMIN] Proveedor actualizado: ${proveedor.nombre}');
      return proveedor;
    } catch (e, stackTrace) {
      _log(
        '❌ [ADMIN] Error actualizando parcialmente',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  Future<ProveedorModel> editarMiContacto({
    String? email,
    String? firstName,
    String? lastName,
  }) async {
    try {
      _log('📤 Editando mis datos de contacto...');

      // Validar que al menos un parámetro esté presente
      if ((email == null || email.isEmpty) &&
          (firstName == null || firstName.isEmpty) &&
          (lastName == null || lastName.isEmpty)) {
        throw ArgumentError('Debes proporcionar al menos un dato de contacto');
      }

      // Construir body con solo los campos que vienen
      final data = <String, dynamic>{};

      if (email != null && email.isNotEmpty) {
        data['email'] = email;
        _log('📧 Email: $email');
      }

      if (firstName != null && firstName.isNotEmpty) {
        data['first_name'] = firstName;
        _log('👤 Nombre: $firstName');
      }

      if (lastName != null && lastName.isNotEmpty) {
        data['last_name'] = lastName;
        _log('👥 Apellido: $lastName');
      }

      _log('📊 Enviando datos: $data');

      final response = await _apiClient.patch(
        ApiConfig.miProveedorEditarContacto,
        data,
      );

      _log('📄 Response JSON: $response');

      // Validar que la respuesta contiene el proveedor
      if (!response.containsKey('proveedor')) {
        _log('⚠️ ADVERTENCIA: Respuesta sin campo "proveedor"');
        _log('📋 Estructura recibida: ${response.keys.toList()}');

        // Como fallback, obtener el proveedor actualizado
        _log('🔄 Obteniendo datos actualizados del servidor...');
        return await obtenerMiProveedor();
      }

      final proveedorData = response['proveedor'] as Map<String, dynamic>;
      final proveedor = ProveedorModel.fromJson(proveedorData);

      _log('✅ Datos de contacto actualizados: ${proveedor.nombreCompleto}');
      return proveedor;
    } catch (e, stackTrace) {
      _log(
        '❌ Error editando mis datos de contacto',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// PATCH - Editar contacto del proveedor (Admin)
  /// Edita: email, first_name, last_name del usuario vinculado
  Future<ProveedorModel> editarContactoProveedorAdmin(
    int id, {
    String? email,
    String? firstName,
    String? lastName,
  }) async {
    try {
      _log('🛡️ [ADMIN] Editando contacto de proveedor ID: $id');

      final data = <String, dynamic>{};
      if (email != null) data['email'] = email;
      if (firstName != null) data['first_name'] = firstName;
      if (lastName != null) data['last_name'] = lastName;

      if (data.isEmpty) {
        throw ArgumentError('Debe proporcionar al menos un campo para editar');
      }

      _log('📊 Datos: $data');

      final response = await _apiClient.patch(
        ApiConfig.adminProveedorEditarContacto(id),
        data,
      );

      if (response.isEmpty || response['id'] == null) {
        _log(
          '⚠️ [ADMIN] Respuesta incompleta en editar_contacto, obteniendo datos actualizados...',
        );
        return await obtenerProveedorAdmin(id);
      }

      final proveedor = ProveedorModel.fromJson(response);

      _log('✅ [ADMIN] Contacto editado para: ${proveedor.nombre}');
      return proveedor;
    } catch (e, stackTrace) {
      _log(
        '❌ [ADMIN] Error editando contacto',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// POST - Verificar proveedor (Admin)
  Future<ProveedorModel> verificarProveedorAdmin(
    int id, {
    required bool verificado,
    String? motivo,
  }) async {
    try {
      _log(
        '🛡️ [ADMIN] ${verificado ? 'Verificando' : 'Rechazando'} proveedor ID: $id',
      );

      final body = {
        'verificado': verificado,
        if (motivo != null) 'motivo': motivo,
      };

      final response = await _apiClient.post(
        ApiConfig.adminProveedorVerificar(id),
        body,
      );

      final proveedor = ProveedorModel.fromJson(response['proveedor']);

      _log(
        '✅ [ADMIN] Proveedor ${verificado ? 'verificado' : 'rechazado'}: ${proveedor.nombre}',
      );
      return proveedor;
    } catch (e, stackTrace) {
      _log(
        '❌ [ADMIN] Error verificando proveedor',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// POST - Desactivar proveedor (Admin)
  Future<ProveedorModel> desactivarProveedorAdmin(int id) async {
    try {
      _log('🛡️ [ADMIN] Desactivando proveedor ID: $id');

      final response = await _apiClient.post(
        ApiConfig.adminProveedorDesactivar(id),
        {},
      );

      final proveedor = ProveedorModel.fromJson(response['proveedor']);

      _log('✅ [ADMIN] Proveedor desactivado: ${proveedor.nombre}');
      return proveedor;
    } catch (e, stackTrace) {
      _log('❌ [ADMIN] Error desactivando', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// POST - Activar proveedor (Admin)
  Future<ProveedorModel> activarProveedorAdmin(int id) async {
    try {
      _log('🛡️ [ADMIN] Activando proveedor ID: $id');

      final response = await _apiClient.post(
        ApiConfig.adminProveedorActivar(id),
        {},
      );

      final proveedor = ProveedorModel.fromJson(response['proveedor']);

      _log('✅ [ADMIN] Proveedor activado: ${proveedor.nombre}');
      return proveedor;
    } catch (e, stackTrace) {
      _log('❌ [ADMIN] Error activando', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// GET - Proveedores pendientes (Admin)
  Future<List<ProveedorListModel>> obtenerProveedoresPendientes() async {
    try {
      _log('🛡️ [ADMIN] Obteniendo proveedores pendientes...');

      final response = await _apiClient.get(
        ApiConfig.adminProveedoresPendientes,
      );

      final List<dynamic> proveedoresJson;
      if (response.containsKey('proveedores')) {
        proveedoresJson = response['proveedores'] as List<dynamic>;
      } else if (response.containsKey('results')) {
        proveedoresJson = response['results'] as List<dynamic>;
      } else {
        proveedoresJson = [];
      }

      final proveedores = proveedoresJson
          .map(
            (json) => ProveedorListModel.fromJson(json as Map<String, dynamic>),
          )
          .toList();

      _log('✅ [ADMIN] ${proveedores.length} proveedores pendientes obtenidos');
      return proveedores;
    } catch (e, stackTrace) {
      _log(
        '❌ [ADMIN] Error obteniendo pendientes',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // BLOQUE 7: 🔧 UTILIDADES
  // ════════════════════════════════════════════════════════════════════════

  /// Validar si el usuario actual puede editar el proveedor
  bool puedeEditar(ProveedorModel proveedor) {
    final userRole = _apiClient.userRole;
    final userId = _apiClient.userId;

    // Admin puede editar cualquiera
    if (userRole == ApiConfig.rolAdministrador) return true;

    // Proveedor solo puede editar el suyo
    if (userRole == ApiConfig.rolProveedor && proveedor.userId == userId) {
      return true;
    }

    return false;
  }

  /// Verificar si está autenticado como proveedor
  bool get esProveedor {
    return _apiClient.userRole == ApiConfig.rolProveedor;
  }

  /// Verificar si es administrador
  bool get esAdministrador {
    return _apiClient.userRole == ApiConfig.rolAdministrador;
  }

  /// Verificar si tiene rol necesario para admin
  bool tienePermisoAdmin() {
    return esAdministrador;
  }
}
