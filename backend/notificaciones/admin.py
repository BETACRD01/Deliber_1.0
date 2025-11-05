# notificaciones/admin.py
"""
Configuración del panel de administración para notificaciones
✅ Listado optimizado
✅ Filtros y búsqueda
✅ Acciones masivas
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from notificaciones.models import Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    """
    ✅ Administración de notificaciones
    """

    list_display = [
        'id_corto',
        'usuario_email',
        'tipo_badge',
        'titulo',
        'estado_badge',
        'enviada_push_badge',
        'pedido_link',
        'creada_hace',
        'leida_hace'
    ]

    list_filter = [
        'tipo',
        'leida',
        'enviada_push',
        'creada_en'
    ]

    search_fields = [
        'usuario__email',
        'usuario__first_name',
        'usuario__last_name',
        'titulo',
        'mensaje',
        'pedido__id'
    ]

    readonly_fields = [
        'id',
        'usuario',
        'pedido',
        'tipo',
        'titulo',
        'mensaje',
        'datos_extra',
        'enviada_push',
        'error_envio',
        'creada_en',
        'leida_en'
    ]

    fieldsets = (
        ('Información General', {
            'fields': (
                'id',
                'usuario',
                'tipo',
                'pedido'
            )
        }),
        ('Contenido', {
            'fields': (
                'titulo',
                'mensaje',
                'datos_extra'
            )
        }),
        ('Estado', {
            'fields': (
                'leida',
                'enviada_push',
                'error_envio'
            )
        }),
        ('Fechas', {
            'fields': (
                'creada_en',
                'leida_en'
            )
        })
    )

    ordering = ['-creada_en']

    list_per_page = 50

    date_hierarchy = 'creada_en'

    actions = ['marcar_como_leida', 'marcar_como_no_leida', 'reenviar_push']

    # ============================================
    # MÉTODOS PERSONALIZADOS PARA DISPLAY
    # ============================================

    @admin.display(description='ID')
    def id_corto(self, obj):
        """Muestra los primeros 8 caracteres del UUID"""
        return str(obj.id)[:8]

    @admin.display(description='Usuario')
    def usuario_email(self, obj):
        """Muestra el email del usuario"""
        return obj.usuario.email

    @admin.display(description='Tipo')
    def tipo_badge(self, obj):
        """Muestra el tipo con badge de color"""
        colores = {
            'pedido': '#2196F3',      # Azul
            'promocion': '#4CAF50',   # Verde
            'sistema': '#9E9E9E',     # Gris
            'repartidor': '#FF9800'   # Naranja
        }

        color = colores.get(obj.tipo, '#607D8B')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_tipo_display()
        )

    @admin.display(description='Estado', boolean=False)
    def estado_badge(self, obj):
        """Muestra el estado de lectura con badge"""
        if obj.leida:
            return format_html(
                '<span style="background-color: #4CAF50; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">✓ LEÍDA</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #F44336; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">✉ NO LEÍDA</span>'
            )

    @admin.display(description='Push', boolean=True)
    def enviada_push_badge(self, obj):
        """Muestra si se envió push"""
        return obj.enviada_push

    @admin.display(description='Pedido')
    def pedido_link(self, obj):
        """Muestra link al pedido si existe"""
        if obj.pedido:
            from django.urls import reverse
            from django.utils.html import format_html

            url = reverse('admin:pedidos_pedido_change', args=[obj.pedido.pk])
            return format_html('<a href="{}" target="_blank">Pedido #{}</a>', url, obj.pedido.pk)
        return '-'

    @admin.display(description='Creada hace')
    def creada_hace(self, obj):
        """Muestra tiempo desde creación"""
        return obj.tiempo_transcurrido

    @admin.display(description='Leída hace')
    def leida_hace(self, obj):
        """Muestra tiempo desde lectura"""
        if obj.leida and obj.leida_en:
            diff = timezone.now() - obj.leida_en
            minutos = int(diff.total_seconds() // 60)

            if minutos < 1:
                return "Ahora"
            elif minutos < 60:
                return f"{minutos} min"
            elif minutos < 1440:
                horas = minutos // 60
                return f"{horas}h"
            else:
                dias = minutos // 1440
                return f"{dias}d"
        return '-'

    # ============================================
    # ACCIONES MASIVAS
    # ============================================

    @admin.action(description='✓ Marcar como leída')
    def marcar_como_leida(self, request, queryset):
        """Marca las notificaciones seleccionadas como leídas"""
        count = queryset.filter(leida=False).update(
            leida=True,
            leida_en=timezone.now()
        )

        self.message_user(
            request,
            f'{count} notificación(es) marcada(s) como leída(s).'
        )

    @admin.action(description='✉ Marcar como no leída')
    def marcar_como_no_leida(self, request, queryset):
        """Marca las notificaciones seleccionadas como no leídas"""
        count = queryset.filter(leida=True).update(
            leida=False,
            leida_en=None
        )

        self.message_user(
            request,
            f'{count} notificación(es) marcada(s) como no leída(s).'
        )

    @admin.action(description='📤 Reenviar notificación push')
    def reenviar_push(self, request, queryset):
        """Reenvía notificaciones push seleccionadas"""
        from notificaciones.services import enviar_notificacion_push

        exitosos = 0
        fallidos = 0

        for notificacion in queryset:
            exito, _ = enviar_notificacion_push(
                usuario=notificacion.usuario,
                titulo=notificacion.titulo,
                mensaje=notificacion.mensaje,
                datos_extra=notificacion.datos_extra,
                guardar_en_bd=False  # No crear duplicado
            )

            if exito:
                exitosos += 1
            else:
                fallidos += 1

        self.message_user(
            request,
            f'Push reenviado: {exitosos} exitosos, {fallidos} fallidos.'
        )

    # ============================================
    # PERSONALIZACIÓN
    # ============================================

    def has_add_permission(self, request):
        """Deshabilitar creación manual desde admin"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Permitir eliminación desde admin"""
        return request.user.is_superuser
