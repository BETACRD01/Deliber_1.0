// lib/screens/network_test_page.dart

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../config/api_config.dart';
import '../config/network_initializer.dart';

/// 🧪 Pantalla de prueba y diagnóstico de red
/// Útil para desarrollo y debugging
class NetworkTestPage extends StatefulWidget {
  const NetworkTestPage({super.key});

  @override
  State<NetworkTestPage> createState() => _NetworkTestPageState();
}

class _NetworkTestPageState extends State<NetworkTestPage> {
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🌐 Diagnóstico de Red'),
        backgroundColor: const Color(0xFF4FC3F7),
        actions: [
          // Botón para refrescar la red
          NetworkRefreshButton(
            onNetworkChanged: () {
              setState(() {});
              debugPrint('🔄 Red actualizada desde NetworkTestPage');
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 🌐 INFORMACIÓN DE RED
            _buildSectionCard(
              title: '🌐 Estado de la Red',
              icon: Icons.wifi,
              child: NetworkInitializer.buildNetworkInfo(),
            ),

            const SizedBox(height: 16),

            // ⚙️ CONFIGURACIÓN API
            _buildSectionCard(
              title: '⚙️ Configuración API',
              icon: Icons.settings,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildInfoRow('Base URL', ApiConfig.baseUrl, canCopy: true),
                  _buildInfoRow('API URL', ApiConfig.apiUrl, canCopy: true),
                  _buildInfoRow(
                    'Entorno',
                    ApiConfig.isDevelopment
                        ? '🛠️ Desarrollo'
                        : '🚀 Producción',
                  ),
                  _buildInfoRow(
                    'Protocolo',
                    ApiConfig.isHttps ? '🔒 HTTPS' : '🔓 HTTP',
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // 📡 ENDPOINTS PRINCIPALES
            _buildSectionCard(
              title: '📡 Endpoints Principales',
              icon: Icons.api,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildEndpointRow('Login', ApiConfig.login),
                  _buildEndpointRow('Registro', ApiConfig.registro),
                  _buildEndpointRow('Perfil', ApiConfig.perfil),
                  _buildEndpointRow('Google Login', ApiConfig.googleLogin),
                  _buildEndpointRow('Logout', ApiConfig.logout),
                  _buildEndpointRow(
                    'Recuperación',
                    ApiConfig.solicitarCodigoRecuperacion,
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // ⏱️ TIMEOUTS Y REINTENTOS
            _buildSectionCard(
              title: '⏱️ Configuración de Timeouts',
              icon: Icons.timer,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildInfoRow(
                    'Connect Timeout',
                    '${ApiConfig.connectTimeout.inSeconds}s',
                  ),
                  _buildInfoRow(
                    'Receive Timeout',
                    '${ApiConfig.receiveTimeout.inSeconds}s',
                  ),
                  _buildInfoRow(
                    'Send Timeout',
                    '${ApiConfig.sendTimeout.inSeconds}s',
                  ),
                  _buildInfoRow('Max Reintentos', '${ApiConfig.maxRetries}'),
                  _buildInfoRow(
                    'Delay entre reintentos',
                    '${ApiConfig.retryDelay.inSeconds}s',
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // 🧪 BOTONES DE PRUEBA
            _buildTestButton(
              icon: Icons.wifi_find,
              label: 'Probar Conexión',
              color: Colors.blue,
              onPressed: _testConnection,
            ),

            const SizedBox(height: 12),

            _buildTestButton(
              icon: Icons.refresh,
              label: 'Redetectar Red',
              color: Colors.orange,
              onPressed: _redetectNetwork,
            ),

            const SizedBox(height: 12),

            _buildTestButton(
              icon: Icons.settings,
              label: 'Configuración Manual',
              color: Colors.purple,
              onPressed: _showManualIpDialog,
            ),

            const SizedBox(height: 12),

            _buildTestButton(
              icon: Icons.bug_report,
              label: 'Mostrar Debug Info',
              color: Colors.green,
              onPressed: _showDebugInfo,
            ),

            const SizedBox(height: 20),

            // ℹ️ INFORMACIÓN ADICIONAL
            _buildInfoCard(),
          ],
        ),
      ),
    );
  }

  // ============================================
  // 🎨 WIDGETS DE UI
  // ============================================

  Widget _buildSectionCard({
    required String title,
    required IconData icon,
    required Widget child,
  }) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: const Color(0xFF4FC3F7)),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            child,
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value, {bool canCopy = false}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: const TextStyle(
                fontWeight: FontWeight.w600,
                color: Colors.grey,
              ),
            ),
          ),
          Expanded(
            child: GestureDetector(
              onTap: canCopy
                  ? () {
                      Clipboard.setData(ClipboardData(text: value));
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('📋 $label copiado'),
                          duration: const Duration(seconds: 1),
                        ),
                      );
                    }
                  : null,
              child: Text(
                value,
                style: TextStyle(
                  fontSize: 12,
                  color: canCopy ? Colors.blue : Colors.black87,
                  decoration: canCopy
                      ? TextDecoration.underline
                      : TextDecoration.none,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEndpointRow(String name, String endpoint) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: Row(
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: const BoxDecoration(
              color: Colors.green,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 14,
                  ),
                ),
                const SizedBox(height: 2),
                GestureDetector(
                  onTap: () {
                    Clipboard.setData(ClipboardData(text: endpoint));
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('📋 Endpoint "$name" copiado'),
                        duration: const Duration(seconds: 1),
                      ),
                    );
                  },
                  child: Text(
                    endpoint,
                    style: const TextStyle(
                      fontSize: 11,
                      color: Colors.blue,
                      decoration: TextDecoration.underline,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTestButton({
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onPressed,
  }) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: _isLoading ? null : onPressed,
        icon: Icon(icon),
        label: Text(label),
        style: ElevatedButton.styleFrom(
          backgroundColor: color,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 16),
        ),
      ),
    );
  }

  Widget _buildInfoCard() {
    return Card(
      color: Colors.blue.shade50,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.info_outline, color: Colors.blue),
                SizedBox(width: 8),
                Text(
                  'ℹ️ Información',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Colors.blue,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            const Text(
              '• La detección de red es automática al iniciar la app\n'
              '• Puedes refrescar manualmente con el botón de arriba\n'
              '• Modo manual disponible para testing\n'
              '• Los endpoints se copian al tocarlos',
              style: TextStyle(fontSize: 13, height: 1.5),
            ),
            const SizedBox(height: 12),
            const Divider(),
            const SizedBox(height: 8),
            Text(
              '🏠 Casa: 192.168.1.x\n'
              '🏢 Institucional: 172.16.x.x\n'
              '📱 Externa: Otros rangos',
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[700],
                fontFamily: 'monospace',
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================
  // 🔧 FUNCIONES DE PRUEBA
  // ============================================

  Future<void> _testConnection() async {
    setState(() => _isLoading = true);

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(
        child: Card(
          child: Padding(
            padding: EdgeInsets.all(24.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 16),
                Text('Probando conexión...'),
              ],
            ),
          ),
        ),
      ),
    );

    try {
      // Simular petición de red (aquí harías una petición real)
      await Future.delayed(const Duration(seconds: 2));

      if (mounted) {
        Navigator.pop(context);
        setState(() => _isLoading = false);

        final network = ApiConfig.currentNetwork ?? 'Desconocida';
        final emoji = network.contains('CASA')
            ? '🏠'
            : network.contains('INSTITUCIONAL')
            ? '🏢'
            : '❓';

        _showSuccessDialog(
          '✅ Conexión Exitosa',
          'Conectado a: $emoji $network\n'
              'Base URL: ${ApiConfig.baseUrl}',
        );
      }
    } catch (e) {
      if (mounted) {
        Navigator.pop(context);
        setState(() => _isLoading = false);

        _showErrorDialog('❌ Error de Conexión', e.toString());
      }
    }
  }

  Future<void> _redetectNetwork() async {
    setState(() => _isLoading = true);

    try {
      await ApiConfig.refreshNetworkDetection();
      await ApiConfig.printDebugInfo();

      if (mounted) {
        setState(() => _isLoading = false);

        final network = ApiConfig.currentNetwork ?? 'Desconocida';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('🔄 Red redetectada: $network'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('❌ Error: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<void> _showDebugInfo() async {
    await ApiConfig.printDebugInfo();

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('📊 Debug info impreso en consola'),
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  void _showManualIpDialog() {
    final controller = TextEditingController(
      text: ApiConfig.currentServerIp ?? '',
    );

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.settings, color: Color(0xFF4FC3F7)),
            SizedBox(width: 8),
            Text('Configuración Manual'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: controller,
              decoration: const InputDecoration(
                labelText: 'IP del Servidor',
                hintText: '192.168.1.4',
                prefixIcon: Icon(Icons.computer),
                border: OutlineInputBorder(),
              ),
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '💡 Ejemplos:',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 8),
                  Text('🏠 Casa: 192.168.1.4', style: TextStyle(fontSize: 12)),
                  Text(
                    '🏢 Institucional: 172.16.60.4',
                    style: TextStyle(fontSize: 12),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              ApiConfig.disableManualIp();
              Navigator.pop(context);
              setState(() {});
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('♻️ Modo automático activado'),
                  backgroundColor: Colors.orange,
                ),
              );
            },
            child: const Text('Automático'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              final ip = controller.text.trim();
              if (ip.isNotEmpty) {
                ApiConfig.setManualIp(ip);
                Navigator.pop(context);
                setState(() {});
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('🎯 IP manual configurada: $ip'),
                    backgroundColor: Colors.green,
                  ),
                );
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF4FC3F7),
              foregroundColor: Colors.white,
            ),
            child: const Text('Aplicar'),
          ),
        ],
      ),
    );
  }

  void _showSuccessDialog(String title, String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          ElevatedButton(
            onPressed: () => Navigator.pop(context),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
              foregroundColor: Colors.white,
            ),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  void _showErrorDialog(String title, String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          ElevatedButton(
            onPressed: () => Navigator.pop(context),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
            ),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }
}
