// lib/screens/delivery/perfil/pantalla_perfil_repartidor.dart

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../../../models/repartidor.dart';
import '../controllers/perfil_repartidor_controller.dart';

/// 👤 Pantalla de Perfil del Repartidor
/// Permite ver y editar información personal, estadísticas y foto
class PantallaPerfilRepartidor extends StatefulWidget {
  const PantallaPerfilRepartidor({super.key});

  @override
  State<PantallaPerfilRepartidor> createState() =>
      _PantallaPerfilRepartidorState();
}

class _PantallaPerfilRepartidorState extends State<PantallaPerfilRepartidor> {
  // ============================================
  // CONTROLLER
  // ============================================
  late final PerfilRepartidorController _controller;

  // ============================================
  // COLORES
  // ============================================
  static const Color _naranja = Color(0xFFFF9800);
  static const Color _naranjaOscuro = Color(0xFFF57C00);
  static const Color _verde = Color(0xFF4CAF50);
  static const Color _azul = Color(0xFF2196F3);
  static const Color _rojo = Color(0xFFF44336);

  // ============================================
  // CICLO DE VIDA
  // ============================================

  @override
  void initState() {
    super.initState();
    _controller = PerfilRepartidorController();
    _cargarDatos();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  // ============================================
  // CARGA DE DATOS
  // ============================================

  Future<void> _cargarDatos() async {
    await _controller.cargarPerfil();
    if (!mounted) return;

    if (_controller.error != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_controller.error!), backgroundColor: _rojo),
      );
    }
  }

  // ============================================
  // ACCIONES
  // ============================================

  Future<void> _cambiarFoto() async {
    final ImagePicker picker = ImagePicker();

    final opcion = await showModalBottomSheet<String>(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey[300],
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'Cambiar foto de perfil',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 20),
            ListTile(
              leading: Icon(Icons.camera_alt, color: _naranja),
              title: const Text('Tomar foto'),
              onTap: () => Navigator.pop(context, 'camera'),
            ),
            ListTile(
              leading: Icon(Icons.photo_library, color: _azul),
              title: const Text('Elegir de galería'),
              onTap: () => Navigator.pop(context, 'gallery'),
            ),
            if (_controller.perfil?.fotoPerfil != null)
              ListTile(
                leading: Icon(Icons.delete, color: _rojo),
                title: const Text('Eliminar foto'),
                onTap: () => Navigator.pop(context, 'delete'),
              ),
          ],
        ),
      ),
    );

    if (opcion == null || !mounted) return;

    // ✅ Implementar eliminación de foto
    if (opcion == 'delete') {
      final confirmar = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Eliminar foto de perfil'),
          content: const Text(
            '¿Estás seguro de eliminar tu foto de perfil? '
            'Se mostrará el avatar predeterminado.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancelar'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              style: ElevatedButton.styleFrom(backgroundColor: _rojo),
              child: const Text('Eliminar'),
            ),
          ],
        ),
      );

      if (confirmar != true || !mounted) return;

      final exito = await _controller.eliminarFotoPerfil();

      if (!mounted) return;

      if (exito) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                Icon(Icons.check_circle, color: Colors.white),
                const SizedBox(width: 12),
                const Text('Foto eliminada correctamente'),
              ],
            ),
            backgroundColor: _verde,
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_controller.error ?? 'Error al eliminar foto'),
            backgroundColor: _rojo,
          ),
        );
      }
      return;
    }

    final ImageSource source = opcion == 'camera'
        ? ImageSource.camera
        : ImageSource.gallery;

    try {
      final XFile? image = await picker.pickImage(
        source: source,
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 85,
      );

      if (image == null) return;

      final File imageFile = File(image.path);
      final fileSizeInBytes = await imageFile.length();
      final fileSizeInMB = fileSizeInBytes / (1024 * 1024);

      if (fileSizeInMB > 5) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('La imagen es muy grande (máx 5MB)'),
            backgroundColor: Colors.red,
          ),
        );
        return;
      }

      if (!mounted) return;

      // Mostrar diálogo de confirmación con preview
      final confirmar = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Confirmar nueva foto'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Image.file(
                  imageFile,
                  height: 200,
                  width: 200,
                  fit: BoxFit.cover,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Tamaño: ${fileSizeInMB.toStringAsFixed(2)} MB',
                style: TextStyle(color: Colors.grey[600], fontSize: 12),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancelar'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              style: ElevatedButton.styleFrom(backgroundColor: _verde),
              child: const Text('Subir'),
            ),
          ],
        ),
      );

      if (confirmar != true || !mounted) return;

      final exito = await _controller.actualizarFotoPerfil(imageFile);

      if (!mounted) return;

      if (exito) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                Icon(Icons.check_circle, color: Colors.white),
                const SizedBox(width: 12),
                const Text('Foto actualizada correctamente'),
              ],
            ),
            backgroundColor: _verde,
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_controller.error ?? 'Error al actualizar foto'),
            backgroundColor: _rojo,
          ),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: ${e.toString()}'),
          backgroundColor: _rojo,
        ),
      );
    }
  }

  Future<void> _editarTelefono() async {
    final TextEditingController telefonoController = TextEditingController(
      text: _controller.perfil?.telefono ?? '',
    );

    final nuevoTelefono = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Editar Teléfono'),
        content: TextField(
          controller: telefonoController,
          keyboardType: TextInputType.phone,
          decoration: const InputDecoration(
            labelText: 'Teléfono',
            hintText: '0987654321',
            prefixIcon: Icon(Icons.phone),
            border: OutlineInputBorder(),
          ),
          maxLength: 10,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              final telefono = telefonoController.text.trim();
              if (telefono.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Ingresa un teléfono válido')),
                );
                return;
              }
              Navigator.pop(context, telefono);
            },
            style: ElevatedButton.styleFrom(backgroundColor: _naranja),
            child: const Text('Guardar'),
          ),
        ],
      ),
    );

    if (nuevoTelefono == null || !mounted) return;

    final exito = await _controller.actualizarTelefono(nuevoTelefono);

    if (!mounted) return;

    if (exito) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Teléfono actualizado'),
          backgroundColor: _verde,
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(_controller.error ?? 'Error al actualizar'),
          backgroundColor: _rojo,
        ),
      );
    }
  }

  // ============================================
  // UI - BUILD
  // ============================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: _buildAppBar(),
      body: ListenableBuilder(
        listenable: _controller,
        builder: (context, child) {
          if (_controller.loading) {
            return _buildCargando();
          }

          if (_controller.error != null && _controller.perfil == null) {
            return _buildError();
          }

          return _buildContenido();
        },
      ),
    );
  }

  // ============================================
  // APP BAR
  // ============================================

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      title: const Text('Mi Perfil'),
      elevation: 0,
      flexibleSpace: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [_naranja, _naranjaOscuro],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
      ),
      actions: [
        IconButton(
          icon: const Icon(Icons.refresh),
          onPressed: _cargarDatos,
          tooltip: 'Recargar',
        ),
      ],
    );
  }

  // ============================================
  // ESTADOS
  // ============================================

  Widget _buildCargando() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(color: _naranja),
          const SizedBox(height: 16),
          Text('Cargando perfil...', style: TextStyle(color: Colors.grey[600])),
        ],
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: _rojo.withValues(alpha: 0.5),
            ),
            const SizedBox(height: 16),
            Text(
              _controller.error!,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16, color: Colors.grey[700]),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _cargarDatos,
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _naranja,
                padding: const EdgeInsets.symmetric(
                  horizontal: 32,
                  vertical: 12,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================
  // CONTENIDO
  // ============================================

  Widget _buildContenido() {
    final perfil = _controller.perfil!;

    return RefreshIndicator(
      onRefresh: _cargarDatos,
      color: _naranja,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: Column(
          children: [
            _buildFotoPerfil(perfil),
            const SizedBox(height: 16),
            const SizedBox(height: 16),
            _buildSeccionInformacion(perfil),
            const SizedBox(height: 16),
            _buildSeccionVehiculo(perfil),
            const SizedBox(height: 80),
          ],
        ),
      ),
    );
  }

  // ============================================
  // FOTO DE PERFIL
  // ============================================

  Widget _buildFotoPerfil(PerfilRepartidorModel perfil) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [_naranja.withValues(alpha: 0.1), Colors.white],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          Container(
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: _naranja.withValues(alpha: 0.3),
                  blurRadius: 20,
                  spreadRadius: 5,
                ),
              ],
            ),
            child: CircleAvatar(
              radius: 70,
              backgroundColor: Colors.white,
              backgroundImage: perfil.fotoPerfil != null
                  ? NetworkImage(perfil.fotoPerfil!)
                  : null,
              child: perfil.fotoPerfil == null
                  ? Icon(Icons.person, size: 60, color: _naranja)
                  : null,
            ),
          ),
          Positioned(
            bottom: 0,
            right: 0,
            child: Material(
              color: _naranja,
              shape: const CircleBorder(),
              elevation: 4,
              child: InkWell(
                onTap: _controller.subiendoFoto ? null : _cambiarFoto,
                customBorder: const CircleBorder(),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: _controller.subiendoFoto
                      ? SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : const Icon(
                          Icons.camera_alt,
                          color: Colors.white,
                          size: 20,
                        ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ============================================
  // SECCIÓN INFORMACIÓN
  // ============================================

  Widget _buildSeccionInformacion(PerfilRepartidorModel perfil) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withValues(alpha: 0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text(
              'Información Personal',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.grey[800],
              ),
            ),
          ),
          const Divider(height: 1),
          _buildInfoTile(Icons.email, 'Email', perfil.email, null),
          _buildInfoTile(
            Icons.phone,
            'Teléfono',
            perfil.telefono.isEmpty ? 'No registrado' : perfil.telefono,
            _editarTelefono,
          ),
          _buildInfoTile(Icons.badge, 'ID Repartidor', '#${perfil.id}', null),
          _buildInfoTile(
            Icons.verified,
            'Estado Verificación',
            perfil.verificado ? 'Verificado ✓' : 'Pendiente',
            null,
            color: perfil.verificado ? _verde : Colors.orange,
          ),
        ],
      ),
    );
  }

  Widget _buildInfoTile(
    IconData icon,
    String label,
    String value,
    VoidCallback? onTap, {
    Color? color,
  }) {
    return ListTile(
      leading: Icon(icon, color: color ?? _naranja),
      title: Text(
        label,
        style: TextStyle(fontSize: 12, color: Colors.grey[600]),
      ),
      subtitle: Text(
        value,
        style: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w500,
          color: color ?? Colors.grey[800],
        ),
      ),
      trailing: onTap != null
          ? IconButton(
              icon: Icon(Icons.edit, color: _azul),
              onPressed: onTap,
            )
          : null,
    );
  }

  // ============================================
  // SECCIÓN VEHÍCULO
  // ============================================

  Widget _buildSeccionVehiculo(PerfilRepartidorModel perfil) {
    final vehiculo = perfil.vehiculoActivo;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withValues(alpha: 0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Vehículo Activo',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.grey[800],
                  ),
                ),
                if (vehiculo != null)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: _verde.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.check_circle, size: 14, color: _verde),
                        const SizedBox(width: 4),
                        Text(
                          'Activo',
                          style: TextStyle(
                            fontSize: 12,
                            color: _verde,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
          const Divider(height: 1),
          if (vehiculo != null) ...[
            ListTile(
              leading: Icon(Icons.directions_bike, color: _naranja),
              title: const Text('Tipo'),
              subtitle: Text(vehiculo.tipo.nombre),
            ),
            if (vehiculo.placa != null)
              ListTile(
                leading: Icon(Icons.confirmation_number, color: _azul),
                title: const Text('Placa'),
                subtitle: Text(vehiculo.placa ?? 'Sin placa'),
              ),
          ] else
            const Padding(
              padding: EdgeInsets.all(16),
              child: Center(
                child: Text(
                  'No tienes un vehículo activo',
                  style: TextStyle(color: Colors.grey),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
