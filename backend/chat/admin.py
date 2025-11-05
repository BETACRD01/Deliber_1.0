# ============================================
# chat/admin.py
# ============================================

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Chat, Mensaje, TipoChat, TipoMensaje


# ============================================
# ADMIN: MENSAJE (INLINE)
# ============================================

class MensajeInline(admin.TabularInline):
    """Inline para ver mensajes dentro de un chat"""
    model = Mensaje
    extra = 0
    fields = ['remitente', 'tipo', 'contenido_preview', 'leido', 'creado_en']
    readonly_fields = ['remitente', 'tipo', 'contenido_preview', 'leido', 'creado_en']
    can_delete = False

    def contenido_preview(self, obj):
        """Preview del contenido según tipo"""
        if obj.tipo == TipoMensaje.TEXTO:
            return obj.contenido[:100] if obj.contenido else ''
        elif obj.tipo == TipoMensaje.IMAGEN:
            return format_html('<span style="color: blue;">📷 Imagen</span>')
        elif obj.tipo == TipoMensaje.AUDIO:
            return format_html('<span style="color: green;">🎤 Audio</span>')
        return '-'

    contenido_preview.short_description = 'Contenido'

    def has_add_permission(self, request, obj=None):
        return False


# ============================================
# ADMIN: CHAT
# ============================================

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    """Administración de chats"""

    list_display = [
        'id_corto',
        'tipo',
        'titulo',
        'pedido_link',
        'participantes_lista',
        'total_mensajes_badge',
        'activo_badge',
        'creado_en',
        'actualizado_en'
    ]

    list_filter = [
        'tipo',
        'activo',
        'creado_en',
        'actualizado_en'
    ]

    search_fields = [
        'id',
        'titulo',
        'pedido__pk',
        'proveedor__nombre',
        'participantes__email',
        'participantes__first_name',
        'participantes__last_name'
    ]

    readonly_fields = [
        'id',
        'creado_en',
        'actualizado_en',
        'cerrado_en',
        'total_mensajes',
        'tiene_mensajes_sin_leer'
    ]

    filter_horizontal = ['participantes']

    inlines = [MensajeInline]

    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'tipo', 'titulo', 'activo')
        }),
        ('Relaciones', {
            'fields': ('pedido', 'proveedor', 'participantes')
        }),
        ('Estadísticas', {
            'fields': ('total_mensajes', 'tiene_mensajes_sin_leer')
        }),
        ('Auditoría', {
            'fields': ('creado_en', 'actualizado_en', 'cerrado_en'),
            'classes': ('collapse',)
        }),
    )

    def id_corto(self, obj):
        """Muestra ID corto"""
        return str(obj.id)[:8]
    id_corto.short_description = 'ID'

    def pedido_link(self, obj):
        """Link al pedido si existe"""
        if obj.pedido:
            from django.urls import reverse
            url = reverse('admin:pedidos_pedido_change', args=[obj.pedido.pk])
            return format_html('<a href="{}"  target="_blank">Pedido #{}</a>', url, obj.pedido.pk)
        return '-'
    pedido_link.short_description = 'Pedido'

    def participantes_lista(self, obj):
        """Lista de participantes"""
        participantes = obj.participantes.all()
        if participantes:
            nombres = [p.get_full_name() or p.email for p in participantes]
            return ', '.join(nombres)
        return '-'
    participantes_lista.short_description = 'Participantes'

    def total_mensajes_badge(self, obj):
        """Badge con total de mensajes"""
        count = obj.total_mensajes
        if count > 0:
            return format_html(
                '<span style="background-color: #17a2b8; color: white; '
                'padding: 3px 8px; border-radius: 10px;">{}</span>',
                count
            )
        return '0'
    total_mensajes_badge.short_description = 'Mensajes'

    def activo_badge(self, obj):
        """Badge de estado activo"""
        if obj.activo:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 8px; border-radius: 10px;">Activo</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; '
            'padding: 3px 8px; border-radius: 10px;">Cerrado</span>'
        )
    activo_badge.short_description = 'Estado'

    def get_queryset(self, request):
        """Optimiza queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('pedido', 'proveedor').prefetch_related('participantes')


# ============================================
# ADMIN: MENSAJE
# ============================================

@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    """Administración de mensajes"""

    list_display = [
        'id_corto',
        'chat_link',
        'remitente_nombre',
        'tipo_badge',
        'contenido_preview',
        'archivo_badge',
        'leido_badge',
        'eliminado_badge',
        'creado_en'
    ]

    list_filter = [
        'tipo',
        'leido',
        'eliminado',
        'creado_en',
        'chat__tipo'
    ]

    search_fields = [
        'id',
        'contenido',
        'remitente__email',
        'remitente__first_name',
        'remitente__last_name',
        'chat__titulo'
    ]

    readonly_fields = [
        'id',
        'chat',
        'remitente',
        'tipo',
        'contenido',
        'archivo_preview',
        'nombre_archivo',
        'tamano_archivo_mb',
        'duracion_audio',
        'leido_en',
        'creado_en',
        'actualizado_en'
    ]

    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'chat', 'remitente', 'tipo')
        }),
        ('Contenido', {
            'fields': ('contenido', 'archivo_preview', 'archivo', 'nombre_archivo',
                      'tamano_archivo_mb', 'duracion_audio')
        }),
        ('Estado', {
            'fields': ('leido', 'leido_en', 'eliminado')
        }),
        ('Auditoría', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
    )

    def id_corto(self, obj):
        """ID corto"""
        return str(obj.id)[:8]
    id_corto.short_description = 'ID'

    def chat_link(self, obj):
        """Link al chat"""
        from django.urls import reverse
        url = reverse('admin:chat_chat_change', args=[obj.chat.pk])
        return format_html('<a href="{}" target="_blank">{}</a>', url, obj.chat.titulo)
    chat_link.short_description = 'Chat'

    def remitente_nombre(self, obj):
        """Nombre del remitente"""
        if obj.remitente:
            return obj.remitente.get_full_name() or obj.remitente.email
        return 'Sistema'
    remitente_nombre.short_description = 'Remitente'

    def tipo_badge(self, obj):
        """Badge del tipo de mensaje"""
        colors = {
            TipoMensaje.TEXTO: '#007bff',
            TipoMensaje.IMAGEN: '#28a745',
            TipoMensaje.AUDIO: '#17a2b8',
            TipoMensaje.SISTEMA: '#6c757d'
        }
        color = colors.get(obj.tipo, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 10px;">{}</span>',
            color, obj.get_tipo_display()
        )
    tipo_badge.short_description = 'Tipo'

    def contenido_preview(self, obj):
        """Preview del contenido"""
        if obj.tipo == TipoMensaje.TEXTO:
            return obj.contenido[:80] + '...' if len(obj.contenido) > 80 else obj.contenido
        elif obj.tipo == TipoMensaje.IMAGEN:
            return '📷 Imagen adjunta'
        elif obj.tipo == TipoMensaje.AUDIO:
            return f'🎤 Audio ({obj.duracion_audio}s)' if obj.duracion_audio else '🎤 Audio'
        return obj.contenido[:80] if obj.contenido else '-'
    contenido_preview.short_description = 'Contenido'

    def archivo_badge(self, obj):
        """Badge de archivo adjunto"""
        if obj.archivo:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 8px; border-radius: 10px;">Sí</span>'
            )
        return '-'
    archivo_badge.short_description = 'Archivo'

    def archivo_preview(self, obj):
        """Preview del archivo"""
        if obj.archivo:
            if obj.es_imagen:
                return format_html(
                    '<img src="{}" style="max-width: 300px; max-height: 300px;" />',
                    obj.url_archivo
                )
            elif obj.es_audio:
                return format_html(
                    '<audio controls><source src="{}" type="audio/mpeg"></audio>',
                    obj.url_archivo
                )
            return format_html('<a href="{}" target="_blank">Ver archivo</a>', obj.url_archivo)
        return '-'
    archivo_preview.short_description = 'Preview Archivo'

    def leido_badge(self, obj):
        """Badge de leído"""
        if obj.leido:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 8px; border-radius: 10px;">✓✓</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; '
            'padding: 3px 8px; border-radius: 10px;">✓</span>'
        )
    leido_badge.short_description = 'Leído'

    def eliminado_badge(self, obj):
        """Badge de eliminado"""
        if obj.eliminado:
            return format_html(
                '<span style="background-color: #dc3545; color: white; '
                'padding: 3px 8px; border-radius: 10px;">Eliminado</span>'
            )
        return '-'
    eliminado_badge.short_description = 'Eliminado'

    def get_queryset(self, request):
        """Optimiza queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('chat', 'remitente')

    def has_add_permission(self, request):
        """No permitir agregar mensajes desde el admin"""
        return False
