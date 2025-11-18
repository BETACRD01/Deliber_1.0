// lib/screens/delivery/configuracion/pantalla_configuracion_repartidor.dart

import 'package:flutter/material.dart';

/// ⚙️ Pantalla de Configuración del Repartidor
/// Permite ajustar notificaciones, preferencias y datos de la app
class PantallaConfiguracionRepartidor extends StatefulWidget {
  const PantallaConfiguracionRepartidor({super.key});

  @override
  State<PantallaConfiguracionRepartidor> createState() =>
      _PantallaConfiguracionRepartidorState();
}

class _PantallaConfiguracionRepartidorState
    extends State<PantallaConfiguracionRepartidor> {
  // ==========================================================
  // COLORES BASE
  // ==========================================================
  static const Color _naranja = Color(0xFFFF9800);
  static const Color _verde = Color(0xFF4CAF50);
  static const Color _rojo = Color(0xFFF44336);

  // ==========================================================
  // ESTADOS DE CONFIGURACIÓN
  // ==========================================================
  bool notificacionesActivas = true;
  bool modoOscuro = false;
  bool ubicacionEnTiempoReal = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Configuración'),
        backgroundColor: _naranja,
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildSeccionGeneral(),
          const SizedBox(height: 16),
          _buildSeccionPreferencias(),
          const SizedBox(height: 16),
          _buildSeccionSoporte(),
          const SizedBox(height: 16),
          _buildBotonRestablecer(),
        ],
      ),
    );
  }

  // ==========================================================
  // SECCIÓN: CONFIGURACIÓN GENERAL
  // ==========================================================
  Widget _buildSeccionGeneral() {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      elevation: 2,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildTituloSeccion('General'),
          SwitchListTile(
            title: const Text('Notificaciones'),
            subtitle: const Text('Recibir alertas de nuevos pedidos'),
            activeThumbColor: _verde,
            value: notificacionesActivas,
            onChanged: (v) {
              setState(() => notificacionesActivas = v);
            },
          ),
          SwitchListTile(
            title: const Text('Modo oscuro'),
            subtitle: const Text('Usar tema oscuro en la aplicación'),
            activeThumbColor: _verde,
            value: modoOscuro,
            onChanged: (v) {
              setState(() => modoOscuro = v);
            },
          ),
          SwitchListTile(
            title: const Text('Ubicación en tiempo real'),
            subtitle: const Text('Actualizar tu posición automáticamente'),
            activeThumbColor: _verde,
            value: ubicacionEnTiempoReal,
            onChanged: (v) {
              setState(() => ubicacionEnTiempoReal = v);
            },
          ),
        ],
      ),
    );
  }

  // ==========================================================
  // SECCIÓN: PREFERENCIAS DE APLICACIÓN
  // ==========================================================
  Widget _buildSeccionPreferencias() {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      elevation: 2,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildTituloSeccion('Preferencias'),
          ListTile(
            leading: const Icon(Icons.language, color: _naranja),
            title: const Text('Idioma'),
            subtitle: const Text('Español (predeterminado)'),
            onTap: () {
              _mostrarDialogoIdioma(context);
            },
          ),
          ListTile(
            leading: const Icon(Icons.notifications_active, color: _naranja),
            title: const Text('Sonido de notificaciones'),
            subtitle: const Text('Predeterminado'),
            onTap: () {
              _mostrarDialogoSonido(context);
            },
          ),
          ListTile(
            leading: const Icon(Icons.palette, color: _naranja),
            title: const Text('Tema de aplicación'),
            subtitle: Text(modoOscuro ? 'Oscuro' : 'Claro'),
            onTap: () {
              setState(() => modoOscuro = !modoOscuro);
            },
          ),
        ],
      ),
    );
  }

  // ==========================================================
  // SECCIÓN: SOPORTE Y PRIVACIDAD
  // ==========================================================
  Widget _buildSeccionSoporte() {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      elevation: 2,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildTituloSeccion('Soporte y Privacidad'),
          ListTile(
            leading: const Icon(Icons.privacy_tip, color: _verde),
            title: const Text('Política de Privacidad'),
            onTap: () {
              _mostrarDialogoBasico(
                context,
                'Política de Privacidad',
                'Tu información personal se mantiene segura y solo se usa para mejorar el servicio de entrega.',
              );
            },
          ),
          ListTile(
            leading: const Icon(Icons.description, color: _verde),
            title: const Text('Términos del Servicio'),
            onTap: () {
              _mostrarDialogoBasico(
                context,
                'Términos del Servicio',
                'Al usar esta aplicación, aceptas cumplir las políticas y reglas establecidas para repartidores.',
              );
            },
          ),
        ],
      ),
    );
  }

  // ==========================================================
  // BOTÓN DE RESTABLECER
  // ==========================================================
  Widget _buildBotonRestablecer() {
    return Center(
      child: ElevatedButton.icon(
        icon: const Icon(Icons.restart_alt),
        label: const Text('Restablecer configuración'),
        style: ElevatedButton.styleFrom(
          backgroundColor: _rojo,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(30),
          ),
        ),
        onPressed: () {
          setState(() {
            notificacionesActivas = true;
            modoOscuro = false;
            ubicacionEnTiempoReal = true;
          });
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text(
                'Configuración restablecida a valores predeterminados',
              ),
              behavior: SnackBarBehavior.floating,
            ),
          );
        },
      ),
    );
  }

  // ==========================================================
  // UTILITARIOS (Diálogos y títulos)
  // ==========================================================
  Widget _buildTituloSeccion(String titulo) {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Text(
        titulo,
        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
      ),
    );
  }

  void _mostrarDialogoIdioma(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Seleccionar idioma'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              title: const Text('Español'),
              onTap: () => Navigator.pop(context),
            ),
            ListTile(
              title: const Text('Inglés'),
              onTap: () => Navigator.pop(context),
            ),
          ],
        ),
      ),
    );
  }

  void _mostrarDialogoSonido(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Seleccionar sonido'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              title: const Text('Predeterminado'),
              onTap: () => Navigator.pop(context),
            ),
            ListTile(
              title: const Text('Silencio'),
              onTap: () => Navigator.pop(context),
            ),
            ListTile(
              title: const Text('Tono 1'),
              onTap: () => Navigator.pop(context),
            ),
          ],
        ),
      ),
    );
  }

  void _mostrarDialogoBasico(
    BuildContext context,
    String titulo,
    String contenido,
  ) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(titulo),
        content: Text(contenido),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cerrar'),
          ),
        ],
      ),
    );
  }
}
