// lib/screens/auth/forms/registro_usuario_form.dart

import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import '../../../services/auth_service.dart';
import '../../../apis/helpers/api_exception.dart';
import '../../pantalla_router.dart';

class RegistroUsuarioForm extends StatefulWidget {
  const RegistroUsuarioForm({super.key});

  @override
  State<RegistroUsuarioForm> createState() => _RegistroUsuarioFormState();
}

class _RegistroUsuarioFormState extends State<RegistroUsuarioForm> {
  final _formKey = GlobalKey<FormState>();
  final _api = AuthService();

  final _nombreController = TextEditingController();
  final _apellidoController = TextEditingController();
  final _usernameController = TextEditingController();
  final _emailController = TextEditingController();
  final _celularController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmarPasswordController = TextEditingController();

  bool _loading = false;
  bool _obscurePassword = true;
  bool _obscureConfirmar = true;
  bool _aceptaTerminos = false;
  DateTime? _fechaNacimiento;
  String? _error;

  static const Color _azulPrincipal = Color(0xFF4FC3F7);
  static const Color _azulOscuro = Color(0xFF0288D1);
  static const Color _verde = Color(0xFF4CAF50);

  @override
  void dispose() {
    _nombreController.dispose();
    _apellidoController.dispose();
    _usernameController.dispose();
    _emailController.dispose();
    _celularController.dispose();
    _passwordController.dispose();
    _confirmarPasswordController.dispose();
    super.dispose();
  }

  Future<void> _seleccionarFecha() async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: DateTime(2000),
      firstDate: DateTime(1920),
      lastDate: DateTime.now(),
      helpText: 'Selecciona tu fecha de nacimiento',
      cancelText: 'Cancelar',
      confirmText: 'Aceptar',
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.light(
              primary: _azulPrincipal,
              onPrimary: Colors.white,
              surface: Colors.white,
              onSurface: Colors.black,
            ),
          ),
          child: child!,
        );
      },
    );

    if (picked != null) {
      setState(() => _fechaNacimiento = picked);
    }
  }

  int _calcularEdad() {
    if (_fechaNacimiento == null) return 0;
    final hoy = DateTime.now();
    int edad = hoy.year - _fechaNacimiento!.year;
    if (hoy.month < _fechaNacimiento!.month ||
        (hoy.month == _fechaNacimiento!.month &&
            hoy.day < _fechaNacimiento!.day)) {
      edad--;
    }
    return edad;
  }

  String _formatearFechaParaMostrar() {
    if (_fechaNacimiento == null) return 'Selecciona tu fecha de nacimiento';
    return '${_fechaNacimiento!.day.toString().padLeft(2, '0')}/${_fechaNacimiento!.month.toString().padLeft(2, '0')}/${_fechaNacimiento!.year}';
  }

  String _formatearFechaParaBackend() {
    return '${_fechaNacimiento!.year}-${_fechaNacimiento!.month.toString().padLeft(2, '0')}-${_fechaNacimiento!.day.toString().padLeft(2, '0')}';
  }

  Future<void> _registrar() async {
    // Validar formulario
    if (!_formKey.currentState!.validate()) {
      debugPrint('❌ Formulario no válido');
      return;
    }

    // Validar fecha
    if (_fechaNacimiento == null) {
      setState(() => _error = 'Debes ingresar tu fecha de nacimiento');
      return;
    }

    if (_calcularEdad() < 18) {
      setState(() => _error = 'Debes ser mayor de 18 años para registrarte');
      return;
    }

    // Validar términos
    if (!_aceptaTerminos) {
      setState(() => _error = 'Debes aceptar los términos y condiciones');
      return;
    }

    // ✅ VALIDAR CONTRASEÑAS ANTES DE ENVIAR
    final password = _passwordController.text.trim();
    final password2 = _confirmarPasswordController.text.trim();

    if (password.isEmpty || password2.isEmpty) {
      setState(() => _error = 'La contraseña no puede estar vacía');
      return;
    }

    if (password != password2) {
      setState(() => _error = 'Las contraseñas no coinciden');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      // ✅ CONSTRUIR DATOS CON VALORES YA VALIDADOS
      final data = {
        'first_name': _nombreController.text.trim(),
        'last_name': _apellidoController.text.trim(),
        'username': _usernameController.text.trim(),
        'email': _emailController.text.trim(),
        'celular': _celularController.text.trim(),
        'fecha_nacimiento': _formatearFechaParaBackend(),
        'password': password,
        'password2': password2,
        'terminos_aceptados': _aceptaTerminos,
        'rol': 'USUARIO', // ⭐ ROL: Acceso completo inmediato
      };

      // 🐛 DEBUG
      debugPrint('📦 ============ REGISTRO USUARIO ============');
      debugPrint('Rol: USUARIO (acceso completo inmediato)');
      data.forEach((key, value) {
        if (key != 'password' && key != 'password2') {
          debugPrint('$key: "$value"');
        } else {
          debugPrint('$key: [${value.toString().length} caracteres]');
        }
      });
      debugPrint('===========================================');

      await _api.register(data);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Row(
              children: [
                Icon(Icons.check_circle_rounded, color: Colors.white),
                SizedBox(width: 10),
                Text('¡Registro exitoso! Bienvenido'),
              ],
            ),
            backgroundColor: _verde,
            behavior: SnackBarBehavior.floating,
            duration: const Duration(seconds: 2),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
          ),
        );

        // ✅ CORRECCIÓN: Usar Router para detectar rol automáticamente
        Navigator.pushAndRemoveUntil(
          context,
          MaterialPageRoute(builder: (_) => const PantallaRouter()),
          (route) => false, // Limpiar stack completo
        );
      }
    } on ApiException catch (e) {
      debugPrint('❌ ApiException: ${e.message}');
      if (mounted) setState(() => _error = e.message);
    } catch (e) {
      debugPrint('❌ Error inesperado: $e');
      if (mounted) setState(() => _error = 'Error de conexión');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _mostrarTerminos() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.9,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        builder: (_, controller) => Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: _azulPrincipal.withValues(alpha: 0.1),
                  borderRadius: const BorderRadius.vertical(
                    top: Radius.circular(20),
                  ),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.description_rounded,
                      color: _azulOscuro,
                      size: 26,
                    ),
                    const SizedBox(width: 12),
                    const Expanded(
                      child: Text(
                        'Términos y Condiciones',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: _azulOscuro,
                        ),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close_rounded),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: ListView(
                  controller: controller,
                  padding: const EdgeInsets.all(20),
                  children: [
                    _buildSeccion(
                      '1. Aceptación',
                      'Al registrarte en JP Express aceptas estos términos.',
                    ),
                    _buildSeccion(
                      '2. Uso del Servicio',
                      'Debes usar la plataforma de forma responsable.',
                    ),
                    _buildSeccion(
                      '3. Privacidad',
                      'Tus datos están protegidos según nuestra política.',
                    ),
                    _buildSeccion(
                      '4. Pedidos',
                      'Los pedidos están sujetos a disponibilidad.',
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _mostrarPrivacidad() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.9,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        builder: (_, controller) => Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: _verde.withValues(alpha: 0.1),
                  borderRadius: const BorderRadius.vertical(
                    top: Radius.circular(20),
                  ),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.privacy_tip_rounded,
                      color: _verde,
                      size: 26,
                    ),
                    const SizedBox(width: 12),
                    const Expanded(
                      child: Text(
                        'Política de Privacidad',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: _verde,
                        ),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close_rounded),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: ListView(
                  controller: controller,
                  padding: const EdgeInsets.all(20),
                  children: [
                    _buildSeccion(
                      '1. Datos',
                      'Recopilamos nombre, email y teléfono.',
                    ),
                    _buildSeccion(
                      '2. Uso',
                      'Para procesar pedidos y mejorar el servicio.',
                    ),
                    _buildSeccion(
                      '3. Seguridad',
                      'Protegemos tu información personal.',
                    ),
                    _buildSeccion(
                      '4. Derechos',
                      'Puedes acceder y eliminar tus datos.',
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSeccion(String titulo, String texto) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            titulo,
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: _azulOscuro,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            texto,
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[700],
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        children: [
          _buildCampo(
            controller: _nombreController,
            label: 'Nombre',
            icono: Icons.person_outline_rounded,
            validator: (v) => v!.isEmpty ? 'Requerido' : null,
          ),
          const SizedBox(height: 14),
          _buildCampo(
            controller: _apellidoController,
            label: 'Apellido',
            icono: Icons.person_outline_rounded,
            validator: (v) => v!.isEmpty ? 'Requerido' : null,
          ),
          const SizedBox(height: 14),
          _buildCampo(
            controller: _usernameController,
            label: 'Usuario',
            icono: Icons.alternate_email_rounded,
            validator: (v) => v!.isEmpty ? 'Requerido' : null,
          ),
          const SizedBox(height: 14),
          _buildCampo(
            controller: _emailController,
            label: 'Correo electrónico',
            icono: Icons.email_outlined,
            tipo: TextInputType.emailAddress,
            validator: (v) {
              if (v!.isEmpty) return 'Requerido';
              if (!v.contains('@')) return 'Email inválido';
              return null;
            },
          ),
          const SizedBox(height: 14),
          _buildCampo(
            controller: _celularController,
            label: 'Celular',
            hint: '09XXXXXXXX',
            icono: Icons.phone_android_rounded,
            tipo: TextInputType.phone,
            maxLength: 10,
            validator: (v) {
              if (v!.isEmpty) return 'Requerido';
              if (!v.startsWith('09') || v.length != 10) {
                return 'Formato: 09XXXXXXXX';
              }
              return null;
            },
          ),
          const SizedBox(height: 14),
          _buildCampoFecha(),
          const SizedBox(height: 14),
          _buildCampoPassword(
            controller: _passwordController,
            label: 'Contraseña',
            obscure: _obscurePassword,
            onToggle: () =>
                setState(() => _obscurePassword = !_obscurePassword),
            validator: (v) {
              if (v!.isEmpty) return 'Requerido';
              if (v.length < 8) return 'Mínimo 8 caracteres';
              return null;
            },
          ),
          const SizedBox(height: 14),
          _buildCampoPassword(
            controller: _confirmarPasswordController,
            label: 'Confirmar contraseña',
            obscure: _obscureConfirmar,
            onToggle: () =>
                setState(() => _obscureConfirmar = !_obscureConfirmar),
            validator: (v) {
              if (v!.isEmpty) return 'Requerido';
              if (v != _passwordController.text) return 'No coinciden';
              return null;
            },
          ),
          const SizedBox(height: 20),
          _buildTerminos(),
          if (_error != null) _buildError(),
          const SizedBox(height: 24),
          _buildBoton(),
        ],
      ),
    );
  }

  Widget _buildCampo({
    required TextEditingController controller,
    required String label,
    String? hint,
    required IconData icono,
    TextInputType tipo = TextInputType.text,
    int? maxLength,
    String? Function(String?)? validator,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: tipo,
      maxLength: maxLength,
      enabled: !_loading,
      validator: validator,
      style: const TextStyle(fontSize: 15),
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        prefixIcon: Icon(icono, color: _azulOscuro, size: 22),
        counterText: '',
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 16,
        ),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.grey[300]!),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: _azulPrincipal, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Colors.red),
        ),
        filled: true,
        fillColor: Colors.white,
      ),
    );
  }

  Widget _buildCampoFecha() {
    return InkWell(
      onTap: _loading ? null : _seleccionarFecha,
      borderRadius: BorderRadius.circular(12),
      child: InputDecorator(
        decoration: InputDecoration(
          labelText: 'Fecha de nacimiento',
          prefixIcon: const Icon(
            Icons.calendar_today_rounded,
            color: _azulOscuro,
            size: 22,
          ),
          suffixIcon: _fechaNacimiento != null
              ? Chip(
                  label: Text(
                    '${_calcularEdad()} años',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: _calcularEdad() >= 18 ? _verde : Colors.red[700],
                    ),
                  ),
                  backgroundColor: _calcularEdad() >= 18
                      ? _verde.withValues(alpha: 0.1)
                      : Colors.red[50],
                  side: BorderSide.none,
                )
              : null,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 16,
          ),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.grey[300]!),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: _azulPrincipal, width: 2),
          ),
          filled: true,
          fillColor: Colors.white,
        ),
        child: Text(
          _formatearFechaParaMostrar(),
          style: TextStyle(
            fontSize: 15,
            color: _fechaNacimiento == null ? Colors.grey[600] : Colors.black,
          ),
        ),
      ),
    );
  }

  Widget _buildCampoPassword({
    required TextEditingController controller,
    required String label,
    required bool obscure,
    required VoidCallback onToggle,
    String? Function(String?)? validator,
  }) {
    return TextFormField(
      controller: controller,
      obscureText: obscure,
      enabled: !_loading,
      validator: validator,
      style: const TextStyle(fontSize: 15),
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: const Icon(
          Icons.lock_outline_rounded,
          color: _azulOscuro,
          size: 22,
        ),
        suffixIcon: IconButton(
          icon: Icon(
            obscure ? Icons.visibility_off_rounded : Icons.visibility_rounded,
            color: Colors.grey[600],
            size: 22,
          ),
          onPressed: onToggle,
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 16,
        ),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.grey[300]!),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: _azulPrincipal, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Colors.red),
        ),
        filled: true,
        fillColor: Colors.white,
      ),
    );
  }

  Widget _buildTerminos() {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          height: 20,
          width: 20,
          child: Checkbox(
            value: _aceptaTerminos,
            onChanged: _loading
                ? null
                : (v) => setState(() => _aceptaTerminos = v!),
            activeColor: _azulPrincipal,
            materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
            visualDensity: VisualDensity.compact,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: RichText(
            text: TextSpan(
              style: TextStyle(
                fontSize: 13,
                color: Colors.grey[700],
                height: 1.5,
              ),
              children: [
                const TextSpan(text: 'Acepto los '),
                TextSpan(
                  text: 'Términos y Condiciones',
                  style: const TextStyle(
                    color: _azulPrincipal,
                    fontWeight: FontWeight.bold,
                    decoration: TextDecoration.underline,
                  ),
                  recognizer: TapGestureRecognizer()..onTap = _mostrarTerminos,
                ),
                const TextSpan(text: ' y la '),
                TextSpan(
                  text: 'Política de Privacidad',
                  style: const TextStyle(
                    color: _verde,
                    fontWeight: FontWeight.bold,
                    decoration: TextDecoration.underline,
                  ),
                  recognizer: TapGestureRecognizer()
                    ..onTap = _mostrarPrivacidad,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildError() {
    return Container(
      margin: const EdgeInsets.only(top: 16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.red[50],
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.red[200]!),
      ),
      child: Row(
        children: [
          Icon(Icons.error_outline_rounded, color: Colors.red[700], size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              _error!,
              style: TextStyle(color: Colors.red[700], fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBoton() {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: ElevatedButton(
        onPressed: _loading ? null : _registrar,
        style: ElevatedButton.styleFrom(
          backgroundColor: _verde,
          foregroundColor: Colors.white,
          disabledBackgroundColor: Colors.grey[300],
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
        child: _loading
            ? const SizedBox(
                height: 22,
                width: 22,
                child: CircularProgressIndicator(
                  strokeWidth: 2.5,
                  valueColor: AlwaysStoppedAnimation(Colors.white),
                ),
              )
            : const Text(
                'Crear Cuenta',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.5,
                ),
              ),
      ),
    );
  }
}
