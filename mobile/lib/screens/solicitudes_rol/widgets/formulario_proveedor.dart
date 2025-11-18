// lib/screens/user/perfil/solicitudes_rol/widgets/formulario_proveedor.dart

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../../../../theme/jp_theme.dart';
import '../../../../../services/solicitudes_service.dart';
import '../../../../../services/auth_service.dart';
import '../../../../../models/solicitud_cambio_rol.dart';

/// 📝 FORMULARIO PARA SOLICITUD DE PROVEEDOR
class FormularioProveedor extends StatefulWidget {
  final VoidCallback onSubmitSuccess;
  final VoidCallback onBack;

  const FormularioProveedor({
    super.key,
    required this.onSubmitSuccess,
    required this.onBack,
  });

  @override
  State<FormularioProveedor> createState() => _FormularioProveedorState();
}

class _FormularioProveedorState extends State<FormularioProveedor> {
  // ══════════════════════════════════════════════════════════════════════════════
  // 📋 CONTROLADORES Y ESTADO
  // ══════════════════════════════════════════════════════════════════════════════

  final _formKey = GlobalKey<FormState>();
  final _solicitudesService = SolicitudesService();
  final _authService = AuthService(); // ✅ NUEVO: Para verificar rol del usuario

  // Controladores
  final _rucController = TextEditingController();
  final _nombreComercialController = TextEditingController();
  final _descripcionController = TextEditingController();
  final _motivoController = TextEditingController();

  // Valores seleccionados
  String? _tipoNegocio;
  TimeOfDay? _horarioApertura;
  TimeOfDay? _horarioCierre;

  // Estado
  bool _isLoading = false;

  // ══════════════════════════════════════════════════════════════════════════════
  // 🔄 LIFECYCLE
  // ══════════════════════════════════════════════════════════════════════════════

  @override
  void dispose() {
    _rucController.dispose();
    _nombreComercialController.dispose();
    _descripcionController.dispose();
    _motivoController.dispose();
    super.dispose();
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 🎨 BUILD
  // ══════════════════════════════════════════════════════════════════════════════

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Form(
        key: _formKey,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              _buildHeader(),
              const SizedBox(height: 32),

              // ✅ NUEVO: Card mostrando estado del usuario
              _buildCardEstadoUsuario(),
              const SizedBox(height: 24),

              // RUC
              _buildRUCField(),
              const SizedBox(height: 20),

              // Nombre Comercial
              _buildNombreComercialField(),
              const SizedBox(height: 20),

              // Tipo de Negocio
              _buildTipoNegocioField(),
              const SizedBox(height: 20),

              // Descripción
              _buildDescripcionField(),
              const SizedBox(height: 20),

              // Horarios
              _buildHorariosSection(),
              const SizedBox(height: 20),

              // Motivo
              _buildMotivoField(),
              const SizedBox(height: 32),

              // Botones
              _buildBotones(),
            ],
          ),
        ),
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 🧩 WIDGETS
  // ══════════════════════════════════════════════════════════════════════════════

  Widget _buildHeader() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: JPColors.secondary.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(
                Icons.store,
                color: JPColors.secondary,
                size: 32,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Solicitud de Proveedor', style: JPTextStyles.h2),
                  const SizedBox(height: 4),
                  Text(
                    'Completa toda la información de tu negocio',
                    style: JPTextStyles.caption,
                  ),
                ],
              ),
            ),
          ],
        ),

        const SizedBox(height: 16),

        // Banner informativo
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: JPColors.info.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: JPColors.info.withValues(alpha: 0.3)),
          ),
          child: Row(
            children: [
              const Icon(Icons.info_outline, color: JPColors.info, size: 20),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'Tu solicitud será revisada por nuestro equipo',
                  style: TextStyle(
                    color: JPColors.info.withValues(alpha: 0.9),
                    fontSize: 13,
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ✅ NUEVO: Card mostrando estado del usuario
  Widget _buildCardEstadoUsuario() {
    final user = _authService.user;
    final esProveedor = user?.roles.contains('PROVEEDOR') ?? false;
    final esRepartidor = user?.roles.contains('REPARTIDOR') ?? false;
    final esAnonimo =
        user?.email == 'Anonymous' || user?.email == 'AnonymousUser';

    return Card(
      color: esProveedor ? Colors.green[50] : Colors.blue[50],
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '👤 Tu Estado Actual',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: Colors.grey[700],
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'Email: ${user?.email ?? "No autenticado"}',
              style: const TextStyle(fontSize: 14),
            ),
            const SizedBox(height: 12),
            if (esAnonimo)
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: Colors.red,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Text(
                  '❌ Usuario Anónimo - No puedes enviar solicitudes',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              )
            else if (esProveedor)
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: Colors.green,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Text(
                  '✅ Ya eres PROVEEDOR - No necesitas solicitar de nuevo',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              )
            else if (esRepartidor)
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: Colors.orange,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Text(
                  '📦 Eres REPARTIDOR - Puedes solicitar ser PROVEEDOR también',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              )
            else
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: Colors.blue,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Text(
                  '✏️ Usuario Regular - Puedes solicitar ser PROVEEDOR',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildRUCField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'RUC *',
          style: JPTextStyles.body.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        TextFormField(
          controller: _rucController,
          decoration: InputDecoration(
            hintText: '1234567890001',
            prefixIcon: const Icon(Icons.badge),
            filled: true,
            fillColor: Colors.grey.shade50,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
          ),
          keyboardType: TextInputType.number,
          inputFormatters: [
            FilteringTextInputFormatter.digitsOnly,
            LengthLimitingTextInputFormatter(13),
          ],
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'El RUC es obligatorio';
            }
            if (value.length != 13) {
              return 'El RUC debe tener 13 dígitos';
            }
            return null;
          },
        ),
        const SizedBox(height: 4),
        Text(
          'Debe tener exactamente 13 dígitos',
          style: JPTextStyles.caption.copyWith(color: JPColors.textHint),
        ),
      ],
    );
  }

  Widget _buildNombreComercialField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Nombre Comercial *',
          style: JPTextStyles.body.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        TextFormField(
          controller: _nombreComercialController,
          decoration: InputDecoration(
            hintText: 'Ej: Restaurante El Buen Sabor',
            prefixIcon: const Icon(Icons.business),
            filled: true,
            fillColor: Colors.grey.shade50,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
          ),
          textCapitalization: TextCapitalization.words,
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'El nombre comercial es obligatorio';
            }
            if (value.length < 3) {
              return 'Mínimo 3 caracteres';
            }
            return null;
          },
        ),
      ],
    );
  }

  Widget _buildTipoNegocioField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Tipo de Negocio *',
          style: JPTextStyles.body.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          initialValue: _tipoNegocio,
          decoration: InputDecoration(
            hintText: 'Selecciona el tipo',
            prefixIcon: const Icon(Icons.category),
            filled: true,
            fillColor: Colors.grey.shade50,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
          ),
          items: TipoNegocio.values.map((tipo) {
            return DropdownMenuItem(
              value: tipo.value,
              child: Row(
                children: [
                  Icon(tipo.icon, size: 20, color: JPColors.secondary),
                  const SizedBox(width: 12),
                  Text(tipo.label),
                ],
              ),
            );
          }).toList(),
          onChanged: (value) => setState(() => _tipoNegocio = value),
          validator: (value) {
            if (value == null) {
              return 'Selecciona un tipo de negocio';
            }
            return null;
          },
        ),
      ],
    );
  }

  Widget _buildDescripcionField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Descripción del Negocio *',
          style: JPTextStyles.body.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        TextFormField(
          controller: _descripcionController,
          decoration: InputDecoration(
            hintText: '¿Qué vendes? Describe tus productos o servicios',
            prefixIcon: const Icon(Icons.description),
            filled: true,
            fillColor: Colors.grey.shade50,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
          ),
          maxLines: 4,
          maxLength: 500,
          textCapitalization: TextCapitalization.sentences,
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'La descripción es obligatoria';
            }
            if (value.length < 10) {
              return 'Mínimo 10 caracteres';
            }
            return null;
          },
        ),
      ],
    );
  }

  Widget _buildHorariosSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Horarios (Opcional)',
          style: JPTextStyles.body.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        Text(
          'Puedes configurarlos después',
          style: JPTextStyles.caption.copyWith(color: JPColors.textHint),
        ),
        const SizedBox(height: 12),

        Row(
          children: [
            Expanded(
              child: _buildHorarioButton(
                label: 'Apertura',
                icon: Icons.wb_sunny,
                time: _horarioApertura,
                onTap: () => _seleccionarHorario(true),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildHorarioButton(
                label: 'Cierre',
                icon: Icons.nights_stay,
                time: _horarioCierre,
                onTap: () => _seleccionarHorario(false),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildHorarioButton({
    required String label,
    required IconData icon,
    required TimeOfDay? time,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.grey.shade50,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.grey.shade300),
        ),
        child: Column(
          children: [
            Icon(icon, color: JPColors.secondary, size: 24),
            const SizedBox(height: 8),
            Text(label, style: JPTextStyles.caption),
            const SizedBox(height: 4),
            Text(
              time != null ? time.format(context) : '--:--',
              style: JPTextStyles.body.copyWith(
                fontWeight: FontWeight.bold,
                color: time != null ? JPColors.textPrimary : JPColors.textHint,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMotivoField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Motivo de la Solicitud *',
          style: JPTextStyles.body.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        TextFormField(
          controller: _motivoController,
          decoration: InputDecoration(
            hintText: '¿Por qué quieres ser proveedor en nuestra plataforma?',
            prefixIcon: const Icon(Icons.question_answer),
            filled: true,
            fillColor: Colors.grey.shade50,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
          ),
          maxLines: 4,
          maxLength: 500,
          textCapitalization: TextCapitalization.sentences,
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'El motivo es obligatorio';
            }
            if (value.length < 10) {
              return 'Mínimo 10 caracteres';
            }
            return null;
          },
        ),
      ],
    );
  }

  Widget _buildBotones() {
    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: _isLoading ? null : _enviarSolicitud,
            style: ElevatedButton.styleFrom(
              backgroundColor: JPColors.secondary,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.all(16),
              disabledBackgroundColor: Colors.grey.shade300,
            ),
            child: _isLoading
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  )
                : const Text(
                    'Enviar Solicitud',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
          ),
        ),

        const SizedBox(height: 12),

        TextButton(
          onPressed: _isLoading ? null : widget.onBack,
          child: const Text('Volver atrás'),
        ),
      ],
    );
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 🎬 ACCIONES
  // ══════════════════════════════════════════════════════════════════════════════

  Future<void> _seleccionarHorario(bool esApertura) async {
    final TimeOfDay? picked = await showTimePicker(
      context: context,
      initialTime: esApertura
          ? (_horarioApertura ?? const TimeOfDay(hour: 8, minute: 0))
          : (_horarioCierre ?? const TimeOfDay(hour: 18, minute: 0)),
    );

    if (picked != null) {
      setState(() {
        if (esApertura) {
          _horarioApertura = picked;
        } else {
          _horarioCierre = picked;
        }
      });
    }
  }

  // ✅ CORREGIDO: Validar ANTES de enviar
  Future<void> _enviarSolicitud() async {
    final user = _authService.user;

    // ✅ 1. Validar que no sea anónimo
    if (user == null ||
        user.email == 'Anonymous' ||
        user.email == 'AnonymousUser') {
      _mostrarError(
        '❌ Debes iniciar sesión primero\n\n'
        'No puedes enviar solicitudes como usuario anónimo.',
      );
      return;
    }

    // ✅ 2. Validar que NO sea YA PROVEEDOR
    if (user.roles.contains('PROVEEDOR')) {
      _mostrarError(
        '✅ ¡Ya eres PROVEEDOR!\n\n'
        'No necesitas solicitar de nuevo.\n'
        'Si deseas cambiar a otro rol, selecciona REPARTIDOR.',
      );
      return;
    }

    // ✅ 3. Validar formulario
    if (!_formKey.currentState!.validate()) {
      _mostrarError('❌ Por favor completa todos los campos obligatorios');
      return;
    }

    // ✅ 4. Si todo está bien, enviar
    await _enviarSolicitudAlBackend();
  }

  Future<void> _enviarSolicitudAlBackend() async {
    setState(() => _isLoading = true);

    try {
      await _solicitudesService.crearSolicitudProveedor(
        ruc: _rucController.text.trim(),
        nombreComercial: _nombreComercialController.text.trim(),
        tipoNegocio: _tipoNegocio!,
        descripcionNegocio: _descripcionController.text.trim(),
        motivo: _motivoController.text.trim(),
        horarioApertura: _horarioApertura?.format(context),
        horarioCierre: _horarioCierre?.format(context),
      );

      if (!mounted) return;

      // Mostrar éxito
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Row(
            children: [
              Icon(Icons.check_circle, color: Colors.white),
              SizedBox(width: 12),
              Expanded(
                child: Text(
                  '✅ ¡Solicitud enviada exitosamente!\nEl administrador revisará tu solicitud en breve.',
                  style: TextStyle(color: Colors.white),
                ),
              ),
            ],
          ),
          backgroundColor: Colors.green,
          duration: const Duration(seconds: 3),
        ),
      );

      widget.onSubmitSuccess();
    } catch (e) {
      if (!mounted) return;
      _mostrarError('❌ Error: ${e.toString()}');
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  void _mostrarError(String mensaje) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(mensaje, style: const TextStyle(color: Colors.white)),
        backgroundColor: Colors.red,
        duration: const Duration(seconds: 4),
      ),
    );
  }
}
