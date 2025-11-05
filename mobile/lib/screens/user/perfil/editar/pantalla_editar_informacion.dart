// lib/screens/user/perfil/editar/pantalla_editar_informacion.dart

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../../../theme/jp_theme.dart';
import '../../../../services/usuarios_service.dart';
import '../../../../apis/helpers/api_exception.dart';
import '../../../../models/usuario.dart';

/// ✏️ Pantalla para editar información personal
class PantallaEditarInformacion extends StatefulWidget {
  final PerfilModel perfil;

  const PantallaEditarInformacion({super.key, required this.perfil});

  @override
  State<PantallaEditarInformacion> createState() =>
      _PantallaEditarInformacionState();
}

class _PantallaEditarInformacionState extends State<PantallaEditarInformacion> {
  final _formKey = GlobalKey<FormState>();
  final _usuarioService = UsuarioService();

  late final TextEditingController _telefonoController;
  DateTime? _fechaNacimiento;
  bool _guardando = false;

  @override
  void initState() {
    super.initState();
    _telefonoController = TextEditingController(text: widget.perfil.telefono);
    _fechaNacimiento = widget.perfil.fechaNacimiento;
  }

  @override
  void dispose() {
    _telefonoController.dispose();
    super.dispose();
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📅 SELECCIONAR FECHA
  // ══════════════════════════════════════════════════════════════════════════

  Future<void> _seleccionarFecha() async {
    final fechaActual = DateTime.now();
    final fechaMinima = DateTime(fechaActual.year - 100);
    final fechaMaxima = DateTime(fechaActual.year - 13); // Mínimo 13 años

    final fecha = await showDatePicker(
      context: context,
      initialDate: _fechaNacimiento ?? fechaMaxima,
      firstDate: fechaMinima,
      lastDate: fechaMaxima,
      locale: const Locale('es', 'ES'),
      helpText: 'Selecciona tu fecha de nacimiento',
      cancelText: 'Cancelar',
      confirmText: 'Aceptar',
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.light(
              primary: JPColors.primary,
              onPrimary: Colors.white,
              surface: Colors.white,
              onSurface: JPColors.textPrimary,
            ),
          ),
          child: child!,
        );
      },
    );

    if (fecha != null) {
      setState(() => _fechaNacimiento = fecha);
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 💾 GUARDAR CAMBIOS (✅ CORREGIDO)
  // ══════════════════════════════════════════════════════════════════════════

  Future<void> _guardarCambios() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _guardando = true);

    try {
      final datos = <String, dynamic>{};

      // ✅ TELÉFONO - CORREGIDO: Usar 'telefono' (no 'celular')
      final telefono = _telefonoController.text.trim();
      if (telefono != widget.perfil.telefono) {
        // Validar formato ecuatoriano (09 + 8 dígitos)
        if (telefono.isNotEmpty && !RegExp(r'^09\d{8}$').hasMatch(telefono)) {
          if (!mounted) return;
          JPSnackbar.error(
            context,
            'El celular debe comenzar con 09 y tener 10 dígitos',
          );
          setState(() => _guardando = false);
          return;
        }

        // ✅ CRÍTICO: Backend espera 'telefono', NO 'celular'
        datos['telefono'] = telefono.isEmpty ? null : telefono;
      }

      // ✅ FECHA DE NACIMIENTO
      if (_fechaNacimiento != widget.perfil.fechaNacimiento) {
        if (_fechaNacimiento != null) {
          // Formato correcto: YYYY-MM-DD (sin hora)
          final fecha =
              '${_fechaNacimiento!.year.toString().padLeft(4, '0')}-'
              '${_fechaNacimiento!.month.toString().padLeft(2, '0')}-'
              '${_fechaNacimiento!.day.toString().padLeft(2, '0')}';
          datos['fecha_nacimiento'] = fecha;
        } else {
          datos['fecha_nacimiento'] = null;
        }
      }

      // Verificar si hay cambios
      if (datos.isEmpty) {
        if (!mounted) return;
        JPSnackbar.info(context, 'No hay cambios para guardar');
        setState(() => _guardando = false);
        return;
      }

      // 🔍 DEBUG: Ver qué se está enviando
      debugPrint('📤 Datos a enviar al backend: $datos');

      // Enviar al backend
      await _usuarioService.actualizarPerfil(datos);

      if (!mounted) return;
      JPSnackbar.success(context, 'Información actualizada');

      // Retornar true para indicar que hubo cambios
      Navigator.pop(context, true);
    } on ApiException catch (e) {
      if (!mounted) return;
      debugPrint('❌ Error API: ${e.getUserFriendlyMessage()}');
      JPSnackbar.error(context, e.getUserFriendlyMessage());
    } catch (e, stackTrace) {
      if (!mounted) return;
      debugPrint('❌ Error inesperado: $e');
      debugPrint('Stack trace: $stackTrace');
      JPSnackbar.error(context, 'Error al actualizar información');
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🎨 BUILD
  // ══════════════════════════════════════════════════════════════════════════

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: JPColors.background,
      appBar: AppBar(
        title: const Text('Editar Información'),
        backgroundColor: JPColors.primary,
        foregroundColor: Colors.white,
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            // Info del usuario
            _buildInfoCard(),

            const SizedBox(height: 24),

            // Campo de teléfono
            _buildTelefonoField(),

            const SizedBox(height: 24),

            // Campo de fecha de nacimiento
            _buildFechaField(),

            const SizedBox(height: 32),

            // Botón guardar
            ElevatedButton(
              onPressed: _guardando ? null : _guardarCambios,
              style: ElevatedButton.styleFrom(
                backgroundColor: JPColors.primary,
                minimumSize: const Size(double.infinity, 50),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: _guardando
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Text(
                      'Guardar Cambios',
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
  // 🧩 WIDGETS
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildInfoCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: JPColors.primaryGradient,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 30,
            backgroundColor: Colors.white.withValues(alpha: 0.2),
            child: Text(
              widget.perfil.usuarioNombre[0].toUpperCase(),
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.perfil.usuarioNombre,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  widget.perfil.usuarioEmail,
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.white.withValues(alpha: 0.9),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTelefonoField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.phone, color: JPColors.primary, size: 20),
            const SizedBox(width: 8),
            const Text(
              'Teléfono / Celular',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
          ],
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: _telefonoController,
          decoration: InputDecoration(
            hintText: 'Ej: 0987654321',
            prefixIcon: const Icon(Icons.phone_android),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
            filled: true,
            fillColor: JPColors.surface,
          ),
          keyboardType: TextInputType.phone,
          inputFormatters: [
            FilteringTextInputFormatter.digitsOnly,
            LengthLimitingTextInputFormatter(10),
          ],
          validator: (value) {
            if (value == null || value.isEmpty) {
              return null; // Opcional
            }
            if (value.length != 10) {
              return 'Debe tener 10 dígitos';
            }
            if (!value.startsWith('0')) {
              return 'Debe comenzar con 0';
            }
            return null;
          },
        ),
        const SizedBox(height: 8),
        const Text(
          'Formato ecuatoriano: 10 dígitos comenzando con 0',
          style: TextStyle(fontSize: 12, color: JPColors.textSecondary),
        ),
      ],
    );
  }

  Widget _buildFechaField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.cake, color: JPColors.primary, size: 20),
            const SizedBox(width: 8),
            const Text(
              'Fecha de Nacimiento',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
          ],
        ),
        const SizedBox(height: 12),
        InkWell(
          onTap: _seleccionarFecha,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: JPColors.surface,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.grey.shade300),
            ),
            child: Row(
              children: [
                const Icon(Icons.calendar_today, color: JPColors.primary),
                const SizedBox(width: 16),
                Expanded(
                  child: Text(
                    _fechaNacimiento != null
                        ? '${_fechaNacimiento!.day}/${_fechaNacimiento!.month}/${_fechaNacimiento!.year}'
                        : 'Seleccionar fecha',
                    style: TextStyle(
                      fontSize: 16,
                      color: _fechaNacimiento != null
                          ? JPColors.textPrimary
                          : JPColors.textSecondary,
                    ),
                  ),
                ),
                if (_fechaNacimiento != null) ...[
                  Text(
                    '${_calcularEdad(_fechaNacimiento!)} años',
                    style: const TextStyle(
                      fontSize: 14,
                      color: JPColors.textSecondary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 8),
                ],
                const Icon(Icons.arrow_forward_ios, size: 16),
              ],
            ),
          ),
        ),
        const SizedBox(height: 8),
        const Text(
          'Debes tener al menos 13 años',
          style: TextStyle(fontSize: 12, color: JPColors.textSecondary),
        ),
      ],
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🔧 HELPERS
  // ══════════════════════════════════════════════════════════════════════════

  String _calcularEdad(DateTime fecha) {
    final hoy = DateTime.now();
    int edad = hoy.year - fecha.year;
    if (hoy.month < fecha.month ||
        (hoy.month == fecha.month && hoy.day < fecha.day)) {
      edad--;
    }
    return edad.toString();
  }
}
