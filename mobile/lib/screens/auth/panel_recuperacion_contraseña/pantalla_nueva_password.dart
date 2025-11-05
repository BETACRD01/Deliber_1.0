// lib/screens/auth/pantalla_nueva_password.dart

import 'package:flutter/material.dart';
import '../../../services/auth_service.dart';
import '../../../config/rutas.dart';
import '../../../apis/helpers/api_exception.dart';
import '../../../apis/helpers/api_validators.dart';

/// Pantalla para establecer nueva contraseña
/// ✅ Última etapa del flujo de recuperación
class PantallaNuevaPassword extends StatefulWidget {
  const PantallaNuevaPassword({super.key});

  @override
  State<PantallaNuevaPassword> createState() => _PantallaNuevaPasswordState();
}

class _PantallaNuevaPasswordState extends State<PantallaNuevaPassword> {
  // ============================================
  // CONTROLADORES
  // ============================================
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  final _api = AuthService();

  // ============================================
  // ESTADO
  // ============================================
  String? _email;
  String? _codigo;
  bool _loading = false;
  String? _error;
  bool _passwordVisible = false;
  bool _confirmPasswordVisible = false;
  bool _exitoso = false;

  // ============================================
  // COLORES
  // ============================================
  static const Color _azulPrincipal = Color(0xFF4FC3F7);
  static const Color _azulOscuro = Color(0xFF0288D1);

  // ============================================
  // CICLO DE VIDA
  // ============================================

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _obtenerArgumentos();
    });
  }

  @override
  void dispose() {
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  // ============================================
  // MÉTODOS
  // ============================================

  /// Obtiene email y código de los argumentos
  void _obtenerArgumentos() {
    final args = Rutas.obtenerArgumentos<Map<String, dynamic>>(context);
    if (args != null &&
        args.containsKey('email') &&
        args.containsKey('codigo')) {
      setState(() {
        _email = args['email'] as String;
        _codigo = args['codigo'] as String;
      });
    } else {
      // Si no hay datos, volver al inicio
      Rutas.irAYLimpiar(context, Rutas.login);
    }
  }

  /// ✅ Cambia la contraseña
  Future<void> _cambiarPassword() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      await _api.resetPasswordConCodigo(
        email: _email!,
        codigo: _codigo!,
        password: _passwordController.text,
      );

      if (mounted) {
        setState(() {
          _exitoso = true;
          _loading = false;
        });

        // Esperar 2 segundos y volver al login
        await Future.delayed(const Duration(seconds: 2));
        if (mounted) {
          Rutas.completarRecuperacionPassword(context);
        }
      }
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          _error = e.message;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Error al cambiar contraseña. Intenta nuevamente';
          _loading = false;
        });
      }
    }
  }

  // ============================================
  // UI - BUILD
  // ============================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: !_exitoso
            ? IconButton(
                icon: Icon(Icons.arrow_back, color: _azulOscuro),
                onPressed: () => Navigator.pop(context),
              )
            : null,
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [_azulPrincipal.withValues(alpha: 0.1), Colors.white],
          ),
        ),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: _exitoso ? _buildExito() : _buildFormulario(),
            ),
          ),
        ),
      ),
    );
  }

  /// Formulario de nueva contraseña
  Widget _buildFormulario() {
    return Form(
      key: _formKey,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Icono
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: _azulPrincipal.withValues(alpha: 0.1),
            ),
            child: Icon(Icons.lock_open, size: 80, color: _azulPrincipal),
          ),
          const SizedBox(height: 32),

          // Título
          const Text(
            'Nueva Contraseña',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.bold,
              color: Color(0xFF212121),
            ),
          ),
          const SizedBox(height: 12),

          // Descripción
          Text(
            'Crea una contraseña segura para tu cuenta',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 15,
              color: Colors.grey[600],
              height: 1.5,
            ),
          ),
          const SizedBox(height: 40),

          // Campo de contraseña
          TextFormField(
            controller: _passwordController,
            obscureText: !_passwordVisible,
            enabled: !_loading,
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Por favor ingresa tu contraseña';
              }
              final validacion = ApiValidators.validarPassword(value);
              if (!validacion['valida']) {
                final errores = validacion['errores'] as List<String>;
                return errores.first;
              }
              return null;
            },
            decoration: InputDecoration(
              labelText: 'Nueva contraseña',
              labelStyle: TextStyle(color: Colors.grey[700]),
              prefixIcon: Icon(Icons.lock_outline, color: _azulOscuro),
              suffixIcon: IconButton(
                icon: Icon(
                  _passwordVisible ? Icons.visibility_off : Icons.visibility,
                  color: Colors.grey[600],
                ),
                onPressed: () {
                  setState(() => _passwordVisible = !_passwordVisible);
                },
              ),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: Colors.grey[300]!, width: 1.5),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: _azulPrincipal, width: 2),
              ),
              errorBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Colors.red, width: 1.5),
              ),
              focusedErrorBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Colors.red, width: 2),
              ),
              filled: true,
              fillColor: Colors.white,
            ),
          ),

          const SizedBox(height: 16),

          // Campo confirmar contraseña
          TextFormField(
            controller: _confirmPasswordController,
            obscureText: !_confirmPasswordVisible,
            enabled: !_loading,
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Por favor confirma tu contraseña';
              }
              if (value != _passwordController.text) {
                return 'Las contraseñas no coinciden';
              }
              return null;
            },
            decoration: InputDecoration(
              labelText: 'Confirmar contraseña',
              labelStyle: TextStyle(color: Colors.grey[700]),
              prefixIcon: Icon(Icons.lock_outline, color: _azulOscuro),
              suffixIcon: IconButton(
                icon: Icon(
                  _confirmPasswordVisible
                      ? Icons.visibility_off
                      : Icons.visibility,
                  color: Colors.grey[600],
                ),
                onPressed: () {
                  setState(
                    () => _confirmPasswordVisible = !_confirmPasswordVisible,
                  );
                },
              ),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: Colors.grey[300]!, width: 1.5),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: _azulPrincipal, width: 2),
              ),
              errorBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Colors.red, width: 1.5),
              ),
              focusedErrorBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Colors.red, width: 2),
              ),
              filled: true,
              fillColor: Colors.white,
            ),
          ),

          const SizedBox(height: 16),

          // Requisitos de contraseña
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.grey[50],
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: Colors.grey[300]!),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'La contraseña debe tener:',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: Colors.grey[700],
                  ),
                ),
                const SizedBox(height: 8),
                _buildRequisitoPassword('Al menos 8 caracteres'),
                _buildRequisitoPassword('Al menos una letra'),
                _buildRequisitoPassword('Al menos un número'),
                _buildRequisitoPassword('Sin espacios en blanco'),
              ],
            ),
          ),

          // Mensaje de error
          if (_error != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.red[50],
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.red[300]!, width: 1),
              ),
              child: Row(
                children: [
                  Icon(Icons.error_outline, color: Colors.red[700], size: 20),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _error!,
                      style: TextStyle(color: Colors.red[700], fontSize: 14),
                    ),
                  ),
                ],
              ),
            ),
          ],

          const SizedBox(height: 28),

          // Botón cambiar contraseña
          Container(
            height: 54,
            decoration: BoxDecoration(
              gradient: LinearGradient(colors: [_azulPrincipal, _azulOscuro]),
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: _azulPrincipal.withValues(alpha: 0.4),
                  blurRadius: 12,
                  offset: const Offset(0, 6),
                ),
              ],
            ),
            child: ElevatedButton(
              onPressed: _loading ? null : _cambiarPassword,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.transparent,
                shadowColor: Colors.transparent,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: _loading
                  ? const SizedBox(
                      height: 24,
                      width: 24,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : const Text(
                      'Cambiar Contraseña',
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                        letterSpacing: 0.5,
                      ),
                    ),
            ),
          ),
        ],
      ),
    );
  }

  /// Widget para mostrar requisito de contraseña
  Widget _buildRequisitoPassword(String texto) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          Icon(Icons.check_circle_outline, size: 16, color: Colors.grey[600]),
          const SizedBox(width: 8),
          Text(texto, style: TextStyle(fontSize: 12, color: Colors.grey[700])),
        ],
      ),
    );
  }

  /// Pantalla de éxito
  Widget _buildExito() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Icono de éxito
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: Colors.green[50],
          ),
          child: Icon(Icons.check_circle, size: 100, color: Colors.green[600]),
        ),
        const SizedBox(height: 32),

        // Título
        const Text(
          '¡Contraseña Cambiada!',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 26,
            fontWeight: FontWeight.bold,
            color: Color(0xFF212121),
          ),
        ),
        const SizedBox(height: 16),

        // Descripción
        Text(
          'Tu contraseña ha sido actualizada exitosamente.',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 15, color: Colors.grey[600], height: 1.5),
        ),
        const SizedBox(height: 12),

        Text(
          'Ahora puedes iniciar sesión con tu nueva contraseña.',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 14, color: Colors.grey[500], height: 1.5),
        ),
        const SizedBox(height: 40),

        // Indicador de carga
        const Center(child: CircularProgressIndicator()),
        const SizedBox(height: 16),
        Text(
          'Redirigiendo al login...',
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.grey[600]),
        ),
      ],
    );
  }
}
