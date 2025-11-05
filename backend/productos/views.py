from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, F, Count
from django.utils import timezone

from .models import Categoria, Producto, ProductoVariante, ProductoImagen
from .serializers import (
    CategoriaSerializer,
    CategoriaDetailSerializer,
    ProductoListSerializer,
    ProductoSerializer,
    ProductoCreateUpdateSerializer,
    ProductoVarianteSerializer,
    ProductoVarianteCreateSerializer,
    ProductoImagenSerializer,
    ProductoImagenCreateSerializer,
    ProductoStockUpdateSerializer,
    ProductoOfertaSerializer,
    ProductoResumenSerializer,
)
import logging

logger = logging.getLogger('productos')


# ============================================
# CATEGORIA VIEWSET
# ============================================

class CategoriaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Categorías

    Endpoints:
    - GET /categorias/ - Lista todas las categorías
    - GET /categorias/{id}/ - Detalle de una categoría
    - POST /categorias/ - Crear categoría (admin)
    - PUT/PATCH /categorias/{id}/ - Actualizar categoría (admin)
    - DELETE /categorias/{id}/ - Eliminar categoría (admin)
    - GET /categorias/activas/ - Solo categorías activas
    - GET /categorias/{id}/productos/ - Productos de la categoría
    """
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['orden', 'nombre', 'created_at']
    ordering = ['orden', 'nombre']

    def get_permissions(self):
        """
        Permisos:
        - GET: Cualquiera
        - POST/PUT/PATCH/DELETE: Solo autenticados (admin/proveedor)
        """
        if self.action in ['list', 'retrieve', 'activas']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        """Usa serializer detallado para retrieve"""
        if self.action == 'retrieve':
            return CategoriaDetailSerializer
        return CategoriaSerializer

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def activas(self, request):
        """
        GET /categorias/activas/
        Retorna solo categorías activas ordenadas
        """
        categorias = Categoria.objects.activas().ordenadas()
        serializer = self.get_serializer(categorias, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def productos(self, request, pk=None):
        """
        GET /categorias/{id}/productos/
        Retorna todos los productos de una categoría
        """
        categoria = self.get_object()
        productos = Producto.objects.por_categoria(categoria.id)

        # Aplicar filtros opcionales
        activo = request.query_params.get('activo')
        if activo is not None:
            activo = activo.lower() == 'true'
            productos = productos.filter(activo=activo)

        serializer = ProductoListSerializer(
            productos,
            many=True,
            context={'request': request}
        )

        return Response({
            'categoria': CategoriaSerializer(categoria).data,
            'total_productos': productos.count(),
            'productos': serializer.data
        })


# ============================================
# PRODUCTO VIEWSET
# ============================================

class ProductoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Productos

    Endpoints principales:
    - GET /productos/ - Lista productos (con filtros)
    - GET /productos/{id}/ - Detalle del producto
    - POST /productos/ - Crear producto (proveedor/admin)
    - PUT/PATCH /productos/{id}/ - Actualizar producto
    - DELETE /productos/{id}/ - Soft delete del producto

    Acciones adicionales:
    - GET /productos/destacados/ - Productos destacados
    - GET /productos/ofertas/ - Productos en oferta
    - GET /productos/buscar/ - Búsqueda avanzada
    - POST /productos/{id}/actualizar_stock/ - Actualizar stock
    - POST /productos/{id}/activar_oferta/ - Gestionar ofertas
    - GET /productos/resumen/ - Estadísticas generales
    - GET /productos/proveedor/{proveedor_id}/ - Productos por proveedor
    """
    queryset = Producto.objects.select_related('proveedor', 'categoria').prefetch_related('variantes', 'imagenes')
    serializer_class = ProductoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['proveedor', 'categoria', 'activo', 'en_oferta', 'destacado']
    search_fields = ['nombre', 'descripcion', 'sku']
    ordering_fields = ['precio', 'nombre', 'created_at', 'stock']
    ordering = ['-created_at']

    def get_permissions(self):
        """
        Permisos:
        - GET: Cualquiera
        - POST/PUT/PATCH/DELETE: Solo autenticados
        """
        if self.action in ['list', 'retrieve', 'destacados', 'ofertas', 'buscar']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """
        Filtra productos:
        - Solo activos y no eliminados para usuarios no autenticados
        - Todos para usuarios autenticados (para gestión)
        """
        queryset = super().get_queryset()

        # Si no está autenticado, solo mostrar productos activos
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(activo=True, deleted_at__isnull=True)
        else:
            # Si está autenticado, puede ver sus productos aunque no estén activos
            if hasattr(self.request.user, 'proveedor'):
                proveedor = self.request.user.proveedor
                # Ver todos sus productos o productos activos de otros
                queryset = queryset.filter(
                    Q(proveedor=proveedor) | Q(activo=True)
                ).filter(deleted_at__isnull=True)

        return queryset

    def get_serializer_class(self):
        """
        Usa serializers específicos según la acción
        """
        if self.action == 'list':
            return ProductoListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductoCreateUpdateSerializer
        return ProductoSerializer

    def perform_create(self, serializer):
        """
        Al crear, asignar automáticamente el proveedor si es usuario proveedor
        """
        user = self.request.user

        # Si el usuario es proveedor, asignar automáticamente
        if hasattr(user, 'proveedor'):
            serializer.save(proveedor=user.proveedor)
            logger.info(f"✅ Producto creado por proveedor {user.proveedor.id}")
        else:
            serializer.save()

    def perform_update(self, serializer):
        """
        Validar que solo el proveedor dueño o admin pueda editar
        """
        producto = self.get_object()
        user = self.request.user

        # Verificar permisos
        if hasattr(user, 'proveedor'):
            if producto.proveedor.id != user.proveedor.id and not user.is_staff:
                logger.warning(f"⚠️ Usuario {user.id} intentó editar producto {producto.id} sin permisos")
                raise PermissionError("No tienes permiso para editar este producto")

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete del producto
        """
        producto = self.get_object()

        # Verificar permisos
        user = request.user
        if hasattr(user, 'proveedor'):
            if producto.proveedor.id != user.proveedor.id and not user.is_staff:
                return Response(
                    {'error': 'No tienes permiso para eliminar este producto'},
                    status=status.HTTP_403_FORBIDDEN
                )

        producto.soft_delete()

        return Response(
            {'mensaje': 'Producto eliminado exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )

    # ============================================
    # ACCIONES PERSONALIZADAS
    # ============================================

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def destacados(self, request):
        """
        GET /productos/destacados/
        Retorna productos destacados
        """
        productos = self.get_queryset().filter(destacado=True, activo=True)[:12]
        serializer = ProductoListSerializer(productos, many=True, context={'request': request})

        return Response({
            'total': productos.count(),
            'productos': serializer.data
        })

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def ofertas(self, request):
        """
        GET /productos/ofertas/
        Retorna productos en oferta
        """
        productos = self.get_queryset().filter(en_oferta=True, activo=True)
        serializer = ProductoListSerializer(productos, many=True, context={'request': request})

        return Response({
            'total': productos.count(),
            'productos': serializer.data
        })

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def buscar(self, request):
        """
        GET /productos/buscar/?q=pizza&categoria=1&min_precio=10&max_precio=50
        Búsqueda avanzada de productos
        """
        queryset = self.get_queryset().filter(activo=True)

        # Búsqueda por texto
        q = request.query_params.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) |
                Q(descripcion__icontains=q) |
                Q(sku__icontains=q)
            )

        # Filtro por categoría
        categoria = request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)

        # Filtro por proveedor
        proveedor = request.query_params.get('proveedor')
        if proveedor:
            queryset = queryset.filter(proveedor_id=proveedor)

        # Filtro por rango de precio
        min_precio = request.query_params.get('min_precio')
        max_precio = request.query_params.get('max_precio')
        if min_precio:
            queryset = queryset.filter(precio__gte=min_precio)
        if max_precio:
            queryset = queryset.filter(precio__lte=max_precio)

        # Filtro por stock
        con_stock = request.query_params.get('con_stock')
        if con_stock and con_stock.lower() == 'true':
            queryset = queryset.filter(stock__gt=0)

        # Ordenamiento
        orden = request.query_params.get('orden', '-created_at')
        queryset = queryset.order_by(orden)

        # Paginación
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProductoListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ProductoListSerializer(queryset, many=True, context={'request': request})
        return Response({
            'total': queryset.count(),
            'productos': serializer.data
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def actualizar_stock(self, request, pk=None):
        """
        POST /productos/{id}/actualizar_stock/
        Body: {
            "cantidad": 10,
            "operacion": "aumentar" | "descontar"
        }
        """
        producto = self.get_object()

        # Verificar permisos
        user = request.user
        if hasattr(user, 'proveedor'):
            if producto.proveedor.id != user.proveedor.id and not user.is_staff:
                return Response(
                    {'error': 'No tienes permiso para actualizar este producto'},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = ProductoStockUpdateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                resultado = serializer.update_stock(producto)
                return Response(resultado, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def gestionar_oferta(self, request, pk=None):
        """
        POST /productos/{id}/gestionar_oferta/
        Body: {
            "activar": true,
            "precio_oferta": 10.50,  // opcional
            "descuento_porcentaje": 20  // opcional
        }
        """
        producto = self.get_object()

        # Verificar permisos
        user = request.user
        if hasattr(user, 'proveedor'):
            if producto.proveedor.id != user.proveedor.id and not user.is_staff:
                return Response(
                    {'error': 'No tienes permiso para modificar este producto'},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = ProductoOfertaSerializer(data=request.data)
        if serializer.is_valid():
            resultado = serializer.update_oferta(producto)
            return Response(resultado, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def resumen(self, request):
        """
        GET /productos/resumen/
        Retorna estadísticas de productos
        """
        user = request.user
        queryset = Producto.objects.filter(deleted_at__isnull=True)

        # Si es proveedor, solo sus productos
        if hasattr(user, 'proveedor'):
            queryset = queryset.filter(proveedor=user.proveedor)

        # Calcular estadísticas
        total_productos = queryset.count()
        productos_activos = queryset.filter(activo=True).count()
        productos_inactivos = queryset.filter(activo=False).count()
        productos_con_stock = queryset.filter(stock__gt=0).count()
        productos_sin_stock = queryset.filter(stock=0).count()
        productos_en_oferta = queryset.filter(en_oferta=True).count()
        productos_destacados = queryset.filter(destacado=True).count()

        # Valor total del inventario
        valor_inventario = queryset.aggregate(
            total=Sum(F('precio') * F('stock'))
        )['total'] or 0

        serializer = ProductoResumenSerializer(data={
            'total_productos': total_productos,
            'productos_activos': productos_activos,
            'productos_inactivos': productos_inactivos,
            'productos_con_stock': productos_con_stock,
            'productos_sin_stock': productos_sin_stock,
            'productos_en_oferta': productos_en_oferta,
            'productos_destacados': productos_destacados,
            'valor_total_inventario': valor_inventario,
        })

        serializer.is_valid()
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='proveedor/(?P<proveedor_id>[^/.]+)')
    def por_proveedor(self, request, proveedor_id=None):
        """
        GET /productos/proveedor/{proveedor_id}/
        Retorna todos los productos de un proveedor
        """
        productos = self.get_queryset().filter(
            proveedor_id=proveedor_id,
            activo=True
        )

        serializer = ProductoListSerializer(productos, many=True, context={'request': request})

        return Response({
            'proveedor_id': proveedor_id,
            'total': productos.count(),
            'productos': serializer.data
        })


# ============================================
# PRODUCTO VARIANTE VIEWSET
# ============================================

class ProductoVarianteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Variantes de Productos

    Endpoints:
    - GET /variantes/ - Lista variantes
    - GET /variantes/{id}/ - Detalle de variante
    - POST /variantes/ - Crear variante
    - PUT/PATCH /variantes/{id}/ - Actualizar variante
    - DELETE /variantes/{id}/ - Eliminar variante
    - GET /variantes/producto/{producto_id}/ - Variantes de un producto
    """
    queryset = ProductoVariante.objects.select_related('producto')
    serializer_class = ProductoVarianteSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductoVarianteCreateSerializer
        return ProductoVarianteSerializer

    def get_queryset(self):
        """Filtra según el usuario"""
        queryset = super().get_queryset()
        user = self.request.user

        if hasattr(user, 'proveedor'):
            # Proveedor solo ve sus variantes
            queryset = queryset.filter(producto__proveedor=user.proveedor)

        return queryset

    @action(detail=False, methods=['get'], url_path='producto/(?P<producto_id>[^/.]+)')
    def por_producto(self, request, producto_id=None):
        """
        GET /variantes/producto/{producto_id}/
        Retorna todas las variantes de un producto
        """
        variantes = self.get_queryset().filter(producto_id=producto_id, activo=True)
        serializer = self.get_serializer(variantes, many=True)

        return Response({
            'producto_id': producto_id,
            'total': variantes.count(),
            'variantes': serializer.data
        })


# ============================================
# PRODUCTO IMAGEN VIEWSET
# ============================================

class ProductoImagenViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Imágenes de Productos

    Endpoints:
    - GET /imagenes/ - Lista imágenes
    - GET /imagenes/{id}/ - Detalle de imagen
    - POST /imagenes/ - Subir imagen
    - PUT/PATCH /imagenes/{id}/ - Actualizar imagen
    - DELETE /imagenes/{id}/ - Eliminar imagen
    - GET /imagenes/producto/{producto_id}/ - Imágenes de un producto
    """
    queryset = ProductoImagen.objects.select_related('producto')
    serializer_class = ProductoImagenSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductoImagenCreateSerializer
        return ProductoImagenSerializer

    def get_queryset(self):
        """Filtra según el usuario"""
        queryset = super().get_queryset()
        user = self.request.user

        if hasattr(user, 'proveedor'):
            # Proveedor solo ve imágenes de sus productos
            queryset = queryset.filter(producto__proveedor=user.proveedor)

        return queryset

    @action(detail=False, methods=['get'], url_path='producto/(?P<producto_id>[^/.]+)')
    def por_producto(self, request, producto_id=None):
        """
        GET /imagenes/producto/{producto_id}/
        Retorna todas las imágenes de un producto
        """
        imagenes = self.get_queryset().filter(producto_id=producto_id).order_by('orden')
        serializer = self.get_serializer(imagenes, many=True, context={'request': request})

        return Response({
            'producto_id': producto_id,
            'total': imagenes.count(),
            'imagenes': serializer.data
        })
