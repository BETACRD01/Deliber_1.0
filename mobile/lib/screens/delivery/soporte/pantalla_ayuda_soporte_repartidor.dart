// lib/screens/delivery/pantalla_ayuda_soporte_repartidor.dart

import 'package:flutter/material.dart';

/// 🧰 Pantalla de Ayuda y Soporte para Repartidor
/// Incluye contacto directo, preguntas frecuentes y botón de soporte
class PantallaAyudaSoporteRepartidor extends StatelessWidget {
  const PantallaAyudaSoporteRepartidor({super.key});

  // Colores base (coherentes con tu estilo)
  static const Color _naranja = Color(0xFFFF9800);
  static const Color _verde = Color(0xFF4CAF50);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Ayuda y Soporte'),
        backgroundColor: _naranja,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(),
            const SizedBox(height: 24),
            _buildSeccionContacto(),
            const SizedBox(height: 24),
            _buildSeccionFAQ(),
            const SizedBox(height: 32),
            _buildBotonSoporte(context),
          ],
        ),
      ),
    );
  }

  // ==========================================================
  // ENCABEZADO
  // ==========================================================
  Widget _buildHeader() {
    return Row(
      children: [
        Icon(Icons.support_agent, size: 48, color: _naranja),
        const SizedBox(width: 12),
        const Expanded(
          child: Text(
            '¿Necesitas ayuda?',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
        ),
      ],
    );
  }

  // ==========================================================
  // CONTACTO DIRECTO
  // ==========================================================
  Widget _buildSeccionContacto() {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '📞 Contacto Directo',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 8),
            ListTile(
              leading: const Icon(Icons.phone, color: _verde),
              title: const Text('Línea de Soporte'),
              subtitle: const Text('+593 98 765 4321'),
              onTap: () {
                // Aquí podrías integrar un plugin de llamadas o WhatsApp
              },
            ),
            ListTile(
              leading: const Icon(Icons.email, color: _naranja),
              title: const Text('Correo de Soporte'),
              subtitle: const Text('soporte@deliberapp.com'),
              onTap: () {
                // Aquí puedes abrir el correo con url_launcher
              },
            ),
          ],
        ),
      ),
    );
  }

  // ==========================================================
  // PREGUNTAS FRECUENTES
  // ==========================================================
  Widget _buildSeccionFAQ() {
    final faqs = [
      {
        'pregunta': '¿Cómo acepto un pedido?',
        'respuesta':
            'Cuando estés disponible, los pedidos cercanos aparecerán en el mapa. Solo selecciona uno y presiona “Aceptar pedido”.',
      },
      {
        'pregunta': '¿Qué hago si no puedo completar una entrega?',
        'respuesta':
            'Debes informar al soporte mediante la opción “Reportar problema” dentro del pedido en curso.',
      },
      {
        'pregunta': '¿Cómo cambio mi estado de disponibilidad?',
        'respuesta':
            'En el menú lateral (Drawer), usa el botón para activar o desactivar tu disponibilidad.',
      },
      {
        'pregunta': '¿Cómo actualizo mi perfil?',
        'respuesta':
            'Desde la sección “Perfil”, puedes editar tu foto, vehículo y datos personales.',
      },
    ];

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ExpansionPanelList.radio(
        animationDuration: const Duration(milliseconds: 300),
        elevation: 0,
        expandedHeaderPadding: const EdgeInsets.symmetric(vertical: 0),
        children: faqs
            .map(
              (faq) => ExpansionPanelRadio(
                value: faq['pregunta']!,
                headerBuilder: (context, isExpanded) {
                  return ListTile(
                    title: Text(
                      faq['pregunta']!,
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                  );
                },
                body: Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                  child: Text(
                    faq['respuesta']!,
                    style: TextStyle(color: Colors.grey[700]),
                  ),
                ),
              ),
            )
            .toList(),
      ),
    );
  }

  // ==========================================================
  // BOTÓN DE SOPORTE
  // ==========================================================
  Widget _buildBotonSoporte(BuildContext context) {
    return Center(
      child: ElevatedButton.icon(
        icon: const Icon(Icons.chat),
        label: const Text('Contactar Soporte'),
        style: ElevatedButton.styleFrom(
          backgroundColor: _naranja,
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(30),
          ),
          elevation: 4,
        ),
        onPressed: () {
          showDialog(
            context: context,
            builder: (_) => AlertDialog(
              title: const Text('Soporte en Línea'),
              content: const Text(
                'Puedes contactar con soporte a través de WhatsApp o correo.\n\nWhatsApp: +593 98 765 4321\nCorreo: soporte@deliberapp.com',
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Cerrar'),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
