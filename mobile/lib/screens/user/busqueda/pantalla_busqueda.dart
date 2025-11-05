import 'package:flutter/material.dart';

class PantallaBusqueda extends StatefulWidget {
  const PantallaBusqueda({super.key});

  @override
  State<PantallaBusqueda> createState() => _PantallaBusquedaState();
}

class _PantallaBusquedaState extends State<PantallaBusqueda> {
  final TextEditingController _controladorBusqueda = TextEditingController();
  List<String> _resultados = [];
  bool _buscando = false;

  // Datos de ejemplo
  final List<String> _productosEjemplo = [
    'Hamburguesa Clásica',
    'Pizza Margarita',
    'Ensalada César',
    'Pasta Carbonara',
    'Tacos al Pastor',
    'Sushi Roll',
    'Burrito de Pollo',
    'Helado de Vainilla',
    'Café Americano',
    'Jugo Natural',
  ];

  void _buscarProductos(String query) {
    setState(() {
      _buscando = true;
    });

    // Simular búsqueda
    Future.delayed(const Duration(milliseconds: 500), () {
      setState(() {
        if (query.isEmpty) {
          _resultados = [];
        } else {
          _resultados = _productosEjemplo
              .where(
                (producto) =>
                    producto.toLowerCase().contains(query.toLowerCase()),
              )
              .toList();
        }
        _buscando = false;
      });
    });
  }

  @override
  void dispose() {
    _controladorBusqueda.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Buscar'), elevation: 0),
      body: Column(
        children: [
          // Barra de búsqueda
          Container(
            padding: const EdgeInsets.all(16.0),
            color: Theme.of(context).primaryColor.withValues(alpha: 0.05),
            child: TextField(
              controller: _controladorBusqueda,
              onChanged: _buscarProductos,
              decoration: InputDecoration(
                hintText: 'Buscar productos...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _controladorBusqueda.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _controladorBusqueda.clear();
                          _buscarProductos('');
                        },
                      )
                    : null,
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 12,
                ),
              ),
            ),
          ),

          // Resultados
          Expanded(
            child: _buscando
                ? const Center(child: CircularProgressIndicator())
                : _controladorBusqueda.text.isEmpty
                ? _buildEstadoInicial()
                : _resultados.isEmpty
                ? _buildSinResultados()
                : _buildListaResultados(),
          ),
        ],
      ),
    );
  }

  Widget _buildEstadoInicial() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.search, size: 80, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text(
            'Busca tus productos favoritos',
            style: TextStyle(fontSize: 18, color: Colors.grey[600]),
          ),
          const SizedBox(height: 8),
          Text(
            'Escribe en el cuadro de búsqueda',
            style: TextStyle(fontSize: 14, color: Colors.grey[500]),
          ),
        ],
      ),
    );
  }

  Widget _buildSinResultados() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.search_off, size: 80, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text(
            'No se encontraron resultados',
            style: TextStyle(fontSize: 18, color: Colors.grey[600]),
          ),
          const SizedBox(height: 8),
          Text(
            'Intenta con otros términos',
            style: TextStyle(fontSize: 14, color: Colors.grey[500]),
          ),
        ],
      ),
    );
  }

  Widget _buildListaResultados() {
    return ListView.builder(
      padding: const EdgeInsets.all(16.0),
      itemCount: _resultados.length,
      itemBuilder: (context, index) {
        final producto = _resultados[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.all(12),
            leading: Container(
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                color: Colors.grey[300],
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(Icons.fastfood, size: 30, color: Colors.grey[600]),
            ),
            title: Text(
              producto,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            subtitle: Text(
              'Descripción del producto',
              style: TextStyle(color: Colors.grey[600]),
            ),
            trailing: Text(
              '\$${(10 + index * 2).toStringAsFixed(2)}',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Theme.of(context).primaryColor,
              ),
            ),
            onTap: () {
              // Acción al tocar el producto
            },
          ),
        );
      },
    );
  }
}
