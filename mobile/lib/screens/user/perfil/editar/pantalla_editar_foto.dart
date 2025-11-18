// lib/screens/user/perfil/editar/pantalla_editar_foto.dart

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../../../../theme/jp_theme.dart';
import '../../../../services/usuarios_service.dart';
import '../../../../apis/helpers/api_exception.dart';

/// 📸 Pantalla para cambiar foto de perfil
class PantallaEditarFoto extends StatefulWidget {
  final String? fotoActual;

  const PantallaEditarFoto({super.key, this.fotoActual});

  @override
  State<PantallaEditarFoto> createState() => _PantallaEditarFotoState();
}

class _PantallaEditarFotoState extends State<PantallaEditarFoto> {
  final _usuarioService = UsuarioService();
  final _imagePicker = ImagePicker();

  File? _imagenSeleccionada;
  bool _guardando = false;

  // ══════════════════════════════════════════════════════════════════════════
  // 📸 SELECCIONAR IMAGEN
  // ══════════════════════════════════════════════════════════════════════════

  Future<void> _seleccionarDesdeGaleria() async {
    try {
      final XFile? imagen = await _imagePicker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 85,
      );

      if (imagen != null) {
        setState(() {
          _imagenSeleccionada = File(imagen.path);
        });
      }
    } catch (e) {
      if (!mounted) return;
      JPSnackbar.error(context, 'Error al seleccionar imagen: $e');
    }
  }

  Future<void> _tomarFoto() async {
    try {
      final XFile? imagen = await _imagePicker.pickImage(
        source: ImageSource.camera,
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 85,
      );

      if (imagen != null) {
        setState(() {
          _imagenSeleccionada = File(imagen.path);
        });
      }
    } catch (e) {
      if (!mounted) return;
      JPSnackbar.error(context, 'Error al tomar foto: $e');
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 💾 GUARDAR CAMBIOS
  // ══════════════════════════════════════════════════════════════════════════
  Future<void> _guardarCambios() async {
    if (_imagenSeleccionada == null) {
      JPSnackbar.error(context, 'Selecciona una imagen primero');
      return;
    }

    setState(() => _guardando = true);

    try {
      await _usuarioService.subirFotoPerfil(_imagenSeleccionada!);

      if (!mounted) return;

      JPSnackbar.success(context, 'Foto actualizada exitosamente');
      Navigator.pop(context, true);
    } on ApiException catch (e) {
      if (!mounted) return;
      JPSnackbar.error(context, e.getUserFriendlyMessage());
    } catch (e) {
      if (!mounted) return;
      JPSnackbar.error(context, 'Error al actualizar foto');
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  Future<void> _eliminarFoto() async {
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Eliminar foto'),
        content: const Text('¿Estás seguro de eliminar tu foto de perfil?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: JPColors.error),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );

    if (confirmar != true) return;

    setState(() => _guardando = true);

    try {
      await _usuarioService.eliminarFotoPerfil();

      if (!mounted) return;
      JPSnackbar.success(context, 'Foto eliminada');
      Navigator.pop(context, true);
    } on ApiException catch (e) {
      if (!mounted) return;
      JPSnackbar.error(context, e.getUserFriendlyMessage());
    } catch (e) {
      if (!mounted) return;
      JPSnackbar.error(context, 'Error al eliminar foto');
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }
  // ══════════════════════════════════════════════════════════════════════════
  // 🎨 BUILD
  // ══════════════════════════════════════════════════════════════════════════

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: JPColors.background,
      appBar: AppBar(
        title: const Text('Cambiar Foto de Perfil'),
        backgroundColor: JPColors.primary,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            // Vista previa
            _buildPreview(),

            const SizedBox(height: 32),

            // Botones de acción
            if (_imagenSeleccionada == null) ...[
              _buildBotonOpcion(
                icono: Icons.photo_library,
                texto: 'Seleccionar de Galería',
                onTap: _seleccionarDesdeGaleria,
              ),
              const SizedBox(height: 16),
              _buildBotonOpcion(
                icono: Icons.camera_alt,
                texto: 'Tomar Foto',
                onTap: _tomarFoto,
              ),
              if (widget.fotoActual != null) ...[
                const SizedBox(height: 16),
                _buildBotonOpcion(
                  icono: Icons.delete,
                  texto: 'Eliminar Foto Actual',
                  color: JPColors.error,
                  onTap: _eliminarFoto,
                ),
              ],
            ] else ...[
              ElevatedButton.icon(
                onPressed: _guardando ? null : _guardarCambios,
                icon: _guardando
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.check),
                label: Text(_guardando ? 'Guardando...' : 'Guardar Cambios'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: JPColors.success,
                  minimumSize: const Size(double.infinity, 50),
                ),
              ),
              const SizedBox(height: 16),
              OutlinedButton.icon(
                onPressed: _guardando
                    ? null
                    : () {
                        setState(() => _imagenSeleccionada = null);
                      },
                icon: const Icon(Icons.close),
                label: const Text('Cancelar'),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 50),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildPreview() {
    return Container(
      width: 200,
      height: 200,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: JPColors.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.1),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: ClipOval(
        child: _imagenSeleccionada != null
            ? Image.file(_imagenSeleccionada!, fit: BoxFit.cover)
            : widget.fotoActual != null
            ? Image.network(
                widget.fotoActual!,
                fit: BoxFit.cover,
                errorBuilder: (context, error, stackTrace) {
                  return _buildPlaceholder();
                },
              )
            : _buildPlaceholder(),
      ),
    );
  }

  Widget _buildPlaceholder() {
    return Container(
      color: JPColors.primary.withValues(alpha: 0.1),
      child: const Icon(Icons.person, size: 80, color: JPColors.primary),
    );
  }

  Widget _buildBotonOpcion({
    required IconData icono,
    required String texto,
    required VoidCallback onTap,
    Color? color,
  }) {
    return InkWell(
      onTap: _guardando ? null : onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: JPColors.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color ?? JPColors.primary, width: 2),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: (color ?? JPColors.primary).withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(icono, color: color ?? JPColors.primary, size: 28),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Text(
                texto,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: color ?? JPColors.textPrimary,
                ),
              ),
            ),
            Icon(
              Icons.arrow_forward_ios,
              size: 16,
              color: color ?? JPColors.textSecondary,
            ),
          ],
        ),
      ),
    );
  }
}
