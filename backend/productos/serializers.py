from rest_framework import serializers
from .models import Categoria, Producto, ProductoVariante, ProductoImagen
from proveedores.models import Proveedor
import logging

logger = logging.getLogger('productos')


# ============================================
# CATEGORIA SERIALIZERS
# ============================================

class CategoriaSerializer(serializers.ModelSerializer):
    """
    Serializer básico para Categoria
    Usado en listados y select inputs
    """
    total_productos = serializers.IntegerField(read_only=True)

    class Meta:
        model = Categoria
        fields = [
            'id',
            'nombre',
            'descripcion',
            'icono',
            'orden',
            'activo',
            'total_productos',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CategoriaDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para Categoria
    Incluye estadísticas y productos
    """
    total_productos = serializers.SerializerMethodField()
    productos_activos = serializers.SerializerMethodField()

    class Meta:
        model = Categoria
        fields = [
            'id',
            'nombre',
            'descripcion',
            'icono',
            'orden',
            'activo',
            'total_productos',
            'productos_activos',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_productos(self, obj):
        """Total de productos en la categoría"""
        return obj.productos.filter(deleted_at__isnull=True).count()

    def get_productos_activos(self, obj):
        """Total de productos activos"""
        return obj.productos.filter(activo=True, deleted_at__isnull=True).count()


# ============================================
# PRODUCTO IMAGEN SERIALIZERS
# ============================================

class ProductoImagenSerializer(serializers.ModelSerializer):
    """
    Serializer para imágenes adicionales del producto
    """
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductoImagen
        fields = [
            'id',
            'imagen',
            'imagen_url',
            'orden',
            'descripcion',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_imagen_url(self, obj):
        """Retorna URL completa de la imagen"""
        if obj.imagen:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None


class ProductoImagenCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear/actualizar imágenes
    """
    class Meta:
        model = ProductoImagen
        fields = ['id', 'producto', 'imagen', 'orden', 'descripcion']
        read_only_fields = ['id']

    def validate_imagen(self, value):
        """Valida el tamaño y formato de la imagen"""
        if value.size > 5 * 1024 * 1024:  # 5MB
            raise serializers.ValidationError("La imagen no debe superar 5MB")

        valid_formats = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if value.content_type not in valid_formats:
            raise serializers.ValidationError("Formato no válido. Use JPG, PNG o WebP")

        return value


# ============================================
# PRODUCTO VARIANTE SERIALIZERS
# ============================================

class ProductoVarianteSerializer(serializers.ModelSerializer):
    """
    Serializer para variantes del producto (tamaños, presentaciones)
    """
    tiene_stock = serializers.SerializerMethodField()

    class Meta:
        model = ProductoVariante
        fields = [
            'id',
            'nombre',
            'descripcion',
            'precio',
            'sku_variante',
            'stock',
            'tiene_stock',
            'activo',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_tiene_stock(self, obj):
        """Verifica si la variante tiene stock"""
        return obj.stock > 0


class ProductoVarianteCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear/actualizar variantes
    """
    class Meta:
        model = ProductoVariante
        fields = [
            'id',
            'producto',
            'nombre',
            'descripcion',
            'precio',
            'sku_variante',
            'stock',
            'activo',
        ]
        read_only_fields = ['id']

    def validate_precio(self, value):
        """Valida que el precio sea positivo"""
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a 0")
        return value

    def validate(self, data):
        """Validación cruzada"""
        # Validar que el SKU no exista en otra variante
        sku = data.get('sku_variante')
        producto = data.get('producto')
        instance = self.instance

        if sku:
            query = ProductoVariante.objects.filter(sku_variante=sku)
            if instance:
                query = query.exclude(id=instance.id)
            if query.exists():
                raise serializers.ValidationError({
                    'sku_variante': 'Ya existe una variante con este SKU'
                })

        return data


# ============================================
# PRODUCTO SERIALIZERS
# ============================================

class ProductoListSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para listados de productos
    Información mínima necesaria
    """
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    imagen_principal_url = serializers.SerializerMethodField()
    precio_final = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    ahorro = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    tiene_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id',
            'nombre',
            'descripcion',
            'sku',
            'precio',
            'precio_final',
            'ahorro',
            'en_oferta',
            'imagen_principal',
            'imagen_principal_url',
            'proveedor',
            'proveedor_nombre',
            'categoria',
            'categoria_nombre',
            'stock',
            'tiene_stock',
            'activo',
            'destacado',
        ]

    def get_imagen_principal_url(self, obj):
        """Retorna URL completa de la imagen principal"""
        if obj.imagen_principal:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen_principal.url)
            return obj.imagen_principal.url
        return None


class ProductoSerializer(serializers.ModelSerializer):
    """
    Serializer completo para Producto
    Incluye todas las relaciones y campos calculados
    """
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)
    proveedor_logo = serializers.ImageField(source='proveedor.logo', read_only=True)
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    categoria_icono = serializers.ImageField(source='categoria.icono', read_only=True)

    # Campos calculados
    precio_final = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    ahorro = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    tiene_stock = serializers.BooleanField(read_only=True)
    stock_bajo = serializers.BooleanField(read_only=True)
    tiene_variantes = serializers.BooleanField(read_only=True)

    # Relaciones anidadas
    variantes = ProductoVarianteSerializer(many=True, read_only=True)
    imagenes = ProductoImagenSerializer(many=True, read_only=True)

    # URLs de imágenes
    imagen_principal_url = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            'id',
            'proveedor',
            'proveedor_nombre',
            'proveedor_logo',
            'categoria',
            'categoria_nombre',
            'categoria_icono',
            'nombre',
            'descripcion',
            'sku',
            'imagen_principal',
            'imagen_principal_url',
            'precio',
            'precio_final',
            'ahorro',
            'stock',
            'stock_minimo',
            'tiene_stock',
            'stock_bajo',
            'controlar_stock',
            'en_oferta',
            'precio_oferta',
            'descuento_porcentaje',
            'peso',
            'tiempo_preparacion',
            'activo',
            'destacado',
            'tiene_variantes',
            'variantes',
            'imagenes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'precio_final',
            'ahorro',
            'tiene_stock',
            'stock_bajo',
            'tiene_variantes',
        ]

    def get_imagen_principal_url(self, obj):
        """Retorna URL completa de la imagen principal"""
        if obj.imagen_principal:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen_principal.url)
            return obj.imagen_principal.url
        return None


class ProductoCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear y actualizar productos
    Con validaciones específicas
    """
    class Meta:
        model = Producto
        fields = [
            'id',
            'proveedor',
            'categoria',
            'nombre',
            'descripcion',
            'sku',
            'imagen_principal',
            'precio',
            'stock',
            'stock_minimo',
            'controlar_stock',
            'en_oferta',
            'precio_oferta',
            'descuento_porcentaje',
            'peso',
            'tiempo_preparacion',
            'activo',
            'destacado',
        ]
        read_only_fields = ['id']

    def validate_precio(self, value):
        """Valida que el precio sea positivo"""
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a 0")
        return value

    def validate_stock(self, value):
        """Valida que el stock no sea negativo"""
        if value < 0:
            raise serializers.ValidationError("El stock no puede ser negativo")
        return value

    def validate_descuento_porcentaje(self, value):
        """Valida que el descuento esté entre 0 y 100"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("El descuento debe estar entre 0 y 100")
        return value

    def validate_sku(self, value):
        """Valida que el SKU sea único"""
        instance = self.instance
        query = Producto.objects.filter(sku=value, deleted_at__isnull=True)

        if instance:
            query = query.exclude(id=instance.id)

        if query.exists():
            raise serializers.ValidationError("Ya existe un producto con este SKU")

        return value

    def validate(self, data):
        """Validaciones cruzadas"""
        # Validar precio de oferta
        if data.get('en_oferta') and data.get('precio_oferta'):
            if data['precio_oferta'] >= data.get('precio', 0):
                raise serializers.ValidationError({
                    'precio_oferta': 'El precio de oferta debe ser menor al precio normal'
                })

        # Validar que el proveedor esté activo
        proveedor = data.get('proveedor')
        if proveedor and not proveedor.activo:
            raise serializers.ValidationError({
                'proveedor': 'El proveedor no está activo'
            })

        # Validar que la categoría esté activa
        categoria = data.get('categoria')
        if categoria and not categoria.activo:
            raise serializers.ValidationError({
                'categoria': 'La categoría no está activa'
            })

        # Validar stock si se controla inventario
        if data.get('controlar_stock') and data.get('stock', 0) < 0:
            raise serializers.ValidationError({
                'stock': 'El stock no puede ser negativo cuando se controla inventario'
            })

        return data

    def create(self, validated_data):
        """Crea el producto con logging"""
        producto = Producto.objects.create(**validated_data)
        logger.info(f"✅ Producto creado vía API: {producto.nombre} (ID: {producto.id})")
        return producto

    def update(self, instance, validated_data):
        """Actualiza el producto con logging"""
        campos_actualizados = []

        for campo, valor in validated_data.items():
            if getattr(instance, campo) != valor:
                campos_actualizados.append(campo)
                setattr(instance, campo, valor)

        if campos_actualizados:
            instance.save()
            logger.info(
                f"📝 Producto actualizado vía API: {instance.nombre} (ID: {instance.id}). "
                f"Campos: {', '.join(campos_actualizados)}"
            )

        return instance


class ProductoStockUpdateSerializer(serializers.Serializer):
    """
    Serializer específico para actualizar stock
    """
    cantidad = serializers.IntegerField(required=True)
    operacion = serializers.ChoiceField(
        choices=['aumentar', 'descontar'],
        required=True
    )

    def validate_cantidad(self, value):
        """Valida que la cantidad sea positiva"""
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0")
        return value

    def update_stock(self, producto):
        """Actualiza el stock del producto"""
        cantidad = self.validated_data['cantidad']
        operacion = self.validated_data['operacion']

        if operacion == 'aumentar':
            producto.aumentar_stock(cantidad)
            mensaje = f"Stock aumentado en {cantidad} unidades"
        else:  # descontar
            if producto.descontar_stock(cantidad):
                mensaje = f"Stock descontado en {cantidad} unidades"
            else:
                raise serializers.ValidationError("Stock insuficiente para descontar")

        return {
            'mensaje': mensaje,
            'stock_actual': producto.stock,
            'stock_bajo': producto.stock_bajo
        }


class ProductoOfertaSerializer(serializers.Serializer):
    """
    Serializer para activar/desactivar ofertas
    """
    activar = serializers.BooleanField(required=True)
    precio_oferta = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    descuento_porcentaje = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True
    )

    def validate(self, data):
        """Validaciones"""
        if data.get('activar'):
            if not data.get('precio_oferta') and not data.get('descuento_porcentaje'):
                raise serializers.ValidationError(
                    "Debe especificar precio_oferta o descuento_porcentaje"
                )
        return data

    def update_oferta(self, producto):
        """Actualiza la oferta del producto"""
        if self.validated_data['activar']:
            producto.activar_oferta(
                precio_oferta=self.validated_data.get('precio_oferta'),
                descuento_porcentaje=self.validated_data.get('descuento_porcentaje')
            )
            mensaje = "Oferta activada exitosamente"
        else:
            producto.desactivar_oferta()
            mensaje = "Oferta desactivada exitosamente"

        return {
            'mensaje': mensaje,
            'en_oferta': producto.en_oferta,
            'precio_final': float(producto.precio_final)
        }


# ============================================
# SERIALIZERS PARA RESPUESTAS PERSONALIZADAS
# ============================================

class ProductoResumenSerializer(serializers.Serializer):
    """
    Serializer para resumen/estadísticas de productos
    """
    total_productos = serializers.IntegerField()
    productos_activos = serializers.IntegerField()
    productos_inactivos = serializers.IntegerField()
    productos_con_stock = serializers.IntegerField()
    productos_sin_stock = serializers.IntegerField()
    productos_en_oferta = serializers.IntegerField()
    productos_destacados = serializers.IntegerField()
    valor_total_inventario = serializers.DecimalField(max_digits=15, decimal_places=2)
