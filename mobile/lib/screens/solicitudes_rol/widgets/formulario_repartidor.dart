// lib/screens/user/perfil/solicitudes_rol/widgets/formulario_repartidor.dart

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../../../../theme/jp_theme.dart';
import '../../../../../services/solicitudes_service.dart';
import '../../../../../services/auth_service.dart';
import '../../../../../models/solicitud_cambio_rol.dart';

/// 📝 FORMULARIO PARA SOLICITUD DE REPARTIDOR
class FormularioRepartidor extends StatefulWidget {
  final VoidCallback onSubmitSuccess;
  final VoidCallback onBack;

  const FormularioRepartidor({
    super.key,
    required this.onSubmitSuccess,
    required this.onBack,
  });

  @override
  State<FormularioRepartidor> createState() => _FormularioRepartidorState();
}

class _FormularioRepartidorState extends State<FormularioRepartidor> {
  // ══════════════════════════════════════════════════════════════════════════════
  // 📋 CONTROLADORES Y ESTADO
  // ══════════════════════════════════════════════════════════════════════════════

  final _formKey = GlobalKey<FormState>();
  final _solicitudesService = SolicitudesService();
  final _authService = AuthService(); // ✅ NUEVO: Para verificar rol del usuario

  // Controladores
  final _cedulaController = TextEditingController();
  final _zonaCoberturaController = TextEditingController();
  final _motivoController = TextEditingController();

  // Valores seleccionados
  String? _tipoVehiculo;

  // Estado
  bool _isLoading = false;

  // ══════════════════════════════════════════════════════════════════════════════
  // 🔄 LIFECYCLE
  // ══════════════════════════════════════════════════════════════════════════════

  @override
  void dispose() {
    _cedulaController.dispose();
    _zonaCoberturaController.dispose();
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

              // Cédula
              _buildCedulaField(),
              const SizedBox(height: 20),

              // Tipo de Vehículo
              _buildTipoVehiculoField(),
              const SizedBox(height: 20),

              // Zona de Cobertura
              _buildZonaCoberturaField(),
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
                color: JPColors.info.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(
                Icons.delivery_dining,
                color: JPColors.info,
                size: 32,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Solicitud de Repartidor', style: JPTextStyles.h2),
                  const SizedBox(height: 4),
                  Text(
                    'Completa tu información personal',
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
            color: JPColors.success.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: JPColors.success.withValues(alpha: 0.3)),
          ),
          child: Row(
            children: [
              const Icon(
                Icons.check_circle_outline,
                color: JPColors.success,
                size: 20,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'Gana dinero extra con horarios flexibles',
                  style: TextStyle(
                    color: JPColors.success.withValues(alpha: 0.9),
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
      color: esRepartidor ? Colors.green[50] : Colors.blue[50],
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
            else if (esRepartidor)
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
                  '✅ Ya eres REPARTIDOR - No necesitas solicitar de nuevo',
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
                  color: Colors.orange,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Text(
                  '🛍️ Eres PROVEEDOR - Puedes solicitar ser REPARTIDOR también',
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
                  '✏️ Usuario Regular - Puedes solicitar ser REPARTIDOR',
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

  Widget _buildCedulaField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Cédula de Identidad *',
          style: JPTextStyles.body.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        TextFormField(
          controller: _cedulaController,
          decoration: InputDecoration(
            hintText: '1234567890',
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
            LengthLimitingTextInputFormatter(20),
          ],
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'La cédula es obligatoria';
            }
            if (value.length < 10) {
              return 'Mínimo 10 dígitos';
            }
            return null;
          },
        ),
        const SizedBox(height: 4),
        Text(
          'Tu documento de identificación',
          style: JPTextStyles.caption.copyWith(color: JPColors.textHint),
        ),
      ],
    );
  }

  Widget _buildTipoVehiculoField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Tipo de Vehículo *',
          style: JPTextStyles.body.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          initialValue: _tipoVehiculo,
          decoration: InputDecoration(
            hintText: 'Selecciona tu vehículo',
            prefixIcon: const Icon(Icons.two_wheeler),
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
          items: TipoVehiculo.values.map((tipo) {
            return DropdownMenuItem(
              value: tipo.value,
              child: Row(
                children: [
                  Icon(tipo.icon, size: 20, color: JPColors.info),
                  const SizedBox(width: 12),
                  Text(tipo.label),
                ],
              ),
            );
          }).toList(),
          onChanged: (value) => setState(() => _tipoVehiculo = value),
          validator: (value) {
            if (value == null) {
              return 'Selecciona un tipo de vehículo';
            }
            return null;
          },
        ),
      ],
    );
  }

  Widget _buildZonaCoberturaField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Zona de Cobertura *',
          style: JPTextStyles.body.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        TextFormField(
          controller: _zonaCoberturaController,
          decoration: InputDecoration(
            hintText: 'Ej: Centro, Norte, Sur de la ciudad',
            prefixIcon: const Icon(Icons.location_on),
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
              return 'La zona de cobertura es obligatoria';
            }
            if (value.length < 3) {
              return 'Mínimo 3 caracteres';
            }
            return null;
          },
        ),
        const SizedBox(height: 4),
        Text(
          '¿En qué zonas puedes hacer entregas?',
          style: JPTextStyles.caption.copyWith(color: JPColors.textHint),
        ),
      ],
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
            hintText: '¿Por qué quieres ser repartidor?',
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
              backgroundColor: JPColors.info,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              elevation: 0,
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
                : Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.send, size: 20),
                      const SizedBox(width: 8),
                      Text(
                        'Enviar Solicitud',
                        style: JPTextStyles.body.copyWith(
                          fontWeight: FontWeight.w600,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton(
            onPressed: _isLoading ? null : widget.onBack,
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              side: BorderSide(color: Colors.grey.shade300),
            ),
            child: Text(
              'Cancelar',
              style: JPTextStyles.body.copyWith(
                color: JPColors.textSecondary,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ),
      ],
    );
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 🎬 ACCIONES
  // ══════════════════════════════════════════════════════════════════════════════

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

    // ✅ 2. Validar que NO sea YA REPARTIDOR
    if (user.roles.contains('REPARTIDOR')) {
      _mostrarError(
        '✅ ¡Ya eres REPARTIDOR!\n\n'
        'No necesitas solicitar de nuevo.\n'
        'Si deseas cambiar a otro rol, selecciona PROVEEDOR.',
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
      await _solicitudesService.crearSolicitudRepartidor(
        cedulaIdentidad: _cedulaController.text.trim(),
        tipoVehiculo: _tipoVehiculo!,
        zonaCobertura: _zonaCoberturaController.text.trim(),
        motivo: _motivoController.text.trim(),
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
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
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
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    );
  }
}
