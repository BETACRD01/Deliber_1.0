import 'package:flutter/material.dart';
import './panel_registro_rol/registro_usuario_form.dart';

/// Pantalla de registro principal - JP Express
/// Selector de tipo de cuenta con animaciones mejoradas
class PantallaRegistro extends StatefulWidget {
  const PantallaRegistro({super.key});

  @override
  State<PantallaRegistro> createState() => _PantallaRegistroState();
}

class _PantallaRegistroState extends State<PantallaRegistro>
    with TickerProviderStateMixin {
  String _rolSeleccionado = 'USUARIO';
  late AnimationController _formController;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  static const Color _azulPrincipal = Color(0xFF4FC3F7);
  static const Color _azulOscuro = Color(0xFF0288D1);
  static const Color _naranja = Color(0xFFFF9800);

  final List<Map<String, dynamic>> _roles = [
    {
      'valor': 'USUARIO',
      'titulo': 'Usuario',
      'icono': Icons.person_rounded,
      'descripcion': 'Realiza pedidos',
      'color': Color(0xFF4FC3F7),
    },
  ];

  @override
  void initState() {
    super.initState();
    _initAnimations();
  }

  void _initAnimations() {
    _formController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 450),
    );

    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _formController,
        curve: const Interval(0.2, 1.0, curve: Curves.easeOut),
      ),
    );

    _slideAnimation =
        Tween<Offset>(begin: const Offset(0, 0.1), end: Offset.zero).animate(
          CurvedAnimation(parent: _formController, curve: Curves.easeOutCubic),
        );

    _formController.forward();
  }

  void _cambiarRol(String nuevoRol) {
    if (_rolSeleccionado != nuevoRol) {
      setState(() => _rolSeleccionado = nuevoRol);
      _formController.reset();
      _formController.forward();
    }
  }

  @override
  void dispose() {
    _formController.dispose();
    super.dispose();
  }

  Color _getCurrentColor() {
    return _roles.firstWhere(
      (r) => r['valor'] == _rolSeleccionado,
      orElse: () => _roles[0],
    )['color'];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              _azulPrincipal.withValues(alpha: 0.05),
              Colors.white,
              _getCurrentColor().withValues(alpha: 0.03),
            ],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              _buildAppBar(),
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: Column(
                    children: [
                      const SizedBox(height: 10),
                      _buildLogoAnimado(),
                      const SizedBox(height: 16),
                      _buildTitulo(),
                      const SizedBox(height: 20),
                      _buildSelectorRolCompacto(),
                      const SizedBox(height: 24),
                      _buildFormularioAnimado(),
                      const SizedBox(height: 16),
                      _buildTextoLogin(),
                      const SizedBox(height: 20),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ==================== APP BAR ====================
  Widget _buildAppBar() {
    return Padding(
      padding: const EdgeInsets.all(6),
      child: Row(
        children: [
          IconButton(
            icon: Icon(
              Icons.arrow_back_ios_new_rounded,
              color: _azulOscuro,
              size: 22,
            ),
            onPressed: () => Navigator.pop(context),
            tooltip: 'Volver',
          ),
        ],
      ),
    );
  }

  // ==================== LOGO ANIMADO ====================
  Widget _buildLogoAnimado() {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0.0, end: 1.0),
      duration: const Duration(milliseconds: 800),
      curve: Curves.elasticOut,
      builder: (context, value, child) {
        return Transform.scale(
          scale: value,
          child: Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: _getCurrentColor().withValues(alpha: 0.2),
                  blurRadius: 20,
                  spreadRadius: 2,
                ),
              ],
            ),
            child: Container(
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    _getCurrentColor().withValues(alpha: 0.15),
                    _getCurrentColor().withValues(alpha: 0.05),
                  ],
                ),
              ),
              child: ClipOval(
                child: Image.asset(
                  'assets/images/logo.gif',
                  height: 55,
                  width: 55,
                  fit: BoxFit.contain,
                  errorBuilder: (context, error, stackTrace) {
                    return Container(
                      height: 55,
                      width: 55,
                      decoration: BoxDecoration(
                        color: _getCurrentColor().withValues(alpha: 0.1),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        Icons.local_shipping_rounded,
                        size: 32,
                        color: _getCurrentColor(),
                      ),
                    );
                  },
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  // ==================== TÍTULO ====================
  Widget _buildTitulo() {
    return Column(
      children: [
        const Text(
          'Crear Cuenta',
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: Color(0xFF212121),
            letterSpacing: -0.5,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          'Únete a JP Express',
          style: TextStyle(
            fontSize: 13,
            color: Colors.grey[600],
            fontWeight: FontWeight.w400,
          ),
        ),
      ],
    );
  }

  // ==================== SELECTOR DE ROL COMPACTO ====================
  Widget _buildSelectorRolCompacto() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 4),
          child: Text(
            'Tipo de cuenta',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: Colors.grey[700],
              letterSpacing: 0.3,
            ),
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: _roles.asMap().entries.map((entry) {
            return Expanded(
              child: Padding(
                padding: EdgeInsets.only(
                  right: entry.key < _roles.length - 1 ? 10 : 0,
                ),
                child: _buildCardRolAnimado(entry.value),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  // ==================== CARD DE ROL ANIMADO ====================
  Widget _buildCardRolAnimado(Map<String, dynamic> rol) {
    final isSelected = _rolSeleccionado == rol['valor'];
    final color = rol['color'] as Color;

    return GestureDetector(
      onTap: () => _cambiarRol(rol['valor']),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 350),
        curve: Curves.easeOutCubic,
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected ? color.withValues(alpha: 0.15) : Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: isSelected ? color : Colors.grey[300]!,
            width: isSelected ? 2.5 : 1.5,
          ),
          boxShadow: [
            if (isSelected)
              BoxShadow(
                color: color.withValues(alpha: 0.3),
                blurRadius: 12,
                offset: const Offset(0, 4),
              ),
          ],
        ),
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            // Checkmark animado
            if (isSelected)
              Positioned(
                top: -4,
                right: -2,
                child: TweenAnimationBuilder<double>(
                  tween: Tween(begin: 0.0, end: 1.0),
                  duration: const Duration(milliseconds: 300),
                  curve: Curves.elasticOut,
                  builder: (context, value, child) {
                    return Transform.scale(
                      scale: value,
                      child: Container(
                        padding: const EdgeInsets.all(2.5),
                        decoration: BoxDecoration(
                          color: color,
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.check_rounded,
                          color: Colors.white,
                          size: 11,
                        ),
                      ),
                    );
                  },
                ),
              ),
            // Contenido
            Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                AnimatedContainer(
                  duration: const Duration(milliseconds: 300),
                  padding: const EdgeInsets.all(9),
                  decoration: BoxDecoration(
                    color: isSelected ? color : Colors.grey[200],
                    borderRadius: BorderRadius.circular(11),
                  ),
                  child: Icon(
                    rol['icono'],
                    color: isSelected ? Colors.white : Colors.grey[600],
                    size: 22,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  rol['titulo'],
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.bold,
                    color: isSelected ? color : Colors.grey[700],
                    height: 1,
                  ),
                  textAlign: TextAlign.center,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 3),
                Text(
                  rol['descripcion'],
                  style: TextStyle(
                    fontSize: 9,
                    color: Colors.grey[600],
                    height: 1.1,
                  ),
                  textAlign: TextAlign.center,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // ==================== FORMULARIO ANIMADO ====================
  Widget _buildFormularioAnimado() {
    return FadeTransition(
      opacity: _fadeAnimation,
      child: SlideTransition(
        position: _slideAnimation,
        child: _buildFormularioActual(),
      ),
    );
  }

  Widget _buildFormularioActual() {
    switch (_rolSeleccionado) {
      default:
        return RegistroUsuarioForm();
    }
  }

  // ==================== TEXTO LOGIN ====================
  Widget _buildTextoLogin() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          '¿Ya tienes cuenta? ',
          style: TextStyle(color: Colors.grey[600], fontSize: 13),
        ),
        GestureDetector(
          onTap: () => Navigator.pop(context),
          child: Text(
            'Iniciar sesión',
            style: TextStyle(
              color: _naranja,
              fontSize: 13,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ],
    );
  }
}
