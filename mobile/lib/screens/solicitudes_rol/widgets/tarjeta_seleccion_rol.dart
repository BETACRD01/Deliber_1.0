// lib/screens/user/perfil/solicitudes_rol/widgets/tarjeta_seleccion_rol.dart

import 'package:flutter/material.dart';
import '../../../../../theme/jp_theme.dart';
import '../../../../../models/solicitud_cambio_rol.dart';

/// 🎴 TARJETA PARA SELECCIONAR ROL
class TarjetaSeleccionRol extends StatelessWidget {
  final RolSolicitable rol;
  final bool seleccionado;
  final VoidCallback onTap;

  const TarjetaSeleccionRol({
    super.key,
    required this.rol,
    required this.seleccionado,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final color = rol == RolSolicitable.proveedor
        ? JPColors.secondary
        : JPColors.info;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: seleccionado ? color.withValues(alpha: 0.1) : Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: seleccionado ? color : Colors.grey.shade300,
            width: seleccionado ? 3 : 1,
          ),
          boxShadow: seleccionado
              ? [
                  BoxShadow(
                    color: color.withValues(alpha: 0.3),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ]
              : [],
        ),
        child: Row(
          children: [
            // Icono
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(rol.icon, color: color, size: 40),
            ),

            const SizedBox(width: 20),

            // Información
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    rol.label,
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: seleccionado ? color : JPColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(_getDescripcion(rol), style: JPTextStyles.caption),
                  const SizedBox(height: 12),
                  _buildBeneficios(rol, color),
                ],
              ),
            ),

            // Checkbox
            if (seleccionado)
              Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(color: color, shape: BoxShape.circle),
                child: const Icon(Icons.check, color: Colors.white, size: 20),
              )
            else
              Container(
                width: 28,
                height: 28,
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey.shade400, width: 2),
                  shape: BoxShape.circle,
                ),
              ),
          ],
        ),
      ),
    );
  }

  String _getDescripcion(RolSolicitable rol) {
    return rol == RolSolicitable.proveedor
        ? 'Vende tus productos a través de la plataforma'
        : 'Entrega pedidos y gana por cada entrega';
  }

  Widget _buildBeneficios(RolSolicitable rol, Color color) {
    final beneficios = rol == RolSolicitable.proveedor
        ? [
            '📦 Gestiona tu catálogo',
            '💰 Recibe pagos seguros',
            '📊 Reportes de ventas',
          ]
        : ['🚴 Horarios flexibles', '💵 Gana por entrega', '📍 Elige tu zona'];

    return Wrap(
      spacing: 8,
      runSpacing: 4,
      children: beneficios.map((beneficio) {
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            beneficio,
            style: TextStyle(
              color: color,
              fontSize: 11,
              fontWeight: FontWeight.w500,
            ),
          ),
        );
      }).toList(),
    );
  }
}
