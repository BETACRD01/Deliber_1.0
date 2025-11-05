# pedidos/admin.py (CORREGIDO Y OPTIMIZADO)
"""
Configuración del Admin para Pedidos.

✅ CORRECCIONES APLICADAS:
- Try-except en reverse() para modelos no registrados
- Optimización de queries con select_related/prefetch_related
- Acciones masivas robustas con manejo de errores
- Mejoras visuales con badges y formateo
- Logging mejorado en acciones
- Exportación a CSV mejorada
"""

import logging
import csv
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q, Count, Sum

from .models import Pedido, EstadoPedido, TipoPedido

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# ACCIONES PERSONALIZADAS
# ═══════════════════════════════════════════════════════════════════

def exportar_a_csv(modeladmin, request, queryset):
    """
    ✅ Acción para exportar pedidos a CSV con manejo robusto
    """
    try:
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="pedidos_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Tipo', 'Estado', 'Cliente', 'Email Cliente', 'Proveedor',
            'Repartidor', 'Total', 'Comisión Repartidor', 'Comisión Proveedor',
            'Ganancia App', 'Método Pago', 'Creado', 'Entregado', 'Dirección Entrega'
        ])

        # ✅ Optimizar query para exportación
        pedidos = queryset.select_related(
            'cliente__user',
            'proveedor',
            'repartidor__user'
        )

        exportados = 0
        for pedido in pedidos:
            try:
                writer.writerow([
                    pedido.id,
                    pedido.get_tipo_display(),
                    pedido.get_estado_display(),
                    pedido.cliente.user.get_full_name() if pedido.cliente else '-',
                    pedido.cliente.user.email if pedido.cliente else '-',
                    pedido.proveedor.nombre if pedido.proveedor else '-',
                    pedido.repartidor.user.get_full_name() if pedido.repartidor else 'Sin asignar',
                    f"${pedido.total}",
                    f"${pedido.comision_repartidor}",
                    f"${pedido.comision_proveedor}",
                    f"${pedido.ganancia_app}",
                    pedido.get_metodo_pago_display(),
                    pedido.creado_en.strftime('%Y-%m-%d %H:%M:%S'),
                    pedido.fecha_entregado.strftime('%Y-%m-%d %H:%M:%S') if pedido.fecha_entregado else '-',
                    pedido.direccion_entrega
                ])
                exportados += 1
            except Exception as e:
                logger.error(f"Error exportando pedido #{pedido.id}: {e}")
                continue

        modeladmin.message_user(
            request,
            f"✅ {exportados} pedido(s) exportado(s) correctamente.",
            level=messages.SUCCESS
        )

        logger.info(f"[ADMIN] Usuario {request.user.email} exportó {exportados} pedidos a CSV")
        return response

    except Exception as e:
        logger.error(f"[ADMIN] Error en exportación CSV: {e}", exc_info=True)
        modeladmin.message_user(
            request,
            f"❌ Error al exportar: {e}",
            level=messages.ERROR
        )

exportar_a_csv.short_description = "📥 Exportar seleccionados a CSV"


# ═══════════════════════════════════════════════════════════════════
# ADMIN CLASS
# ═══════════════════════════════════════════════════════════════════

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    """
    ✅ Administración completa de pedidos en el panel de Django Admin
    Con optimizaciones y manejo robusto de errores
    """

    # =============================
    # Configuración de listado
    # =============================
    list_display = [
        'id',
        'tipo_badge',
        'estado_badge',
        'cliente_info',
        'proveedor_info',
        'repartidor_info',
        'total_formateado',
        'tiempo_transcurrido_admin',
        'creado_en',
    ]

    list_filter = [
        'tipo',
        'estado',
        'metodo_pago',
        'aceptado_por_repartidor',
        'confirmado_por_proveedor',
        'creado_en',
        'fecha_entregado',
    ]

    search_fields = [
        'id',
        'cliente__user__email',
        'cliente__user__first_name',
        'cliente__user__last_name',
        'proveedor__nombre',
        'repartidor__user__email',
        'repartidor__user__first_name',
        'repartidor__user__last_name',
        'direccion_entrega',
        'descripcion',
    ]

    list_per_page = 25

    date_hierarchy = 'creado_en'

    ordering = ['-creado_en']

    # =============================
    # Configuración de detalle
    # =============================
    fieldsets = (
        ('Información General', {
            'fields': (
                'tipo',
                'estado',
                'descripcion',
                'total',
                'metodo_pago',
            )
        }),
        ('Participantes', {
            'fields': (
                'cliente',
                'proveedor',
                'repartidor',
            )
        }),
        ('Direcciones y Ubicación', {
            'fields': (
                'direccion_origen',
                'latitud_origen',
                'longitud_origen',
                'direccion_entrega',
                'latitud_destino',
                'longitud_destino',
            )
        }),
        ('Control de Estado', {
            'fields': (
                'aceptado_por_repartidor',
                'confirmado_por_proveedor',
                'cancelado_por',
            ),
            'classes': ('collapse',),
        }),
        ('Comisiones y Ganancias', {
            'fields': (
                'comision_repartidor',
                'comision_proveedor',
                'ganancia_app',
            ),
            'classes': ('collapse',),
        }),
        ('Fechas', {
            'fields': (
                'creado_en',
                'actualizado_en',
                'fecha_entregado',
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = [
        'creado_en',
        'actualizado_en',
        'fecha_entregado',
        'comision_repartidor',
        'comision_proveedor',
        'ganancia_app',
    ]

    autocomplete_fields = [
        'cliente',
        'proveedor',
        'repartidor',
    ]

    # =============================
    # Acciones personalizadas
    # =============================
    actions = [
        'marcar_como_en_preparacion',
        'marcar_como_en_ruta',
        'marcar_como_entregado',
        'cancelar_pedidos_seleccionados',
        exportar_a_csv,
        'mostrar_estadisticas',
    ]

    def marcar_como_en_preparacion(self, request, queryset):
        """✅ Marca los pedidos seleccionados como 'En preparación'"""
        actualizados = 0
        errores = []

        for pedido in queryset:
            try:
                if pedido.tipo == TipoPedido.PROVEEDOR and pedido.estado == EstadoPedido.CONFIRMADO:
                    pedido.marcar_en_preparacion()
                    actualizados += 1
                    logger.info(f"[ADMIN] Pedido #{pedido.id} marcado en preparación por {request.user.email}")
                else:
                    errores.append(f"Pedido #{pedido.id}: Estado o tipo inválido")
            except Exception as e:
                errores.append(f"Pedido #{pedido.id}: {str(e)}")
                logger.error(f"[ADMIN] Error actualizando pedido #{pedido.id}: {e}")

        if actualizados > 0:
            self.message_user(
                request,
                f"✅ {actualizados} pedido(s) marcado(s) como 'En preparación'.",
                level=messages.SUCCESS
            )
        if errores:
            self.message_user(
                request,
                f"⚠️ {len(errores)} error(es): {'; '.join(errores[:3])}",
                level=messages.WARNING
            )

    marcar_como_en_preparacion.short_description = "🍳 Marcar como 'En preparación'"

    def marcar_como_en_ruta(self, request, queryset):
        """✅ Marca los pedidos seleccionados como 'En ruta'"""
        actualizados = 0
        errores = []

        for pedido in queryset:
            try:
                if not pedido.repartidor:
                    errores.append(f"Pedido #{pedido.id}: Sin repartidor asignado")
                    continue

                if pedido.estado in [EstadoPedido.EN_PREPARACION, EstadoPedido.CONFIRMADO]:
                    pedido.marcar_en_ruta()
                    actualizados += 1
                    logger.info(f"[ADMIN] Pedido #{pedido.id} marcado en ruta por {request.user.email}")
                else:
                    errores.append(f"Pedido #{pedido.id}: Estado inválido ({pedido.get_estado_display()})")
            except Exception as e:
                errores.append(f"Pedido #{pedido.id}: {str(e)}")
                logger.error(f"[ADMIN] Error actualizando pedido #{pedido.id}: {e}")

        if actualizados > 0:
            self.message_user(
                request,
                f"✅ {actualizados} pedido(s) marcado(s) como 'En ruta'.",
                level=messages.SUCCESS
            )
        if errores:
            self.message_user(
                request,
                f"⚠️ {len(errores)} error(es): {'; '.join(errores[:3])}",
                level=messages.WARNING
            )

    marcar_como_en_ruta.short_description = "🚴 Marcar como 'En ruta'"

    def marcar_como_entregado(self, request, queryset):
        """✅ Marca los pedidos seleccionados como 'Entregado'"""
        actualizados = 0
        errores = []

        for pedido in queryset:
            try:
                if not pedido.repartidor:
                    errores.append(f"Pedido #{pedido.id}: Sin repartidor")
                    continue

                if pedido.estado == EstadoPedido.EN_RUTA:
                    pedido.marcar_entregado()
                    actualizados += 1
                    logger.info(f"[ADMIN] Pedido #{pedido.id} marcado entregado por {request.user.email}")
                else:
                    errores.append(f"Pedido #{pedido.id}: Debe estar 'En ruta'")
            except Exception as e:
                errores.append(f"Pedido #{pedido.id}: {str(e)}")
                logger.error(f"[ADMIN] Error actualizando pedido #{pedido.id}: {e}")

        if actualizados > 0:
            self.message_user(
                request,
                f"✅ {actualizados} pedido(s) marcado(s) como 'Entregado'.",
                level=messages.SUCCESS
            )
        if errores:
            self.message_user(
                request,
                f"⚠️ {len(errores)} error(es): {'; '.join(errores[:3])}",
                level=messages.WARNING
            )

    marcar_como_entregado.short_description = "✅ Marcar como 'Entregado'"

    def cancelar_pedidos_seleccionados(self, request, queryset):
        """✅ Cancela los pedidos seleccionados"""
        cancelados = 0
        errores = []

        for pedido in queryset:
            try:
                # ✅ Usar el método del modelo si existe
                if hasattr(pedido, 'puede_ser_cancelado'):
                    if pedido.puede_ser_cancelado:
                        pedido.cancelar("Cancelado desde admin", actor="admin")
                        cancelados += 1
                        logger.info(f"[ADMIN] Pedido #{pedido.id} cancelado por {request.user.email}")
                    else:
                        errores.append(f"Pedido #{pedido.id}: No puede cancelarse")
                else:
                    # Fallback: verificar estado manualmente
                    if pedido.estado not in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]:
                        pedido.estado = EstadoPedido.CANCELADO
                        pedido.cancelado_por = "admin"
                        pedido.save()
                        cancelados += 1
                    else:
                        errores.append(f"Pedido #{pedido.id}: Ya está {pedido.get_estado_display()}")
            except Exception as e:
                errores.append(f"Pedido #{pedido.id}: {str(e)}")
                logger.error(f"[ADMIN] Error cancelando pedido #{pedido.id}: {e}")

        if cancelados > 0:
            self.message_user(
                request,
                f"✅ {cancelados} pedido(s) cancelado(s).",
                level=messages.SUCCESS
            )
        if errores:
            self.message_user(
                request,
                f"⚠️ {len(errores)} error(es): {'; '.join(errores[:3])}",
                level=messages.WARNING
            )

    cancelar_pedidos_seleccionados.short_description = "❌ Cancelar pedidos seleccionados"

    def mostrar_estadisticas(self, request, queryset):
        """✅ Muestra estadísticas de los pedidos seleccionados"""
        try:
            estadisticas = queryset.aggregate(
                total_pedidos=Count('id'),
                total_ventas=Sum('total'),
                total_comision_repartidores=Sum('comision_repartidor'),
                total_comision_proveedores=Sum('comision_proveedor'),
                total_ganancia_app=Sum('ganancia_app'),
            )

            # Contar por estado
            por_estado = {}
            for estado in EstadoPedido.values:
                count = queryset.filter(estado=estado).count()
                if count > 0:
                    por_estado[EstadoPedido(estado).label] = count

            mensaje = (
                f"📊 Estadísticas de {estadisticas['total_pedidos']} pedidos:\n"
                f"💰 Ventas totales: ${estadisticas['total_ventas'] or 0}\n"
                f"🚴 Comisión repartidores: ${estadisticas['total_comision_repartidores'] or 0}\n"
                f"🏪 Comisión proveedores: ${estadisticas['total_comision_proveedores'] or 0}\n"
                f"📱 Ganancia app: ${estadisticas['total_ganancia_app'] or 0}\n"
                f"📈 Por estado: {', '.join([f'{k}: {v}' for k, v in por_estado.items()])}"
            )

            self.message_user(request, mensaje, level=messages.INFO)
            logger.info(f"[ADMIN] {request.user.email} consultó estadísticas de {estadisticas['total_pedidos']} pedidos")

        except Exception as e:
            self.message_user(
                request,
                f"❌ Error calculando estadísticas: {e}",
                level=messages.ERROR
            )
            logger.error(f"[ADMIN] Error en estadísticas: {e}", exc_info=True)

    mostrar_estadisticas.short_description = "📊 Mostrar estadísticas"

    # =============================
    # Métodos personalizados para display
    # =============================
    def tipo_badge(self, obj):
        """✅ Muestra el tipo de pedido con badge de color"""
        colores = {
            TipoPedido.PROVEEDOR: '#17a2b8',  # Cyan
            TipoPedido.DIRECTO: '#6f42c1',     # Purple
        }
        color = colores.get(obj.tipo, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_tipo_display()
        )
    tipo_badge.short_description = 'Tipo'

    def estado_badge(self, obj):
        """✅ Muestra el estado del pedido con badge de color"""
        colores = {
            EstadoPedido.CONFIRMADO: '#ffc107',      # Amarillo
            EstadoPedido.EN_PREPARACION: '#fd7e14',  # Naranja
            EstadoPedido.EN_RUTA: '#0dcaf0',         # Celeste
            EstadoPedido.ENTREGADO: '#28a745',       # Verde
            EstadoPedido.CANCELADO: '#dc3545',       # Rojo
        }
        color = colores.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'

    def cliente_info(self, obj):
        """✅ Muestra información del cliente con enlace (con try-except)"""
        if not obj.cliente:
            return format_html('<span style="color: #999;">-</span>')

        try:
            # Intentar generar URL al admin de Perfil
            url = reverse('admin:usuarios_perfil_change', args=[obj.cliente.id])
            nombre = obj.cliente.user.get_full_name() or obj.cliente.user.email
            email = obj.cliente.user.email

            return format_html(
                '<a href="{}" title="Ver perfil">{}</a><br>'
                '<small style="color: #6c757d;">{}</small>',
                url,
                nombre,
                email
            )
        except Exception as e:
            # ✅ Fallback si el modelo no está registrado o hay error
            try:
                nombre = obj.cliente.user.get_full_name() or obj.cliente.user.email
                email = obj.cliente.user.email
                return format_html(
                    '{}<br><small style="color: #6c757d;">{}</small>',
                    nombre,
                    email
                )
            except:
                return format_html('<span style="color: #999;">Cliente #{}</span>', obj.cliente.id)

    cliente_info.short_description = 'Cliente'

    def proveedor_info(self, obj):
        """✅ Muestra información del proveedor con enlace (con try-except)"""
        if not obj.proveedor:
            return format_html('<span style="color: #6c757d;">-</span>')

        try:
            # Intentar generar URL al admin de Proveedor
            url = reverse('admin:proveedores_proveedor_change', args=[obj.proveedor.id])
            return format_html(
                '<a href="{}" title="Ver proveedor">{}</a>',
                url,
                obj.proveedor.nombre
            )
        except Exception:
            # ✅ Fallback si el modelo no está registrado
            return format_html('{}', obj.proveedor.nombre)

    proveedor_info.short_description = 'Proveedor'

    def repartidor_info(self, obj):
        """✅ Muestra información del repartidor con enlace (con try-except)"""
        if not obj.repartidor:
            return format_html('<span style="color: #999;">Sin asignar</span>')

        try:
            # Intentar generar URL al admin de Repartidor
            url = reverse('admin:repartidores_repartidor_change', args=[obj.repartidor.id])
            nombre = obj.repartidor.user.get_full_name() or obj.repartidor.user.email

            return format_html(
                '<a href="{}" title="Ver repartidor">{}</a>',
                url,
                nombre
            )
        except Exception:
            # ✅ Fallback si el modelo no está registrado
            try:
                nombre = obj.repartidor.user.get_full_name() or obj.repartidor.user.email
                return format_html('{}', nombre)
            except:
                return format_html('<span style="color: #999;">Repartidor #{}</span>', obj.repartidor.id)

    repartidor_info.short_description = 'Repartidor'

    def total_formateado(self, obj):
        """✅ Muestra el total con formato de moneda"""
        return format_html(
            '<strong style="color: #28a745; font-size: 13px;">${}</strong>',
            obj.total
        )
    total_formateado.short_description = 'Total'

    def tiempo_transcurrido_admin(self, obj):
        """✅ Muestra el tiempo transcurrido desde la creación"""
        try:
            # Usar propiedad del modelo si existe
            if hasattr(obj, 'tiempo_transcurrido'):
                tiempo = obj.tiempo_transcurrido
            else:
                # Calcular manualmente
                delta = timezone.now() - obj.creado_en
                minutos = int(delta.total_seconds() / 60)

                if minutos < 60:
                    tiempo = f"{minutos} min"
                elif minutos < 1440:  # 24 horas
                    horas = minutos // 60
                    tiempo = f"{horas} h"
                else:
                    dias = minutos // 1440
                    tiempo = f"{dias} d"

            # Color según tiempo
            if obj.estado == EstadoPedido.ENTREGADO:
                color = '#28a745'  # Verde
            elif obj.estado == EstadoPedido.CANCELADO:
                color = '#6c757d'  # Gris
            else:
                # Alerta si lleva mucho tiempo
                delta_minutos = int((timezone.now() - obj.creado_en).total_seconds() / 60)
                if delta_minutos > 60:
                    color = '#dc3545'  # Rojo
                elif delta_minutos > 30:
                    color = '#ffc107'  # Amarillo
                else:
                    color = '#17a2b8'  # Azul

            return format_html(
                '<span style="color: {}; font-weight: 500;">{}</span>',
                color,
                tiempo
            )
        except Exception as e:
            logger.error(f"Error calculando tiempo transcurrido para pedido #{obj.id}: {e}")
            return '-'

    tiempo_transcurrido_admin.short_description = 'Tiempo'

    # =============================
    # Métodos de control
    # =============================
    def has_delete_permission(self, request, obj=None):
        """
        ✅ Evita eliminar pedidos entregados o en proceso.
        Solo permite eliminar cancelados o muy antiguos.
        """
        if obj:
            # No permitir eliminar pedidos entregados
            if obj.estado == EstadoPedido.ENTREGADO:
                return False

            # No permitir eliminar pedidos activos
            if hasattr(obj, 'es_pedido_activo') and obj.es_pedido_activo:
                return False

            # Verificar si está en proceso
            if obj.estado in [EstadoPedido.EN_PREPARACION, EstadoPedido.EN_RUTA]:
                return False

        return super().has_delete_permission(request, obj)

    def get_queryset(self, request):
        """✅ Optimiza las queries con select_related"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'cliente__user',
            'proveedor',
            'repartidor__user'
        )

    def get_readonly_fields(self, request, obj=None):
        """
        ✅ Hace ciertos campos de solo lectura después de la creación
        """
        readonly = list(self.readonly_fields)

        if obj:  # Si está editando un pedido existente
            # No permitir cambiar el tipo después de creado
            readonly.append('tipo')

            # Si está entregado, hacer casi todo readonly
            if obj.estado == EstadoPedido.ENTREGADO:
                readonly.extend([
                    'estado',
                    'total',
                    'cliente',
                    'proveedor',
                    'repartidor',
                    'metodo_pago'
                ])

            # Si está cancelado, hacer todo readonly
            if obj.estado == EstadoPedido.CANCELADO:
                readonly.extend([
                    'estado',
                    'descripcion',
                    'total',
                    'cliente',
                    'proveedor',
                    'repartidor'
                ])

        return readonly

    def save_model(self, request, obj, form, change):
        """✅ Hook para logging al guardar desde admin"""
        if not change:
            logger.info(f"[ADMIN] Pedido #{obj.id} creado por {request.user.email}")
        else:
            logger.info(f"[ADMIN] Pedido #{obj.id} actualizado por {request.user.email}")

        super().save_model(request, obj, form, change)

    class Media:
        """Assets CSS/JS adicionales para el admin"""
        css = {
            'all': ('admin/css/pedidos_admin.css',)
        }
