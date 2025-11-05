// lib/screens/auth/pantalla_recuperar_password.dart

import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import '../../config/rutas.dart';
import '../../config/api_config.dart';
import '../../apis/helpers/api_exception.dart';
import '../../apis/helpers/api_validators.dart';

/// Pantalla de recuperación de contraseña - JP Express
/// ✅ Integrada con sistema de código de 6 dígitos
/// ✅ Manejo de rate limiting y bloqueos temporales
class PantallaRecuperarPassword extends StatefulWidget {
  const PantallaRecuperarPassword({super.key});

  @override
  State<PantallaRecuperarPassword> createState() =>
      _PantallaRecuperarPasswordState();
}

class _PantallaRecuperarPasswordState extends State<PantallaRecuperarPassword> {
  // ============================================
  // CONTROLADORES Y SERVICIOS
  // ============================================
  final _emailController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  final _api = AuthService();

  // ============================================
  // ESTADO
  // ============================================
  bool _loading = false;
  String? _error;
  bool _codigoEnviado = false;

  // ✅ Estado de rate limiting
  int? _tiempoEspera;
  int? _intentosRestantes;
  bool _bloqueadoTemporalmente = false;

  // ============================================
  // COLORES JP EXPRESS
  // ============================================
  static const Color _azulPrincipal = Color(0xFF4FC3F7);
  static const Color _azulOscuro = Color(0xFF0288D1);

  // ============================================
  // MÉTODOS
  // ============================================

  /// ✅ Envía código de recuperación de 6 dígitos
  Future<void> _enviarCodigo() async {
    // Validar formulario
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
      _tiempoEspera = null;
      _intentosRestantes = null;
      _bloqueadoTemporalmente = false;
    });

    try {
      // ✅ Usar el nuevo método de código de 6 dígitos
      await _api.solicitarCodigoRecuperacion(
        email: _emailController.text.trim(),
      );

      if (mounted) {
        setState(() {
          _codigoEnviado = true;
          _loading = false;
        });

        // ✅ Navegar a pantalla de verificación de código
        await Future.delayed(const Duration(seconds: 2));
        if (mounted) {
          Rutas.irAVerificarCodigo(context, _emailController.text.trim());
        }
      }
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          if (e.statusCode == 429) {
            // ✅ Bloqueado por rate limiting
            _bloqueadoTemporalmente = true;
            _tiempoEspera = e.retryAfter ?? 60;
            _error = e.message;
            _mostrarDialogoBloqueado();
          } else {
            _error = e.message;
            _intentosRestantes = e.intentosRestantes;
          }
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Error de conexión. Intenta nuevamente';
          _loading = false;
        });
      }
    }
  }

  /// ✅ Muestra diálogo cuando está bloqueado temporalmente
  void _mostrarDialogoBloqueado() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Row(
          children: [
            Icon(Icons.block, color: Colors.red[700], size: 28),
            const SizedBox(width: 12),
            const Expanded(
              child: Text(
                'Demasiados Intentos',
                style: TextStyle(fontSize: 18),
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Has excedido el número de intentos de recuperación.',
              style: TextStyle(fontSize: 15, color: Colors.grey[800]),
            ),
            const SizedBox(height: 12),
            if (_tiempoEspera != null)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.orange[50],
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.orange[300]!),
                ),
                child: Row(
                  children: [
                    Icon(Icons.schedule, color: Colors.orange[700], size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Espera ${AuthService.formatearTiempoEspera(_tiempoEspera!)} antes de intentar nuevamente',
                        style: TextStyle(
                          color: Colors.orange[900],
                          fontWeight: FontWeight.w500,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 12),
            Text(
              'Esto es una medida de seguridad. Si necesitas ayuda inmediata, contacta con soporte.',
              style: TextStyle(fontSize: 13, color: Colors.grey[600]),
            ),
          ],
        ),
        actions: [
          ElevatedButton(
            onPressed: () => Navigator.pop(context),
            style: ElevatedButton.styleFrom(
              backgroundColor: _azulPrincipal,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            ),
            child: const Text(
              'Entendido',
              style: TextStyle(color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }

  /// Vuelve a la pantalla de login
  void _volverAlLogin() {
    Navigator.pop(context);
  }

  // ============================================
  // CICLO DE VIDA
  // ============================================

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  // ============================================
  // UI - BUILD PRINCIPAL
  // ============================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: _azulOscuro),
          onPressed: _volverAlLogin,
        ),
      ),
      body: Container(
        decoration: _buildGradienteFondo(),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: _codigoEnviado
                  ? _buildCodigoEnviadoExito()
                  : _buildFormularioRecuperacion(),
            ),
          ),
        ),
      ),
    );
  }

  // ============================================
  // UI - COMPONENTES
  // ============================================

  /// Gradiente de fondo
  BoxDecoration _buildGradienteFondo() {
    return BoxDecoration(
      gradient: LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [_azulPrincipal.withValues(alpha: 0.1), Colors.white],
      ),
    );
  }

  /// Formulario de recuperación
  Widget _buildFormularioRecuperacion() {
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
            child: Icon(Icons.lock_reset, size: 80, color: _azulPrincipal),
          ),
          const SizedBox(height: 32),

          // Título
          const Text(
            '¿Olvidaste tu contraseña?',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.bold,
              color: Color(0xFF212121),
            ),
          ),
          const SizedBox(height: 12),

          // Descripción actualizada
          Text(
            'Te enviaremos un código de verificación de 6 dígitos a tu correo electrónico',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 15,
              color: Colors.grey[600],
              height: 1.5,
            ),
          ),
          const SizedBox(height: 40),

          // Campo de email con validación
          Container(
            constraints: const BoxConstraints(maxWidth: 400),
            child: TextFormField(
              controller: _emailController,
              keyboardType: TextInputType.emailAddress,
              autocorrect: false,
              enabled: !_loading && !_bloqueadoTemporalmente,
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Por favor ingresa tu correo electrónico';
                }
                if (!ApiValidators.esEmailValido(value)) {
                  return 'Por favor ingresa un correo válido';
                }
                return null;
              },
              decoration: InputDecoration(
                labelText: 'Correo electrónico',
                labelStyle: TextStyle(color: Colors.grey[700]),
                prefixIcon: Icon(Icons.email_outlined, color: _azulOscuro),
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
                fillColor: _bloqueadoTemporalmente
                    ? Colors.grey[100]
                    : Colors.white,
              ),
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

          // ✅ Mostrar intentos restantes si hay
          if (_intentosRestantes != null && _intentosRestantes! > 0) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.amber[50],
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.amber[300]!, width: 1),
              ),
              child: Row(
                children: [
                  Icon(Icons.warning_amber, color: Colors.amber[700], size: 20),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Te quedan $_intentosRestantes ${_intentosRestantes == 1 ? "intento" : "intentos"}',
                      style: TextStyle(
                        color: Colors.amber[900],
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],

          const SizedBox(height: 28),

          // Botón de enviar
          Container(
            height: 54,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: _bloqueadoTemporalmente
                    ? [Colors.grey[400]!, Colors.grey[500]!]
                    : [_azulPrincipal, _azulOscuro],
              ),
              borderRadius: BorderRadius.circular(12),
              boxShadow: _bloqueadoTemporalmente
                  ? []
                  : [
                      BoxShadow(
                        color: _azulPrincipal.withValues(alpha: 0.4),
                        blurRadius: 12,
                        offset: const Offset(0, 6),
                      ),
                    ],
            ),
            child: ElevatedButton(
              onPressed: (_loading || _bloqueadoTemporalmente)
                  ? null
                  : _enviarCodigo,
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
                  : Text(
                      _bloqueadoTemporalmente
                          ? 'Bloqueado Temporalmente'
                          : 'Enviar código de verificación',
                      style: const TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                        letterSpacing: 0.5,
                      ),
                    ),
            ),
          ),

          const SizedBox(height: 20),

          // Botón volver
          TextButton(
            onPressed: (_loading || _bloqueadoTemporalmente)
                ? null
                : _volverAlLogin,
            child: Text(
              'Volver al inicio de sesión',
              style: TextStyle(
                color: (_loading || _bloqueadoTemporalmente)
                    ? Colors.grey
                    : _azulOscuro,
                fontSize: 15,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Pantalla de éxito cuando se envió el código
  Widget _buildCodigoEnviadoExito() {
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
          child: Icon(
            Icons.mark_email_read_outlined,
            size: 100,
            color: Colors.green[600],
          ),
        ),
        const SizedBox(height: 32),

        // Título
        const Text(
          '¡Código enviado!',
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
          'Hemos enviado un código de 6 dígitos a\n${_emailController.text}',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 15, color: Colors.grey[600], height: 1.5),
        ),
        const SizedBox(height: 12),

        Text(
          'Revisa tu bandeja de entrada e ingresa el código en la siguiente pantalla.',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 14, color: Colors.grey[500], height: 1.5),
        ),
        const SizedBox(height: 40),

        // Nota importante
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.blue[50],
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.blue[200]!, width: 1),
          ),
          child: Row(
            children: [
              Icon(Icons.info_outline, color: Colors.blue[700], size: 24),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'El código expira en ${ApiConfig.codigoExpiracionMinutos} minutos',
                  style: TextStyle(
                    color: Colors.blue[700],
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 24),

        // Indicador de carga
        const Center(child: CircularProgressIndicator()),
        const SizedBox(height: 16),
        Text(
          'Redirigiendo a verificación...',
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.grey[600]),
        ),
      ],
    );
  }
}
