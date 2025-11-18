// lib/screens/user/perfil/solicitudes_rol/pantalla_mis_solicitudes.dart

import 'package:flutter/material.dart';
import '../../../../theme/jp_theme.dart';
import '../../../../services/solicitudes_service.dart';
import '../../../../models/solicitud_cambio_rol.dart';
import 'pantalla_solicitar_rol.dart';

/// 📋 PANTALLA DE MIS SOLICITUDES DE CAMBIO DE ROL
class PantallaMisSolicitudes extends StatefulWidget {
  const PantallaMisSolicitudes({super.key});

  @override
  State<PantallaMisSolicitudes> createState() => _PantallaMisSolicitudesState();
}

class _PantallaMisSolicitudesState extends State<PantallaMisSolicitudes>
    with SingleTickerProviderStateMixin {
  // ══════════════════════════════════════════════════════════════════════════════
  // 📋 ESTADO Y CONTROLADORES
  // ══════════════════════════════════════════════════════════════════════════════

  final _solicitudesService = SolicitudesService();
  late TabController _tabController;

  List<SolicitudCambioRol> _todasLasSolicitudes = [];
  bool _isLoading = true;
  String? _error;

  // ══════════════════════════════════════════════════════════════════════════════
  // 🔄 LIFECYCLE
  // ══════════════════════════════════════════════════════════════════════════════

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _cargarSolicitudes();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 🌐 CARGA DE DATOS
  // ══════════════════════════════════════════════════════════════════════════════

  Future<void> _cargarSolicitudes() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final response = await _solicitudesService.obtenerMisSolicitudes();
      final solicitudesJson = response['solicitudes'] as List<dynamic>?;

      if (solicitudesJson != null) {
        _todasLasSolicitudes = solicitudesJson
            .map((json) => SolicitudCambioRol.fromJson(json))
            .toList();
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 🎨 BUILD
  // ══════════════════════════════════════════════════════════════════════════════

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: _buildAppBar(),
      body: _isLoading
          ? _buildLoadingState()
          : _error != null
          ? _buildErrorState()
          : _buildContent(),
      floatingActionButton: _buildFAB(),
    );
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 🧩 WIDGETS PRINCIPALES
  // ══════════════════════════════════════════════════════════════════════════════

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      title: const Text('Mis Solicitudes'),
      bottom: TabBar(
        controller: _tabController,
        isScrollable: true,
        indicatorColor: Colors.white,
        labelColor: Colors.white,
        unselectedLabelColor: Colors.white70,
        tabs: [
          Tab(
            child: Row(
              children: [
                const Text('Todas'),
                const SizedBox(width: 8),
                _buildBadgeCount(_todasLasSolicitudes.length),
              ],
            ),
          ),
          Tab(
            child: Row(
              children: [
                const Text('Pendientes'),
                const SizedBox(width: 8),
                _buildBadgeCount(_todasLasSolicitudes.pendientes.length),
              ],
            ),
          ),
          Tab(
            child: Row(
              children: [
                const Text('Aceptadas'),
                const SizedBox(width: 8),
                _buildBadgeCount(_todasLasSolicitudes.aceptadas.length),
              ],
            ),
          ),
          Tab(
            child: Row(
              children: [
                const Text('Rechazadas'),
                const SizedBox(width: 8),
                _buildBadgeCount(_todasLasSolicitudes.rechazadas.length),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBadgeCount(int count) {
    if (count == 0) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        count.toString(),
        style: const TextStyle(
          color: JPColors.primary,
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildContent() {
    return RefreshIndicator(
      onRefresh: _cargarSolicitudes,
      color: JPColors.primary,
      child: TabBarView(
        controller: _tabController,
        children: [
          _buildListaSolicitudes(_todasLasSolicitudes),
          _buildListaSolicitudes(_todasLasSolicitudes.pendientes),
          _buildListaSolicitudes(_todasLasSolicitudes.aceptadas),
          _buildListaSolicitudes(_todasLasSolicitudes.rechazadas),
        ],
      ),
    );
  }

  Widget _buildListaSolicitudes(List<SolicitudCambioRol> solicitudes) {
    if (solicitudes.isEmpty) {
      return _buildEmptyState();
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: solicitudes.length,
      itemBuilder: (context, index) {
        return _buildSolicitudCard(solicitudes[index]);
      },
    );
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 🎴 CARD DE SOLICITUD
  // ══════════════════════════════════════════════════════════════════════════════

  Widget _buildSolicitudCard(SolicitudCambioRol solicitud) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: solicitud.colorEstado.withValues(alpha: 0.3),
          width: 1,
        ),
      ),
      child: InkWell(
        onTap: () => _verDetalle(solicitud),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header: Rol + Estado
              Row(
                children: [
                  // Icono del rol
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: JPColors.info.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(
                      solicitud.iconoRol,
                      color: JPColors.info,
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 12),

                  // Título
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(solicitud.rolTexto, style: JPTextStyles.h4),
                        const SizedBox(height: 4),
                        Text(
                          solicitud.fechaCreacionFormateada,
                          style: JPTextStyles.caption,
                        ),
                      ],
                    ),
                  ),

                  // Badge de estado
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: solicitud.colorEstado.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                        color: solicitud.colorEstado,
                        width: 1.5,
                      ),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          solicitud.iconoEstado,
                          size: 14,
                          color: solicitud.colorEstado,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          solicitud.estadoTexto,
                          style: TextStyle(
                            color: solicitud.colorEstado,
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 16),
              const Divider(height: 1),
              const SizedBox(height: 16),

              // Datos específicos
              _buildDatosEspecificos(solicitud),

              const SizedBox(height: 12),

              // Motivo (preview)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.grey.shade50,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(
                          Icons.message_outlined,
                          size: 16,
                          color: JPColors.textSecondary,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'Motivo',
                          style: JPTextStyles.caption.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      solicitud.motivo.length > 100
                          ? '${solicitud.motivo.substring(0, 100)}...'
                          : solicitud.motivo,
                      style: JPTextStyles.caption,
                    ),
                  ],
                ),
              ),

              // Días pendiente (si aplica)
              if (solicitud.estaPendiente && solicitud.diasPendiente != null)
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.schedule,
                        size: 16,
                        color: JPColors.warning,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'Pendiente hace ${solicitud.diasPendienteTexto}',
                        style: JPTextStyles.caption.copyWith(
                          color: JPColors.warning,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),

              // Respuesta del admin (si aplica)
              if (solicitud.motivoRespuesta != null) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: solicitud.fueAceptada
                        ? JPColors.success.withValues(alpha: 0.1)
                        : JPColors.error.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: solicitud.fueAceptada
                          ? JPColors.success
                          : JPColors.error,
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            solicitud.fueAceptada
                                ? Icons.check_circle_outline
                                : Icons.cancel_outlined,
                            size: 16,
                            color: solicitud.fueAceptada
                                ? JPColors.success
                                : JPColors.error,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            'Respuesta del Administrador',
                            style: JPTextStyles.caption.copyWith(
                              fontWeight: FontWeight.bold,
                              color: solicitud.fueAceptada
                                  ? JPColors.success
                                  : JPColors.error,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        solicitud.motivoRespuesta!,
                        style: JPTextStyles.caption,
                      ),
                      if (solicitud.fechaRespuestaFormateada != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          solicitud.fechaRespuestaFormateada!,
                          style: JPTextStyles.small.copyWith(
                            fontStyle: FontStyle.italic,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ],

              // Botón ver detalle
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () => _verDetalle(solicitud),
                  icon: const Icon(Icons.visibility, size: 18),
                  label: const Text('Ver Detalle Completo'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    side: BorderSide(color: Colors.grey.shade300),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDatosEspecificos(SolicitudCambioRol solicitud) {
    if (solicitud.esProveedor) {
      return Column(
        children: [
          _buildDatoRow(Icons.receipt_long, 'RUC', solicitud.ruc ?? 'N/A'),
          const SizedBox(height: 8),
          _buildDatoRow(
            Icons.store,
            'Negocio',
            solicitud.nombreComercial ?? 'N/A',
          ),
          const SizedBox(height: 8),
          _buildDatoRow(
            Icons.category,
            'Tipo',
            solicitud.tipoNegocioTexto ?? 'N/A',
          ),
        ],
      );
    } else {
      return Column(
        children: [
          _buildDatoRow(
            Icons.badge,
            'Cédula',
            solicitud.cedulaIdentidad ?? 'N/A',
          ),
          const SizedBox(height: 8),
          _buildDatoRow(
            Icons.two_wheeler,
            'Vehículo',
            solicitud.tipoVehiculoTexto ?? 'N/A',
          ),
          const SizedBox(height: 8),
          _buildDatoRow(
            Icons.location_on,
            'Zona',
            solicitud.zonaCobertura ?? 'N/A',
          ),
        ],
      );
    }
  }

  Widget _buildDatoRow(IconData icon, String label, String value) {
    return Row(
      children: [
        Icon(icon, size: 16, color: JPColors.textSecondary),
        const SizedBox(width: 8),
        Text(
          '$label:',
          style: JPTextStyles.caption.copyWith(fontWeight: FontWeight.w600),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            value,
            style: JPTextStyles.caption,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 🎨 ESTADOS
  // ══════════════════════════════════════════════════════════════════════════════

  Widget _buildLoadingState() {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: 3,
      itemBuilder: (context, index) {
        return Card(
          margin: const EdgeInsets.only(bottom: 16),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    JPSkeleton(
                      width: 40,
                      height: 40,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          JPSkeleton(
                            width: double.infinity,
                            height: 20,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          const SizedBox(height: 8),
                          JPSkeleton(
                            width: 150,
                            height: 16,
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ],
                      ),
                    ),
                    JPSkeleton(
                      width: 80,
                      height: 30,
                      borderRadius: BorderRadius.circular(20),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                JPSkeleton(
                  width: double.infinity,
                  height: 60,
                  borderRadius: BorderRadius.circular(8),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildEmptyState() {
    return JPEmptyState(
      icon: Icons.inbox_outlined,
      message: 'No tienes solicitudes en esta categoría',
      actionLabel: 'Crear Nueva Solicitud',
      onAction: _crearNuevaSolicitud,
    );
  }

  Widget _buildErrorState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 80, color: JPColors.error),
            const SizedBox(height: 16),
            Text(
              'Error al cargar solicitudes',
              style: JPTextStyles.h3,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              _error ?? 'Ocurrió un error desconocido',
              style: JPTextStyles.bodySecondary,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _cargarSolicitudes,
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
            ),
          ],
        ),
      ),
    );
  }

  Widget? _buildFAB() {
    if (_isLoading) return null;

    return FloatingActionButton.extended(
      onPressed: _crearNuevaSolicitud,
      icon: const Icon(Icons.add),
      label: const Text('Nueva Solicitud'),
      backgroundColor: JPColors.secondary,
    );
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 🎬 ACCIONES
  // ══════════════════════════════════════════════════════════════════════════════

  void _verDetalle(SolicitudCambioRol solicitud) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Row(
          children: [
            Icon(solicitud.iconoRol, color: JPColors.info),
            const SizedBox(width: 12),
            Expanded(child: Text(solicitud.rolTexto)),
          ],
        ),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              // Estado
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: solicitud.colorEstado.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: solicitud.colorEstado),
                ),
                child: Row(
                  children: [
                    Icon(solicitud.iconoEstado, color: solicitud.colorEstado),
                    const SizedBox(width: 12),
                    Text(
                      solicitud.estadoTexto,
                      style: TextStyle(
                        color: solicitud.colorEstado,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 16),

              // Datos específicos completos
              if (solicitud.esProveedor) ...[
                _buildDetalleItem('RUC', solicitud.ruc ?? 'N/A'),
                _buildDetalleItem('Nombre', solicitud.nombreComercial ?? 'N/A'),
                _buildDetalleItem('Tipo', solicitud.tipoNegocioTexto ?? 'N/A'),
                _buildDetalleItem(
                  'Descripción',
                  solicitud.descripcionNegocio ?? 'N/A',
                ),
                if (solicitud.horarioApertura != null)
                  _buildDetalleItem(
                    'Horario',
                    '${solicitud.horarioApertura} - ${solicitud.horarioCierre ?? "N/A"}',
                  ),
              ] else ...[
                _buildDetalleItem('Cédula', solicitud.cedulaIdentidad ?? 'N/A'),
                _buildDetalleItem(
                  'Vehículo',
                  solicitud.tipoVehiculoTexto ?? 'N/A',
                ),
                _buildDetalleItem('Zona', solicitud.zonaCobertura ?? 'N/A'),
              ],

              const Divider(height: 24),

              // Motivo completo
              Text(
                'Motivo:',
                style: JPTextStyles.body.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(solicitud.motivo, style: JPTextStyles.caption),

              // Respuesta del admin
              if (solicitud.motivoRespuesta != null) ...[
                const Divider(height: 24),
                Text(
                  'Respuesta:',
                  style: JPTextStyles.body.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                Text(solicitud.motivoRespuesta!, style: JPTextStyles.caption),
                if (solicitud.fechaRespuestaFormateada != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    solicitud.fechaRespuestaFormateada!,
                    style: JPTextStyles.small.copyWith(
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ],
              ],
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cerrar'),
          ),
        ],
      ),
    );
  }

  Widget _buildDetalleItem(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: JPTextStyles.caption.copyWith(
              fontWeight: FontWeight.bold,
              color: JPColors.textSecondary,
            ),
          ),
          const SizedBox(height: 4),
          Text(value, style: JPTextStyles.body),
        ],
      ),
    );
  }

  void _crearNuevaSolicitud() async {
    final resultado = await Navigator.push<bool>(
      context,
      MaterialPageRoute(builder: (context) => const PantallaSolicitarRol()),
    );

    if (resultado == true) {
      _cargarSolicitudes();
    }
  }
}
