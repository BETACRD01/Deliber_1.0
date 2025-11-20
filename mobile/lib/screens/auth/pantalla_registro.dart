import 'package:flutter/material.dart';
import './panel_registro_rol/registro_usuario_form.dart';

/// Pantalla de registro simplificada - JP Express
class PantallaRegistro extends StatelessWidget {
  const PantallaRegistro({super.key});

  static const Color _grisOscuro = Color(0xFF2C2C2C);
  static const Color _grisTexto = Color(0xFF666666);
  static const Color _grisClaro = Color(0xFFE0E0E0);
  static const Color _acento = Color(0xFF5A5A5A);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            _buildAppBar(context),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Column(
                  children: [
                    const SizedBox(height: 40),
                    _buildLogo(),
                    const SizedBox(height: 32),
                    _buildTitulo(),
                    const SizedBox(height: 40),
                    const RegistroUsuarioForm(),
                    const SizedBox(height: 24),
                    _buildTextoLogin(context),
                    const SizedBox(height: 32),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAppBar(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(8),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(
              Icons.arrow_back_ios_new_rounded,
              color: _grisOscuro,
              size: 20,
            ),
            onPressed: () => Navigator.pop(context),
          ),
        ],
      ),
    );
  }

  Widget _buildLogo() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFF5F5F5),
        shape: BoxShape.circle,
        border: Border.all(
          color: _grisClaro,
          width: 1,
        ),
      ),
      child: Image.asset(
        'assets/images/logo.gif',
        height: 50,
        width: 50,
        fit: BoxFit.contain,
        errorBuilder: (context, error, stackTrace) {
          return const Icon(
            Icons.local_shipping_rounded,
            size: 50,
            color: _acento,
          );
        },
      ),
    );
  }

  Widget _buildTitulo() {
    return Column(
      children: [
        const Text(
          'Crear Cuenta',
          style: TextStyle(
            fontSize: 28,
            fontWeight: FontWeight.w600,
            color: _grisOscuro,
            letterSpacing: -0.5,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Completa los datos para registrarte',
          style: TextStyle(
            fontSize: 14,
            color: _grisTexto,
            fontWeight: FontWeight.w400,
          ),
        ),
      ],
    );
  }

  Widget _buildTextoLogin(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          '¿Ya tienes cuenta? ',
          style: TextStyle(
            color: _grisTexto,
            fontSize: 14,
          ),
        ),
        GestureDetector(
          onTap: () => Navigator.pop(context),
          child: const Text(
            'Iniciar sesión',
            style: TextStyle(
              color: _grisOscuro,
              fontSize: 14,
              fontWeight: FontWeight.w600,
              decoration: TextDecoration.underline,
            ),
          ),
        ),
      ],
    );
  }
}