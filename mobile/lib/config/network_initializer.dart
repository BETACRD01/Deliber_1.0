// lib/config/network_initializer.dart
import 'package:flutter/material.dart';
import 'api_config.dart';

/// 🌐 Inicializador de Red Inteligente
/// Wrapper que simplifica el uso de ApiConfig
class NetworkInitializer {
  /// Inicializar la detección de red al arrancar la app
  static Future<void> initialize() async {
    debugPrint('🚀 Inicializando detección de red...');
    await ApiConfig.detectServerIp();
    await ApiConfig.printDebugInfo();
  }

  /// Widget para mostrar información de red actual
  static Widget buildNetworkInfo() {
    final network = ApiConfig.currentNetwork ?? 'No detectada';
    final serverIp = ApiConfig.currentServerIp ?? 'N/A';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildInfoRow('Red Actual', network, _getNetworkIcon(network)),
        _buildInfoRow('IP Servidor', serverIp, Icons.dns),
        _buildInfoRow(
          'Estado',
          ApiConfig.currentServerIp != null ? 'Conectado' : 'Desconectado',
          ApiConfig.currentServerIp != null ? Icons.check_circle : Icons.error,
        ),
      ],
    );
  }

  static IconData _getNetworkIcon(String network) {
    if (network.contains('CASA')) return Icons.home;
    if (network.contains('INSTITUCIONAL')) return Icons.business;
    if (network.contains('DESCONOCIDA')) return Icons.help_outline;
    return Icons.public;
  }

  static Widget _buildInfoRow(String label, String value, IconData icon) {
    Color iconColor;
    if (label == 'Estado') {
      iconColor = value == 'Conectado' ? Colors.green : Colors.red;
    } else {
      iconColor = Colors.blue;
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Row(
        children: [
          Icon(icon, size: 20, color: iconColor),
          const SizedBox(width: 8),
          Text('$label: ', style: const TextStyle(fontWeight: FontWeight.w600)),
          Expanded(
            child: Text(value, style: const TextStyle(color: Colors.grey)),
          ),
        ],
      ),
    );
  }

  // Getters para acceso rápido
  static String? get currentNetwork => ApiConfig.currentNetwork;
  static String? get serverIp => ApiConfig.currentServerIp;
  static String get baseUrl => ApiConfig.baseUrl;
}

/// 🔄 Botón para refrescar la red manualmente
class NetworkRefreshButton extends StatefulWidget {
  final VoidCallback? onNetworkChanged;

  const NetworkRefreshButton({super.key, this.onNetworkChanged});

  @override
  State<NetworkRefreshButton> createState() => _NetworkRefreshButtonState();
}

class _NetworkRefreshButtonState extends State<NetworkRefreshButton> {
  bool _isRefreshing = false;

  Future<void> _refresh() async {
    setState(() => _isRefreshing = true);

    try {
      await ApiConfig.refreshNetworkDetection();
      widget.onNetworkChanged?.call();

      if (mounted) {
        setState(() => _isRefreshing = false);

        final network = ApiConfig.currentNetwork ?? 'Desconocida';
        final emoji = network.contains('CASA')
            ? '🏠'
            : network.contains('INSTITUCIONAL')
            ? '🏢'
            : '❓';

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('🔄 Red actualizada: $emoji $network'),
            duration: const Duration(seconds: 2),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isRefreshing = false);

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('❌ Error al actualizar: $e'),
            duration: const Duration(seconds: 3),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return IconButton(
      onPressed: _isRefreshing ? null : _refresh,
      icon: _isRefreshing
          ? const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : const Icon(Icons.refresh),
      tooltip: 'Refrescar red',
    );
  }
}
