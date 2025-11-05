from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from proveedores.models import Proveedor
import logging

logger = logging.getLogger('productos')


class CategoriaManager(models.Manager):
    """Manager personalizado para Categoria"""

    def activas(self):
        """Retorna solo categorías activas"""
        return self.filter(activo=True)

    def ordenadas(self):
        """Retorna categorías ordenadas"""
        return self.filter(activo=True).order_by('orden', 'nombre')


class Categoria(models.Model):
    """
    Modelo para categorías de productos
    Ej: Pizzas, Bebidas, Postres, Hamburguesas, etc.
    """
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre',
        help_text='Nombre de la categoría'
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción de la categoría'
    )

    icono = models.ImageField(
        upload_to='categorias/iconos/',
        null=True,
        blank=True,
        verbose_name='Icono',
        help_text='Icono representativo de la categoría'
    )

    orden = models.IntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de visualización (menor = primero)',
        db_index=True
    )

    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si la categoría está visible',
        db_index=True
    )

    # Auditoría
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    # Manager personalizado
    objects = CategoriaManager()

    class Meta:
        db_table = 'categorias'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['orden', 'nombre']
        indexes = [
            models.Index(fields=['activo']),
            models.Index(fields=['orden']),
        ]

    def __str__(self):
        return self.nombre

    def __repr__(self):
        return f"<Categoria: {self.nombre} (ID: {self.id})>"

    def total_productos(self):
        """Retorna el total de productos activos en esta categoría"""
        return self.productos.filter(activo=True, deleted_at__isnull=True).count()


class ProductoManager(models.Manager):
    """Manager personalizado para Producto"""

    def activos(self):
        """Retorna solo productos activos y no eliminados"""
        return self.filter(activo=True, deleted_at__isnull=True)

    def disponibles(self):
        """Retorna productos activos y con stock"""
        return self.filter(
            activo=True,
            deleted_at__isnull=True,
            stock__gt=0
        )

    def en_oferta(self):
        """Retorna productos en oferta"""
        return self.filter(
            activo=True,
            deleted_at__isnull=True,
            en_oferta=True
        )

    def por_proveedor(self, proveedor_id):
        """Retorna productos de un proveedor específico"""
        return self.filter(
            proveedor_id=proveedor_id,
            activo=True,
            deleted_at__isnull=True
        )

    def por_categoria(self, categoria_id):
        """Retorna productos de una categoría específica"""
        return self.filter(
            categoria_id=categoria_id,
            activo=True,
            deleted_at__isnull=True
        )


class Producto(models.Model):
    """
    Modelo principal de Productos

    ✅ CARACTERÍSTICAS:
    - Relación con Proveedor y Categoría
    - Control de stock e inventario
    - Sistema de descuentos
    - Soft delete
    - Múltiples imágenes (vía ProductoImagen)
    - Variantes opcionales (vía ProductoVariante)
    """

    # ============================================
    # RELACIONES
    # ============================================
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        related_name='productos',
        verbose_name='Proveedor',
        help_text='Proveedor que ofrece este producto',
        db_index=True
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='productos',
        verbose_name='Categoría',
        help_text='Categoría del producto',
        db_index=True
    )

    # ============================================
    # INFORMACIÓN BÁSICA
    # ============================================
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre',
        help_text='Nombre del producto',
        db_index=True
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción detallada del producto'
    )

    sku = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='SKU',
        help_text='Código único del producto',
        db_index=True
    )

    # ============================================
    # IMAGEN PRINCIPAL
    # ============================================
    imagen_principal = models.ImageField(
        upload_to='productos/',
        null=True,
        blank=True,
        verbose_name='Imagen Principal',
        help_text='Imagen principal del producto'
    )

    # ============================================
    # PRECIO Y STOCK
    # ============================================
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Precio',
        help_text='Precio base del producto'
    )

    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Stock',
        help_text='Cantidad disponible en inventario',
        db_index=True
    )

    stock_minimo = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0)],
        verbose_name='Stock Mínimo',
        help_text='Cantidad mínima antes de alerta'
    )

    controlar_stock = models.BooleanField(
        default=True,
        verbose_name='Controlar Stock',
        help_text='Si se debe controlar inventario para este producto'
    )

    # ============================================
    # DESCUENTOS Y OFERTAS
    # ============================================
    en_oferta = models.BooleanField(
        default=False,
        verbose_name='En Oferta',
        help_text='Si el producto está en oferta',
        db_index=True
    )

    precio_oferta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Precio de Oferta',
        help_text='Precio con descuento (opcional)'
    )

    descuento_porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Descuento (%)',
        help_text='Porcentaje de descuento (0-100)'
    )

    # ============================================
    # CARACTERÍSTICAS ADICIONALES
    # ============================================
    peso = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Peso (kg)',
        help_text='Peso del producto en kilogramos'
    )

    tiempo_preparacion = models.IntegerField(
        default=15,
        validators=[MinValueValidator(0)],
        verbose_name='Tiempo de Preparación (min)',
        help_text='Tiempo estimado de preparación en minutos'
    )

    # ============================================
    # ESTADO
    # ============================================
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si el producto está disponible para venta',
        db_index=True
    )

    destacado = models.BooleanField(
        default=False,
        verbose_name='Destacado',
        help_text='Si el producto aparece destacado en la app',
        db_index=True
    )

    # ============================================
    # AUDITORÍA
    # ============================================
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Eliminación',
        help_text='Soft delete'
    )

    # Manager personalizado
    objects = ProductoManager()

    class Meta:
        db_table = 'productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['proveedor', 'activo']),
            models.Index(fields=['categoria', 'activo']),
            models.Index(fields=['sku']),
            models.Index(fields=['activo']),
            models.Index(fields=['en_oferta']),
            models.Index(fields=['destacado']),
            models.Index(fields=['deleted_at']),
            models.Index(fields=['stock']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(precio__gte=0),
                name='precio_no_negativo'
            ),
            models.CheckConstraint(
                check=models.Q(stock__gte=0),
                name='stock_no_negativo'
            ),
        ]

    def __str__(self):
        return f"{self.nombre} - {self.proveedor.nombre}"

    def __repr__(self):
        return f"<Producto: {self.nombre} (ID: {self.id}, SKU: {self.sku})>"

    # ============================================
    # PROPIEDADES
    # ============================================
    @property
    def precio_final(self):
        """Retorna el precio final considerando ofertas"""
        if self.en_oferta and self.precio_oferta:
            return self.precio_oferta
        if self.descuento_porcentaje > 0:
            descuento = self.precio * (self.descuento_porcentaje / 100)
            return self.precio - descuento
        return self.precio

    @property
    def ahorro(self):
        """Retorna el ahorro si hay descuento"""
        if self.precio_final < self.precio:
            return self.precio - self.precio_final
        return 0

    @property
    def tiene_stock(self):
        """Verifica si hay stock disponible"""
        if not self.controlar_stock:
            return True
        return self.stock > 0

    @property
    def stock_bajo(self):
        """Verifica si el stock está bajo"""
        if not self.controlar_stock:
            return False
        return self.stock <= self.stock_minimo

    @property
    def tiene_variantes(self):
        """Verifica si el producto tiene variantes"""
        return self.variantes.exists()

    # ============================================
    # MÉTODOS
    # ============================================
    def descontar_stock(self, cantidad):
        """
        Descuenta stock del producto

        Args:
            cantidad (int): Cantidad a descontar

        Returns:
            bool: True si se pudo descontar, False si no hay suficiente
        """
        if not self.controlar_stock:
            logger.info(f"Producto {self.id} no controla stock")
            return True

        if self.stock >= cantidad:
            self.stock -= cantidad
            self.save(update_fields=['stock'])
            logger.info(f"Stock descontado: Producto {self.id}, Cantidad: {cantidad}, Nuevo stock: {self.stock}")
            return True
        else:
            logger.warning(f"Stock insuficiente: Producto {self.id}, Disponible: {self.stock}, Solicitado: {cantidad}")
            return False

    def aumentar_stock(self, cantidad):
        """Aumenta el stock del producto"""
        if not self.controlar_stock:
            return

        self.stock += cantidad
        self.save(update_fields=['stock'])
        logger.info(f"Stock aumentado: Producto {self.id}, Cantidad: {cantidad}, Nuevo stock: {self.stock}")

    def activar_oferta(self, precio_oferta=None, descuento_porcentaje=None):
        """Activa una oferta en el producto"""
        self.en_oferta = True

        if precio_oferta:
            self.precio_oferta = precio_oferta

        if descuento_porcentaje:
            self.descuento_porcentaje = descuento_porcentaje

        self.save(update_fields=['en_oferta', 'precio_oferta', 'descuento_porcentaje'])
        logger.info(f"✅ Oferta activada: Producto {self.id}")

    def desactivar_oferta(self):
        """Desactiva la oferta del producto"""
        self.en_oferta = False
        self.precio_oferta = None
        self.descuento_porcentaje = 0
        self.save(update_fields=['en_oferta', 'precio_oferta', 'descuento_porcentaje'])
        logger.info(f"❌ Oferta desactivada: Producto {self.id}")

    def soft_delete(self):
        """Eliminación suave del producto"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.activo = False
        self.save(update_fields=['deleted_at', 'activo'])
        logger.warning(f"🗑️ Producto {self.id} marcado como eliminado")

    def restore(self):
        """Restaura un producto eliminado"""
        self.deleted_at = None
        self.activo = True
        self.save(update_fields=['deleted_at', 'activo'])
        logger.info(f"♻️ Producto {self.id} restaurado")

    # ============================================
    # VALIDACIONES
    # ============================================
    def clean(self):
        """Validaciones antes de guardar"""
        super().clean()

        # Validar precio de oferta
        if self.en_oferta and self.precio_oferta:
            if self.precio_oferta >= self.precio:
                raise ValidationError({
                    'precio_oferta': 'El precio de oferta debe ser menor al precio normal'
                })

        # Validar descuento
        if self.descuento_porcentaje < 0 or self.descuento_porcentaje > 100:
            raise ValidationError({
                'descuento_porcentaje': 'El descuento debe estar entre 0 y 100'
            })

        # Validar stock mínimo
        if self.stock_minimo < 0:
            raise ValidationError({
                'stock_minimo': 'El stock mínimo no puede ser negativo'
            })

    def save(self, *args, **kwargs):
        """Override save para validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)


class ProductoVariante(models.Model):
    """
    Modelo para variantes de productos
    Ej: Pizza Pequeña, Mediana, Grande
         Gaseosa 500ml, 1L, 2L
    """
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='variantes',
        verbose_name='Producto',
        db_index=True
    )

    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre',
        help_text='Nombre de la variante (Ej: Grande, 500ml, Familiar)'
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción adicional de la variante'
    )

    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Precio',
        help_text='Precio específico de esta variante'
    )

    sku_variante = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='SKU Variante',
        help_text='Código único de la variante',
        db_index=True
    )

    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Stock',
        help_text='Stock específico de esta variante'
    )

    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        db_index=True
    )

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'producto_variantes'
        verbose_name = 'Variante de Producto'
        verbose_name_plural = 'Variantes de Productos'
        ordering = ['producto', 'precio']
        unique_together = [['producto', 'nombre']]
        indexes = [
            models.Index(fields=['producto', 'activo']),
            models.Index(fields=['sku_variante']),
        ]

    def __str__(self):
        return f"{self.producto.nombre} - {self.nombre} (${self.precio})"

    def descontar_stock(self, cantidad):
        """Descuenta stock de la variante"""
        if self.stock >= cantidad:
            self.stock -= cantidad
            self.save(update_fields=['stock'])
            logger.info(f"Stock variante descontado: {self.id}, Cantidad: {cantidad}")
            return True
        return False

    def aumentar_stock(self, cantidad):
        """Aumenta stock de la variante"""
        self.stock += cantidad
        self.save(update_fields=['stock'])
        logger.info(f"Stock variante aumentado: {self.id}, Cantidad: {cantidad}")


class ProductoImagen(models.Model):
    """
    Modelo para múltiples imágenes de productos
    """
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='imagenes',
        verbose_name='Producto',
        db_index=True
    )

    imagen = models.ImageField(
        upload_to='productos/galeria/',
        verbose_name='Imagen'
    )

    orden = models.IntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de visualización'
    )

    descripcion = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción de la imagen'
    )

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'producto_imagenes'
        verbose_name = 'Imagen de Producto'
        verbose_name_plural = 'Imágenes de Productos'
        ordering = ['producto', 'orden']
        indexes = [
            models.Index(fields=['producto', 'orden']),
        ]

    def __str__(self):
        return f"Imagen {self.orden} - {self.producto.nombre}"


# ============================================
# SIGNALS
# ============================================

@receiver(post_save, sender=Producto)
def producto_post_save(sender, instance, created, **kwargs):
    """Signal después de guardar producto"""
    if created:
        logger.info(f"✅ Producto creado: {instance.nombre} (ID: {instance.id}, SKU: {instance.sku})")

        # Alertar si el stock es bajo al crear
        if instance.controlar_stock and instance.stock_bajo:
            logger.warning(f"⚠️ Producto {instance.id} creado con stock bajo: {instance.stock}")
    else:
        # Alertar si el stock llegó a nivel bajo
        if instance.controlar_stock and instance.stock_bajo and instance.stock > 0:
            logger.warning(f"⚠️ Stock bajo: Producto {instance.id} ({instance.nombre}), Stock: {instance.stock}")

        # Alertar si se agotó el stock
        if instance.controlar_stock and instance.stock == 0:
            logger.error(f"🚫 Stock agotado: Producto {instance.id} ({instance.nombre})")


@receiver(pre_delete, sender=Producto)
def producto_pre_delete(sender, instance, **kwargs):
    """Signal antes de eliminar producto"""
    logger.warning(f"🗑️ Eliminando producto: {instance.nombre} (ID: {instance.id})")
