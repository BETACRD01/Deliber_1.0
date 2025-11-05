// lib/screens/user/perfil/editar/pantalla_agregar_direccion.dart

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';
import '../../../../theme/jp_theme.dart';
import '../../../../services/usuarios_service.dart';
import '../../../../apis/helpers/api_exception.dart';
import '../../../../models/usuario.dart';

/// 📍 Pantalla con autocompletado GPS
/// ✅ CORREGIDO: NO envía etiqueta - el backend la genera automáticamente
class PantallaAgregarDireccion extends StatefulWidget {
  final DireccionModel? direccion;

  const PantallaAgregarDireccion({super.key, this.direccion});

  @override
  State<PantallaAgregarDireccion> createState() =>
      _PantallaAgregarDireccionState();
}

class _PantallaAgregarDireccionState extends State<PantallaAgregarDireccion> {
  final _formKey = GlobalKey<FormState>();
  final _usuarioService = UsuarioService();

  late final TextEditingController _direccionController;
  late final TextEditingController _referenciaController;
  late final TextEditingController _ciudadController;

  double? _latitud;
  double? _longitud;
  String? _ciudad;
  bool _guardando = false;
  bool _obteniendoUbicacion = false;

  @override
  void initState() {
    super.initState();
    final dir = widget.direccion;
    _direccionController = TextEditingController(text: dir?.direccion);
    _referenciaController = TextEditingController(text: dir?.referencia);
    _ciudadController = TextEditingController(text: dir?.ciudad ?? '');
    _latitud = dir?.latitud;
    _longitud = dir?.longitud;
    _ciudad = dir?.ciudad;
  }

  @override
  void dispose() {
    _direccionController.dispose();
    _referenciaController.dispose();
    _ciudadController.dispose();
    super.dispose();
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📍 OBTENER UBICACIÓN + AUTOCOMPLETAR DIRECCIÓN
  // ══════════════════════════════════════════════════════════════════════════

  Future<void> _obtenerUbicacionYDireccion() async {
    setState(() => _obteniendoUbicacion = true);

    try {
      LocationPermission permiso = await Geolocator.checkPermission();

      if (permiso == LocationPermission.denied) {
        permiso = await Geolocator.requestPermission();
        if (permiso == LocationPermission.denied) {
          throw Exception('Permiso de ubicación denegado');
        }
      }

      if (permiso == LocationPermission.deniedForever) {
        throw Exception(
          'Los permisos están deshabilitados.\n'
          'Actívalos en Configuración > Aplicaciones',
        );
      }

      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: const Duration(seconds: 15),
      );

      if (!_validarCoordenadasEcuador(position.latitude, position.longitude)) {
        throw Exception('La ubicación debe estar en Ecuador');
      }

      debugPrint(
        '✅ Coordenadas obtenidas: Lat=${position.latitude}, Lon=${position.longitude}',
      );

      final placemarks = await placemarkFromCoordinates(
        position.latitude,
        position.longitude,
      );

      if (placemarks.isNotEmpty) {
        final place = placemarks.first;
        final direccionGenerada = _construirDireccion(place);

        setState(() {
          _latitud = position.latitude;
          _longitud = position.longitude;
          _direccionController.text = direccionGenerada;
          _ciudad = place.locality ?? '';
          _ciudadController.text = _ciudad ?? '';
        });

        if (!mounted) return;
        JPSnackbar.success(context, '✓ Ubicación obtenida correctamente.');
      } else {
        throw Exception('No se pudo obtener la dirección');
      }
    } catch (e) {
      if (!mounted) return;
      JPSnackbar.error(context, 'Error: ${e.toString()}');
      debugPrint('❌ Error completo: $e');
    } finally {
      if (mounted) setState(() => _obteniendoUbicacion = false);
    }
  }

  String _construirDireccion(Placemark place) {
    final List<String> partes = [];

    if (place.street != null && place.street!.isNotEmpty) {
      partes.add(place.street!);
    }
    if (place.subLocality != null && place.subLocality!.isNotEmpty) {
      partes.add(place.subLocality!);
    }
    if (place.locality != null && place.locality!.isNotEmpty) {
      partes.add(place.locality!);
    }

    if (partes.isEmpty) {
      return 'Ubicación: ${_latitud!.toStringAsFixed(6)}, ${_longitud!.toStringAsFixed(6)}';
    }

    return partes.join(', ');
  }

  bool _validarCoordenadasEcuador(double lat, double lon) {
    return (lat >= -5.0 && lat <= 2.0) && (lon >= -92.0 && lon <= -75.0);
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 💾 GUARDAR DIRECCIÓN - ✅ COMPLETAMENTE CORREGIDO
  // ══════════════════════════════════════════════════════════════════════════

  Future<void> _guardarDireccion() async {
    if (!_formKey.currentState!.validate()) return;

    if (_latitud == null || _longitud == null) {
      JPSnackbar.error(context, 'Debes obtener tu ubicación GPS');
      return;
    }

    setState(() => _guardando = true);

    try {
      final direccionTexto = _direccionController.text.trim();
      final referencia = _referenciaController.text.trim();
      final ciudad = _ciudadController.text.trim();

      // ✅ CAMBIO CRÍTICO: etiqueta vacía (el backend la genera)
      final nuevaDireccion = DireccionModel(
        id: widget.direccion?.id ?? '',
        tipo: 'casa',
        tipoDisplay: 'Casa',
        etiqueta: '', // ✅ VACÍO - el backend generará automáticamente
        direccion: direccionTexto,
        referencia: referencia.isEmpty ? null : referencia,
        latitud: _latitud!,
        longitud: _longitud!,
        ciudad: ciudad.isEmpty ? null : ciudad,
        esPredeterminada: true,
        activa: true,
        vecesUsada: widget.direccion?.vecesUsada ?? 0,
        ultimoUso: widget.direccion?.ultimoUso,
        direccionCompleta: referencia.isEmpty
            ? direccionTexto
            : '$direccionTexto - $referencia',
        createdAt: widget.direccion?.createdAt ?? DateTime.now(),
        updatedAt: DateTime.now(),
      );

      debugPrint(
        '═══════════════════════════════════════════════════════════════',
      );
      debugPrint('💾 Guardando dirección...');
      debugPrint('   ✅ Etiqueta: VACÍA (backend la generará automáticamente)');
      debugPrint('   Dirección: $direccionTexto');
      debugPrint('   Ciudad: $ciudad');
      debugPrint('   Coordenadas: ($_latitud, $_longitud)');
      debugPrint(
        '═══════════════════════════════════════════════════════════════',
      );

      try {
        // ✅ INTENTO 1: Crear dirección nueva
        final resultado = await _usuarioService.crearDireccion(nuevaDireccion);

        debugPrint('✅ Dirección creada exitosamente');
        debugPrint('   Etiqueta generada por backend: "${resultado.etiqueta}"');
        debugPrint('   Dirección: ${resultado.direccion}');

        // ✅ CRÍTICO: Limpiar caché ANTES de cerrar
        _usuarioService.limpiarCacheDirecciones();
        debugPrint('🧹 Caché limpiado antes de cerrar pantalla');

        if (!mounted) return;

        JPSnackbar.success(context, '✓ Dirección guardada correctamente');

        // ✅ Retornar true para indicar éxito
        Navigator.pop(context, true);
        return;
      } on ApiException catch (e) {
        debugPrint(
          '─────────────────────────────────────────────────────────────',
        );
        debugPrint('⚠️ ApiException capturada:');
        debugPrint('   Status: ${e.statusCode}');
        debugPrint('   Message: ${e.message}');
        debugPrint('   Errors: ${e.errors}');
        debugPrint(
          '─────────────────────────────────────────────────────────────',
        );

        // ✅ DETECTAR ERRORES DE DUPLICADO
        final errorEtiqueta = e.errors['etiqueta']?.toString() ?? '';
        final errorLatitud = e.errors['latitud']?.toString() ?? '';
        final errorGeneral = e.errors['error']?.toString() ?? '';
        final errorDetalles = e.errors['detalles']?.toString() ?? '';

        final esDuplicadoEtiqueta =
            errorEtiqueta.contains('Ya tienes una dirección') ||
            errorGeneral.contains('Ya tienes una dirección') ||
            (errorDetalles.contains('etiqueta') &&
                errorDetalles.contains('Ya tienes'));

        final esDuplicadoUbicacion =
            errorLatitud.contains('muy cercana') ||
            errorGeneral.contains('muy cercana');

        // ══════════════════════════════════════════════════════════════════════
        // 🔄 CASO: DIRECCIÓN DUPLICADA → ACTUALIZAR EN LUGAR DE CREAR
        // ══════════════════════════════════════════════════════════════════════

        if (esDuplicadoEtiqueta || esDuplicadoUbicacion) {
          debugPrint('🔄 Dirección duplicada detectada');
          debugPrint(
            '   Tipo: ${esDuplicadoEtiqueta ? "Etiqueta" : "Ubicación"}',
          );
          debugPrint('   Acción: Buscar dirección existente y actualizarla');

          try {
            // ✅ PASO 1: Obtener todas las direcciones del usuario
            debugPrint('📥 Obteniendo direcciones existentes...');
            final direcciones = await _usuarioService.listarDirecciones(
              forzarRecarga: true,
            );

            debugPrint('   Total direcciones: ${direcciones.length}');

            if (direcciones.isEmpty) {
              throw Exception('No se encontraron direcciones para actualizar');
            }

            // ✅ PASO 2: Buscar la dirección duplicada
            DireccionModel direccionExistente;

            if (esDuplicadoUbicacion) {
              debugPrint('🔍 Buscando por ubicación cercana...');
              direccionExistente = direcciones.firstWhere(
                (d) {
                  final deltaLat = (d.latitud - nuevaDireccion.latitud).abs();
                  final deltaLon = (d.longitud - nuevaDireccion.longitud).abs();
                  final esCercana = deltaLat < 0.0005 && deltaLon < 0.0005;

                  if (esCercana) {
                    debugPrint(
                      '   ✓ Encontrada: ${d.etiqueta} (Δlat: $deltaLat, Δlon: $deltaLon)',
                    );
                  }

                  return esCercana;
                },
                orElse: () => direcciones.first, // Fallback: primera dirección
              );
            } else {
              // Fallback: usar la primera dirección
              direccionExistente = direcciones.first;
            }

            debugPrint('📍 Dirección a actualizar encontrada:');
            debugPrint('   ID: ${direccionExistente.id}');
            debugPrint('   Etiqueta actual: ${direccionExistente.etiqueta}');
            debugPrint('   Dirección actual: ${direccionExistente.direccion}');

            // ✅ PASO 3: Actualizar la dirección existente
            debugPrint('🔄 Actualizando dirección...');

            final dataActualizacion = nuevaDireccion.toCreateJson();
            debugPrint(
              '   Datos a enviar: ${dataActualizacion.keys.join(", ")}',
            );

            await _usuarioService.actualizarDireccion(
              direccionExistente.id,
              dataActualizacion,
            );

            debugPrint('✅ Dirección actualizada exitosamente');

            // ✅ CRÍTICO: Limpiar caché después de actualizar
            _usuarioService.limpiarCacheDirecciones();
            debugPrint('🧹 Caché limpiado después de actualizar');

            if (!mounted) return;

            JPSnackbar.success(
              context,
              '✓ Tu dirección fue actualizada correctamente',
            );

            // ✅ Retornar true para indicar éxito
            Navigator.pop(context, true);
            return;
          } catch (updateError, stackTrace) {
            debugPrint('❌ Error actualizando dirección duplicada');
            debugPrint('   Error: $updateError');
            debugPrint('   Stack: $stackTrace');

            if (!mounted) return;

            JPSnackbar.error(
              context,
              'Error al actualizar: ${updateError.toString()}',
            );
          }
        } else {
          // ══════════════════════════════════════════════════════════════════════
          // ❌ OTRO TIPO DE ERROR (NO ES DUPLICADO)
          // ══════════════════════════════════════════════════════════════════════

          debugPrint('❌ Error de validación (no es duplicado)');

          if (!mounted) return;

          // ✅ Mostrar mensaje específico del backend
          if (e.errors.containsKey('etiqueta')) {
            JPSnackbar.error(context, e.errors['etiqueta'].toString());
          } else if (e.errors.containsKey('latitud')) {
            JPSnackbar.error(context, e.errors['latitud'].toString());
          } else if (e.errors.containsKey('detalles')) {
            final detalles = e.errors['detalles'];
            if (detalles is Map && detalles.containsKey('etiqueta')) {
              final mensajesList = detalles['etiqueta'];
              if (mensajesList is List && mensajesList.isNotEmpty) {
                JPSnackbar.error(context, mensajesList[0].toString());
              } else {
                JPSnackbar.error(context, e.getUserFriendlyMessage());
              }
            } else {
              JPSnackbar.error(context, e.getUserFriendlyMessage());
            }
          } else {
            JPSnackbar.error(context, e.getUserFriendlyMessage());
          }
        }
      }
    } catch (e, stackTrace) {
      debugPrint(
        '═══════════════════════════════════════════════════════════════',
      );
      debugPrint('💥 Error inesperado guardando dirección');
      debugPrint('   Error: $e');
      debugPrint('   Stack: $stackTrace');
      debugPrint(
        '═══════════════════════════════════════════════════════════════',
      );

      if (!mounted) return;
      JPSnackbar.error(context, 'Error al guardar dirección');
    } finally {
      if (mounted) {
        setState(() => _guardando = false);
      }
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🎨 UI
  // ══════════════════════════════════════════════════════════════════════════

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: JPColors.background,
      appBar: AppBar(
        title: const Text('Mi Dirección'),
        backgroundColor: JPColors.primary,
        foregroundColor: Colors.white,
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            _buildInfoCard(),
            const SizedBox(height: 24),
            _buildCampoTexto(
              controller: _direccionController,
              label: 'Dirección',
              icon: Icons.home,
              hint: 'Se completará automáticamente con GPS',
              maxLines: 2,
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Campo obligatorio';
                }
                if (value.trim().length < 10) {
                  return 'Mínimo 10 caracteres';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            _buildCampoTexto(
              controller: _referenciaController,
              label: 'Referencia (opcional)',
              icon: Icons.place,
              hint: 'Ej: Casa azul, portón café',
              maxLines: 2,
            ),
            const SizedBox(height: 16),
            _buildCampoTexto(
              controller: _ciudadController,
              label: 'Ciudad',
              icon: Icons.location_city,
              hint: 'Se autocompletará según GPS',
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Campo obligatorio';
                }
                return null;
              },
            ),
            const SizedBox(height: 24),
            _buildBotonGPS(),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: _guardando ? null : _guardarDireccion,
              style: ElevatedButton.styleFrom(
                backgroundColor: JPColors.primary,
                minimumSize: const Size(double.infinity, 52),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: _guardando
                  ? const SizedBox(
                      width: 22,
                      height: 22,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        color: Colors.white,
                      ),
                    )
                  : const Text(
                      'Guardar',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🧩 COMPONENTES VISUALES
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildInfoCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: JPColors.info.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: JPColors.info, width: 1.5),
      ),
      child: Row(
        children: [
          Icon(Icons.lightbulb_outline, color: JPColors.info, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              '📍 El GPS completará tu dirección y ciudad automáticamente.\n'
              'Puedes editarla si no es correcta.',
              style: TextStyle(
                color: JPColors.info.withValues(alpha: 0.9),
                fontSize: 13,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBotonGPS() {
    final tieneUbicacion = _latitud != null && _longitud != null;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: tieneUbicacion ? JPColors.success : Colors.grey.shade300,
          width: 2,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: (tieneUbicacion ? JPColors.success : JPColors.primary)
                      .withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(
                  tieneUbicacion ? Icons.check_circle : Icons.gps_not_fixed,
                  color: tieneUbicacion ? JPColors.success : JPColors.primary,
                  size: 28,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Ubicación GPS',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      tieneUbicacion
                          ? '✓ Dirección y ciudad obtenidas'
                          : 'Presiona para obtener ubicación',
                      style: TextStyle(
                        fontSize: 13,
                        color: tieneUbicacion
                            ? JPColors.success
                            : JPColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          ElevatedButton.icon(
            onPressed: _obteniendoUbicacion
                ? null
                : _obtenerUbicacionYDireccion,
            icon: _obteniendoUbicacion
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  )
                : Icon(
                    tieneUbicacion ? Icons.refresh : Icons.gps_fixed,
                    size: 20,
                  ),
            label: Text(
              _obteniendoUbicacion
                  ? 'Obteniendo dirección...'
                  : tieneUbicacion
                  ? 'Actualizar ubicación'
                  : 'Obtener mi dirección',
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: JPColors.primary,
              minimumSize: const Size(double.infinity, 44),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCampoTexto({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    required String hint,
    int maxLines = 1,
    String? Function(String?)? validator,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, color: JPColors.primary, size: 20),
            const SizedBox(width: 8),
            Text(
              label,
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
            ),
          ],
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: controller,
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: TextStyle(color: Colors.grey.shade400, fontSize: 14),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
            focusedBorder: const OutlineInputBorder(
              borderRadius: BorderRadius.all(Radius.circular(12)),
              borderSide: BorderSide(color: JPColors.primary, width: 2),
            ),
            filled: true,
            fillColor: Colors.white,
            contentPadding: const EdgeInsets.all(16),
          ),
          maxLines: maxLines,
          validator: validator,
        ),
      ],
    );
  }
}
