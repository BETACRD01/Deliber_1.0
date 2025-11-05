// lib/screens/auth/pantalla_verificar_codigo.dart

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../../services/auth_service.dart';
import '../../../config/rutas.dart';
import '../../../config/api_config.dart';
import '../../../apis/helpers/api_exception.dart';

/// Pantalla para verificar el código de 6 dígitos
/// ✅ Maneja rate limiting y bloqueos
class PantallaVerificarCodigo extends StatefulWidget {
  const PantallaVerificarCodigo({super.key});

  @override
  State<PantallaVerificarCodigo> createState() =>
      _PantallaVerificarCodigoState();
}

class _PantallaVerificarCodigoState extends State<PantallaVerificarCodigo> {
  // ============================================
  // CONTROLADORES
  // ============================================
  final List<TextEditingController> _controllers = List.generate(
    6,
    (_) => TextEditingController(),
  );
  final List<FocusNode> _focusNodes = List.generate(6, (_) => FocusNode());
  final _api = AuthService();

  // ============================================
  // ESTADO
  // ============================================
  String? _email;
  bool _loading = false;
  String? _error;
  int? _intentosRestantes;
  bool _bloqueado = false;

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
    for (var controller in _controllers) {
      controller.dispose();
    }
    for (var node in _focusNodes) {
      node.dispose();
    }
    super.dispose();
  }

  // ============================================
  // MÉTODOS
  // ============================================

  /// Obtiene el email de los argumentos de navegación
  void _obtenerArgumentos() {
    final args = Rutas.obtenerArgumentos<Map<String, dynamic>>(context);
    if (args != null && args.containsKey('email')) {
      setState(() {
        _email = args['email'] as String;
      });
      // Auto-focus en el primer campo
      _focusNodes[0].requestFocus();
    } else {
      // Si no hay email, volver atrás
      Navigator.pop(context);
    }
  }

  /// Obtiene el código completo de los 6 campos
  String _obtenerCodigo() {
    return _controllers.map((c) => c.text).join();
  }

  /// Verifica si el código está completo
  bool _codigoCompleto() {
    return _obtenerCodigo().length == 6;
  }

  /// ✅ Verifica el código con el backend
  Future<void> _verificarCodigo() async {
    if (!_codigoCompleto()) {
      setState(() => _error = 'Por favor ingresa los 6 dígitos');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final codigo = _obtenerCodigo();

      await _api.verificarCodigoRecuperacion(email: _email!, codigo: codigo);

      if (mounted) {
        // ✅ Código válido, ir a pantalla de nueva contraseña
        Rutas.irANuevaPassword(context, email: _email!, codigo: codigo);
      }
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          _error = e.message;
          _intentosRestantes = e.intentosRestantes;
          _bloqueado = e.isCuentaBloqueada || e.statusCode == 429;
          _loading = false;
        });

        // Si está bloqueado, mostrar diálogo
        if (_bloqueado) {
          _mostrarDialogoBloqueado(e);
        }
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

  /// Muestra diálogo de cuenta bloqueada
  void _mostrarDialogoBloqueado(ApiException error) {
    final tiempoEspera = error.retryAfter ?? 900; // 15 minutos por defecto

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
              child: Text('Código Bloqueado', style: TextStyle(fontSize: 18)),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Has excedido el número máximo de intentos para verificar el código.',
              style: TextStyle(fontSize: 15, color: Colors.grey[800]),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.orange[50],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.orange[300]!),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.schedule, color: Colors.orange[700], size: 20),
                      const SizedBox(width: 8),
                      Text(
                        'Tiempo de espera:',
                        style: TextStyle(
                          color: Colors.orange[900],
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    AuthService.formatearTiempoEspera(tiempoEspera),
                    style: TextStyle(
                      color: Colors.orange[900],
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'Por seguridad, deberás solicitar un nuevo código después de este tiempo.',
              style: TextStyle(fontSize: 13, color: Colors.grey[600]),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context); // Cerrar diálogo
              Navigator.pop(context); // Volver a recuperar password
            },
            child: const Text('Volver'),
          ),
        ],
      ),
    );
  }

  /// Solicita un nuevo código
  Future<void> _solicitarNuevoCodigo() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      await _api.solicitarCodigoRecuperacion(email: _email!);

      if (mounted) {
        setState(() => _loading = false);

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Nuevo código enviado a tu email'),
            backgroundColor: Colors.green,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
          ),
        );

        // Limpiar campos
        for (var controller in _controllers) {
          controller.clear();
        }
        _focusNodes[0].requestFocus();
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
          _error = 'Error al enviar nuevo código';
          _loading = false;
        });
      }
    }
  }

  /// Maneja el cambio de texto en los campos
  void _onChanged(int index, String value) {
    if (value.length == 1 && index < 5) {
      // Avanzar al siguiente campo
      _focusNodes[index + 1].requestFocus();
    } else if (value.isEmpty && index > 0) {
      // Retroceder al campo anterior
      _focusNodes[index - 1].requestFocus();
    }

    // Si el código está completo, verificar automáticamente
    if (_codigoCompleto() && !_loading) {
      _verificarCodigo();
    }

    setState(() {}); // Actualizar UI
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
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: _azulOscuro),
          onPressed: () => Navigator.pop(context),
        ),
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
                    child: Icon(
                      Icons.verified_user,
                      size: 80,
                      color: _azulPrincipal,
                    ),
                  ),
                  const SizedBox(height: 32),

                  // Título
                  const Text(
                    'Verificar Código',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF212121),
                    ),
                  ),
                  const SizedBox(height: 12),

                  // Descripción
                  if (_email != null)
                    Text(
                      'Ingresa el código de 6 dígitos que enviamos a\n$_email',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 15,
                        color: Colors.grey[600],
                        height: 1.5,
                      ),
                    ),
                  const SizedBox(height: 40),

                  // Campos de código
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: List.generate(6, (index) {
                      return Container(
                        width: 50,
                        height: 60,
                        margin: const EdgeInsets.symmetric(horizontal: 4),
                        child: TextField(
                          controller: _controllers[index],
                          focusNode: _focusNodes[index],
                          enabled: !_loading && !_bloqueado,
                          textAlign: TextAlign.center,
                          keyboardType: TextInputType.number,
                          maxLength: 1,
                          style: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                          inputFormatters: [
                            FilteringTextInputFormatter.digitsOnly,
                          ],
                          decoration: InputDecoration(
                            counterText: '',
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                            enabledBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                              borderSide: BorderSide(
                                color: Colors.grey[300]!,
                                width: 2,
                              ),
                            ),
                            focusedBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                              borderSide: BorderSide(
                                color: _azulPrincipal,
                                width: 2,
                              ),
                            ),
                            filled: true,
                            fillColor: _bloqueado
                                ? Colors.grey[100]
                                : Colors.white,
                          ),
                          onChanged: (value) => _onChanged(index, value),
                        ),
                      );
                    }),
                  ),

                  const SizedBox(height: 24),

                  // Mensaje de error
                  if (_error != null) ...[
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.red[50],
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.red[300]!, width: 1),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            Icons.error_outline,
                            color: Colors.red[700],
                            size: 20,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _error!,
                              style: TextStyle(
                                color: Colors.red[700],
                                fontSize: 14,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),
                  ],

                  // ✅ Intentos restantes
                  if (_intentosRestantes != null &&
                      _intentosRestantes! > 0) ...[
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.amber[50],
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.amber[300]!, width: 1),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            Icons.warning_amber,
                            color: Colors.amber[700],
                            size: 20,
                          ),
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
                    const SizedBox(height: 12),
                  ],

                  // Info de expiración
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.blue[50],
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: Colors.blue[200]!, width: 1),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.info_outline,
                          color: Colors.blue[700],
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'El código expira en ${ApiConfig.codigoExpiracionMinutos} minutos',
                            style: TextStyle(
                              color: Colors.blue[700],
                              fontSize: 13,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 28),

                  // Botón verificar (manual)
                  if (!_loading)
                    Container(
                      height: 54,
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: _codigoCompleto() && !_bloqueado
                              ? [_azulPrincipal, _azulOscuro]
                              : [Colors.grey[300]!, Colors.grey[400]!],
                        ),
                        borderRadius: BorderRadius.circular(12),
                        boxShadow: _codigoCompleto() && !_bloqueado
                            ? [
                                BoxShadow(
                                  color: _azulPrincipal.withValues(alpha: 0.4),
                                  blurRadius: 12,
                                  offset: const Offset(0, 6),
                                ),
                              ]
                            : [],
                      ),
                      child: ElevatedButton(
                        onPressed: _codigoCompleto() && !_bloqueado
                            ? _verificarCodigo
                            : null,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.transparent,
                          shadowColor: Colors.transparent,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        child: const Text(
                          'Verificar Código',
                          style: TextStyle(
                            fontSize: 17,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                            letterSpacing: 0.5,
                          ),
                        ),
                      ),
                    ),

                  // Indicador de carga
                  if (_loading) ...[
                    const Center(child: CircularProgressIndicator()),
                    const SizedBox(height: 16),
                    Text(
                      'Verificando código...',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey[600]),
                    ),
                  ],

                  const SizedBox(height: 20),

                  // Botón solicitar nuevo código
                  TextButton(
                    onPressed: (_loading || _bloqueado)
                        ? null
                        : _solicitarNuevoCodigo,
                    child: Text(
                      '¿No recibiste el código? Solicitar uno nuevo',
                      style: TextStyle(
                        color: (_loading || _bloqueado)
                            ? Colors.grey
                            : _azulOscuro,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
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
