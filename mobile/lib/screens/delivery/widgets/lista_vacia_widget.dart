// lib/screens/delivery/widgets/lista_vacia_widget.dart

import 'package:flutter/material.dart';

/// 📭 Widget reutilizable para mostrar estados vacíos
/// Muestra ícono, mensaje y opcionalmente un botón de acción
class ListaVaciaWidget extends StatelessWidget {
  final IconData icono;
  final String mensaje;
  final String submensaje;
  final Widget? accionBoton;
  final Color? colorIcono;
  final double? tamanoIcono;

  const ListaVaciaWidget({
    super.key,
    required this.icono,
    required this.mensaje,
    required this.submensaje,
    this.accionBoton,
    this.colorIcono,
    this.tamanoIcono,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icono,
              size: tamanoIcono ?? 80,
              color: colorIcono ?? Colors.grey[300],
            ),
            const SizedBox(height: 16),
            Text(
              mensaje,
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.grey[700],
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              submensaje,
              style: TextStyle(fontSize: 14, color: Colors.grey[500]),
              textAlign: TextAlign.center,
            ),
            if (accionBoton != null) ...[
              const SizedBox(height: 24),
              accionBoton!,
            ],
          ],
        ),
      ),
    );
  }
}
