from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoriaViewSet,
    ProductoViewSet,
    ProductoVarianteViewSet,
    ProductoImagenViewSet,
)

# ============================================
# ROUTER PARA VIEWSETS
# ============================================

router = DefaultRouter()

# Registro de ViewSets
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'productos', ProductoViewSet, basename='producto')
router.register(r'variantes', ProductoVarianteViewSet, basename='variante')
router.register(r'imagenes', ProductoImagenViewSet, basename='imagen')

# ============================================
# URL PATTERNS
# ============================================

urlpatterns = [
    # Incluir todas las rutas del router
    path('', include(router.urls)),
]

"""
============================================
ENDPOINTS DISPONIBLES
============================================

CATEGORÍAS:
-----------
GET     /api/categorias/                    - Lista todas las categorías
GET     /api/categorias/{id}/               - Detalle de una categoría
POST    /api/categorias/                    - Crear categoría (autenticado)
PUT     /api/categorias/{id}/               - Actualizar categoría (autenticado)
PATCH   /api/categorias/{id}/               - Actualizar parcial (autenticado)
DELETE  /api/categorias/{id}/               - Eliminar categoría (autenticado)

GET     /api/categorias/activas/            - Solo categorías activas
GET     /api/categorias/{id}/productos/     - Productos de una categoría


PRODUCTOS:
----------
GET     /api/productos/                     - Lista productos (con filtros)
GET     /api/productos/{id}/                - Detalle de un producto
POST    /api/productos/                     - Crear producto (autenticado)
PUT     /api/productos/{id}/                - Actualizar producto (autenticado)
PATCH   /api/productos/{id}/                - Actualizar parcial (autenticado)
DELETE  /api/productos/{id}/                - Soft delete producto (autenticado)

# Acciones personalizadas
GET     /api/productos/destacados/          - Productos destacados
GET     /api/productos/ofertas/             - Productos en oferta
GET     /api/productos/buscar/              - Búsqueda avanzada
GET     /api/productos/resumen/             - Estadísticas (autenticado)
GET     /api/productos/proveedor/{id}/      - Productos por proveedor

POST    /api/productos/{id}/actualizar_stock/      - Actualizar inventario (autenticado)
POST    /api/productos/{id}/gestionar_oferta/      - Gestionar ofertas (autenticado)


VARIANTES:
----------
GET     /api/variantes/                     - Lista variantes (autenticado)
GET     /api/variantes/{id}/                - Detalle de variante (autenticado)
POST    /api/variantes/                     - Crear variante (autenticado)
PUT     /api/variantes/{id}/                - Actualizar variante (autenticado)
PATCH   /api/variantes/{id}/                - Actualizar parcial (autenticado)
DELETE  /api/variantes/{id}/                - Eliminar variante (autenticado)

GET     /api/variantes/producto/{id}/       - Variantes de un producto (autenticado)


IMÁGENES:
---------
GET     /api/imagenes/                      - Lista imágenes (autenticado)
GET     /api/imagenes/{id}/                 - Detalle de imagen (autenticado)
POST    /api/imagenes/                      - Subir imagen (autenticado)
PUT     /api/imagenes/{id}/                 - Actualizar imagen (autenticado)
PATCH   /api/imagenes/{id}/                 - Actualizar parcial (autenticado)
DELETE  /api/imagenes/{id}/                 - Eliminar imagen (autenticado)

GET     /api/imagenes/producto/{id}/        - Imágenes de un producto (autenticado)


============================================
EJEMPLOS DE USO
============================================

# 1. LISTAR PRODUCTOS CON FILTROS
GET /api/productos/?categoria=1&activo=true&en_oferta=true

# 2. BUSCAR PRODUCTOS
GET /api/productos/buscar/?q=pizza&min_precio=10&max_precio=30&con_stock=true

# 3. PRODUCTOS DE UN PROVEEDOR
GET /api/productos/proveedor/5/

# 4. ACTUALIZAR STOCK
POST /api/productos/123/actualizar_stock/
{
    "cantidad": 10,
    "operacion": "aumentar"  // o "descontar"
}

# 5. ACTIVAR OFERTA
POST /api/productos/123/gestionar_oferta/
{
    "activar": true,
    "precio_oferta": 12.50,
    "descuento_porcentaje": 20
}

# 6. CREAR PRODUCTO
POST /api/productos/
{
    "proveedor": 1,
    "categoria": 2,
    "nombre": "Pizza Margarita",
    "descripcion": "Pizza clásica con queso y tomate",
    "sku": "PIZZA-MARG-001",
    "precio": 15.00,
    "stock": 50,
    "controlar_stock": true,
    "activo": true
}

# 7. CREAR VARIANTE
POST /api/variantes/
{
    "producto": 123,
    "nombre": "Grande",
    "precio": 18.00,
    "sku_variante": "PIZZA-MARG-001-L",
    "stock": 30
}

# 8. SUBIR IMAGEN ADICIONAL
POST /api/imagenes/
Content-Type: multipart/form-data
{
    "producto": 123,
    "imagen": [archivo],
    "orden": 1,
    "descripcion": "Vista frontal"
}

# 9. OBTENER ESTADÍSTICAS
GET /api/productos/resumen/

# 10. PRODUCTOS DE UNA CATEGORÍA
GET /api/categorias/2/productos/?activo=true

============================================
FILTROS DISPONIBLES EN /api/productos/
============================================

?proveedor=1                - Filtrar por proveedor
?categoria=2                - Filtrar por categoría
?activo=true                - Solo productos activos
?en_oferta=true             - Solo productos en oferta
?destacado=true             - Solo productos destacados
?search=pizza               - Buscar por nombre/descripción/SKU
?ordering=precio            - Ordenar por precio ascendente
?ordering=-precio           - Ordenar por precio descendente
?ordering=nombre            - Ordenar alfabéticamente
?ordering=-created_at       - Ordenar por más recientes

# Combinar múltiples filtros:
?categoria=1&activo=true&en_oferta=true&ordering=-created_at

============================================
RESPUESTAS TÍPICAS
============================================

# Lista de productos:
{
    "count": 50,
    "next": "http://api.com/productos/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "nombre": "Pizza Margarita",
            "precio": 15.00,
            "precio_final": 12.00,
            "ahorro": 3.00,
            "en_oferta": true,
            "stock": 50,
            "tiene_stock": true,
            ...
        }
    ]
}

# Detalle de producto:
{
    "id": 1,
    "nombre": "Pizza Margarita",
    "descripcion": "...",
    "precio": 15.00,
    "precio_final": 12.00,
    "variantes": [
        {
            "id": 1,
            "nombre": "Pequeña",
            "precio": 10.00,
            "stock": 20
        },
        {
            "id": 2,
            "nombre": "Grande",
            "precio": 18.00,
            "stock": 15
        }
    ],
    "imagenes": [
        {
            "id": 1,
            "imagen_url": "http://...",
            "orden": 0
        }
    ],
    "proveedor_nombre": "Restaurante El Buen Sabor",
    "categoria_nombre": "Pizzas",
    ...
}

# Resumen de productos:
{
    "total_productos": 150,
    "productos_activos": 140,
    "productos_inactivos": 10,
    "productos_con_stock": 120,
    "productos_sin_stock": 30,
    "productos_en_oferta": 25,
    "productos_destacados": 15,
    "valor_total_inventario": 25000.00
}
"""
