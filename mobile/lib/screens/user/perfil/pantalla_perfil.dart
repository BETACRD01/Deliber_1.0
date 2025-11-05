// lib/screens/user/perfil/pantalla_perfil.dart

import 'package:flutter/material.dart';
import '../../../theme/jp_theme.dart';
import '../../../models/usuario.dart';
import '../../../controllers/perfil_controller.dart';
import 'editar/pantalla_editar_informacion.dart';
import 'editar/pantalla_editar_foto.dart';
import 'editar/pantalla_agregar_direccion.dart';

/// 👤 PANTALLA DE PERFIL COMPLETA
/// Muestra TODA la información del usuario disponible en el backend
/// ✅ CORRECCIÓN: Manejo mejorado de direcciones
class PantallaPerfil extends StatefulWidget {
  const PantallaPerfil({super.key});

  @override
  State<PantallaPerfil> createState() => _PantallaPerfilState();
}

class _PantallaPerfilState extends State<PantallaPerfil> {
  // ══════════════════════════════════════════════════════════════════════════
  // 🎮 CONTROLADOR
  // ══════════════════════════════════════════════════════════════════════════

  late final PerfilController _controller;

  // ══════════════════════════════════════════════════════════════════════════
  // 🔄 LIFECYCLE
  // ══════════════════════════════════════════════════════════════════════════

  @override
  void initState() {
    super.initState();
    _controller = PerfilController();

    // ✅ SIMPLIFICADO: Listener para debugging (opcional)
    _controller.addListener(() {
      debugPrint('🔔 Estado del controlador cambió');
    });

    _cargarDatos();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📥 CARGA DE DATOS
  // ══════════════════════════════════════════════════════════════════════════

  Future<void> _cargarDatos() async {
    await _controller.cargarDatosCompletos();
  }

  Future<void> _recargarDatos() async {
    await _controller.cargarDatosCompletos(forzarRecarga: true);
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🎨 BUILD
  // ══════════════════════════════════════════════════════════════════════════

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: JPColors.background,
      appBar: _buildAppBar(),
      body: AnimatedBuilder(
        animation: _controller,
        builder: (context, _) {
          // Estado de carga inicial
          if (_controller.isLoading && !_controller.tieneDatos) {
            return const JPLoading(message: 'Cargando perfil...');
          }

          // Estado de error TOTAL (todo falló)
          if (_controller.tieneError &&
              !_controller.tieneDatos &&
              !_controller.tieneDirecciones) {
            return _buildErrorState();
          }

          // ✅ Mostrar datos aunque algunos fallen
          return RefreshIndicator(
            onRefresh: _recargarDatos,
            color: JPColors.primary,
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              child: Column(
                children: [
                  // ⚠️ Mostrar advertencia si hay errores parciales
                  if (_controller.errorPerfil != null ||
                      _controller.errorEstadisticas != null)
                    _buildWarningBanner(),

                  _buildHeader(),
                  const SizedBox(height: 16),
                  _buildInfoPersonal(),
                  const SizedBox(height: 16),
                  _buildNotificaciones(),
                  const SizedBox(height: 16),
                  _buildEstadisticas(),
                  const SizedBox(height: 16),
                  _buildDirecciones(),
                  const SizedBox(height: 24),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📱 APP BAR
  // ══════════════════════════════════════════════════════════════════════════

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      title: const Text('Mi Perfil'),
      backgroundColor: JPColors.primary,
      foregroundColor: Colors.white,
      elevation: 0,
      actions: [
        IconButton(
          icon: const Icon(Icons.settings),
          tooltip: 'Configuración',
          onPressed: () {
            JPSnackbar.show(context, 'Configuración próximamente');
          },
        ),
        PopupMenuButton<String>(
          icon: const Icon(Icons.more_vert),
          tooltip: 'Más opciones',
          onSelected: (value) {
            if (value == 'logout') {
              _confirmarCerrarSesion();
            }
          },
          itemBuilder: (context) => [
            const PopupMenuItem(
              value: 'logout',
              child: Row(
                children: [
                  Icon(Icons.logout, color: JPColors.error, size: 20),
                  SizedBox(width: 12),
                  Text(
                    'Cerrar Sesión',
                    style: TextStyle(color: JPColors.error),
                  ),
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // ⚠️ BANNER DE ADVERTENCIA (ERRORES PARCIALES)
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildWarningBanner() {
    final List<String> errores = [];

    if (_controller.errorPerfil != null) {
      errores.add('información de perfil');
    }
    if (_controller.errorEstadisticas != null) {
      errores.add('estadísticas');
    }

    final String mensaje = errores.length == 1
        ? 'No se pudo cargar ${errores[0]}'
        : 'No se pudo cargar: ${errores.join(", ")}';

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: JPColors.warning.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: JPColors.warning, width: 1),
      ),
      child: Row(
        children: [
          Icon(Icons.warning_amber_rounded, color: JPColors.warning, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Carga parcial',
                  style: TextStyle(
                    color: JPColors.warning,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  mensaje,
                  style: TextStyle(
                    color: JPColors.warning.withValues(alpha: 0.8),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.refresh, size: 20),
            color: JPColors.warning,
            onPressed: _recargarDatos,
            tooltip: 'Reintentar',
          ),
        ],
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // ❌ ESTADO DE ERROR TOTAL
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildErrorState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Icono de error
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: JPColors.error.withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.error_outline,
                size: 64,
                color: JPColors.error,
              ),
            ),

            const SizedBox(height: 24),

            // Título del error
            Text(
              'Error al cargar perfil',
              style: JPTextStyles.h3.copyWith(color: JPColors.error),
              textAlign: TextAlign.center,
            ),

            const SizedBox(height: 12),

            // Mensaje del error
            Text(
              _controller.error ??
                  'No se pudo cargar la información del perfil',
              style: JPTextStyles.bodySecondary,
              textAlign: TextAlign.center,
            ),

            const SizedBox(height: 32),

            // Botón de reintentar
            ElevatedButton.icon(
              onPressed: _recargarDatos,
              icon: const Icon(Icons.refresh, size: 20),
              label: const Text('Reintentar'),
              style: ElevatedButton.styleFrom(
                backgroundColor: JPColors.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(
                  horizontal: 32,
                  vertical: 16,
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Botón secundario para volver
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Volver atrás'),
            ),
          ],
        ),
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 👤 HEADER DEL PERFIL
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildHeader() {
    final perfil = _controller.perfil;
    if (perfil == null) return const SizedBox.shrink();

    return Container(
      width: double.infinity,
      decoration: const BoxDecoration(
        gradient: JPColors.primaryGradient,
        borderRadius: BorderRadius.vertical(bottom: Radius.circular(24)),
      ),
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          // ✅ CORREGIDO: Usar JPAvatar con showEditIcon
          JPAvatar(
            imageUrl: perfil.fotoPerfilUrl,
            radius: 60,
            showEditIcon: true,
            onTap: _editarFoto,
          ),

          const SizedBox(height: 16),

          // Nombre
          Text(
            perfil.usuarioNombre,
            style: JPTextStyles.h2.copyWith(color: Colors.white),
            textAlign: TextAlign.center,
          ),

          const SizedBox(height: 8),

          // Email
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.email, size: 16, color: Colors.white70),
              const SizedBox(width: 8),
              Text(
                perfil.usuarioEmail,
                style: const TextStyle(color: Colors.white70),
              ),
            ],
          ),

          const SizedBox(height: 16),

          // Stats compactas
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildStatChip(
                icon: Icons.star,
                label: perfil.calificacion.toStringAsFixed(1),
                sublabel: '${perfil.totalResenas} reseñas',
              ),
              _buildStatChip(
                icon: Icons.shopping_bag,
                label: '${perfil.totalPedidos}',
                sublabel: 'pedidos',
              ),
            ],
          ),

          // Badge VIP
          if (perfil.esClienteFrecuente) ...[
            const SizedBox(height: 12),
            const JPBadge(
              label: '⭐ Cliente Frecuente',
              color: JPColors.accent,
              icon: Icons.verified,
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildStatChip({
    required IconData icon,
    required String label,
    required String sublabel,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          Icon(icon, color: Colors.white, size: 20),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
              Text(
                sublabel,
                style: const TextStyle(color: Colors.white70, fontSize: 11),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📋 INFORMACIÓN PERSONAL
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildInfoPersonal() {
    final perfil = _controller.perfil;
    if (perfil == null) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: JPCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Información Personal', style: JPTextStyles.h3),
                IconButton(
                  icon: const Icon(Icons.edit, size: 20),
                  color: JPColors.primary,
                  onPressed: _editarPerfil,
                ),
              ],
            ),
            const Divider(height: 24),

            // Teléfono
            _buildInfoRow(
              icon: Icons.phone,
              label: 'Teléfono',
              value: perfil.telefono ?? 'No registrado',
              hasValue: perfil.tieneTelefono,
            ),

            const SizedBox(height: 16),

            // Fecha de nacimiento
            _buildInfoRow(
              icon: Icons.cake,
              label: 'Fecha de nacimiento',
              value: perfil.fechaNacimiento != null
                  ? '${perfil.fechaNacimiento!.day}/${perfil.fechaNacimiento!.month}/${perfil.fechaNacimiento!.year}'
                  : 'No registrada',
              hasValue: perfil.fechaNacimiento != null,
            ),

            // Edad
            if (perfil.edad != null) ...[
              const SizedBox(height: 8),
              Padding(
                padding: const EdgeInsets.only(left: 40),
                child: Text('${perfil.edad} años', style: JPTextStyles.caption),
              ),
            ],

            // Mensaje de completitud
            if (!_controller.perfilCompleto) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: JPColors.warning.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.info_outline,
                      color: JPColors.warning,
                      size: 20,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        _controller.mensajeCompletitud,
                        style: const TextStyle(
                          color: JPColors.warning,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow({
    required IconData icon,
    required String label,
    required String value,
    required bool hasValue,
  }) {
    return Row(
      children: [
        Icon(
          icon,
          size: 24,
          color: hasValue ? JPColors.primary : JPColors.textHint,
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: JPTextStyles.caption),
              const SizedBox(height: 4),
              Text(
                value,
                style: JPTextStyles.body.copyWith(
                  color: hasValue ? JPColors.textPrimary : JPColors.textHint,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
  // ══════════════════════════════════════════════════════════════════════════
  // 🔔 NOTIFICACIONES
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildNotificaciones() {
    final perfil = _controller.perfil;
    if (perfil == null) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: JPCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Notificaciones', style: JPTextStyles.h3),
            const Divider(height: 24),

            // Estado de notificaciones push
            if (perfil.puedeRecibirNotificaciones)
              Container(
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: JPColors.success.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: JPColors.success),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.check_circle,
                      color: JPColors.success,
                      size: 20,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Notificaciones push activas',
                        style: JPTextStyles.caption.copyWith(
                          color: JPColors.success,
                        ),
                      ),
                    ),
                  ],
                ),
              )
            else
              Container(
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: JPColors.warning.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: JPColors.warning),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.notifications_off,
                      color: JPColors.warning,
                      size: 20,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Notificaciones push desactivadas',
                        style: JPTextStyles.caption.copyWith(
                          color: JPColors.warning,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

            // Switch de notificaciones de pedidos
            _buildNotificationSwitch(
              icon: Icons.shopping_bag,
              title: 'Notificaciones de pedidos',
              subtitle: 'Recibe actualizaciones sobre tus pedidos',
              value: perfil.notificacionesPedido,
              onChanged: _cambiarNotificacionPedidos,
            ),

            const SizedBox(height: 16),

            // Switch de notificaciones de promociones
            _buildNotificationSwitch(
              icon: Icons.local_offer,
              title: 'Notificaciones de promociones',
              subtitle: 'Recibe ofertas y descuentos especiales',
              value: perfil.notificacionesPromociones,
              onChanged: _cambiarNotificacionPromociones,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNotificationSwitch({
    required IconData icon,
    required String title,
    required String subtitle,
    required bool value,
    required Function(bool) onChanged,
  }) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: JPColors.primary.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: JPColors.primary, size: 24),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: JPTextStyles.body),
              const SizedBox(height: 4),
              Text(subtitle, style: JPTextStyles.caption),
            ],
          ),
        ),
        Switch(
          value: value,
          onChanged: onChanged,
          activeTrackColor: JPColors.success.withValues(alpha: 0.5),
          activeThumbColor: JPColors.success,
        ),
      ],
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📊 ESTADÍSTICAS
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildEstadisticas() {
    final estadisticas = _controller.estadisticas;
    if (estadisticas == null) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: JPCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Estadísticas', style: JPTextStyles.h3),
            const Divider(height: 24),

            // Nivel de cliente
            _buildStatRow(
              icon: Icons.workspace_premium,
              label: 'Nivel',
              value: _controller.nivelCliente,
              color: JPColors.accent,
            ),

            const SizedBox(height: 16),

            // Pedidos este mes
            _buildStatRow(
              icon: Icons.calendar_today,
              label: 'Pedidos este mes',
              value: '${estadisticas.pedidosMesActual}',
              color: JPColors.info,
            ),

            const SizedBox(height: 16),

            // Rifa mensual
            _buildRifaCard(),
          ],
        ),
      ),
    );
  }

  Widget _buildStatRow({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: color, size: 24),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: JPTextStyles.caption),
              const SizedBox(height: 4),
              Text(value, style: JPTextStyles.body),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildRifaCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            JPColors.accent.withValues(alpha: 0.1),
            JPColors.secondary.withValues(alpha: 0.1),
          ],
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: _controller.puedeParticiparRifa
              ? JPColors.success
              : JPColors.warning,
          width: 2,
        ),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Icon(
                _controller.puedeParticiparRifa
                    ? Icons.celebration
                    : Icons.emoji_events,
                color: _controller.puedeParticiparRifa
                    ? JPColors.success
                    : JPColors.warning,
                size: 32,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      '🎉 Rifa Mensual',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(_controller.mensajeRifa, style: JPTextStyles.caption),
                  ],
                ),
              ),
            ],
          ),

          const SizedBox(height: 12),

          // Barra de progreso
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: _controller.progresoRifa,
              backgroundColor: Colors.grey.shade200,
              valueColor: AlwaysStoppedAnimation<Color>(
                _controller.puedeParticiparRifa
                    ? JPColors.success
                    : JPColors.warning,
              ),
              minHeight: 8,
            ),
          ),
        ],
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 📍 DIRECCIONES - ✅ COMPLETAMENTE CORREGIDO
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildDirecciones() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Direcciones Favoritas', style: JPTextStyles.h3),
              TextButton.icon(
                onPressed: _agregarDireccion,
                icon: const Icon(Icons.add, size: 20),
                label: const Text('Agregar'),
              ),
            ],
          ),

          const SizedBox(height: 12),

          // Lista de direcciones
          if (_controller.isLoadingDirecciones)
            const Center(
              child: Padding(
                padding: EdgeInsets.all(32),
                child: CircularProgressIndicator(),
              ),
            )
          else if (_controller.errorDirecciones != null)
            _buildErrorDirecciones()
          else if (!_controller.tieneDirecciones)
            _buildEmptyDirecciones()
          else
            _buildListaDirecciones(),
        ],
      ),
    );
  }

  Widget _buildErrorDirecciones() {
    return JPCard(
      child: Column(
        children: [
          Icon(Icons.error_outline, size: 48, color: JPColors.error),
          const SizedBox(height: 8),
          Text(
            _controller.errorDirecciones ?? 'Error al cargar direcciones',
            style: JPTextStyles.bodySecondary,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: _controller.recargarDirecciones,
            icon: const Icon(Icons.refresh, size: 20),
            label: const Text('Reintentar'),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyDirecciones() {
    return JPCard(
      child: Column(
        children: [
          Icon(Icons.location_off, size: 64, color: JPColors.textHint),
          const SizedBox(height: 16),
          Text(
            'No tienes direcciones guardadas',
            style: JPTextStyles.body.copyWith(color: JPColors.textSecondary),
          ),
          const SizedBox(height: 8),
          Text(
            'Agrega una dirección para pedidos más rápidos',
            style: JPTextStyles.caption,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: _agregarDireccion,
            icon: const Icon(Icons.add_location),
            label: const Text('Agregar Dirección'),
          ),
        ],
      ),
    );
  }

  Widget _buildListaDirecciones() {
    final direcciones = _controller.direcciones!;

    return Column(
      children: direcciones.map((direccion) {
        return Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: _buildDireccionCard(direccion),
        );
      }).toList(),
    );
  }

  Widget _buildDireccionCard(DireccionModel direccion) {
    return JPCard(
      onTap: () => _verDetalleDireccion(direccion),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: JPColors.primary.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  direccion.iconoTipo,
                  style: const TextStyle(fontSize: 20),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          direccion.etiqueta,
                          style: JPTextStyles.body.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        if (direccion.esPredeterminada) ...[
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: JPColors.success.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(
                                color: JPColors.success,
                                width: 1,
                              ),
                            ),
                            child: const Text(
                              'Predeterminada',
                              style: TextStyle(
                                color: JPColors.success,
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      direccion.direccion,
                      style: JPTextStyles.caption,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              PopupMenuButton<String>(
                icon: const Icon(Icons.more_vert),
                onSelected: (value) => _accionDireccion(value, direccion),
                itemBuilder: (context) => [
                  if (!direccion.esPredeterminada)
                    const PopupMenuItem(
                      value: 'predeterminada',
                      child: Row(
                        children: [
                          Icon(Icons.star, size: 20),
                          SizedBox(width: 8),
                          Text('Predeterminada'),
                        ],
                      ),
                    ),
                  const PopupMenuItem(
                    value: 'editar',
                    child: Row(
                      children: [
                        Icon(Icons.edit, size: 20),
                        SizedBox(width: 8),
                        Text('Editar'),
                      ],
                    ),
                  ),
                  const PopupMenuItem(
                    value: 'eliminar',
                    child: Row(
                      children: [
                        Icon(Icons.delete, size: 20, color: JPColors.error),
                        SizedBox(width: 8),
                        Text(
                          'Eliminar',
                          style: TextStyle(color: JPColors.error),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🎬 ACCIONES - ✅ MÉTODOS SIMPLIFICADOS Y CORREGIDOS
  // ══════════════════════════════════════════════════════════════════════════

  void _editarFoto() async {
    final resultado = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (context) =>
            PantallaEditarFoto(fotoActual: _controller.perfil?.fotoPerfilUrl),
      ),
    );

    if (resultado == true) {
      _recargarDatos();
    }
  }

  void _editarPerfil() async {
    if (_controller.perfil == null) return;

    final resultado = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (context) =>
            PantallaEditarInformacion(perfil: _controller.perfil!),
      ),
    );

    if (resultado == true) {
      _recargarDatos();
    }
  }

  /// ✅ CORRECCIÓN CRÍTICA: Método completamente simplificado
  void _agregarDireccion() async {
    debugPrint(
      '═══════════════════════════════════════════════════════════════',
    );
    debugPrint('🚀 Navegando a agregar dirección...');
    debugPrint(
      '═══════════════════════════════════════════════════════════════',
    );

    final resultado = await Navigator.push<bool>(
      context,
      MaterialPageRoute(builder: (context) => const PantallaAgregarDireccion()),
    );

    debugPrint(
      '───────────────────────────────────────────────────────────────',
    );
    debugPrint('🔙 Resultado de navegación: $resultado');
    debugPrint(
      '───────────────────────────────────────────────────────────────',
    );

    // ✅ CRÍTICO: Recargar SIEMPRE, sin importar el resultado
    // Esto asegura que la UI se actualice incluso si hubo actualización
    debugPrint('♻️ Recargando direcciones...');
    await _controller.recargarDirecciones();

    debugPrint(
      '───────────────────────────────────────────────────────────────',
    );
    debugPrint('📊 Estado después de recargar:');
    debugPrint(
      '   Direcciones en memoria: ${_controller.direcciones?.length ?? 0}',
    );
    debugPrint('   Cargando: ${_controller.isLoadingDirecciones}');
    debugPrint('   Error: ${_controller.errorDirecciones ?? "ninguno"}');

    if (_controller.direcciones != null &&
        _controller.direcciones!.isNotEmpty) {
      debugPrint('📋 Lista actualizada:');
      for (var dir in _controller.direcciones!) {
        debugPrint('   - ${dir.etiqueta}: ${dir.direccion}');
      }
    }
    debugPrint(
      '═══════════════════════════════════════════════════════════════',
    );

    // ✅ CRÍTICO: Forzar actualización de UI
    if (mounted) {
      setState(() {
        debugPrint('🔄 setState() ejecutado - UI actualizada');
      });
    }

    // ✅ OPCIONAL: Mostrar mensaje de confirmación si resultado es true
    if (resultado == true && mounted) {
      // Ya se muestra el snackbar en pantalla_agregar_direccion
      // Este es solo para debug
      debugPrint('✅ Operación completada exitosamente');
    }
  }

  void _verDetalleDireccion(DireccionModel direccion) {
    JPSnackbar.show(context, 'Ver detalle: ${direccion.etiqueta}');
  }

  /// ✅ CORREGIDO: Manejo más robusto de acciones
  void _accionDireccion(String accion, DireccionModel direccion) async {
    switch (accion) {
      // 🌟 MARCAR COMO PREDETERMINADA
      case 'predeterminada':
        final exito = await _controller.establecerDireccionPredeterminada(
          direccion.id,
        );

        if (!mounted) return;

        if (exito) {
          JPSnackbar.success(context, 'Dirección predeterminada actualizada');
          // ✅ El controlador ya actualiza su estado interno, solo refrescar UI
          setState(() {});
        } else {
          JPSnackbar.error(context, 'Error al actualizar');
        }
        break;

      // ✏️ EDITAR DIRECCIÓN
      case 'editar':
        final resultado = await Navigator.push<bool>(
          context,
          MaterialPageRoute(
            builder: (context) =>
                PantallaAgregarDireccion(direccion: direccion),
          ),
        );

        if (resultado == true) {
          debugPrint('✅ Dirección editada, recargando...');
          await _controller.recargarDirecciones();

          if (mounted) {
            setState(() {});
          }
        }
        break;

      // 🗑️ ELIMINAR DIRECCIÓN
      case 'eliminar':
        _confirmarEliminarDireccion(direccion);
        break;
    }
  }

  /// ✅ CORREGIDO: Confirmación mejorada
  void _confirmarEliminarDireccion(DireccionModel direccion) {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Eliminar dirección'),
        content: Text('¿Estás seguro de eliminar "${direccion.etiqueta}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(dialogContext);

              debugPrint('🗑️ Eliminando dirección: ${direccion.id}');

              final exito = await _controller.eliminarDireccion(direccion.id);

              debugPrint('   Resultado: ${exito ? "✅ Éxito" : "❌ Error"}');
              debugPrint(
                '   Direcciones restantes: ${_controller.direcciones?.length ?? 0}',
              );

              if (!mounted) return;

              if (exito) {
                JPSnackbar.success(context, 'Dirección eliminada');
                // ✅ El controlador ya actualizó su lista, solo refrescar UI
                setState(() {});
              } else {
                JPSnackbar.error(context, 'Error al eliminar');
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: JPColors.error),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );
  }

  void _cambiarNotificacionPedidos(bool value) async {
    final exito = await _controller.actualizarNotificaciones(
      notificacionesPedido: value,
    );

    if (!mounted) return;

    if (exito) {
      JPSnackbar.success(
        context,
        value
            ? 'Notificaciones de pedidos activadas'
            : 'Notificaciones de pedidos desactivadas',
      );
    } else {
      JPSnackbar.error(context, 'Error al actualizar notificaciones');
    }
  }

  void _cambiarNotificacionPromociones(bool value) async {
    final exito = await _controller.actualizarNotificaciones(
      notificacionesPromociones: value,
    );

    if (!mounted) return;

    if (exito) {
      JPSnackbar.success(
        context,
        value
            ? 'Notificaciones de promociones activadas'
            : 'Notificaciones de promociones desactivadas',
      );
    } else {
      JPSnackbar.error(context, 'Error al actualizar notificaciones');
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 🚪 CERRAR SESIÓN
  // ══════════════════════════════════════════════════════════════════════════

  void _confirmarCerrarSesion() {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.logout, color: JPColors.error),
            SizedBox(width: 12),
            Text('Cerrar Sesión'),
          ],
        ),
        content: const Text(
          '¿Estás seguro de que deseas cerrar sesión?',
          style: TextStyle(fontSize: 16),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(dialogContext);
              _cerrarSesion();
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: JPColors.error,
              foregroundColor: Colors.white,
            ),
            child: const Text('Cerrar Sesión'),
          ),
        ],
      ),
    );
  }

  void _cerrarSesion() async {
    // Mostrar indicador de carga
    if (!mounted) return;

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(
        child: Card(
          child: Padding(
            padding: EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 16),
                Text('Cerrando sesión...'),
              ],
            ),
          ),
        ),
      ),
    );

    try {
      // Aquí deberías llamar a tu servicio de autenticación
      // Ejemplo: await AuthService.logout();

      // Simular delay de logout
      await Future.delayed(const Duration(seconds: 1));

      if (!mounted) return;

      // Cerrar el diálogo de carga
      Navigator.pop(context);

      // Navegar a la pantalla de login y limpiar el stack de navegación
      Navigator.of(context).pushNamedAndRemoveUntil(
        '/login', // Cambia esto por tu ruta de login
        (route) => false,
      );

      // Mostrar mensaje de confirmación
      JPSnackbar.show(context, 'Sesión cerrada exitosamente');
    } catch (e) {
      if (!mounted) return;

      // Cerrar el diálogo de carga
      Navigator.pop(context);

      // Mostrar error
      JPSnackbar.error(context, 'Error al cerrar sesión: ${e.toString()}');
    }
  }
}
