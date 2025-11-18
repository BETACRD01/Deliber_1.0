// lib/screens/supplier/screens/perfil_proveedor_editable.dart

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import 'dart:io';
import '../../../config/api_config.dart';
import '../controllers/supplier_controller.dart';

/// Panel de perfil del proveedor con modo edición moderno
/// ✅ COMPLETO: Edición de email, nombre, teléfono, RUC y tipo de proveedor
class PerfilProveedorEditable extends StatefulWidget {
  const PerfilProveedorEditable({super.key});

  @override
  State<PerfilProveedorEditable> createState() =>
      _PerfilProveedorEditableState();
}

class _PerfilProveedorEditableState extends State<PerfilProveedorEditable>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;

  bool _editando = false;

  // Datos del Negocio
  late TextEditingController _nombreController;
  late TextEditingController _descripcionController;
  late TextEditingController _direccionController;
  late TextEditingController _ciudadController;
  late TextEditingController _horarioAperturaController;
  late TextEditingController _horarioCierreController;
  late TextEditingController _rucController;

  // Datos de Contacto
  late TextEditingController _emailController;
  late TextEditingController _nombreCompletoController;
  late TextEditingController _telefonoController;

  String? _tipoProveedorSeleccionado;
  File? _logoSeleccionado;
  bool _subiendoLogo = false;
  bool _guardando = false;
  String? _mensajeError;

  static const Color _azul = Color(0xFF2196F3);
  static const Color _azulOscuro = Color(0xFF1976D2);
  static const Color _verde = Color(0xFF4CAF50);
  static const Color _naranja = Color(0xFFFF9800);
  static const Color _rojo = Color(0xFFF44336);

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
    _inicializarFormulario();
  }

  @override
  void dispose() {
    _animationController.dispose();
    _nombreController.dispose();
    _descripcionController.dispose();
    _direccionController.dispose();
    _ciudadController.dispose();
    _horarioAperturaController.dispose();
    _horarioCierreController.dispose();
    _rucController.dispose();
    _emailController.dispose();
    _nombreCompletoController.dispose();
    _telefonoController.dispose();
    super.dispose();
  }

  void _inicializarFormulario() {
    final controller = context.read<SupplierController>();

    _nombreController = TextEditingController(text: controller.nombreNegocio);
    _descripcionController = TextEditingController(
      text: controller.proveedor?.descripcion ?? '',
    );
    _direccionController = TextEditingController(text: controller.direccion);
    _ciudadController = TextEditingController(text: controller.ciudad);
    _horarioAperturaController = TextEditingController(
      text: controller.horarioApertura ?? '',
    );
    _horarioCierreController = TextEditingController(
      text: controller.horarioCierre ?? '',
    );
    _rucController = TextEditingController(text: controller.ruc);
    _tipoProveedorSeleccionado = controller.proveedor?.tipoProveedor;
    _emailController = TextEditingController(text: controller.email);
    _nombreCompletoController = TextEditingController(
      text: controller.nombreCompleto,
    );
    _telefonoController = TextEditingController(text: controller.telefono);
  }

  Future<void> _seleccionarLogo() async {
    final imagePicker = ImagePicker();
    try {
      final pickedFile = await imagePicker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 85,
      );
      if (pickedFile != null) {
        setState(() => _logoSeleccionado = File(pickedFile.path));
      }
    } catch (e) {
      _mostrarError('Error al seleccionar imagen: $e');
    }
  }

  Future<void> _seleccionarHora(
    TextEditingController controller, {
    required String titulo,
  }) async {
    final hora = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.now(),
    );
    if (hora != null) {
      final horaFormato =
          '${hora.hour.toString().padLeft(2, '0')}:${hora.minute.toString().padLeft(2, '0')}:00';
      controller.text = horaFormato;
    }
  }

  bool _validarFormulario() {
    if (_nombreController.text.trim().isEmpty) {
      _mostrarError('El nombre del negocio es requerido');
      return false;
    }

    if (_rucController.text.trim().isEmpty) {
      _mostrarError('El RUC es requerido');
      return false;
    }

    if (_rucController.text.trim().length < 10) {
      _mostrarError('El RUC debe tener al menos 10 caracteres');
      return false;
    }

    if (_tipoProveedorSeleccionado == null ||
        _tipoProveedorSeleccionado!.isEmpty) {
      _mostrarError('Debes seleccionar un tipo de proveedor');
      return false;
    }

    if (_direccionController.text.trim().isEmpty) {
      _mostrarError('La dirección es requerida');
      return false;
    }

    if (_ciudadController.text.trim().isEmpty) {
      _mostrarError('La ciudad es requerida');
      return false;
    }

    if (_emailController.text.trim().isEmpty) {
      _mostrarError('El email es requerido');
      return false;
    }

    if (!_esEmailValido(_emailController.text.trim())) {
      _mostrarError('El email no es válido');
      return false;
    }

    if (_nombreCompletoController.text.trim().isEmpty) {
      _mostrarError('El nombre completo es requerido');
      return false;
    }

    if (_telefonoController.text.trim().isEmpty) {
      _mostrarError('El teléfono es requerido');
      return false;
    }

    if (_horarioAperturaController.text.isNotEmpty ||
        _horarioCierreController.text.isNotEmpty) {
      if (_horarioAperturaController.text.isEmpty ||
          _horarioCierreController.text.isEmpty) {
        _mostrarError('Completa ambos horarios o déjalos vacíos');
        return false;
      }

      try {
        final apertura = _parseHora(_horarioAperturaController.text);
        final cierre = _parseHora(_horarioCierreController.text);

        if (cierre.compareTo(apertura) <= 0) {
          _mostrarError('La hora de cierre debe ser posterior a la apertura');
          return false;
        }
      } catch (e) {
        _mostrarError('Formato de hora inválido (usa HH:MM:SS)');
        return false;
      }
    }

    return true;
  }

  bool _esEmailValido(String email) {
    final regex = RegExp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$');
    return regex.hasMatch(email);
  }

  TimeOfDay _parseHora(String hora) {
    final partes = hora.split(':');
    return TimeOfDay(hour: int.parse(partes[0]), minute: int.parse(partes[1]));
  }

  Future<void> _guardarCambios() async {
    if (!_validarFormulario()) return;

    setState(() {
      _guardando = true;
      _mensajeError = null;
    });

    try {
      final controller = context.read<SupplierController>();

      // Preparar datos del negocio
      final datosPerfil = <String, dynamic>{
        'nombre': _nombreController.text.trim(),
        'ruc': _rucController.text.trim(),
        'tipo_proveedor': _tipoProveedorSeleccionado,
        'descripcion': _descripcionController.text.trim(),
        'direccion': _direccionController.text.trim(),
        'ciudad': _ciudadController.text.trim(),
        if (_horarioAperturaController.text.isNotEmpty)
          'horario_apertura': _horarioAperturaController.text.trim(),
        if (_horarioCierreController.text.isNotEmpty)
          'horario_cierre': _horarioCierreController.text.trim(),
      };

      debugPrint('📊 Guardando perfil: $datosPerfil');
      final successPerfil = await controller.actualizarPerfil(datosPerfil);

      if (!successPerfil) {
        setState(() {
          _mensajeError = controller.error ?? 'Error al guardar';
        });
        setState(() => _guardando = false);
        return;
      }

      // Preparar datos de contacto
      final emailNuevo = _emailController.text.trim();
      final nombreCompletoNuevo = _nombreCompletoController.text.trim();
      final telefonoNuevo = _telefonoController.text.trim();

      final partes = nombreCompletoNuevo.split(' ');
      final firstName = partes.isNotEmpty ? partes[0] : '';
      final lastName = partes.length > 1 ? partes.sublist(1).join(' ') : '';

      debugPrint(
        '👤 Guardando contacto: email=$emailNuevo, nombre=$firstName, apellido=$lastName, tel=$telefonoNuevo',
      );

      final successContacto = await controller.actualizarDatosContacto(
        email: emailNuevo,
        firstName: firstName,
        lastName: lastName,
        telefono: telefonoNuevo,
      );

      if (!successContacto) {
        setState(() {
          _mensajeError = controller.error ?? 'Error al guardar contacto';
        });
        setState(() => _guardando = false);
        return;
      }

      // Subir logo si se seleccionó
      if (_logoSeleccionado != null) {
        setState(() => _subiendoLogo = true);
        final logoSuccess = await controller.subirLogo(_logoSeleccionado!);

        if (!logoSuccess) {
          setState(() {
            _mensajeError = controller.error ?? 'Error al subir logo';
          });
          setState(() {
            _guardando = false;
            _subiendoLogo = false;
          });
          return;
        }
      }

      setState(() {
        _editando = false;
        _logoSeleccionado = null;
      });

      if (mounted) {
        _mostrarExito('✅ Cambios guardados correctamente');
      }
    } catch (e) {
      setState(() => _mensajeError = 'Error: $e');
    } finally {
      setState(() {
        _guardando = false;
        _subiendoLogo = false;
      });
    }
  }

  void _toggleEdicion() {
    if (_editando) {
      setState(() {
        _editando = false;
        _logoSeleccionado = null;
        _mensajeError = null;
        _inicializarFormulario();
      });
      _animationController.reverse();
    } else {
      setState(() => _editando = true);
      _animationController.forward();
    }
  }

  void _mostrarError(String mensaje) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.error_outline, color: Colors.white),
            const SizedBox(width: 12),
            Expanded(child: Text(mensaje)),
          ],
        ),
        backgroundColor: _rojo,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }

  void _mostrarExito(String mensaje) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.check_circle, color: Colors.white),
            const SizedBox(width: 12),
            Expanded(child: Text(mensaje)),
          ],
        ),
        backgroundColor: _verde,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: _buildAppBar(),
      body: Consumer<SupplierController>(
        builder: (context, controller, child) {
          if (controller.loading) {
            return _buildCargando();
          }

          return SingleChildScrollView(
            child: Column(
              children: [
                _buildHeader(controller),
                const SizedBox(height: 24),
                _buildFormulario(controller),
                const SizedBox(height: 24),
                if (_editando) _buildBotones(),
                const SizedBox(height: 24),
              ],
            ),
          );
        },
      ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      title: const Text(
        'Mi Perfil',
        style: TextStyle(fontWeight: FontWeight.bold),
      ),
      elevation: 0,
      flexibleSpace: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [_azul, _azulOscuro],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
      ),
      actions: [
        Padding(
          padding: const EdgeInsets.only(right: 8),
          child: Center(
            child: FilledButton.icon(
              onPressed: _editando ? null : _toggleEdicion,
              icon: Icon(_editando ? Icons.close : Icons.edit),
              label: Text(_editando ? 'Cancelar' : 'Editar'),
              style: FilledButton.styleFrom(
                backgroundColor: _editando ? _rojo : _azul,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildHeader(SupplierController controller) {
    final logoUrl = _logoSeleccionado != null
        ? FileImage(_logoSeleccionado!)
        : (controller.logo != null
              ? NetworkImage(controller.logo!) as ImageProvider
              : null);

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [_azul.withValues(alpha: 0.05), Colors.white],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: Column(
        children: [
          GestureDetector(
            onTap: _editando ? _seleccionarLogo : null,
            child: Stack(
              clipBehavior: Clip.none,
              children: [
                Container(
                  width: 120,
                  height: 120,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.grey[200],
                    border: Border.all(color: _azul, width: 3),
                    image: logoUrl != null
                        ? DecorationImage(image: logoUrl, fit: BoxFit.cover)
                        : null,
                  ),
                  child: logoUrl == null
                      ? Icon(Icons.store, size: 60, color: Colors.grey[400])
                      : null,
                ),
                if (_editando)
                  Positioned(
                    bottom: -8,
                    right: -8,
                    child: Container(
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: _azul,
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.2),
                            blurRadius: 8,
                          ),
                        ],
                      ),
                      padding: const EdgeInsets.all(8),
                      child: Icon(
                        _subiendoLogo
                            ? Icons.hourglass_bottom
                            : Icons.camera_alt,
                        color: Colors.white,
                        size: 20,
                      ),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          if (!_editando)
            Text(
              _nombreController.text,
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.black87,
              ),
              textAlign: TextAlign.center,
            )
          else
            TextField(
              controller: _nombreController,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              decoration: InputDecoration(
                hintText: 'Nombre del negocio',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                filled: true,
                fillColor: Colors.grey[50],
              ),
            ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: controller.verificado ? _verde : _naranja,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  controller.verificado ? Icons.check_circle : Icons.warning,
                  color: Colors.white,
                  size: 18,
                ),
                const SizedBox(width: 8),
                Text(
                  controller.verificado ? 'Verificado' : 'Sin Verificar',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFormulario(SupplierController controller) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: [
          // 👤 CONTACTO
          _buildSeccion(
            titulo: '📞 Datos de Contacto',
            children: [
              _buildCampo(
                etiqueta: 'Email',
                icono: Icons.email,
                editable: _editando,
                controlador: _emailController,
              ),
              const SizedBox(height: 12),
              _buildCampo(
                etiqueta: 'Nombre Completo',
                icono: Icons.person,
                editable: _editando,
                controlador: _nombreCompletoController,
              ),
              const SizedBox(height: 12),
              _buildCampo(
                etiqueta: 'Teléfono',
                icono: Icons.phone,
                editable: _editando,
                controlador: _telefonoController,
              ),
            ],
          ),
          const SizedBox(height: 20),

          // 🏪 NEGOCIO
          _buildSeccion(
            titulo: '🏪 Información del Negocio',
            children: [
              _buildCampo(
                etiqueta: 'Nombre del negocio',
                icono: Icons.store,
                editable: _editando,
                controlador: _nombreController,
              ),
              const SizedBox(height: 12),
              _buildCampo(
                etiqueta: 'RUC',
                icono: Icons.badge,
                editable: _editando,
                controlador: _rucController,
              ),
              const SizedBox(height: 12),
              _buildDropdownTipo(),
              const SizedBox(height: 12),
              _buildCampo(
                etiqueta: 'Descripción',
                icono: Icons.description,
                editable: _editando,
                controlador: _descripcionController,
                maxLineas: 3,
              ),
            ],
          ),
          const SizedBox(height: 20),

          // 📍 UBICACIÓN
          _buildSeccion(
            titulo: '📍 Ubicación',
            children: [
              _buildCampo(
                etiqueta: 'Dirección',
                icono: Icons.location_on,
                editable: _editando,
                controlador: _direccionController,
              ),
              const SizedBox(height: 12),
              _buildCampo(
                etiqueta: 'Ciudad',
                icono: Icons.location_city,
                editable: _editando,
                controlador: _ciudadController,
              ),
            ],
          ),
          const SizedBox(height: 20),

          // ⏰ HORARIOS
          _buildSeccion(
            titulo: '⏰ Horarios',
            children: [
              _buildCampoHora(
                etiqueta: 'Apertura',
                controlador: _horarioAperturaController,
                editable: _editando,
              ),
              const SizedBox(height: 12),
              _buildCampoHora(
                etiqueta: 'Cierre',
                controlador: _horarioCierreController,
                editable: _editando,
              ),
            ],
          ),

          if (_mensajeError != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: _rojo.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: _rojo),
              ),
              child: Row(
                children: [
                  Icon(Icons.error_outline, color: _rojo),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(_mensajeError!, style: TextStyle(color: _rojo)),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildDropdownTipo() {
    if (!_editando) {
      return _buildInfoRow(
        label: 'Tipo de Proveedor',
        value: _getTipoProveedorDisplay(_tipoProveedorSeleccionado),
        icono: Icons.category,
      );
    }

    return DropdownButtonFormField<String>(
      initialValue: _tipoProveedorSeleccionado,
      decoration: InputDecoration(
        labelText: 'Tipo de Proveedor',
        prefixIcon: const Icon(Icons.category, color: _azul),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
        filled: true,
        fillColor: Colors.grey[50],
      ),
      items: ApiConfig.tiposProveedor.map((tipo) {
        return DropdownMenuItem(
          value: tipo,
          child: Text(_getTipoProveedorDisplay(tipo)),
        );
      }).toList(),
      onChanged: (valor) {
        setState(() => _tipoProveedorSeleccionado = valor);
      },
    );
  }

  String _getTipoProveedorDisplay(String? tipo) {
    if (tipo == null) return 'Selecciona tipo';
    switch (tipo) {
      case 'restaurante':
        return '🍽️ Restaurante';
      case 'farmacia':
        return '💊 Farmacia';
      case 'supermercado':
        return '🛒 Supermercado';
      case 'tienda':
        return '🏪 Tienda';
      case 'otro':
        return '📦 Otro';
      default:
        return tipo;
    }
  }

  Widget _buildSeccion({
    required String titulo,
    required List<Widget> children,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          titulo.toUpperCase(),
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.bold,
            color: Colors.grey[700],
            letterSpacing: 1.2,
          ),
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.05),
                blurRadius: 8,
              ),
            ],
          ),
          child: Column(children: children),
        ),
      ],
    );
  }

  Widget _buildCampo({
    required String etiqueta,
    required IconData icono,
    required bool editable,
    required TextEditingController controlador,
    int maxLineas = 1,
  }) {
    if (!editable) {
      return _buildInfoRow(
        label: etiqueta,
        value: controlador.text.isEmpty ? '---' : controlador.text,
        icono: icono,
      );
    }

    return TextField(
      controller: controlador,
      maxLines: maxLineas,
      decoration: InputDecoration(
        labelText: etiqueta,
        prefixIcon: Icon(icono, color: _azul),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
        filled: true,
        fillColor: Colors.grey[50],
      ),
    );
  }

  Widget _buildCampoHora({
    required String etiqueta,
    required TextEditingController controlador,
    required bool editable,
  }) {
    if (!editable) {
      return _buildInfoRow(
        label: etiqueta,
        value: controlador.text.isEmpty ? '---' : controlador.text,
        icono: Icons.access_time,
      );
    }

    return GestureDetector(
      onTap: () => _seleccionarHora(controlador, titulo: etiqueta),
      child: TextField(
        controller: controlador,
        enabled: false,
        decoration: InputDecoration(
          labelText: etiqueta,
          prefixIcon: const Icon(Icons.access_time, color: _azul),
          suffixIcon: const Icon(Icons.arrow_drop_down, color: _azul),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
          filled: true,
          fillColor: Colors.grey[50],
        ),
      ),
    );
  }

  Widget _buildInfoRow({
    required String label,
    required String value,
    required IconData icono,
  }) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: _azul.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icono, color: _azul, size: 20),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: TextStyle(fontSize: 12, color: Colors.grey[600]),
              ),
              const SizedBox(height: 4),
              Text(
                value,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildBotones() {
    return FadeTransition(
      opacity: _fadeAnimation,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: _guardando ? null : _toggleEdicion,
                style: OutlinedButton.styleFrom(
                  foregroundColor: _rojo,
                  side: const BorderSide(color: _rojo, width: 2),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text(
                  'Cancelar',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: FilledButton(
                onPressed: _guardando ? null : _guardarCambios,
                style: FilledButton.styleFrom(
                  backgroundColor: _verde,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: _guardando
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation(Colors.white),
                        ),
                      )
                    : const Text(
                        'Guardar',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCargando() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(color: _azul, strokeWidth: 3),
          const SizedBox(height: 16),
          Text('Cargando perfil...', style: TextStyle(color: Colors.grey[600])),
        ],
      ),
    );
  }
}
