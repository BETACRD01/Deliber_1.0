from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, F
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Categoria, Producto, ProductoVariante, ProductoImagen


# ============================================
# CATEGORIA ADMIN
# ============================================

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """
    Administración de Categorías en Django Admin
    """
    list_display = [
        'id',
        'nombre',
        'mostrar_icono',
        'orden',
        'activo',
        'total_productos_admin',
        'created_at',
    ]
    list_display_links = ['id', 'nombre']
    list_filter = ['activo', 'created_at']
    search_fields = ['nombre', 'descripcion']
    ordering = ['orden', 'nombre']
    list_editable = ['orden', 'activo']

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'icono')
        }),
        ('Configuración', {
            'fields': ('orden', 'activo')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def mostrar_icono(self, obj):
        """Muestra el icono en miniatura"""
        if obj.icono:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius: 5px;" />',
                obj.icono.url
            )
        return '—'
    mostrar_icono.short_description = 'Icono'

    def total_productos_admin(self, obj):
        """Muestra el total de productos activos"""
        total = obj.total_productos()
        if total > 0:
            url = reverse('admin:productos_producto_changelist') + f'?categoria__id__exact={obj.id}'
            return format_html(
                '<a href="{}" style="color: #417690; font-weight: bold;">{} productos</a>',
                url, total
            )
        return '0 productos'
    total_productos_admin.short_description = 'Productos'

    actions = ['activar_categorias', 'desactivar_categorias']

    def activar_categorias(self, request, queryset):
        """Activa categorías seleccionadas"""
        count = queryset.update(activo=True)
        self.message_user(request, f'{count} categoría(s) activada(s).')
    activar_categorias.short_description = '✅ Activar categorías seleccionadas'

    def desactivar_categorias(self, request, queryset):
        """Desactiva categorías seleccionadas"""
        count = queryset.update(activo=False)
        self.message_user(request, f'{count} categoría(s) desactivada(s).')
    desactivar_categorias.short_description = '❌ Desactivar categorías seleccionadas'


# ============================================
# INLINES PARA PRODUCTO
# ============================================

class ProductoVarianteInline(admin.TabularInline):
    """
    Inline para gestionar variantes dentro del producto
    """
    model = ProductoVariante
    extra = 0
    fields = ['nombre', 'precio', 'sku_variante', 'stock', 'activo']
    ordering = ['precio']


class ProductoImagenInline(admin.TabularInline):
    """
    Inline para gestionar imágenes adicionales dentro del producto
    """
    model = ProductoImagen
    extra = 0
    fields = ['imagen', 'mostrar_imagen_preview', 'orden', 'descripcion']
    readonly_fields = ['mostrar_imagen_preview']
    ordering = ['orden']

    def mostrar_imagen_preview(self, obj):
        """Muestra preview de la imagen"""
        if obj.imagen:
            return format_html(
                '<img src="{}" width="80" height="80" style="object-fit: cover; border-radius: 5px;" />',
                obj.imagen.url
            )
        return '—'
    mostrar_imagen_preview.short_description = 'Preview'


# ============================================
# PRODUCTO ADMIN
# ============================================

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """
    Administración de Productos en Django Admin
    """
    list_display = [
        'id',
        'mostrar_imagen',
        'nombre',
        'sku',
        'proveedor',
        'categoria',
        'mostrar_precio',
        'stock',
        'estado_stock',
        'activo',
        'en_oferta',
        'destacado',
        'created_at',
    ]
    list_display_links = ['id', 'nombre']
    list_filter = [
        'activo',
        'en_oferta',
        'destacado',
        'controlar_stock',
        'categoria',
        'proveedor',
        'created_at',
    ]
    search_fields = [
        'nombre',
        'descripcion',
        'sku',
        'proveedor__nombre',
        'categoria__nombre',
    ]
    ordering = ['-created_at']
    list_editable = ['activo', 'destacado']
    list_per_page = 25

    fieldsets = (
        ('Relaciones', {
            'fields': ('proveedor', 'categoria')
        }),
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'sku', 'imagen_principal')
        }),
        ('Precio y Stock', {
            'fields': (
                'precio',
                ('stock', 'stock_minimo'),
                'controlar_stock',
            )
        }),
        ('Ofertas y Descuentos', {
            'fields': (
                'en_oferta',
                'precio_oferta',
                'descuento_porcentaje',
            ),
            'classes': ('collapse',)
        }),
        ('Características', {
            'fields': ('peso', 'tiempo_preparacion'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('activo', 'destacado')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at', 'deleted_at']

    inlines = [ProductoVarianteInline, ProductoImagenInline]

    autocomplete_fields = ['proveedor', 'categoria']

    def mostrar_imagen(self, obj):
        """Muestra la imagen principal en miniatura"""
        if obj.imagen_principal:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />',
                obj.imagen_principal.url
            )
        return '📷'
    mostrar_imagen.short_description = 'Imagen'

    def mostrar_precio(self, obj):
        """Muestra el precio con formato y descuento si aplica"""
        if obj.en_oferta and obj.precio_final < obj.precio:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">${}</span><br>'
                '<span style="color: #e74c3c; font-weight: bold;">${}</span>',
                obj.precio,
                obj.precio_final
            )
        return format_html('<span>${}</span>', obj.precio)
    mostrar_precio.short_description = 'Precio'

    def estado_stock(self, obj):
        """Muestra el estado del stock con colores"""
        if not obj.controlar_stock:
            return format_html(
                '<span style="color: #95a5a6;">⚪ Sin control</span>'
            )

        if obj.stock == 0:
            return format_html(
                '<span style="color: #e74c3c; font-weight: bold;">🔴 Agotado</span>'
            )
        elif obj.stock_bajo:
            return format_html(
                '<span style="color: #f39c12; font-weight: bold;">🟡 Stock bajo</span>'
            )
        else:
            return format_html(
                '<span style="color: #27ae60; font-weight: bold;">🟢 Disponible</span>'
            )
    estado_stock.short_description = 'Estado'

    actions = [
        'activar_productos',
        'desactivar_productos',
        'destacar_productos',
        'quitar_destacado',
        'activar_ofertas',
        'desactivar_ofertas',
        'marcar_agotado',
    ]

    def activar_productos(self, request, queryset):
        """Activa productos seleccionados"""
        count = queryset.update(activo=True)
        self.message_user(request, f'{count} producto(s) activado(s).')
    activar_productos.short_description = '✅ Activar productos'

    def desactivar_productos(self, request, queryset):
        """Desactiva productos seleccionados"""
        count = queryset.update(activo=False)
        self.message_user(request, f'{count} producto(s) desactivado(s).')
    desactivar_productos.short_description = '❌ Desactivar productos'

    def destacar_productos(self, request, queryset):
        """Marca productos como destacados"""
        count = queryset.update(destacado=True)
        self.message_user(request, f'{count} producto(s) destacado(s).')
    destacar_productos.short_description = '⭐ Destacar productos'

    def quitar_destacado(self, request, queryset):
        """Quita el destacado de productos"""
        count = queryset.update(destacado=False)
        self.message_user(request, f'{count} producto(s) sin destacar.')
    quitar_destacado.short_description = '⚪ Quitar destacado'

    def activar_ofertas(self, request, queryset):
        """Activa ofertas en productos seleccionados"""
        count = queryset.update(en_oferta=True)
        self.message_user(request, f'{count} producto(s) en oferta.')
    activar_ofertas.short_description = '🏷️ Activar ofertas'

    def desactivar_ofertas(self, request, queryset):
        """Desactiva ofertas en productos seleccionados"""
        count = queryset.update(en_oferta=False, precio_oferta=None, descuento_porcentaje=0)
        self.message_user(request, f'{count} oferta(s) desactivada(s).')
    desactivar_ofertas.short_description = '🚫 Desactivar ofertas'

    def marcar_agotado(self, request, queryset):
        """Marca productos como agotados (stock = 0)"""
        count = queryset.update(stock=0)
        self.message_user(request, f'{count} producto(s) marcado(s) como agotado(s).')
    marcar_agotado.short_description = '🔴 Marcar como agotado'

    def get_queryset(self, request):
        """Optimiza la consulta con select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('proveedor', 'categoria').filter(deleted_at__isnull=True)


# ============================================
# PRODUCTO VARIANTE ADMIN
# ============================================

@admin.register(ProductoVariante)
class ProductoVarianteAdmin(admin.ModelAdmin):
    """
    Administración de Variantes de Productos
    """
    list_display = [
        'id',
        'producto',
        'nombre',
        'sku_variante',
        'precio',
        'stock',
        'activo',
        'created_at',
    ]
    list_display_links = ['id', 'nombre']
    list_filter = ['activo', 'producto__categoria', 'created_at']
    search_fields = [
        'nombre',
        'sku_variante',
        'producto__nombre',
        'producto__sku',
    ]
    ordering = ['-created_at']
    list_editable = ['activo']

    fieldsets = (
        ('Producto', {
            'fields': ('producto',)
        }),
        ('Información de la Variante', {
            'fields': ('nombre', 'descripcion', 'sku_variante')
        }),
        ('Precio y Stock', {
            'fields': ('precio', 'stock')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    autocomplete_fields = ['producto']

    actions = ['activar_variantes', 'desactivar_variantes']

    def activar_variantes(self, request, queryset):
        """Activa variantes seleccionadas"""
        count = queryset.update(activo=True)
        self.message_user(request, f'{count} variante(s) activada(s).')
    activar_variantes.short_description = '✅ Activar variantes'

    def desactivar_variantes(self, request, queryset):
        """Desactiva variantes seleccionadas"""
        count = queryset.update(activo=False)
        self.message_user(request, f'{count} variante(s) desactivada(s).')
    desactivar_variantes.short_description = '❌ Desactivar variantes'


# ============================================
# PRODUCTO IMAGEN ADMIN
# ============================================

@admin.register(ProductoImagen)
class ProductoImagenAdmin(admin.ModelAdmin):
    """
    Administración de Imágenes de Productos
    """
    list_display = [
        'id',
        'producto',
        'mostrar_preview',
        'orden',
        'descripcion',
        'created_at',
    ]
    list_display_links = ['id', 'producto']
    list_filter = ['producto__categoria', 'created_at']
    search_fields = ['producto__nombre', 'descripcion']
    ordering = ['producto', 'orden']
    list_editable = ['orden']

    fieldsets = (
        ('Producto', {
            'fields': ('producto',)
        }),
        ('Imagen', {
            'fields': ('imagen', 'mostrar_preview_grande', 'orden', 'descripcion')
        }),
        ('Auditoría', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'mostrar_preview_grande']

    autocomplete_fields = ['producto']

    def mostrar_preview(self, obj):
        """Muestra preview pequeño en la lista"""
        if obj.imagen:
            return format_html(
                '<img src="{}" width="60" height="60" style="object-fit: cover; border-radius: 5px;" />',
                obj.imagen.url
            )
        return '—'
    mostrar_preview.short_description = 'Preview'

    def mostrar_preview_grande(self, obj):
        """Muestra preview grande en el detalle"""
        if obj.imagen:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 400px; border-radius: 10px;" />',
                obj.imagen.url
            )
        return '—'
    mostrar_preview_grande.short_description = 'Preview Imagen'


# ============================================
# CONFIGURACIÓN ADICIONAL
# ============================================

# Personalizar títulos del admin
admin.site.site_header = 'Administración de Productos - Delivery'
admin.site.site_title = 'Productos Admin'
admin.site.index_title = 'Panel de Administración'
