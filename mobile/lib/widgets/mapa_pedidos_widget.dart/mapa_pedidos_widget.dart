// lib/widgets/mapa_pedidos_widget.dart

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:geolocator/geolocator.dart';
import '../../models/pedido.dart';
import '../../services/repartidor_service.dart';
import '../../apis/subapis/http_client.dart';
import '../../config/api_config.dart';
import 'dart:developer' as developer;

class MapaPedidosScreen extends StatefulWidget {
  const MapaPedidosScreen({super.key});

  @override
  State<MapaPedidosScreen> createState() => _MapaPedidosScreenState();
}

class _MapaPedidosScreenState extends State<MapaPedidosScreen> {
  // ============================================
  // CONTROLADORES Y SERVICIOS
  // ============================================
  final RepartidorService _service = RepartidorService();
  final ApiClient _apiClient = ApiClient();
  GoogleMapController? _mapController;
  Timer? _ubicacionTimer;

  // ============================================
  // ESTADO
  // ============================================
  Set<Marker> _markers = {};
  Position? _ubicacionActual;
  PedidosDisponiblesResponse? _pedidosResponse;
  bool _cargando = true;
  double _radioKm = 15.0;
  String? _rolUsuario; // ✅ Cache del rol

  // ============================================
  // LIFECYCLE
  // ============================================
  @override
  void initState() {
    super.initState();
    _inicializarMapa();
  }

  @override
  void dispose() {
    _ubicacionTimer?.cancel();
    _mapController?.dispose();
    super.dispose();
  }

  // ============================================
  // INICIALIZACIÓN
  // ============================================
  Future<void> _inicializarMapa() async {
    try {
      // ✅ PRIMERO: Verificar rol del usuario
      await _verificarRolUsuario();

      // ✅ SEGUNDO: Si no es repartidor, mostrar error y salir
      if (_rolUsuario != ApiConfig.rolRepartidor) {
        setState(() => _cargando = false);
        return;
      }

      // ✅ TERCERO: Continuar con inicialización normal
      await _obtenerUbicacionActual();
      await _cargarPedidosDisponibles();
      _iniciarActualizacionAutomatica();
    } catch (e) {
      _mostrarError('Error al inicializar mapa: $e');
    } finally {
      if (mounted) {
        setState(() => _cargando = false);
      }
    }
  }

  // ============================================
  // ✅ VERIFICACIÓN DE ROL
  // ============================================
  Future<void> _verificarRolUsuario() async {
    try {
      final info = await _apiClient.get(ApiConfig.infoRol);
      _rolUsuario = info['rol'];
      developer.log('👤 Rol del usuario: $_rolUsuario', name: 'MapaPedidos');

      // Advertencia si no es repartidor
      if (_rolUsuario != ApiConfig.rolRepartidor) {
        developer.log(
          '⚠️ ADVERTENCIA: Usuario con rol $_rolUsuario intentando acceder a pantalla de repartidor',
          name: 'MapaPedidos',
        );
      }
    } catch (e) {
      developer.log('❌ Error verificando rol: $e', name: 'MapaPedidos');
      _rolUsuario = null;
      rethrow;
    }
  }

  // ============================================
  // ACTUALIZACIÓN DE UBICACIÓN
  // ============================================
  Future<void> _obtenerUbicacionActual() async {
    try {
      LocationPermission permission = await Geolocator.checkPermission();

      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          throw Exception('Permisos de ubicación denegados');
        }
      }

      if (permission == LocationPermission.deniedForever) {
        throw Exception('Permisos de ubicación permanentemente denegados');
      }

      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );

      setState(() => _ubicacionActual = position);
    } catch (e) {
      debugPrint('Error obteniendo ubicación: $e');
      rethrow;
    }
  }

  void _iniciarActualizacionAutomatica() {
    _ubicacionTimer = Timer.periodic(
      const Duration(seconds: 30),
      (_) => _actualizarTodo(),
    );
  }

  Future<void> _actualizarTodo() async {
    await _obtenerUbicacionActual();
    await _cargarPedidosDisponibles();
  }

  // ============================================
  // CARGAR PEDIDOS
  // ============================================
  Future<void> _cargarPedidosDisponibles() async {
    if (_ubicacionActual == null) {
      _mostrarError('No se ha obtenido tu ubicación actual');
      return;
    }

    try {
      // ✅ NUEVO: Enviar ubicación explícita en la petición
      final response = await _service.obtenerPedidosDisponibles(
        radioKm: _radioKm,
        latitud: _ubicacionActual!.latitude,
        longitud: _ubicacionActual!.longitude,
      );

      setState(() {
        _pedidosResponse = response;
        _actualizarMarcadores();
      });
    } catch (e) {
      _mostrarError('Error al cargar pedidos: $e');
    }
  }

  void _actualizarMarcadores() {
    if (_pedidosResponse == null || _ubicacionActual == null) return;

    final markers = <Marker>{};

    markers.add(
      Marker(
        markerId: const MarkerId('mi_ubicacion'),
        position: LatLng(
          _ubicacionActual!.latitude,
          _ubicacionActual!.longitude,
        ),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(title: 'Mi ubicación'),
      ),
    );

    for (final pedido in _pedidosResponse!.pedidos) {
      markers.add(
        Marker(
          markerId: MarkerId('pedido_${pedido.id}'),
          position: LatLng(pedido.latitud, pedido.longitud),
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
          infoWindow: InfoWindow(
            title:
                '${pedido.distanciaKm.toStringAsFixed(1)}km - \$${pedido.montoTotal.toStringAsFixed(2)}',
            snippet: pedido.direccionEntrega,
          ),
          onTap: () => _mostrarDetallePedido(pedido),
        ),
      );
    }

    setState(() => _markers = markers);
  }

  // ============================================
  // ACCIONES DE PEDIDO
  // ============================================
  void _mostrarDetallePedido(PedidoDisponible pedido) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _buildDetallePedido(pedido),
    );
  }

  Widget _buildDetallePedido(PedidoDisponible pedido) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              const Icon(Icons.delivery_dining, size: 32, color: Colors.orange),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Pedido #${pedido.id}',
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      pedido.clienteNombre,
                      style: TextStyle(color: Colors.grey[600]),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const Divider(height: 32),
          _buildInfoRow(
            Icons.location_on,
            'Dirección',
            pedido.direccionEntrega,
          ),
          const SizedBox(height: 12),
          _buildInfoRow(
            Icons.route,
            'Distancia',
            '${pedido.distanciaKm.toStringAsFixed(1)} km',
          ),
          const SizedBox(height: 12),
          _buildInfoRow(
            Icons.timer,
            'Tiempo estimado',
            '~${pedido.tiempoEstimadoMin} min',
          ),
          const SizedBox(height: 12),
          _buildInfoRow(
            Icons.attach_money,
            'Monto',
            '\$${pedido.montoTotal.toStringAsFixed(2)}',
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () {
                    Navigator.pop(context);
                    _rechazarPedido(pedido.id);
                  },
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.red,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  child: const Text('Rechazar'),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                flex: 2,
                child: ElevatedButton(
                  onPressed: () {
                    Navigator.pop(context);
                    _aceptarPedido(pedido.id);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  child: const Text(
                    'Aceptar pedido',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Row(
      children: [
        Icon(icon, size: 20, color: Colors.grey[600]),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: TextStyle(fontSize: 12, color: Colors.grey[600]),
              ),
              Text(
                value,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Future<void> _aceptarPedido(int pedidoId) async {
    try {
      if (!mounted) return;
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => const Center(child: CircularProgressIndicator()),
      );

      await _service.aceptarPedido(pedidoId);

      if (!mounted) return;
      Navigator.pop(context);

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('✅ Pedido aceptado correctamente'),
          backgroundColor: Colors.green,
        ),
      );

      await _cargarPedidosDisponibles();
    } catch (e) {
      if (!mounted) return;
      Navigator.pop(context);
      _mostrarError('Error al aceptar pedido: $e');
    }
  }

  Future<void> _rechazarPedido(int pedidoId) async {
    try {
      await _service.rechazarPedido(pedidoId, motivo: 'Muy lejos');

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Pedido rechazado'),
          backgroundColor: Colors.orange,
        ),
      );

      await _cargarPedidosDisponibles();
    } catch (e) {
      _mostrarError('Error al rechazar pedido: $e');
    }
  }

  void _mostrarCambiarRadio() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Radio de búsqueda'),
        content: StatefulBuilder(
          builder: (context, setDialogState) => Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '${_radioKm.toStringAsFixed(0)} km',
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Slider(
                value: _radioKm,
                min: 5,
                max: 30,
                divisions: 25,
                label: '${_radioKm.toStringAsFixed(0)} km',
                onChanged: (value) {
                  setDialogState(() => _radioKm = value);
                  setState(() => _radioKm = value);
                },
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              _cargarPedidosDisponibles();
            },
            child: const Text('Aplicar'),
          ),
        ],
      ),
    );
  }

  void _mostrarError(String mensaje) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(mensaje), backgroundColor: Colors.red),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_cargando) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    // ✅ PANTALLA DE ACCESO DENEGADO
    if (_rolUsuario != ApiConfig.rolRepartidor) {
      return Scaffold(
        appBar: AppBar(title: const Text('Acceso Denegado')),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.block, size: 80, color: Colors.red.shade300),
                const SizedBox(height: 24),
                const Text(
                  'Acceso restringido',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 16),
                Text(
                  'Esta pantalla es solo para repartidores.\nTu rol actual: ${_rolUsuario ?? "Desconocido"}',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 16, color: Colors.grey[600]),
                ),
                const SizedBox(height: 32),
                ElevatedButton.icon(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.arrow_back),
                  label: const Text('Volver'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 32,
                      vertical: 16,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    // ✅ PANTALLA NORMAL (solo para repartidores)
    return Scaffold(
      appBar: AppBar(
        title: const Text('Pedidos Disponibles'),
        actions: [
          IconButton(
            icon: const Icon(Icons.tune),
            onPressed: _mostrarCambiarRadio,
            tooltip: 'Cambiar radio',
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _cargarPedidosDisponibles,
            tooltip: 'Actualizar',
          ),
        ],
      ),
      body: _ubicacionActual == null
          ? _buildErrorUbicacion()
          : Stack(
              children: [
                GoogleMap(
                  initialCameraPosition: CameraPosition(
                    target: LatLng(
                      _ubicacionActual!.latitude,
                      _ubicacionActual!.longitude,
                    ),
                    zoom: 14,
                  ),
                  markers: _markers,
                  myLocationEnabled: true,
                  myLocationButtonEnabled: true,
                  zoomControlsEnabled: false,
                  mapToolbarEnabled: false,
                  onMapCreated: (controller) => _mapController = controller,
                ),
                if (_pedidosResponse != null)
                  Positioned(
                    top: 16,
                    left: 16,
                    right: 16,
                    child: _buildPanelInfo(),
                  ),
              ],
            ),
    );
  }

  Widget _buildPanelInfo() {
    final totalPedidos = _pedidosResponse?.totalPedidos ?? 0;

    return Card(
      elevation: 4,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.orange.shade100,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(
                    Icons.delivery_dining,
                    color: Colors.orange.shade700,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '$totalPedidos pedido${totalPedidos != 1 ? 's' : ''} disponible${totalPedidos != 1 ? 's' : ''}',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        'Radio: ${_radioKm.toStringAsFixed(0)} km',
                        style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                      ),
                    ],
                  ),
                ),
                if (totalPedidos > 0)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.green,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '$totalPedidos',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
              ],
            ),
            if (totalPedidos == 0) ...[
              const SizedBox(height: 12),
              Text(
                'No hay pedidos disponibles en tu zona',
                style: TextStyle(color: Colors.grey[600], fontSize: 12),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildErrorUbicacion() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.location_off, size: 64, color: Colors.grey[400]),
          const SizedBox(height: 16),
          const Text(
            'No se pudo obtener tu ubicación',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text(
            'Verifica que los permisos de ubicación estén activados',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey[600]),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: _inicializarMapa,
            icon: const Icon(Icons.refresh),
            label: const Text('Reintentar'),
          ),
        ],
      ),
    );
  }
}
