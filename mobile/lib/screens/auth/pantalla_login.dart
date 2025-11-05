// lib/screens/auth/pantalla_login.dart

import 'package:flutter/material.dart';
import '../../theme/jp_theme.dart';
import '../../services/auth_service.dart';
import './pantalla_registro.dart';
import './pantalla_recuperar_password.dart';
import '../../apis/helpers/api_exception.dart';
import '../pantalla_router.dart';

/// Pantalla de inicio de sesión - JP Express
/// ✅ CON RATE LIMITING Y DETECCIÓN DE INTENTOS RESTANTES
class PantallaLogin extends StatefulWidget {
  const PantallaLogin({super.key});

  @override
  State<PantallaLogin> createState() => _PantallaLoginState();
}

class _PantallaLoginState extends State<PantallaLogin> {
  // ============================================
  // CONTROLADORES Y SERVICIOS
  // ============================================
  final _usuarioController = TextEditingController();
  final _passwordController = TextEditingController();
  final _api = AuthService();

  // ============================================
  // ESTADO
  // ============================================
  bool _loading = false;
  bool _obscurePassword = true;
  String? _error;

  // ✅ Estado de rate limiting
  int? _intentosRestantes;
  int? _tiempoEspera;
  bool _bloqueadoTemporalmente = false;

  // ============================================
  // MÉTODOS DE AUTENTICACIÓN
  // ============================================

  /// Procesa el inicio de sesión con manejo de rate limiting
  Future<void> _login() async {
    // Validación básica
    if (_usuarioController.text.isEmpty || _passwordController.text.isEmpty) {
      setState(() {
        _error = 'Por favor completa todos los campos';
        _intentosRestantes = null;
      });
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
      _intentosRestantes = null;
      _tiempoEspera = null;
      _bloqueadoTemporalmente = false;
    });

    try {
      await _api.login(
        email: _usuarioController.text.trim(),
        password: _passwordController.text,
      );

      // ✅ Login exitoso
      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const PantallaRouter()),
        );
      }
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          if (e.statusCode == 429) {
            // Bloqueado por rate limiting
            _bloqueadoTemporalmente = true;
            _tiempoEspera = e.details?['retry_after'];
            _error = e.message;

            _mostrarDialogoBloqueado();
          } else if (e.statusCode == 400) {
            // Login fallido - mostrar intentos restantes
            _intentosRestantes = e.details?['intentos_restantes'];
            _error = e.message;

            if (_intentosRestantes != null && _intentosRestantes! <= 5) {
              _mostrarAdvertenciaIntentos();
            }
          } else {
            _error = e.message;
          }
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _error = 'Error de conexión con el servidor');
      }
    } finally {
      if (mounted) setState(() => _loading = false);
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
            Icon(Icons.block, color: JPColors.error, size: 28),
            const SizedBox(width: 12),
            const Expanded(child: Text('Bloqueado Temporalmente')),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Has excedido el número de intentos permitidos.',
              style: TextStyle(fontSize: 15, color: Colors.grey[800]),
            ),
            const SizedBox(height: 12),
            if (_tiempoEspera != null)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: JPColors.warning.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: JPColors.warning),
                ),
                child: Row(
                  children: [
                    Icon(Icons.schedule, color: JPColors.warning, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Espera $_tiempoEspera segundos antes de intentar nuevamente',
                        style: const TextStyle(
                          color: JPColors.warning,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 12),
            Text(
              'Esto es por tu seguridad. Si olvidaste tu contraseña, usa la opción de recuperación.',
              style: TextStyle(fontSize: 13, color: Colors.grey[600]),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _irARecuperarPassword();
            },
            child: const Text('Recuperar Contraseña'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context),
            style: ElevatedButton.styleFrom(
              backgroundColor: JPColors.primary,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            child: const Text('Entendido'),
          ),
        ],
      ),
    );
  }

  /// ✅ Muestra advertencia cuando quedan pocos intentos
  void _mostrarAdvertenciaIntentos() {
    if (_intentosRestantes != null && _intentosRestantes! > 0) {
      JPSnackbar.show(
        context,
        '⚠️ Te quedan $_intentosRestantes intentos',
        isError: true,
        duration: const Duration(seconds: 4),
      );
    }
  }

  /// Navega a la pantalla de registro
  void _irARegistro() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const PantallaRegistro()),
    );
  }

  /// Navega a la pantalla de recuperación de contraseña
  void _irARecuperarPassword() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const PantallaRecuperarPassword()),
    );
  }

  /// Navega a la pantalla de test
  void _irATest() {
    Navigator.pushNamed(context, '/test');
  }

  /// Inicia sesión con Google
  Future<void> _loginConGoogle() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      // Integración con Google pendiente
      await Future.delayed(const Duration(seconds: 1));

      if (mounted) {
        JPSnackbar.info(context, '🔐 Login con Google en desarrollo');
      }
    } catch (e) {
      if (mounted) {
        setState(() => _error = 'Error al iniciar sesión con Google');
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  /// Inicia sesión con Facebook
  Future<void> _loginConFacebook() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      // Integración con Facebook pendiente
      await Future.delayed(const Duration(seconds: 1));

      if (mounted) {
        JPSnackbar.info(context, '🔐 Login con Facebook en desarrollo');
      }
    } catch (e) {
      if (mounted) {
        setState(() => _error = 'Error al iniciar sesión con Facebook');
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  /// Inicia sesión con Apple
  Future<void> _loginConApple() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      // Integración con Apple pendiente
      await Future.delayed(const Duration(seconds: 1));

      if (mounted) {
        JPSnackbar.info(context, '🔐 Login con Apple en desarrollo');
      }
    } catch (e) {
      if (mounted) {
        setState(() => _error = 'Error al iniciar sesión con Apple');
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  // ============================================
  // CICLO DE VIDA
  // ============================================

  @override
  void dispose() {
    _usuarioController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  // ============================================
  // UI - BUILD PRINCIPAL
  // ============================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _irATest,
        icon: const Icon(Icons.bug_report),
        label: const Text('Test API'),
        backgroundColor: JPColors.secondary,
        tooltip: 'Probar conexión con el servidor',
      ),
      body: Container(
        decoration: _buildGradienteFondo(),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _buildLogo(),
                  const SizedBox(height: 40),
                  _buildTitulos(),
                  const SizedBox(height: 40),
                  _buildFormulario(),
                  const SizedBox(height: 20),
                  _buildTextoRegistro(),
                  const SizedBox(height: 32),
                  _buildDivisorSocial(),
                  const SizedBox(height: 24),
                  _buildBotonesSociales(),
                  const SizedBox(height: 60),
                ],
              ),
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
        colors: [JPColors.primary.withValues(alpha: 0.1), Colors.white],
      ),
    );
  }

  /// Logo con efecto circular
  Widget _buildLogo() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: JPColors.primary.withValues(alpha: 0.2),
            blurRadius: 25,
            spreadRadius: 3,
          ),
        ],
      ),
      child: ClipOval(
        child: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: RadialGradient(
              colors: [
                JPColors.primary.withValues(alpha: 0.1),
                JPColors.primary.withValues(alpha: 0.05),
              ],
            ),
          ),
          child: Image.asset(
            'assets/images/logo.gif',
            height: 120,
            width: 120,
            fit: BoxFit.contain,
            errorBuilder: (context, error, stackTrace) {
              return Container(
                height: 120,
                width: 120,
                decoration: BoxDecoration(
                  color: JPColors.primary.withValues(alpha: 0.1),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.local_shipping,
                  size: 60,
                  color: JPColors.primary,
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  /// Títulos de la app
  Widget _buildTitulos() {
    return const Column(
      children: [
        Text(
          'JP Express',
          style: TextStyle(
            fontSize: 32,
            fontWeight: FontWeight.bold,
            color: JPColors.textPrimary,
            letterSpacing: 1.2,
          ),
        ),
        SizedBox(height: 8),
        Text(
          'Servicio Delivery',
          style: TextStyle(
            fontSize: 16,
            color: JPColors.textSecondary,
            letterSpacing: 0.5,
          ),
        ),
      ],
    );
  }

  /// Divisor con texto "O continúa con"
  Widget _buildDivisorSocial() {
    return Row(
      children: [
        Expanded(child: Divider(color: Colors.grey[300], thickness: 1)),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Text(
            'O continúa con',
            style: TextStyle(color: Colors.grey[600], fontSize: 14),
          ),
        ),
        Expanded(child: Divider(color: Colors.grey[300], thickness: 1)),
      ],
    );
  }

  /// Botones de redes sociales
  Widget _buildBotonesSociales() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        _buildBotonSocial(
          onTap: _loginConGoogle,
          icono: Icons.g_mobiledata,
          color: const Color(0xFFDB4437),
          tooltip: 'Google',
        ),
        const SizedBox(width: 16),
        _buildBotonSocial(
          onTap: _loginConFacebook,
          icono: Icons.facebook,
          color: const Color(0xFF1877F2),
          tooltip: 'Facebook',
        ),
        const SizedBox(width: 16),
        _buildBotonSocial(
          onTap: _loginConApple,
          icono: Icons.apple,
          color: const Color(0xFF000000),
          tooltip: 'Apple',
        ),
      ],
    );
  }

  /// Botón individual de red social
  Widget _buildBotonSocial({
    required VoidCallback onTap,
    required IconData icono,
    required Color color,
    required String tooltip,
  }) {
    return Tooltip(
      message: 'Iniciar con $tooltip',
      child: InkWell(
        onTap: _loading ? null : onTap,
        borderRadius: BorderRadius.circular(12),
        child: AnimatedOpacity(
          opacity: _loading ? 0.5 : 1.0,
          duration: const Duration(milliseconds: 200),
          child: Container(
            width: 60,
            height: 60,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: color.withValues(alpha: 0.3),
                  blurRadius: 8,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Icon(icono, color: Colors.white, size: 32),
          ),
        ),
      ),
    );
  }

  /// Formulario de login
  Widget _buildFormulario() {
    return Container(
      constraints: const BoxConstraints(maxWidth: 400),
      child: Column(
        children: [
          _buildCampoUsuario(),
          const SizedBox(height: 16),
          _buildCampoPassword(),
          const SizedBox(height: 8),
          _buildOlvidastePassword(),
          _buildMensajeError(),
          _buildIntentosRestantes(),
          const SizedBox(height: 28),
          _buildBotonLogin(),
        ],
      ),
    );
  }

  /// Campo de usuario
  Widget _buildCampoUsuario() {
    return TextField(
      controller: _usuarioController,
      keyboardType: TextInputType.text,
      autocorrect: false,
      enabled: !_loading && !_bloqueadoTemporalmente,
      decoration: InputDecoration(
        labelText: 'Usuario o Email',
        labelStyle: const TextStyle(color: JPColors.textSecondary),
        prefixIcon: const Icon(Icons.person_outline, color: JPColors.primary),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.grey[300]!, width: 1.5),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: JPColors.primary, width: 2),
        ),
        filled: true,
        fillColor: _bloqueadoTemporalmente ? Colors.grey[100] : Colors.white,
      ),
    );
  }

  /// Campo de contraseña
  Widget _buildCampoPassword() {
    return TextField(
      controller: _passwordController,
      obscureText: _obscurePassword,
      enabled: !_loading && !_bloqueadoTemporalmente,
      decoration: InputDecoration(
        labelText: 'Contraseña',
        labelStyle: const TextStyle(color: JPColors.textSecondary),
        prefixIcon: const Icon(Icons.lock_outline, color: JPColors.primary),
        suffixIcon: IconButton(
          icon: Icon(
            _obscurePassword ? Icons.visibility_off : Icons.visibility,
            color: JPColors.primary,
          ),
          onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
        ),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.grey[300]!, width: 1.5),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: JPColors.primary, width: 2),
        ),
        filled: true,
        fillColor: _bloqueadoTemporalmente ? Colors.grey[100] : Colors.white,
      ),
    );
  }

  /// Botón "¿Olvidaste tu contraseña?"
  Widget _buildOlvidastePassword() {
    return Align(
      alignment: Alignment.centerRight,
      child: TextButton(
        onPressed: (_loading || _bloqueadoTemporalmente)
            ? null
            : _irARecuperarPassword,
        style: TextButton.styleFrom(
          padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
        ),
        child: Text(
          '¿Olvidaste tu contraseña?',
          style: TextStyle(
            color: (_loading || _bloqueadoTemporalmente)
                ? Colors.grey
                : JPColors.primary,
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
    );
  }

  /// Mensaje de error
  Widget _buildMensajeError() {
    if (_error == null) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.only(top: 16),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: JPColors.error.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: JPColors.error, width: 1),
        ),
        child: Row(
          children: [
            const Icon(Icons.error_outline, color: JPColors.error, size: 20),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                _error!,
                style: const TextStyle(color: JPColors.error, fontSize: 14),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// ✅ Muestra intentos restantes
  Widget _buildIntentosRestantes() {
    if (_intentosRestantes == null || _intentosRestantes! <= 0) {
      return const SizedBox.shrink();
    }

    Color color;
    IconData icono;
    if (_intentosRestantes! <= 2) {
      color = JPColors.error;
      icono = Icons.warning;
    } else if (_intentosRestantes! <= 5) {
      color = JPColors.warning;
      icono = Icons.info_outline;
    } else {
      color = JPColors.info;
      icono = Icons.info;
    }

    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: color.withValues(alpha: 0.3)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icono, color: color, size: 18),
            const SizedBox(width: 8),
            Text(
              'Te quedan $_intentosRestantes intentos',
              style: TextStyle(
                color: color,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Botón de inicio de sesión
  Widget _buildBotonLogin() {
    return Container(
      width: double.infinity,
      height: 54,
      decoration: BoxDecoration(
        gradient: _bloqueadoTemporalmente
            ? LinearGradient(colors: [Colors.grey[400]!, Colors.grey[500]!])
            : JPColors.primaryGradient,
        borderRadius: BorderRadius.circular(12),
        boxShadow: _bloqueadoTemporalmente
            ? []
            : [
                BoxShadow(
                  color: JPColors.primary.withValues(alpha: 0.4),
                  blurRadius: 12,
                  offset: const Offset(0, 6),
                ),
              ],
      ),
      child: ElevatedButton(
        onPressed: (_loading || _bloqueadoTemporalmente) ? null : _login,
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
                    : 'Iniciar Sesión',
                style: const TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                  letterSpacing: 0.5,
                ),
              ),
      ),
    );
  }

  /// Texto de registro con "Crear cuenta" resaltado
  Widget _buildTextoRegistro() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const Text(
          '¿No tienes cuenta? ',
          style: TextStyle(color: JPColors.textSecondary, fontSize: 15),
        ),
        GestureDetector(
          onTap: _loading ? null : _irARegistro,
          child: AnimatedDefaultTextStyle(
            duration: const Duration(milliseconds: 200),
            style: TextStyle(
              color: _loading ? Colors.grey : JPColors.secondary,
              fontSize: 15,
              fontWeight: FontWeight.bold,
            ),
            child: const Text('Crear cuenta'),
          ),
        ),
      ],
    );
  }
}
