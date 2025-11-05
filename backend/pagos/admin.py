# pagos/admin.py
"""
Configuración del Admin de Django para el módulo de Pagos.

✅ CARACTERÍSTICAS:
- Panel completo de gestión de pagos
- Verificación manual de transferencias
- Procesamiento de reembolsos
- Filtros avanzados y búsqueda
- Vista detallada de transacciones
- Estadísticas en tiempo real
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.contrib import messages
from django.shortcuts import redirect
from .models import (
    MetodoPago, Pago, Transaccion, EstadisticasPago,
    EstadoPago, TipoMetodoPago
)
import logging

logger = logging.getLogger('pagos')


# ==========================================================
# 🔧 INLINES
# ==========================================================

class TransaccionInline(admin.TabularInline):
    """Inline para mostrar transacciones del pago"""
    model = Transaccion
    extra = 0
    can_delete = False
    fields = (
        'tipo',
        'monto',
        'exitosa_display',
        'descripcion',
        'creado_en'
    )
    readonly_fields = (
        'tipo',
        'monto',
        'exitosa_display',
        'descripcion',
        'creado_en'
    )

    def exitosa_display(self, obj):
        """Muestra estado con íconos"""
        if obj.exitosa is True:
            return format_html('<span style="color: green;">✓ Exitosa</span>')
        elif obj.exitosa is False:
            return format_html('<span style="color: red;">✗ Fallida</span>')
        else:
            return format_html('<span style="color: orange;">⏳ En proceso</span>')
    exitosa_display.short_description = 'Estado'

    def has_add_permission(self, request, obj=None):
        return False


# ==========================================================
# 💳 ADMIN: MÉTODO DE PAGO
# ==========================================================

@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    """Administración de métodos de pago"""

    list_display = (
        'tipo',
        'nombre',
        'activo_display',
        'requiere_verificacion',
        'permite_reembolso',
        'pasarela_nombre',
        'total_pagos_hoy'
    )

    list_filter = (
        'activo',
        'tipo',
        'requiere_verificacion',
        'permite_reembolso'
    )

    search_fields = (
        'nombre',
        'descripcion',
        'pasarela_nombre'
    )

    fieldsets = (
        ('Información Básica', {
            'fields': (
                'tipo',
                'nombre',
                'descripcion',
                'activo'
            )
        }),
        ('Configuración', {
            'fields': (
                'requiere_verificacion',
                'permite_reembolso'
            )
        }),
        ('Pasarela Externa', {
            'fields': (
                'pasarela_nombre',
                'pasarela_api_key',
                'pasarela_configuracion'
            ),
            'classes': ('collapse',),
            'description': 'Configuración para pasarelas de pago externas (Stripe, Kushki, etc.)'
        }),
        ('Auditoría', {
            'fields': (
                'creado_en',
                'actualizado_en'
            ),
            'classes': ('collapse',)
        })
    )

    readonly_fields = ('creado_en', 'actualizado_en')

    def activo_display(self, obj):
        """Muestra estado activo con ícono"""
        if obj.activo:
            return format_html('<span style="color: green;">✓ Activo</span>')
        return format_html('<span style="color: red;">✗ Inactivo</span>')
    activo_display.short_description = 'Estado'
    activo_display.admin_order_field = 'activo'

    def total_pagos_hoy(self, obj):
        """Muestra total de pagos del día con este método"""
        hoy = timezone.now().date()
        count = obj.pagos.filter(creado_en__date=hoy).count()
        return f"{count} pagos"
    total_pagos_hoy.short_description = 'Pagos Hoy'


# ==========================================================
# 💰 ADMIN: PAGO
# ==========================================================

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    """Administración principal de pagos"""

    list_display = (
        'referencia_corta',
        'pedido_link',
        'cliente_info',
        'metodo_display',
        'monto_display',
        'estado_display',
        'verificado_display',
        'creado_hace',
        'acciones_rapidas'
    )

    list_filter = (
        'estado',
        ('metodo_pago__tipo', admin.ChoicesFieldListFilter),
        'creado_en',
        ('verificado_por', admin.EmptyFieldListFilter),
    )

    search_fields = (
        'referencia',
        'pedido__id',
        'pedido__cliente__user__email',
        'pedido__cliente__user__first_name',
        'pedido__cliente__user__last_name',
        'pasarela_id_transaccion',
        'transferencia_numero_operacion'
    )

    date_hierarchy = 'creado_en'

    readonly_fields = (
        'referencia',
        'referencia_display',
        'pedido_detalle',
        'estado_visual',
        'monto_pendiente_reembolso',
        'tiempo_desde_creacion',
        'transacciones_historial',
        'creado_en',
        'actualizado_en',
        'fecha_completado',
        'fecha_reembolso',
        'fecha_verificacion'
    )

    fieldsets = (
        ('Información Principal', {
            'fields': (
                'referencia_display',
                'pedido_detalle',
                'metodo_pago',
                'estado_visual'
            )
        }),
        ('Montos', {
            'fields': (
                'monto',
                'monto_reembolsado',
                'monto_pendiente_reembolso'
            )
        }),
        ('Tarjeta', {
            'fields': (
                'tarjeta_ultimos_digitos',
                'tarjeta_marca'
            ),
            'classes': ('collapse',),
            'description': 'Información de la tarjeta (solo últimos 4 dígitos)'
        }),
        ('Transferencia Bancaria', {
            'fields': (
                'transferencia_banco',
                'transferencia_numero_operacion',
                'transferencia_comprobante'
            ),
            'classes': ('collapse',)
        }),
        ('Pasarela Externa', {
            'fields': (
                'pasarela_id_transaccion',
                'pasarela_respuesta'
            ),
            'classes': ('collapse',)
        }),
        ('Verificación', {
            'fields': (
                'verificado_por',
                'fecha_verificacion'
            ),
            'classes': ('collapse',)
        }),
        ('Información Adicional', {
            'fields': (
                'metadata',
                'notas'
            ),
            'classes': ('collapse',)
        }),
        ('Historial de Transacciones', {
            'fields': (
                'transacciones_historial',
            ),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': (
                'tiempo_desde_creacion',
                'creado_en',
                'actualizado_en',
                'fecha_completado',
                'fecha_reembolso'
            ),
            'classes': ('collapse',)
        })
    )

    inlines = [TransaccionInline]

    actions = [
        'marcar_como_completado',
        'verificar_transferencia',
        'procesar_reembolso_total',
        'marcar_como_fallido',
        'exportar_reporte'
    ]

    # ==========================================================
    # MÉTODOS DE VISUALIZACIÓN
    # ==========================================================

    def referencia_corta(self, obj):
        """Muestra referencia corta"""
        ref = str(obj.referencia)
        return f"{ref[:8]}..."
    referencia_corta.short_description = 'Referencia'

    def referencia_display(self, obj):
        """Muestra referencia completa con formato"""
        return format_html(
            '<code style="background: #f5f5f5; padding: 5px; border-radius: 3px;">{}</code>',
            obj.referencia
        )
    referencia_display.short_description = 'Referencia UUID'

    def pedido_link(self, obj):
        """Link al pedido"""
        url = reverse('admin:pedidos_pedido_change', args=[obj.pedido.pk])
        return format_html(
            '<a href="{}" target="_blank">Pedido #{}</a>',
            url, obj.pedido.pk
        )
    pedido_link.short_description = 'Pedido'

    def pedido_detalle(self, obj):
        """Muestra detalles del pedido"""
        url = reverse('admin:pedidos_pedido_change', args=[obj.pedido.pk])
        return format_html(
            '<div style="line-height: 1.8;">'
            '<strong>Pedido:</strong> <a href="{}" target="_blank">#{}</a><br>'
            '<strong>Cliente:</strong> {}<br>'
            '<strong>Estado Pedido:</strong> {}<br>'
            '<strong>Total Pedido:</strong> ${}'
            '</div>',
            url,
            obj.pedido.pk,
            obj.pedido.cliente.user.get_full_name(),
            obj.pedido.get_estado_display(),
            obj.pedido.total
        )
    pedido_detalle.short_description = 'Detalles del Pedido'

    def cliente_info(self, obj):
        """Muestra información del cliente"""
        cliente = obj.pedido.cliente
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            cliente.user.get_full_name(),
            cliente.user.email
        )
    cliente_info.short_description = 'Cliente'

    def metodo_display(self, obj):
        """Muestra método de pago con ícono"""
        iconos = {
            'efectivo': '💵',
            'transferencia': '🏦',
            'tarjeta_credito': '💳',
            'tarjeta_debito': '💳'
        }
        icono = iconos.get(obj.metodo_pago.tipo, '💰')
        return format_html(
            '{} {}',
            icono,
            obj.metodo_pago.nombre
        )
    metodo_display.short_description = 'Método'
    metodo_display.admin_order_field = 'metodo_pago__tipo'

    def monto_display(self, obj):
        """Muestra monto con formato"""
        html = f'<strong style="font-size: 14px;">${obj.monto}</strong>'

        if obj.monto_reembolsado > 0:
            html += format_html(
                '<br><small style="color: #d32f2f;">Reemb: ${}</small>',
                obj.monto_reembolsado
            )

        return format_html(html)
    monto_display.short_description = 'Monto'
    monto_display.admin_order_field = 'monto'

    def estado_display(self, obj):
        """Muestra estado con colores"""
        colores = {
            EstadoPago.PENDIENTE: '#ff9800',
            EstadoPago.PROCESANDO: '#2196f3',
            EstadoPago.COMPLETADO: '#4caf50',
            EstadoPago.FALLIDO: '#f44336',
            EstadoPago.REEMBOLSADO: '#9c27b0',
            EstadoPago.CANCELADO: '#757575'
        }
        color = colores.get(obj.estado, '#000')

        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display().upper()
        )
    estado_display.short_description = 'Estado'
    estado_display.admin_order_field = 'estado'

    def estado_visual(self, obj):
        """Estado visual expandido con detalles"""
        colores = {
            EstadoPago.PENDIENTE: '#ff9800',
            EstadoPago.PROCESANDO: '#2196f3',
            EstadoPago.COMPLETADO: '#4caf50',
            EstadoPago.FALLIDO: '#f44336',
            EstadoPago.REEMBOLSADO: '#9c27b0',
            EstadoPago.CANCELADO: '#757575'
        }
        color = colores.get(obj.estado, '#000')

        html = format_html(
            '<div style="background: {}; color: white; padding: 15px; '
            'border-radius: 5px; text-align: center; font-size: 16px; '
            'font-weight: bold; margin: 10px 0;">{}</div>',
            color,
            obj.get_estado_display().upper()
        )

        # Información adicional según estado
        if obj.estado == EstadoPago.PENDIENTE and obj.requiere_verificacion_manual:
            html += format_html(
                '<div style="background: #fff3cd; color: #856404; padding: 10px; '
                'border-radius: 5px; margin-top: 10px;">⚠️ Requiere verificación manual</div>'
            )

        if obj.fue_reembolsado_parcialmente:
            html += format_html(
                '<div style="background: #e1bee7; color: #4a148c; padding: 10px; '
                'border-radius: 5px; margin-top: 10px;">💰 Reembolso parcial: ${}</div>',
                obj.monto_reembolsado
            )

        return html
    estado_visual.short_description = 'Estado Actual'

    def verificado_display(self, obj):
        """Muestra si fue verificado"""
        if obj.verificado_por:
            return format_html(
                '<span style="color: green;">✓ {}</span>',
                obj.verificado_por.get_full_name()
            )
        elif obj.requiere_verificacion_manual:
            return format_html('<span style="color: orange;">⏳ Pendiente</span>')
        return format_html('<span style="color: gray;">N/A</span>')
    verificado_display.short_description = 'Verificado'

    def creado_hace(self, obj):
        """Tiempo desde creación"""
        return obj.tiempo_desde_creacion
    creado_hace.short_description = 'Creado'
    creado_hace.admin_order_field = 'creado_en'

    def acciones_rapidas(self, obj):
        """Botones de acciones rápidas"""
        botones = []

        if obj.estado == EstadoPago.PENDIENTE:
            if obj.es_transferencia and not obj.verificado_por:
                botones.append(
                    '<a class="button" href="#" onclick="return false;" '
                    'style="background: #4caf50; color: white; padding: 5px 10px; '
                    'border-radius: 3px; text-decoration: none; font-size: 11px;">✓ Verificar</a>'
                )
            else:
                botones.append(
                    '<a class="button" href="#" onclick="return false;" '
                    'style="background: #2196f3; color: white; padding: 5px 10px; '
                    'border-radius: 3px; text-decoration: none; font-size: 11px;">✓ Completar</a>'
                )

        if obj.estado == EstadoPago.COMPLETADO and obj.metodo_pago.permite_reembolso:
            botones.append(
                '<a class="button" href="#" onclick="return false;" '
                'style="background: #9c27b0; color: white; padding: 5px 10px; '
                'border-radius: 3px; text-decoration: none; font-size: 11px; '
                'margin-left: 5px;">↩ Reembolsar</a>'
            )

        return format_html(' '.join(botones)) if botones else '-'
    acciones_rapidas.short_description = 'Acciones'

    def transacciones_historial(self, obj):
        """Muestra historial de transacciones"""
        transacciones = obj.transacciones.all()

        if not transacciones:
            return format_html('<p>No hay transacciones registradas</p>')

        html = '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background: #f5f5f5;">'
        html += '<th style="padding: 8px; text-align: left;">Fecha</th>'
        html += '<th style="padding: 8px; text-align: left;">Tipo</th>'
        html += '<th style="padding: 8px; text-align: right;">Monto</th>'
        html += '<th style="padding: 8px; text-align: center;">Estado</th>'
        html += '<th style="padding: 8px; text-align: left;">Descripción</th>'
        html += '</tr>'

        for t in transacciones:
            estado_icon = '✓' if t.exitosa else ('✗' if t.exitosa is False else '⏳')
            color = 'green' if t.exitosa else ('red' if t.exitosa is False else 'orange')

            html += '<tr style="border-bottom: 1px solid #ddd;">'
            html += f'<td style="padding: 8px;">{t.creado_en.strftime("%d/%m/%Y %H:%M")}</td>'
            html += f'<td style="padding: 8px;">{t.get_tipo_display()}</td>'
            html += f'<td style="padding: 8px; text-align: right;">${t.monto}</td>'
            html += f'<td style="padding: 8px; text-align: center; color: {color};">{estado_icon}</td>'
            html += f'<td style="padding: 8px;"><small>{t.descripcion}</small></td>'
            html += '</tr>'

        html += '</table>'

        return format_html(html)
    transacciones_historial.short_description = 'Historial de Transacciones'

    # ==========================================================
    # ACCIONES PERSONALIZADAS
    # ==========================================================

    def marcar_como_completado(self, request, queryset):
        """Marca pagos seleccionados como completados"""
        exitosos = 0
        errores = 0

        for pago in queryset:
            try:
                if pago.estado == EstadoPago.PENDIENTE or pago.estado == EstadoPago.PROCESANDO:
                    pago.marcar_completado(verificado_por=request.user)
                    exitosos += 1
                else:
                    errores += 1
            except Exception as e:
                logger.error(f"Error al completar pago {pago.pk}: {e}")
                errores += 1

        if exitosos > 0:
            self.message_user(
                request,
                f"✅ {exitosos} pago(s) marcado(s) como completado",
                messages.SUCCESS
            )

        if errores > 0:
            self.message_user(
                request,
                f"⚠️ {errores} pago(s) no pudo(ieron) ser completado(s)",
                messages.WARNING
            )

    marcar_como_completado.short_description = "✓ Marcar como completado"

    def verificar_transferencia(self, request, queryset):
        """Verifica y completa transferencias"""
        verificados = 0

        for pago in queryset.filter(metodo_pago__tipo=TipoMetodoPago.TRANSFERENCIA):
            try:
                if pago.estado == EstadoPago.PENDIENTE:
                    pago.marcar_completado(verificado_por=request.user)
                    verificados += 1
            except Exception as e:
                logger.error(f"Error al verificar transferencia {pago.pk}: {e}")

        self.message_user(
            request,
            f"✅ {verificados} transferencia(s) verificada(s) y completada(s)",
            messages.SUCCESS
        )

    verificar_transferencia.short_description = "🏦 Verificar transferencias"

    def procesar_reembolso_total(self, request, queryset):
        """Procesa reembolso total de pagos seleccionados"""
        reembolsados = 0
        errores = 0

        for pago in queryset:
            try:
                if pago.estado == EstadoPago.COMPLETADO:
                    pago.procesar_reembolso(motivo='Reembolso procesado desde admin')
                    reembolsados += 1
                else:
                    errores += 1
            except Exception as e:
                logger.error(f"Error al reembolsar pago {pago.pk}: {e}")
                errores += 1

        if reembolsados > 0:
            self.message_user(
                request,
                f"✅ {reembolsados} pago(s) reembolsado(s)",
                messages.SUCCESS
            )

        if errores > 0:
            self.message_user(
                request,
                f"⚠️ {errores} pago(s) no pudo(ieron) ser reembolsado(s)",
                messages.WARNING
            )

    procesar_reembolso_total.short_description = "↩ Procesar reembolso total"

    def marcar_como_fallido(self, request, queryset):
        """Marca pagos como fallidos"""
        fallidos = 0

        for pago in queryset:
            try:
                if pago.estado not in [EstadoPago.COMPLETADO, EstadoPago.REEMBOLSADO]:
                    pago.marcar_fallido('Marcado como fallido desde admin')
                    fallidos += 1
            except Exception as e:
                logger.error(f"Error al marcar pago fallido {pago.pk}: {e}")

        self.message_user(
            request,
            f"✅ {fallidos} pago(s) marcado(s) como fallido",
            messages.SUCCESS
        )

    marcar_como_fallido.short_description = "✗ Marcar como fallido"

    def exportar_reporte(self, request, queryset):
        """Exporta reporte de pagos (implementar según necesidad)"""
        self.message_user(
            request,
            "📊 Funcionalidad de exportación próximamente",
            messages.INFO
        )

    exportar_reporte.short_description = "📊 Exportar reporte"

    # ==========================================================
    # PERMISOS Y CONFIGURACIÓN
    # ==========================================================

    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar pagos"""
        return False


# ==========================================================
# 📝 ADMIN: TRANSACCIÓN
# ==========================================================

@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    """Administración de transacciones"""

    list_display = (
        'id',
        'pago_link',
        'tipo',
        'monto',
        'exitosa_display',
        'descripcion_corta',
        'creado_en'
    )

    list_filter = (
        'tipo',
        'exitosa',
        'creado_en'
    )

    search_fields = (
        'pago__referencia',
        'descripcion',
        'codigo_respuesta'
    )

    date_hierarchy = 'creado_en'

    readonly_fields = (
        'pago',
        'tipo',
        'monto',
        'exitosa',
        'descripcion',
        'codigo_respuesta',
        'mensaje_respuesta',
        'metadata',
        'ip_address',
        'user_agent',
        'creado_en'
    )

    def pago_link(self, obj):
        """Link al pago"""
        url = reverse('admin:pagos_pago_change', args=[obj.pago.pk])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            str(obj.pago.referencia)[:8] + '...'
        )
    pago_link.short_description = 'Pago'

    def exitosa_display(self, obj):
        """Estado con ícono"""
        if obj.exitosa is True:
            return format_html('<span style="color: green;">✓ Exitosa</span>')
        elif obj.exitosa is False:
            return format_html('<span style="color: red;">✗ Fallida</span>')
        else:
            return format_html('<span style="color: orange;">⏳ En proceso</span>')
    exitosa_display.short_description = 'Estado'
    exitosa_display.admin_order_field = 'exitosa'

    def descripcion_corta(self, obj):
        """Descripción truncada"""
        if len(obj.descripcion) > 50:
            return f"{obj.descripcion[:50]}..."
        return obj.descripcion
    descripcion_corta.short_description = 'Descripción'

    def has_add_permission(self, request):
        """No permitir crear transacciones manualmente"""
        return False

    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar transacciones"""
        return False


# ==========================================================
# 📊 ADMIN: ESTADÍSTICAS
# ==========================================================

@admin.register(EstadisticasPago)
class EstadisticasPagoAdmin(admin.ModelAdmin):
    """Administración de estadísticas de pagos"""

    list_display = (
        'fecha',
        'total_pagos',
        'pagos_completados',
        'tasa_exito_display',
        'monto_total_display',
        'ticket_promedio_display',
        'actualizado_en'
    )

    list_filter = (
        'fecha',
    )

    date_hierarchy = 'fecha'

    readonly_fields = (
        'fecha',
        'total_pagos',
        'pagos_completados',
        'pagos_pendientes',
        'pagos_fallidos',
        'pagos_reembolsados',
        'monto_total',
        'monto_efectivo',
        'monto_transferencias',
        'monto_tarjetas',
        'monto_reembolsado',
        'ticket_promedio',
        'tasa_exito',
        'resumen_visual',
        'actualizado_en'
    )

    fieldsets = (
        ('Información', {
            'fields': ('fecha', 'actualizado_en')
        }),
        ('Resumen Visual', {
            'fields': ('resumen_visual',)
        }),
        ('Contadores', {
            'fields': (
                'total_pagos',
                'pagos_completados',
                'pagos_pendientes',
                'pagos_fallidos',
                'pagos_reembolsados'
            )
        }),
        ('Montos por Método', {
            'fields': (
                'monto_total',
                'monto_efectivo',
                'monto_transferencias',
                'monto_tarjetas',
                'monto_reembolsado'
            )
        }),
        ('Métricas', {
            'fields': (
                'ticket_promedio',
                'tasa_exito'
            )
        })
    )

    def tasa_exito_display(self, obj):
        """Tasa de éxito con color"""
        color = 'green' if obj.tasa_exito >= 80 else ('orange' if obj.tasa_exito >= 60 else 'red')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            obj.tasa_exito
        )
    tasa_exito_display.short_description = 'Tasa Éxito'
    tasa_exito_display.admin_order_field = 'tasa_exito'

    def monto_total_display(self, obj):
        """Monto total formateado"""
        return format_html('<strong>${:,.2f}</strong>', obj.monto_total)
    monto_total_display.short_description = 'Monto Total'
    monto_total_display.admin_order_field = 'monto_total'

    def ticket_promedio_display(self, obj):
        """Ticket promedio formateado"""
        return f"${obj.ticket_promedio:,.2f}"
    ticket_promedio_display.short_description = 'Ticket Promedio'
    ticket_promedio_display.admin_order_field = 'ticket_promedio'

    def resumen_visual(self, obj):
        """Resumen visual con gráficos"""
        # Calcular porcentajes
        total = obj.total_pagos if obj.total_pagos > 0 else 1
        pct_completados = (obj.pagos_completados / total) * 100
        pct_pendientes = (obj.pagos_pendientes / total) * 100
        pct_fallidos = (obj.pagos_fallidos / total) * 100

        html = '<div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">'

        # Resumen de pagos
        html += '<h3 style="margin-top: 0;">📊 Resumen del Día</h3>'
        html += '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px;">'

        # Card: Total
        html += f'''
        <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; text-align: center;">
            <div style="font-size: 24px; font-weight: bold; color: #1976d2;">{obj.total_pagos}</div>
            <div style="color: #666; font-size: 12px;">Total Pagos</div>
        </div>
        '''

        # Card: Completados
        html += f'''
        <div style="background: #e8f5e9; padding: 15px; border-radius: 5px; text-align: center;">
            <div style="font-size: 24px; font-weight: bold; color: #4caf50;">{obj.pagos_completados}</div>
            <div style="color: #666; font-size: 12px;">Completados ({pct_completados:.1f}%)</div>
        </div>
        '''

        # Card: Fallidos
        html += f'''
        <div style="background: #ffebee; padding: 15px; border-radius: 5px; text-align: center;">
            <div style="font-size: 24px; font-weight: bold; color: #f44336;">{obj.pagos_fallidos}</div>
            <div style="color: #666; font-size: 12px;">Fallidos ({pct_fallidos:.1f}%)</div>
        </div>
        '''

        html += '</div>'

        # Montos por método
        html += '<h4>💰 Montos por Método de Pago</h4>'
        html += '<div style="margin-bottom: 20px;">'

        total_monto = float(obj.monto_total) if obj.monto_total > 0 else 1

        metodos = [
            ('Efectivo', obj.monto_efectivo, '#4caf50'),
            ('Transferencias', obj.monto_transferencias, '#2196f3'),
            ('Tarjetas', obj.monto_tarjetas, '#9c27b0')
        ]

        for nombre, monto, color in metodos:
            if monto and monto > 0:
                porcentaje = (float(monto) / total_monto) * 100
                html += f'''
                <div style="margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>{nombre}</span>
                        <span style="font-weight: bold;">${monto:,.2f} ({porcentaje:.1f}%)</span>
                    </div>
                    <div style="background: #e0e0e0; height: 25px; border-radius: 12px; overflow: hidden;">
                        <div style="background: {color}; height: 100%; width: {porcentaje}%; transition: width 0.3s;"></div>
                    </div>
                </div>
                '''

        html += '</div>'

        # Métricas clave
        html += '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">'

        html += f'''
        <div style="background: #fff3e0; padding: 15px; border-radius: 5px;">
            <div style="color: #666; font-size: 12px; margin-bottom: 5px;">Ticket Promedio</div>
            <div style="font-size: 20px; font-weight: bold; color: #ff9800;">${obj.ticket_promedio:,.2f}</div>
        </div>
        '''

        tasa_color = '#4caf50' if obj.tasa_exito >= 80 else ('#ff9800' if obj.tasa_exito >= 60 else '#f44336')
        html += f'''
        <div style="background: #f3e5f5; padding: 15px; border-radius: 5px;">
            <div style="color: #666; font-size: 12px; margin-bottom: 5px;">Tasa de Éxito</div>
            <div style="font-size: 20px; font-weight: bold; color: {tasa_color};">{obj.tasa_exito:.1f}%</div>
        </div>
        '''

        html += '</div>'
        html += '</div>'

        return format_html(html)
    resumen_visual.short_description = 'Resumen Visual'

    def has_add_permission(self, request):
        """No permitir crear estadísticas manualmente"""
        return False

    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar estadísticas"""
        return False

    actions = ['recalcular_estadisticas']

    def recalcular_estadisticas(self, request, queryset):
        """Recalcula estadísticas seleccionadas"""
        recalculadas = 0

        for estadistica in queryset:
            try:
                EstadisticasPago.calcular_y_guardar(estadistica.fecha)
                recalculadas += 1
            except Exception as e:
                logger.error(f"Error al recalcular estadísticas: {e}")

        self.message_user(
            request,
            f"✅ {recalculadas} estadística(s) recalculada(s)",
            messages.SUCCESS
        )

    recalcular_estadisticas.short_description = "🔄 Recalcular estadísticas"


# ==========================================================
# 📌 CONFIGURACIÓN ADICIONAL DEL ADMIN
# ==========================================================

# Personalizar el título del admin
admin.site.site_header = "Administración de Pagos"
admin.site.site_title = "Sistema de Pagos"
admin.site.index_title = "Panel de Control de Pagos"
