// lib/screens/user/perfil/solicitudes_rol/pantalla_solicitar_rol.dart

import 'package:flutter/material.dart';
import '../../../../theme/jp_theme.dart';
import '../../../../models/solicitud_cambio_rol.dart';
import 'widgets/tarjeta_seleccion_rol.dart';
import 'widgets/formulario_proveedor.dart';
import 'widgets/formulario_repartidor.dart';

/// 🎯 PANTALLA PARA SOLICITAR CAMBIO DE ROL
/// Permite elegir entre Proveedor o Repartidor y llenar el formulario
class PantallaSolicitarRol extends StatefulWidget {
  final String? rolInicial; // 'PROVEEDOR' o 'REPARTIDOR'

  const PantallaSolicitarRol({super.key, this.rolInicial});

  @override
  State<PantallaSolicitarRol> createState() => _PantallaSolicitarRolState();
}

class _PantallaSolicitarRolState extends State<PantallaSolicitarRol> {
  // ══════════════════════════════════════════════════════════════════════════════
  // 📊 ESTADO
  // ══════════════════════════════════════════════════════════════════════════════

  String? _rolSeleccionado;
  final PageController _pageController = PageController();
  int _currentPage = 0;

  // ══════════════════════════════════════════════════════════════════════════════
  // 🔄 LIFECYCLE
  // ══════════════════════════════════════════════════════════════════════════════

  @override
  void initState() {
    super.initState();
    _rolSeleccionado = widget.rolInicial;

    // Si viene con rol inicial, avanzar automáticamente
    if (widget.rolInicial != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _avanzarAPagina(1);
      });
    }
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 🎨 BUILD
  // ══════════════════════════════════════════════════════════════════════════════

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: JPColors.background,
      appBar: _buildAppBar(),
      body: PageView(
        controller: _pageController,
        physics: const NeverScrollableScrollPhysics(),
        onPageChanged: (index) => setState(() => _currentPage = index),
        children: [_buildPaginaSeleccion(), _buildPaginaFormulario()],
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 📱 APP BAR
  // ══════════════════════════════════════════════════════════════════════════════

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      title: Text(
        _currentPage == 0 ? 'Selecciona tu rol' : 'Completa tu solicitud',
      ),
      backgroundColor: JPColors.primary,
      foregroundColor: Colors.white,
      elevation: 0,
    );
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 📄 PÁGINA 1: SELECCIÓN DE ROL
  // ══════════════════════════════════════════════════════════════════════════════

  Widget _buildPaginaSeleccion() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Título
          Text('¿Qué rol deseas?', style: JPTextStyles.h2),
          const SizedBox(height: 8),
          Text(
            'Elige el rol que mejor se adapte a lo que quieres hacer',
            style: JPTextStyles.bodySecondary,
          ),

          const SizedBox(height: 32),

          // Tarjeta PROVEEDOR
          TarjetaSeleccionRol(
            rol: RolSolicitable.proveedor,
            seleccionado: _rolSeleccionado == 'PROVEEDOR',
            onTap: () {
              setState(() => _rolSeleccionado = 'PROVEEDOR');
            },
          ),

          const SizedBox(height: 16),

          // Tarjeta REPARTIDOR
          TarjetaSeleccionRol(
            rol: RolSolicitable.repartidor,
            seleccionado: _rolSeleccionado == 'REPARTIDOR',
            onTap: () {
              setState(() => _rolSeleccionado = 'REPARTIDOR');
            },
          ),

          const SizedBox(height: 32),

          // Botón continuar
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _rolSeleccionado != null
                  ? () => _avanzarAPagina(1)
                  : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: JPColors.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.all(16),
                disabledBackgroundColor: Colors.grey.shade300,
              ),
              child: const Text(
                'Continuar',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 📄 PÁGINA 2: FORMULARIO
  // ══════════════════════════════════════════════════════════════════════════════

  Widget _buildPaginaFormulario() {
    if (_rolSeleccionado == null) {
      return const Center(child: Text('Selecciona un rol primero'));
    }

    return _rolSeleccionado == 'PROVEEDOR'
        ? FormularioProveedor(
            onSubmitSuccess: _handleSubmitSuccess,
            onBack: () => _avanzarAPagina(0),
          )
        : FormularioRepartidor(
            onSubmitSuccess: _handleSubmitSuccess,
            onBack: () => _avanzarAPagina(0),
          );
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 🎬 ACCIONES
  // ══════════════════════════════════════════════════════════════════════════════

  void _avanzarAPagina(int pagina) {
    _pageController.animateToPage(
      pagina,
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  void _handleSubmitSuccess() {
    Navigator.pop(context, true);
  }
}
