// ============================================================================
// ARCHIVO: lib/screens/user/pantalla_inicio.dart
// ============================================================================
// Pantalla principal con navegación inferior mediante BottomNavigationBar
// Mantiene las pantallas en memoria usando IndexedStack para mejor rendimiento
// ============================================================================

import 'package:flutter/material.dart';
import 'inicio/pantalla_home.dart';
import 'busqueda/pantalla_busqueda.dart';
import 'pedidos/pantalla_mis_pedidos.dart';
import 'perfil/pantalla_perfil.dart';

// ============================================================================
// 🎯 PANTALLA PRINCIPAL CON NAVEGACIÓN
// ============================================================================

/// Pantalla principal que contiene el BottomNavigationBar y gestiona
/// la navegación entre las 4 pantallas principales de la aplicación
class PantallaInicio extends StatefulWidget {
  const PantallaInicio({super.key});

  @override
  State<PantallaInicio> createState() => _PantallaInicioState();
}

class _PantallaInicioState extends State<PantallaInicio> {
  /// Índice de la pantalla actualmente seleccionada
  int _indiceActual = 0;

  /// Lista de pantallas que se mantienen en memoria para mejor rendimiento
  /// IndexedStack solo muestra la pantalla activa pero mantiene el estado de todas
  final List<Widget> _pantallas = const [
    PantallaHome(),
    PantallaBusqueda(),
    PantallaMisPedidos(),
    PantallaPerfil(),
  ];

  /// Cambia la pantalla activa cuando el usuario toca un item del navbar
  void _cambiarPantalla(int indice) {
    if (_indiceActual != indice) {
      setState(() {
        _indiceActual = indice;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // IndexedStack muestra solo la pantalla del índice actual
      // pero mantiene el estado de todas las demás pantallas
      body: IndexedStack(index: _indiceActual, children: _pantallas),

      // Barra de navegación inferior
      bottomNavigationBar: _construirBottomNavBar(context),
    );
  }

  /// Construye el BottomNavigationBar con los 4 items principales
  Widget _construirBottomNavBar(BuildContext context) {
    final colorPrimario = Theme.of(context).primaryColor;

    return BottomNavigationBar(
      // Configuración general
      currentIndex: _indiceActual,
      onTap: _cambiarPantalla,
      type: BottomNavigationBarType.fixed,

      // Colores
      selectedItemColor: colorPrimario,
      unselectedItemColor: Colors.grey.shade600,
      backgroundColor: Colors.white,

      // Estilo de los labels
      selectedFontSize: 12,
      unselectedFontSize: 11,
      selectedLabelStyle: const TextStyle(fontWeight: FontWeight.w600),

      // Elevación para dar profundidad
      elevation: 8,

      // Items de navegación
      items: const [
        BottomNavigationBarItem(
          icon: Icon(Icons.home_outlined),
          activeIcon: Icon(Icons.home),
          label: 'Inicio',
          tooltip: 'Ir a Inicio',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.search_outlined),
          activeIcon: Icon(Icons.search),
          label: 'Buscar',
          tooltip: 'Buscar productos',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.shopping_bag_outlined),
          activeIcon: Icon(Icons.shopping_bag),
          label: 'Pedidos',
          tooltip: 'Ver mis pedidos',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.person_outline),
          activeIcon: Icon(Icons.person),
          label: 'Perfil',
          tooltip: 'Ver perfil',
        ),
      ],
    );
  }
}
