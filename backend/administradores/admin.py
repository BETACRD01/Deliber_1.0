# -*- coding: utf-8 -*-
# administradores/admin.py
"""
Configuración del Django Admin para el módulo de administradores
✅ Interfaz completa para gestionar administradores
✅ Logs de acciones con filtros avanzados
✅ Configuración del sistema
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Administrador, AccionAdministrativa, ConfiguracionSistema


# ============================================
# ADMIN: ADMINISTRADOR
# ============================================

@admin.register(Administrador)
class AdministradorAdmin(admin.ModelAdmin):
    """
    Administración de perfiles de administradores
    """
    list_display = [
        'id',
        'usuario_info',
        'cargo',
        'departamento',
        'permisos_resumen',
        'total_acciones',
        'activo_badge',
        'creado_en',
    ]

    list_filter = [
        'activo',
        'puede_gestionar_usuarios',
        'puede_gestionar_pedidos',
        'puede_gestionar_proveedores',
        'puede_gestionar_repartidores',
        'puede_gestionar_rifas',
        'puede_ver_reportes',
        'puede_configurar_sistema',
        'creado_en',
    ]

    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'cargo',
        'departamento',
    ]

    readonly_fields = [
        'user',
        'total_acciones',
        'es_super_admin',
        'creado_en',
        'actualizado_en',
    ]

    fieldsets = (
        ('Información del Usuario', {
            'fields': ('user', 'cargo', 'departamento')
        }),
        ('Permisos de Gestión', {
            'fields': (
                'puede_gestionar_usuarios',
                'puede_gestionar_pedidos',
                'puede_gestionar_proveedores',
                'puede_gestionar_repartidores',
                'puede_gestionar_rifas',
                'puede_ver_reportes',
                'puede_configurar_sistema',
            ),
            'description': 'Configura los permisos específicos del administrador'
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Información Adicional', {
            'fields': (
                'total_acciones',
                'es_super_admin',
                'creado_en',
                'actualizado_en',
            ),
            'classes': ('collapse',)
        }),
    )

    ordering = ['-creado_en']
    date_hierarchy = 'creado_en'

    def usuario_info(self, obj):
        """Muestra información del usuario"""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.user.get_full_name() or obj.user.username,
            obj.user.email
        )
    usuario_info.short_description = 'Usuario'

    def permisos_resumen(self, obj):
        """Muestra resumen de permisos"""
        permisos = []
        if obj.puede_gestionar_usuarios:
            permisos.append('👥 Usuarios')
        if obj.puede_gestionar_pedidos:
            permisos.append('📦 Pedidos')
        if obj.puede_gestionar_proveedores:
            permisos.append('🏪 Proveedores')
        if obj.puede_gestionar_repartidores:
            permisos.append('🚚 Repartidores')
        if obj.puede_gestionar_rifas:
            permisos.append('🎲 Rifas')
        if obj.puede_ver_reportes:
            permisos.append('📊 Reportes')
        if obj.puede_configurar_sistema:
            permisos.append('⚙️ Sistema')

        if not permisos:
            return format_html('<span style="color: #999;">Sin permisos</span>')

        return format_html('<br>'.join(permisos))
    permisos_resumen.short_description = 'Permisos'

    def activo_badge(self, obj):
        """Badge de estado activo"""
        if obj.activo:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 3px;">✓ Activo</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; '
            'padding: 3px 10px; border-radius: 3px;">✗ Inactivo</span>'
        )
    activo_badge.short_description = 'Estado'

    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar administradores desde el admin"""
        return False


# ============================================
# ADMIN: ACCIÓN ADMINISTRATIVA
# ============================================

@admin.register(AccionAdministrativa)
class AccionAdministrativaAdmin(admin.ModelAdmin):
    """
    Administración de logs de acciones administrativas
    """
    list_display = [
        'id',
        'fecha_accion',
        'administrador_info',
        'tipo_accion_badge',
        'descripcion_corta',
        'modelo_afectado',
        'objeto_id',
        'exitosa_badge',
    ]

    list_filter = [
        'tipo_accion',
        'exitosa',
        'fecha_accion',
        'modelo_afectado',
    ]

    search_fields = [
        'descripcion',
        'administrador__user__email',
        'administrador__user__first_name',
        'administrador__user__last_name',
        'objeto_id',
        'ip_address',
    ]

    readonly_fields = [
        'id',
        'administrador',
        'tipo_accion',
        'descripcion',
        'modelo_afectado',
        'objeto_id',
        'datos_anteriores_formatted',
        'datos_nuevos_formatted',
        'ip_address',
        'user_agent',
        'exitosa',
        'mensaje_error',
        'fecha_accion',
    ]

    fieldsets = (
        ('Información de la Acción', {
            'fields': (
                'id',
                'administrador',
                'tipo_accion',
                'descripcion',
                'fecha_accion',
            )
        }),
        ('Objeto Afectado', {
            'fields': (
                'modelo_afectado',
                'objeto_id',
            )
        }),
        ('Cambios Realizados', {
            'fields': (
                'datos_anteriores_formatted',
                'datos_nuevos_formatted',
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'ip_address',
                'user_agent',
                'exitosa',
                'mensaje_error',
            ),
            'classes': ('collapse',)
        }),
    )

    ordering = ['-fecha_accion']
    date_hierarchy = 'fecha_accion'

    def administrador_info(self, obj):
        """Muestra información del administrador"""
        if obj.administrador:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.administrador.user.get_full_name(),
                obj.administrador.user.email
            )
        return format_html('<span style="color: #999;">Admin eliminado</span>')
    administrador_info.short_description = 'Administrador'

    def tipo_accion_badge(self, obj):
        """Badge de tipo de acción con colores"""
        colores = {
            'crear_usuario': '#28a745',
            'editar_usuario': '#007bff',
            'desactivar_usuario': '#ffc107',
            'activar_usuario': '#28a745',
            'cambiar_rol': '#17a2b8',
            'resetear_password': '#6c757d',
            'verificar_proveedor': '#28a745',
            'rechazar_proveedor': '#dc3545',
            'verificar_repartidor': '#28a745',
            'rechazar_repartidor': '#dc3545',
            'cancelar_pedido': '#dc3545',
            'configurar_sistema': '#6f42c1',
        }

        color = colores.get(obj.tipo_accion, '#6c757d')

        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_tipo_accion_display()
        )
    tipo_accion_badge.short_description = 'Tipo'

    def descripcion_corta(self, obj):
        """Descripción truncada"""
        if len(obj.descripcion) > 100:
            return obj.descripcion[:100] + '...'
        return obj.descripcion
    descripcion_corta.short_description = 'Descripción'

    def exitosa_badge(self, obj):
        """Badge de estado exitoso"""
        if obj.exitosa:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Exitosa</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">✗ Fallida</span>'
        )
    exitosa_badge.short_description = 'Estado'

    def datos_anteriores_formatted(self, obj):
        """Formatea datos anteriores como JSON"""
        if obj.datos_anteriores:
            import json
            formatted = json.dumps(obj.datos_anteriores, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', formatted)
        return '-'
    datos_anteriores_formatted.short_description = 'Datos Anteriores'

    def datos_nuevos_formatted(self, obj):
        """Formatea datos nuevos como JSON"""
        if obj.datos_nuevos:
            import json
            formatted = json.dumps(obj.datos_nuevos, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', formatted)
        return '-'
    datos_nuevos_formatted.short_description = 'Datos Nuevos'

    def has_add_permission(self, request):
        """No permitir crear logs manualmente"""
        return False

    def has_change_permission(self, request, obj=None):
        """No permitir editar logs"""
        return False

    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar logs (auditoría)"""
        return False


# ============================================
# ADMIN: CONFIGURACIÓN DEL SISTEMA
# ============================================

@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    """
    Administración de la configuración del sistema
    """
    list_display = [
        'id',
        'comision_app_proveedor',
        'comision_app_directo',
        'pedidos_minimos_rifa',
        'mantenimiento_badge',
        'modificado_por_info',
        'actualizado_en',
    ]

    readonly_fields = [
        'modificado_por',
        'actualizado_en',
    ]

    fieldsets = (
        ('Comisiones - Pedidos de Proveedor', {
            'fields': (
                'comision_app_proveedor',
                'comision_repartidor_proveedor',
            ),
            'description': 'Porcentajes de comisión para pedidos de proveedor'
        }),
        ('Comisiones - Encargos Directos', {
            'fields': (
                'comision_app_directo',
                'comision_repartidor_directo',
            ),
            'description': 'Porcentajes de comisión para encargos directos'
        }),
        ('Configuración de Rifas', {
            'fields': (
                'pedidos_minimos_rifa',
            ),
            'description': 'Configuración del sistema de rifas mensuales'
        }),
        ('Límites de Pedidos', {
            'fields': (
                'pedido_maximo',
                'pedido_minimo',
                'tiempo_maximo_entrega',
            ),
            'description': 'Límites y tiempos del sistema de pedidos'
        }),
        ('Información de Contacto', {
            'fields': (
                'telefono_soporte',
                'email_soporte',
            ),
            'description': 'Información de contacto para soporte'
        }),
        ('Modo Mantenimiento', {
            'fields': (
                'mantenimiento',
                'mensaje_mantenimiento',
            ),
            'description': '⚠️ Activar solo cuando se requiera mantenimiento del sistema'
        }),
        ('Auditoría', {
            'fields': (
                'modificado_por',
                'actualizado_en',
            ),
            'classes': ('collapse',)
        }),
    )

    def modificado_por_info(self, obj):
        """Muestra quién modificó la configuración"""
        if obj.modificado_por:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.modificado_por.user.get_full_name(),
                obj.modificado_por.user.email
            )
        return '-'
    modificado_por_info.short_description = 'Modificado Por'

    def mantenimiento_badge(self, obj):
        """Badge de estado de mantenimiento"""
        if obj.mantenimiento:
            return format_html(
                '<span style="background-color: #dc3545; color: white; '
                'padding: 5px 15px; border-radius: 3px; font-weight: bold;">'
                '⚠️ MANTENIMIENTO ACTIVO</span>'
            )
        return format_html(
            '<span style="background-color: #28a745; color: white; '
            'padding: 5px 15px; border-radius: 3px;">✓ Sistema Normal</span>'
        )
    mantenimiento_badge.short_description = 'Estado del Sistema'

    def has_add_permission(self, request):
        """Solo permitir una instancia (singleton)"""
        return not ConfiguracionSistema.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar la configuración"""
        return False

    def save_model(self, request, obj, form, change):
        """Guardar quién modificó la configuración"""
        try:
            admin = request.user.perfil_admin
            obj.modificado_por = admin
        except:
            pass

        super().save_model(request, obj, form, change)


# ============================================
# PERSONALIZACIÓN DEL ADMIN SITE
# ============================================

admin.site.site_header = "JP Express - Panel de Administración"
admin.site.site_title = "JP Express Admin"
admin.site.index_title = "Gestión del Sistema"
