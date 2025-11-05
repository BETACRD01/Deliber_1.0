import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import 'dart:async';
import '../config/api_config.dart';
import '../services/auth_service.dart';
import '../apis/helpers/api_exception.dart';

/// Pantalla de prueba de conexión con el backend - JP Express
/// Ejecuta múltiples tests para diagnosticar problemas de conectividad
class TestConnectionScreen extends StatefulWidget {
  const TestConnectionScreen({super.key});

  @override
  State<TestConnectionScreen> createState() => _TestConnectionScreenState();
}

class _TestConnectionScreenState extends State<TestConnectionScreen> {
  final List<Map<String, dynamic>> _testResults = [];
  bool _isLoading = false;
  int _currentTest = 0;
  final _api = AuthService();

  // Colores
  static const Color _azulPrincipal = Color(0xFF4FC3F7);

  @override
  void initState() {
    super.initState();
    // Imprimir configuración al iniciar
    ApiConfig.printDebugInfo();
  }

  // ============================================
  // EJECUTAR TODOS LOS TESTS
  // ============================================

  Future<void> _runAllTests() async {
    setState(() {
      _testResults.clear();
      _isLoading = true;
      _currentTest = 0;
    });

    await _testVerificarConfiguracion();
    await _testPingServidor();
    await _testConexionDirecta();
    await _testEndpointHome();
    await _testEndpointRegistro();
    await _testEndpointLogin();
    await _testConApiService();

    setState(() {
      _isLoading = false;
      _currentTest = 0;
    });

    _showSummary();
  }

  void _addResult({
    required String testName,
    required bool success,
    required String message,
    String? details,
    Map<String, dynamic>? data,
  }) {
    setState(() {
      _testResults.add({
        'test': testName,
        'success': success,
        'message': message,
        'details': details,
        'data': data,
        'timestamp': DateTime.now(),
      });
    });
  }

  // ============================================
  // TEST 1: VERIFICAR CONFIGURACIÓN
  // ============================================

  Future<void> _testVerificarConfiguracion() async {
    setState(() => _currentTest = 1);
    await Future.delayed(const Duration(milliseconds: 300));

    try {
      final config = {
        'Base URL': ApiConfig.baseUrl,
        'API URL': ApiConfig.apiUrl,
        'Login Endpoint': ApiConfig.login,
        'Registro Endpoint': ApiConfig.registro,
        'Perfil Endpoint': ApiConfig.perfil,
        'Protocolo': ApiConfig.isHttps ? 'HTTPS 🔒' : 'HTTP 🔓',
        'Modo': ApiConfig.isProduction ? 'PRODUCCIÓN 🚀' : 'DESARROLLO 🛠️',
        'Plataforma': Platform.operatingSystem,
      };

      final details = config.entries
          .map((e) => '• ${e.key}: ${e.value}')
          .join('\n');

      _addResult(
        testName: '1️⃣ Configuración de API',
        success: true,
        message: 'Configuración cargada correctamente',
        details: details,
        data: config,
      );
    } catch (e) {
      _addResult(
        testName: '1️⃣ Configuración de API',
        success: false,
        message: 'Error al cargar configuración',
        details: e.toString(),
      );
    }
  }

  // ============================================
  // TEST 2: PING AL SERVIDOR (Básico)
  // ============================================

  Future<void> _testPingServidor() async {
    setState(() => _currentTest = 2);
    await Future.delayed(const Duration(milliseconds: 300));

    try {
      final uri = Uri.parse(ApiConfig.baseUrl);
      final host = uri.host;
      final port = uri.port;

      _addResult(
        testName: '2️⃣ Información del Servidor',
        success: true,
        message: 'Host: $host | Puerto: $port',
        details: '• Host: $host\n• Puerto: $port\n• Esquema: ${uri.scheme}',
      );
    } catch (e) {
      _addResult(
        testName: '2️⃣ Información del Servidor',
        success: false,
        message: 'Error al parsear URL',
        details: e.toString(),
      );
    }
  }

  // ============================================
  // TEST 3: CONEXIÓN DIRECTA (GET /)
  // ============================================

  Future<void> _testConexionDirecta() async {
    setState(() => _currentTest = 3);

    try {
      final stopwatch = Stopwatch()..start();

      final response = await http
          .get(Uri.parse(ApiConfig.baseUrl))
          .timeout(const Duration(seconds: 10));

      stopwatch.stop();

      final success = response.statusCode == 200;
      final details = StringBuffer();
      details.writeln('• URL: ${ApiConfig.baseUrl}');
      details.writeln('• Status Code: ${response.statusCode}');
      details.writeln('• Tiempo: ${stopwatch.elapsedMilliseconds}ms');
      details.writeln('• Content-Type: ${response.headers['content-type']}');
      details.writeln('\n📦 Response Body:');
      details.writeln(
        response.body.length > 500
            ? '${response.body.substring(0, 500)}...'
            : response.body,
      );

      _addResult(
        testName: '3️⃣ Conexión Directa (GET /)',
        success: success,
        message: success
            ? '✅ Servidor respondió en ${stopwatch.elapsedMilliseconds}ms'
            : '⚠️ Status ${response.statusCode}',
        details: details.toString(),
      );
    } on SocketException catch (e) {
      _addResult(
        testName: '3️⃣ Conexión Directa (GET /)',
        success: false,
        message: '❌ Error de red - No se puede conectar',
        details:
            '🌐 No se pudo establecer conexión con el servidor.\n\n'
            '🔍 Verifica:\n'
            '• Tu móvil está conectado a WiFi\n'
            '• Django está corriendo en: ${ApiConfig.baseUrl}\n'
            '• Ejecuta: python manage.py runserver 192.168.1.4:8000\n\n'
            'Error técnico: ${e.message}',
      );
    } on TimeoutException {
      _addResult(
        testName: '3️⃣ Conexión Directa (GET /)',
        success: false,
        message: '⏱️ Timeout - El servidor no responde',
        details:
            '⏱️ La petición tardó más de 10 segundos.\n\n'
            '🔍 Verifica:\n'
            '• El servidor Django está corriendo\n'
            '• No hay firewall bloqueando el puerto 8000\n'
            '• La IP del servidor es correcta: ${ApiConfig.baseUrl}',
      );
    } catch (e) {
      _addResult(
        testName: '3️⃣ Conexión Directa (GET /)',
        success: false,
        message: '❌ Error desconocido',
        details: e.toString(),
      );
    }
  }

  // ============================================
  // TEST 4: ENDPOINT HOME CON HEADERS
  // ============================================

  Future<void> _testEndpointHome() async {
    setState(() => _currentTest = 4);

    try {
      final response = await http
          .get(
            Uri.parse(ApiConfig.baseUrl),
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
          )
          .timeout(const Duration(seconds: 10));

      final success = response.statusCode == 200;
      String details = '• Status: ${response.statusCode}\n';

      if (success) {
        try {
          final data = json.decode(response.body);
          details += '\n✅ JSON Válido\n\n';
          details += '📊 Datos recibidos:\n';
          details += '• Mensaje: ${data['message']}\n';
          details += '• Versión: ${data['version']}\n';
          details += '• Estado: ${data['status']}\n';
          details += '\n🔗 Endpoints disponibles:\n';

          if (data['endpoints'] != null) {
            final endpoints = data['endpoints'] as Map;
            endpoints.forEach((key, value) {
              details +=
                  '• $key: ${value.toString().split(',').length} rutas\n';
            });
          }
        } catch (e) {
          details += '\n⚠️ Error al parsear JSON: $e';
        }
      }

      _addResult(
        testName: '4️⃣ Endpoint Home (JSON)',
        success: success,
        message: success
            ? '✅ JSON recibido correctamente'
            : '⚠️ Respuesta inválida',
        details: details,
      );
    } catch (e) {
      _addResult(
        testName: '4️⃣ Endpoint Home (JSON)',
        success: false,
        message: '❌ Error en petición',
        details: e.toString(),
      );
    }
  }

  // ============================================
  // TEST 5: ENDPOINT REGISTRO (POST)
  // ============================================

  Future<void> _testEndpointRegistro() async {
    setState(() => _currentTest = 5);

    try {
      final response = await http
          .post(
            Uri.parse(ApiConfig.registro),
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: json.encode({}), // Body vacío para probar
          )
          .timeout(const Duration(seconds: 10));

      // Esperamos 400 porque no enviamos datos válidos
      final success = response.statusCode == 400;

      String details = '• URL: ${ApiConfig.registro}\n';
      details += '• Status: ${response.statusCode}\n';
      details += '\n📦 Response:\n';

      try {
        final data = json.decode(response.body);
        details += json.encode(data);
      } catch (e) {
        details += response.body.length > 300
            ? '${response.body.substring(0, 300)}...'
            : response.body;
      }

      _addResult(
        testName: '5️⃣ Endpoint Registro (POST)',
        success: success,
        message: success
            ? '✅ Endpoint responde (400 esperado)'
            : '⚠️ Respuesta inesperada: ${response.statusCode}',
        details: details,
      );
    } catch (e) {
      _addResult(
        testName: '5️⃣ Endpoint Registro (POST)',
        success: false,
        message: '❌ Error en petición POST',
        details: e.toString(),
      );
    }
  }

  // ============================================
  // TEST 6: ENDPOINT LOGIN (Credenciales inválidas)
  // ✅ CORREGIDO: Espera 401 en lugar de 400
  // ============================================

  Future<void> _testEndpointLogin() async {
    setState(() => _currentTest = 6);

    try {
      final response = await http
          .post(
            Uri.parse(ApiConfig.login),
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: json.encode({
              'email': 'test_usuario@test.com',
              'password': 'password_incorrecto_123',
            }),
          )
          .timeout(const Duration(seconds: 10));

      // ✅ Esperamos 401 (Unauthorized) por credenciales incorrectas
      final success = response.statusCode == 401 || response.statusCode == 400;

      String details = '• URL: ${ApiConfig.login}\n';
      details += '• Status: ${response.statusCode}\n';
      details += '\n📦 Response:\n';

      try {
        final data = json.decode(response.body);
        details += json.encode(data);
      } catch (e) {
        details += response.body;
      }

      _addResult(
        testName: '6️⃣ Endpoint Login (POST)',
        success: success,
        message: success
            ? '✅ Endpoint funciona (401 Unauthorized esperado)'
            : '⚠️ Status inesperado: ${response.statusCode}',
        details: details,
      );
    } on TimeoutException {
      _addResult(
        testName: '6️⃣ Endpoint Login (POST)',
        success: false,
        message: '⏱️ Timeout en login',
        details: 'La petición tardó más de 10 segundos',
      );
    } catch (e) {
      _addResult(
        testName: '6️⃣ Endpoint Login (POST)',
        success: false,
        message: '❌ Error en petición de login',
        details: e.toString(),
      );
    }
  }

  // ============================================
  // TEST 7: TEST CON ApiService (Tu servicio real)
  // ✅ CORREGIDO: Acepta 401 además de 400
  // ============================================

  Future<void> _testConApiService() async {
    setState(() => _currentTest = 7);

    try {
      // Intentar login con credenciales incorrectas
      await _api.login(email: 'test@example.com', password: 'wrongpassword123');

      _addResult(
        testName: '7️⃣ ApiService (Login fallido)',
        success: false,
        message: '⚠️ No debería llegar aquí',
        details: 'Login exitoso con credenciales incorrectas (anómalo)',
      );
    } on ApiException catch (e) {
      // ✅ Aceptar tanto 400 como 401
      final success = e.statusCode == 400 || e.statusCode == 401;

      _addResult(
        testName: '7️⃣ ApiService (Login fallido)',
        success: success,
        message: success
            ? '✅ ApiService funciona correctamente'
            : '⚠️ Status inesperado: ${e.statusCode}',
        details:
            '• Status Code: ${e.statusCode}\n'
            '• Mensaje: ${e.message}\n'
            '• Errores: ${e.errors}',
      );
    } catch (e) {
      _addResult(
        testName: '7️⃣ ApiService (Login fallido)',
        success: false,
        message: '❌ Error en ApiService',
        details: e.toString(),
      );
    }
  }

  // ============================================
  // MOSTRAR RESUMEN
  // ============================================

  void _showSummary() {
    final exitosos = _testResults.where((r) => r['success'] == true).length;
    final total = _testResults.length;
    final porcentaje = ((exitosos / total) * 100).toStringAsFixed(0);

    String mensaje;
    IconData icono;
    Color color;

    if (exitosos == total) {
      mensaje =
          '¡Perfecto! Todas las pruebas pasaron.\nTu conexión está funcionando correctamente.';
      icono = Icons.check_circle;
      color = Colors.green;
    } else if (exitosos >= total * 0.7) {
      mensaje =
          'La mayoría de pruebas pasaron.\nRevisa los tests fallidos para más detalles.';
      icono = Icons.check_circle_outline;
      color = Colors.orange;
    } else if (exitosos > 0) {
      mensaje =
          'Algunas pruebas fallaron.\nVerifica la configuración del servidor.';
      icono = Icons.warning;
      color = Colors.orange;
    } else {
      mensaje = 'Todas las pruebas fallaron.\nNo hay conexión con el servidor.';
      icono = Icons.error;
      color = Colors.red;
    }

    if (mounted) {
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Row(
            children: [
              Icon(icono, color: color, size: 32),
              const SizedBox(width: 12),
              const Text('Resumen de Tests'),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '$exitosos de $total tests exitosos ($porcentaje%)',
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 12),
              Text(mensaje),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Entendido'),
            ),
          ],
        ),
      );
    }
  }

  // ============================================
  // UI
  // ============================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🧪 Test de Conexión'),
        backgroundColor: _azulPrincipal,
        foregroundColor: Colors.white,
        actions: [
          if (!_isLoading)
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: _runAllTests,
              tooltip: 'Ejecutar tests',
            ),
        ],
      ),
      body: Column(
        children: [
          _buildConfigCard(),
          if (_isLoading) _buildProgressIndicator(),
          Expanded(child: _buildResultsList()),
        ],
      ),
      floatingActionButton: _isLoading
          ? null
          : FloatingActionButton.extended(
              onPressed: _runAllTests,
              icon: const Icon(Icons.play_arrow),
              label: const Text('Ejecutar Tests'),
              backgroundColor: _azulPrincipal,
            ),
    );
  }

  Widget _buildConfigCard() {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.all(12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [_azulPrincipal.withValues(alpha: 0.1), Colors.white],
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _azulPrincipal.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '🌐 Configuración Actual',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          _buildInfoRow('Base URL', ApiConfig.baseUrl),
          _buildInfoRow('API URL', ApiConfig.apiUrl),
          _buildInfoRow(
            'Protocolo',
            ApiConfig.isHttps ? 'HTTPS 🔒' : 'HTTP 🔓',
          ),
          _buildInfoRow(
            'Modo',
            ApiConfig.isProduction ? 'Producción 🚀' : 'Desarrollo 🛠️',
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$label: ',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: Colors.grey[700],
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(fontSize: 12, color: Colors.grey[800]),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProgressIndicator() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          LinearProgressIndicator(
            backgroundColor: Colors.grey[200],
            valueColor: AlwaysStoppedAnimation<Color>(_azulPrincipal),
          ),
          const SizedBox(height: 8),
          Text(
            'Ejecutando test $_currentTest de 7...',
            style: TextStyle(fontSize: 12, color: Colors.grey[600]),
          ),
        ],
      ),
    );
  }

  Widget _buildResultsList() {
    if (_testResults.isEmpty && !_isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.science, size: 80, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              'Presiona el botón para\nejecutar los tests',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16, color: Colors.grey[600]),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: _testResults.length,
      itemBuilder: (context, index) {
        final result = _testResults[index];
        return _buildResultCard(result);
      },
    );
  }

  Widget _buildResultCard(Map<String, dynamic> result) {
    final success = result['success'] as bool;
    final color = success ? Colors.green : Colors.red;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: color.withValues(alpha: 0.3), width: 1.5),
      ),
      child: ExpansionTile(
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.1),
            shape: BoxShape.circle,
          ),
          child: Icon(
            success ? Icons.check_circle : Icons.error,
            color: color,
            size: 24,
          ),
        ),
        title: Text(
          result['test'],
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
        ),
        subtitle: Text(
          result['message'],
          style: TextStyle(color: Colors.grey[700], fontSize: 13),
        ),
        children: [
          if (result['details'] != null)
            Container(
              width: double.infinity,
              margin: const EdgeInsets.all(12),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(8),
              ),
              child: SelectableText(
                result['details'],
                style: const TextStyle(
                  fontSize: 11,
                  fontFamily: 'monospace',
                  height: 1.5,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
