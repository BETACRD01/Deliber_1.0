// lib/screens/auth/pantalla_login.dart

import 'package:flutter/material.dart';
import '../../theme/jp_theme.dart';
import '../../services/auth_service.dart';
import './pantalla_registro.dart';
import './pantalla_recuperar_password.dart';
import '../../apis/helpers/api_exception.dart';
import '../pantalla_router.dart';

/// Pantalla de inicio de sesión - JP Express
/// Refactorizada: UI Limpia, Modular y SIN SCROLL
class PantallaLogin extends StatefulWidget {
  const PantallaLogin({super.key});

  @override
  State<PantallaLogin> createState() => _PantallaLoginState();
}

class _PantallaLoginState extends State<PantallaLogin> {
  // ============================================
  // DEPENDENCIAS Y ESTADO
  // ============================================
  final _usuarioController = TextEditingController();
  final _passwordController = TextEditingController();
  final _api = AuthService();

  bool _loading = false;
  bool _obscurePassword = true;
  String? _error;

  // Rate Limiting
  int? _intentosRestantes;
  int? _tiempoEspera;
  bool _bloqueadoTemporalmente = false;

  @override
  void dispose() {
    _usuarioController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  // ============================================
  // LÓGICA DE NEGOCIO
  // ============================================

  Future<void> _login() async {
    if (_usuarioController.text.isEmpty || _passwordController.text.isEmpty) {
      _mostrarError('Por favor completa todos los campos');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
      _intentosRestantes = null;
    });

    try {
      await _api.login(
        email: _usuarioController.text.trim(),
        password: _passwordController.text,
      );

      debugPrint('🔐 LOGIN EXITOSO');
      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const PantallaRouter()),
        );
      }
    } on ApiException catch (e) {
      if (!mounted) return;
      _manejarErrorApi(e);
    } catch (e) {
      if (mounted) _mostrarError('Error de conexión con el servidor');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _manejarErrorApi(ApiException e) {
    setState(() {
      if (e.statusCode == 429) {
        _bloqueadoTemporalmente = true;
        _tiempoEspera = e.details?['retry_after'];
        _error = e.message;
        _mostrarDialogoBloqueado();
      } else if (e.statusCode == 400) {
        _intentosRestantes = e.details?['intentos_restantes'];
        _error = e.message;
        if (_intentosRestantes != null && _intentosRestantes! <= 5) {
          JPSnackbar.show(context, '⚠️ Quedan $_intentosRestantes intentos', isError: true);
        }
      } else {
        _error = e.message;
      }
    });
  }

  void _mostrarError(String mensaje) {
    setState(() => _error = mensaje);
  }

  void _mostrarDialogoBloqueado() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => _DialogoBloqueo(
        tiempoEspera: _tiempoEspera,
        onRecuperar: () {
          Navigator.pop(context);
          Navigator.push(context, MaterialPageRoute(builder: (_) => const PantallaRecuperarPassword()));
        },
      ),
    );
  }

  // ============================================
  // UI PRINCIPAL SIN SCROLL
  // ============================================

  @override
  Widget build(BuildContext context) {
    // Reducir márgenes para pantallas pequeñas
    final double verticalPadding = MediaQuery.of(context).size.height * 0.02;
    final double horizontalPadding = MediaQuery.of(context).size.width * 0.08;

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: horizontalPadding, vertical: verticalPadding),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 450),
              child: Column(
                // Ocupar todo el espacio disponible y distribuirlo
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const _HeaderLogoPersonalizado(), // Logo y título
                  
                  // Formulario
                  _InputCampo(
                    controller: _usuarioController,
                    label: 'Usuario o Email',
                    icon: Icons.person_outline,
                    enabled: !_loading && !_bloqueadoTemporalmente,
                  ),
                  const SizedBox(height: 12), // Espacio reducido
                  _InputPassword(
                    controller: _passwordController,
                    obscureText: _obscurePassword,
                    onToggleVisibility: () => setState(() => _obscurePassword = !_obscurePassword),
                    enabled: !_loading && !_bloqueadoTemporalmente,
                  ),
                  
                  // Mensajes de estado
                  if (_error != null) _MensajeError(mensaje: _error!),
                  if (_intentosRestantes != null) 
                    _BadgeIntentos(intentos: _intentosRestantes!),

                  const SizedBox(height: 8), // Espacio reducido
                  _OpcionRecuperar(
                    enabled: !_loading && !_bloqueadoTemporalmente,
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PantallaRecuperarPassword())),
                  ),
                  
                  const SizedBox(height: 24), // Espacio reducido
                  _BotonLogin(
                    loading: _loading,
                    bloqueado: _bloqueadoTemporalmente,
                    onPressed: _login,
                  ),

                  // Separadores y botones sociales, ahora más compactos
                  const SizedBox(height: 24),
                  const _DivisorSocial(),
                  const SizedBox(height: 16),
                  const _BotonesRedesSociales(),
                  
                  // Footer de registro (más compacto)
                  const SizedBox(height: 24),
                  _FooterRegistro(
                    enabled: !_loading,
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PantallaRegistro())),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// ============================================
// WIDGETS FACTORIZADOS (PRIVADOS)
// ============================================

/// Encabezado con Logo Personalizado y Título (SIN ANIMACIÓN NI HERO)
class _HeaderLogoPersonalizado extends StatelessWidget {
  const _HeaderLogoPersonalizado();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // La imagen que has proporcionado
        Container(
          height: 80, // Tamaño reducido para que quepa todo
          width: 80,
          decoration: BoxDecoration(
            color: JPColors.primary.withValues(alpha: 0.05),
            shape: BoxShape.circle,
          ),
          padding: const EdgeInsets.all(8), // Padding reducido
          child: Image.asset(
            'assets/icon/logo.png', // Tu ruta de imagen
            fit: BoxFit.contain,
            errorBuilder: (_, __, ___) => const Icon(Icons.local_shipping, size: 40, color: JPColors.primary),
          ),
        ),
        const SizedBox(height: 16), // Espacio reducido
        Text(
          'JP Express',
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.w800,
                color: JPColors.textPrimary,
                fontSize: 28, // Tamaño de fuente ajustado
              ),
        ),
        const SizedBox(height: 4), // Espacio reducido
        Text(
          'Bienvenido de nuevo',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: JPColors.textSecondary,
                fontSize: 14, // Tamaño de fuente ajustado
              ),
        ),
        const SizedBox(height: 24), // Espacio para separar del formulario
      ],
    );
  }
}

/// Input Genérico Limpio
class _InputCampo extends StatelessWidget {
  final TextEditingController controller;
  final String label;
  final IconData icon;
  final bool enabled;

  const _InputCampo({
    required this.controller,
    required this.label,
    required this.icon,
    this.enabled = true,
  });

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      enabled: enabled,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, size: 20), // Icono más pequeño
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none), // Radio más pequeño
        filled: true,
        fillColor: Colors.grey[100],
        contentPadding: const EdgeInsets.symmetric(vertical: 14, horizontal: 18), // Padding reducido
      ),
    );
  }
}

/// Input de Password Específico
class _InputPassword extends StatelessWidget {
  final TextEditingController controller;
  final bool obscureText;
  final VoidCallback onToggleVisibility;
  final bool enabled;

  const _InputPassword({
    required this.controller,
    required this.obscureText,
    required this.onToggleVisibility,
    this.enabled = true,
  });

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      obscureText: obscureText,
      enabled: enabled,
      decoration: InputDecoration(
        labelText: 'Contraseña',
        prefixIcon: const Icon(Icons.lock_outline, size: 20), // Icono más pequeño
        suffixIcon: IconButton(
          icon: Icon(obscureText ? Icons.visibility_off : Icons.visibility, size: 20), // Icono más pequeño
          onPressed: onToggleVisibility,
        ),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none), // Radio más pequeño
        filled: true,
        fillColor: Colors.grey[100],
        contentPadding: const EdgeInsets.symmetric(vertical: 14, horizontal: 18), // Padding reducido
      ),
    );
  }
}

/// Botón de Login Principal
class _BotonLogin extends StatelessWidget {
  final bool loading;
  final bool bloqueado;
  final VoidCallback onPressed;

  const _BotonLogin({
    required this.loading,
    required this.bloqueado,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 50, // Altura reducida
      child: ElevatedButton(
        onPressed: (loading || bloqueado) ? null : onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: JPColors.primary,
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)), // Radio más pequeño
        ),
        child: loading
            ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) // Tamaño reducido
            : Text(
                bloqueado ? 'Cuenta Bloqueada' : 'Iniciar Sesión',
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white), // Tamaño de fuente ajustado
              ),
      ),
    );
  }
}

/// Enlace de Recuperación de Contraseña
class _OpcionRecuperar extends StatelessWidget {
  final bool enabled;
  final VoidCallback onTap;

  const _OpcionRecuperar({required this.enabled, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerRight,
      child: TextButton(
        onPressed: enabled ? onTap : null,
        style: TextButton.styleFrom(
          padding: EdgeInsets.zero, // Eliminar padding extra
          minimumSize: const Size(0, 0), // Eliminar tamaño mínimo
          tapTargetSize: MaterialTapTargetSize.shrinkWrap, // Ajustar área de toque
        ),
        child: const Text(
          '¿Olvidaste tu contraseña?',
          style: TextStyle(color: JPColors.primary, fontWeight: FontWeight.w600, fontSize: 13), // Tamaño de fuente ajustado
        ),
      ),
    );
  }
}

/// Badge de Intentos Restantes
class _BadgeIntentos extends StatelessWidget {
  final int intentos;

  const _BadgeIntentos({required this.intentos});

  @override
  Widget build(BuildContext context) {
    final color = intentos <= 2 ? JPColors.error : JPColors.warning;
    return Container(
      margin: const EdgeInsets.only(top: 6), // Margen reducido
      padding: const EdgeInsets.all(6), // Padding reducido
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(6), // Radio reducido
      ),
      child: Row(
        children: [
          Icon(Icons.info_outline, size: 14, color: color), // Icono más pequeño
          const SizedBox(width: 6), // Espacio reducido
          Text('Intentos restantes: $intentos', style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 11)), // Fuente más pequeña
        ],
      ),
    );
  }
}

/// Mensaje de Error Estilizado
class _MensajeError extends StatelessWidget {
  final String mensaje;

  const _MensajeError({required this.mensaje});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 10), // Padding reducido
      child: Text(
        mensaje,
        style: const TextStyle(color: JPColors.error, fontSize: 12, fontWeight: FontWeight.w500), // Fuente más pequeña
        textAlign: TextAlign.center,
      ),
    );
  }
}

/// Divisor de secciones
class _DivisorSocial extends StatelessWidget {
  const _DivisorSocial();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Expanded(child: Divider()),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12), // Padding reducido
          child: Text('O continúa con', style: TextStyle(color: Colors.grey[500], fontSize: 11)), // Fuente más pequeña
        ),
        const Expanded(child: Divider()),
      ],
    );
  }
}

/// Botones de Redes Sociales
class _BotonesRedesSociales extends StatelessWidget {
  const _BotonesRedesSociales();

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        _SocialIconBtn(icon: Icons.g_mobiledata, color: const Color(0xFFDB4437), onTap: () {}),
        const SizedBox(width: 16), // Espacio reducido
        _SocialIconBtn(icon: Icons.facebook, color: const Color(0xFF1877F2), onTap: () {}),
        const SizedBox(width: 16), // Espacio reducido
        _SocialIconBtn(icon: Icons.apple, color: Colors.black, onTap: () {}),
      ],
    );
  }
}

class _SocialIconBtn extends StatelessWidget {
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _SocialIconBtn({required this.icon, required this.color, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(50),
      child: Container(
        padding: const EdgeInsets.all(10), // Padding reducido
        decoration: BoxDecoration(
          border: Border.all(color: Colors.grey[200]!),
          shape: BoxShape.circle,
          color: Colors.white,
        ),
        child: Icon(icon, color: color, size: 24), // Icono más pequeño
      ),
    );
  }
}

/// Footer para ir a Registro
class _FooterRegistro extends StatelessWidget {
  final bool enabled;
  final VoidCallback onTap;

  const _FooterRegistro({required this.enabled, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const Text('¿No tienes cuenta? ', style: TextStyle(color: JPColors.textSecondary, fontSize: 13)), // Fuente más pequeña
        GestureDetector(
          onTap: enabled ? onTap : null,
          child: const Text('Crear cuenta', style: TextStyle(color: JPColors.secondary, fontWeight: FontWeight.bold, fontSize: 13)), // Fuente más pequeña
        ),
      ],
    );
  }
}

/// Diálogo Específico para Bloqueo (sin cambios significativos en tamaño)
class _DialogoBloqueo extends StatelessWidget {
  final int? tiempoEspera;
  final VoidCallback onRecuperar;

  const _DialogoBloqueo({this.tiempoEspera, required this.onRecuperar});

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      title: const Row(
        children: [Icon(Icons.block, color: JPColors.error), SizedBox(width: 10), Text('Acceso Bloqueado')],
      ),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Has excedido el número de intentos permitidos.'),
          if (tiempoEspera != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: Colors.orange[50], borderRadius: BorderRadius.circular(8)),
              child: Text('Espera $tiempoEspera segundos.', style: const TextStyle(color: Colors.orange, fontWeight: FontWeight.bold)),
            )
          ]
        ],
      ),
      actions: [
        TextButton(onPressed: onRecuperar, child: const Text('Recuperar Password')),
        ElevatedButton(
          onPressed: () => Navigator.pop(context),
          style: ElevatedButton.styleFrom(backgroundColor: JPColors.primary),
          child: const Text('Entendido'),
        ),
      ],
    );
  }
}