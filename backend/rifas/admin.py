# -*- coding: utf-8 -*-
# rifas/admin.py
"""
Django Admin para Sistema de Rifas

✅ FUNCIONALIDADES:
- Gestión completa de rifas desde el admin
- Botón para realizar sorteo manual
- Vista de participantes elegibles
- Historial de ganadores
- Filtros avanzados
- Acciones masivas
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from .models import Rifa, Participacion, EstadoRifa
from pedidos.models import EstadoPedido
import logging

logger = logging.getLogger('rifas')


# ============================================
# 🎲 ADMIN: RIFA
# ============================================

@admin.register(Rifa)
class RifaAdmin(admin.ModelAdmin):
    """
    Admin personalizado para Rifas

    ✅ CARACTERÍSTICAS:
    - Ver participantes elegibles
    - Realizar sorteo con un clic
    - Filtros por estado, mes, año
    - Campos calculados (participantes, días restantes)
    """

    list_display = [
        'titulo_con_emoji',
        'mes_anio',
        'estado_badge',
        'total_participantes_badge',
        'premio_corto',
        'valor_premio',
        'dias_restantes_badge',
        'ganador_info',
        'acciones_rapidas'
    ]

    list_filter = [
        'estado',
        'anio',
        'mes',
        'fecha_inicio',
    ]

    search_fields = [
        'titulo',
        'descripcion',
        'premio',
        'ganador__email',
        'ganador__first_name',
        'ganador__last_name'
    ]

    readonly_fields = [
        'id',
        'mes',
        'anio',
        'creado_en',
        'actualizado_en',
        'fecha_sorteo',
        'ganador',
        'mostrar_participantes_elegibles',
        'mostrar_estadisticas',
        'creado_por'
    ]

    fieldsets = (
        ('📋 Información Básica', {
            'fields': (
                'id',
                'titulo',
                'descripcion',
                'imagen'
            )
        }),
        ('🎁 Premio', {
            'fields': (
                'premio',
                'valor_premio'
            )
        }),
        ('📅 Fechas', {
            'fields': (
                'fecha_inicio',
                'fecha_fin',
                'fecha_sorteo',
                'mes',
                'anio'
            )
        }),
        ('⚙️ Configuración', {
            'fields': (
                'pedidos_minimos',
                'estado'
            )
        }),
        ('🏆 Ganador', {
            'fields': (
                'ganador',
            ),
            'classes': ('collapse',)
        }),
        ('📊 Estadísticas', {
            'fields': (
                'mostrar_estadisticas',
                'mostrar_participantes_elegibles'
            ),
            'classes': ('collapse',)
        }),
        ('🔒 Auditoría', {
            'fields': (
                'creado_por',
                'creado_en',
                'actualizado_en'
            ),
            'classes': ('collapse',)
        })
    )

    actions = [
        'realizar_sorteo_masivo',
        'finalizar_rifas',
        'cancelar_rifas'
    ]

    # ============================================
    # 🎨 MÉTODOS DE VISUALIZACIÓN
    # ============================================

    def titulo_con_emoji(self, obj):
        """Título con emoji según estado"""
        emojis = {
            EstadoRifa.ACTIVA: '🎲',
            EstadoRifa.FINALIZADA: '✅',
            EstadoRifa.CANCELADA: '❌'
        }
        emoji = emojis.get(obj.estado, '📋')
        return f"{emoji} {obj.titulo}"
    titulo_con_emoji.short_description = 'Rifa'

    def mes_anio(self, obj):
        """Muestra mes y año"""
        return f"{obj.mes_nombre} {obj.anio}"
    mes_anio.short_description = 'Período'

    def estado_badge(self, obj):
        """Badge de estado con colores"""
        colors = {
            EstadoRifa.ACTIVA: '#28a745',
            EstadoRifa.FINALIZADA: '#6c757d',
            EstadoRifa.CANCELADA: '#dc3545'
        }
        color = colors.get(obj.estado, '#6c757d')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'

    def total_participantes_badge(self, obj):
        """Badge con total de participantes"""
        total = obj.total_participantes
        color = '#28a745' if total > 0 else '#dc3545'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">👥 {}</span>',
            color,
            total
        )
    total_participantes_badge.short_description = 'Participantes'

    def premio_corto(self, obj):
        """Premio truncado"""
        if len(obj.premio) > 50:
            return f"{obj.premio[:47]}..."
        return obj.premio
    premio_corto.short_description = 'Premio'

    def dias_restantes_badge(self, obj):
        """Badge con días restantes"""
        if obj.estado != EstadoRifa.ACTIVA:
            return '—'

        dias = obj.dias_restantes

        if dias > 7:
            color = '#28a745'
            icon = '✅'
        elif dias > 3:
            color = '#ffc107'
            icon = '⚠️'
        else:
            color = '#dc3545'
            icon = '🔥'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{} {} días</span>',
            color,
            icon,
            dias
        )
    dias_restantes_badge.short_description = 'Días Restantes'

    def ganador_info(self, obj):
        """Información del ganador"""
        if not obj.ganador:
            return '—'

        return format_html(
            '🏆 <strong>{}</strong><br>'
            '<small style="color: #666;">{}</small>',
            obj.ganador.get_full_name(),
            obj.ganador.email
        )
    ganador_info.short_description = 'Ganador'

    def acciones_rapidas(self, obj):
        """Botones de acción rápida"""
        if obj.estado == EstadoRifa.ACTIVA:
            url = reverse('admin:rifas_realizar_sorteo', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}" style="background-color: #28a745; '
                'color: white; padding: 5px 10px; text-decoration: none; '
                'border-radius: 3px;">🎲 Sortear</a>',
                url
            )
        elif obj.estado == EstadoRifa.FINALIZADA and obj.ganador:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✅ Sorteada</span>'
            )

        return '—'
    acciones_rapidas.short_description = 'Acciones'

    # ============================================
    # 📊 CAMPOS READONLY PERSONALIZADOS
    # ============================================

    def mostrar_estadisticas(self, obj):
        """Muestra estadísticas detalladas"""
        if not obj.pk:
            return "Guarda la rifa para ver estadísticas"

        total_participantes = obj.total_participantes
        dias_restantes = obj.dias_restantes if obj.esta_activa else 0

        html = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
            <h3 style="margin-top: 0;">📊 Estadísticas</h3>

            <table style="width: 100%;">
                <tr>
                    <td><strong>👥 Participantes Elegibles:</strong></td>
                    <td style="text-align: right;">{total_participantes}</td>
                </tr>
                <tr>
                    <td><strong>📅 Días Restantes:</strong></td>
                    <td style="text-align: right;">{dias_restantes}</td>
                </tr>
                <tr>
                    <td><strong>📋 Pedidos Mínimos:</strong></td>
                    <td style="text-align: right;">{obj.pedidos_minimos}</td>
                </tr>
                <tr>
                    <td><strong>💰 Valor del Premio:</strong></td>
                    <td style="text-align: right;">${obj.valor_premio}</td>
                </tr>
            </table>
        </div>
        """

        return format_html(html)
    mostrar_estadisticas.short_description = 'Estadísticas'

    def mostrar_participantes_elegibles(self, obj):
        """Muestra lista de participantes elegibles"""
        if not obj.pk:
            return "Guarda la rifa para ver participantes"

        participantes = obj.obtener_participantes_elegibles()
        total = participantes.count()

        if total == 0:
            return format_html(
                '<div style="background: #fff3cd; padding: 15px; border-radius: 5px; '
                'border-left: 4px solid #ffc107;">'
                '⚠️ <strong>No hay participantes elegibles aún</strong><br>'
                '<small>Los usuarios deben completar al menos {} pedidos durante el período de la rifa.</small>'
                '</div>',
                obj.pedidos_minimos
            )

        # Mostrar primeros 10 participantes
        lista_html = "<ul style='margin: 10px 0; padding-left: 20px;'>"

        for participante in participantes[:10]:
            elegibilidad = obj.usuario_es_elegible(participante)
            pedidos = elegibilidad['pedidos']

            lista_html += f"""
            <li style="margin: 5px 0;">
                <strong>{participante.get_full_name()}</strong>
                ({participante.email})
                <br>
                <small style="color: #666;">
                    ✅ {pedidos} pedidos completados
                </small>
            </li>
            """

        if total > 10:
            lista_html += f"<li><em>... y {total - 10} participantes más</em></li>"

        lista_html += "</ul>"

        html = f"""
        <div style="background: #d4edda; padding: 15px; border-radius: 5px;
                    border-left: 4px solid #28a745;">
            <h3 style="margin-top: 0;">👥 Participantes Elegibles ({total})</h3>
            {lista_html}
        </div>
        """

        return format_html(html)
    mostrar_participantes_elegibles.short_description = 'Participantes Elegibles'

    # ============================================
    # 🎲 SORTEO MANUAL
    # ============================================

    def get_urls(self):
        """Añade URL personalizada para realizar sorteo"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<uuid:rifa_id>/sortear/',
                self.admin_site.admin_view(self.realizar_sorteo_view),
                name='rifas_realizar_sorteo'
            ),
        ]
        return custom_urls + urls

    def realizar_sorteo_view(self, request, rifa_id):
        """Vista para realizar sorteo manual"""
        rifa = self.get_object(request, rifa_id)

        if not rifa:
            self.message_user(
                request,
                "Rifa no encontrada",
                level=messages.ERROR
            )
            return redirect('admin:rifas_rifa_changelist')

        # Verificar si se puede sortear
        if rifa.estado != EstadoRifa.ACTIVA:
            self.message_user(
                request,
                f"⚠️ No se puede sortear una rifa {rifa.get_estado_display().lower()}",
                level=messages.WARNING
            )
            return redirect('admin:rifas_rifa_change', rifa_id)

        if rifa.ganador:
            self.message_user(
                request,
                "⚠️ Esta rifa ya tiene un ganador",
                level=messages.WARNING
            )
            return redirect('admin:rifas_rifa_change', rifa_id)

        # Confirmar sorteo
        if request.method == 'POST':
            try:
                ganador = rifa.realizar_sorteo()

                if ganador:
                    self.message_user(
                        request,
                        f"🎉 ¡Sorteo realizado! Ganador: {ganador.get_full_name()} ({ganador.email})",
                        level=messages.SUCCESS
                    )

                    logger.info(
                        f"Sorteo manual realizado por {request.user.email} "
                        f"para rifa {rifa.titulo}. Ganador: {ganador.email}"
                    )
                else:
                    self.message_user(
                        request,
                        "⚠️ No hay participantes elegibles para sortear",
                        level=messages.WARNING
                    )

                return redirect('admin:rifas_rifa_change', rifa_id)

            except Exception as e:
                self.message_user(
                    request,
                    f"❌ Error al realizar sorteo: {str(e)}",
                    level=messages.ERROR
                )
                logger.error(f"Error en sorteo manual: {str(e)}")
                return redirect('admin:rifas_rifa_change', rifa_id)

        # Mostrar página de confirmación
        participantes = rifa.obtener_participantes_elegibles()

        context = {
            **self.admin_site.each_context(request),
            'title': f'Realizar Sorteo: {rifa.titulo}',
            'rifa': rifa,
            'total_participantes': participantes.count(),
            'participantes': participantes[:20],  # Primeros 20
            'opts': self.model._meta,
        }

        return render(
            request,
            'admin/rifas/confirmar_sorteo.html',
            context
        )

    # ============================================
    # 📦 ACCIONES MASIVAS
    # ============================================

    @admin.action(description='🎲 Realizar sorteo en rifas seleccionadas')
    def realizar_sorteo_masivo(self, request, queryset):
        """Realiza sorteo en múltiples rifas"""
        rifas_activas = queryset.filter(
            estado=EstadoRifa.ACTIVA,
            ganador__isnull=True
        )

        if not rifas_activas.exists():
            self.message_user(
                request,
                "⚠️ No hay rifas activas sin ganador en la selección",
                level=messages.WARNING
            )
            return

        sorteadas = 0
        sin_participantes = 0

        for rifa in rifas_activas:
            try:
                ganador = rifa.realizar_sorteo()
                if ganador:
                    sorteadas += 1
                else:
                    sin_participantes += 1
            except Exception as e:
                logger.error(f"Error al sortear {rifa.titulo}: {str(e)}")

        mensaje = f"✅ {sorteadas} rifa(s) sorteada(s)"
        if sin_participantes > 0:
            mensaje += f" | ⚠️ {sin_participantes} sin participantes"

        self.message_user(request, mensaje, level=messages.SUCCESS)

    @admin.action(description='✅ Finalizar rifas seleccionadas')
    def finalizar_rifas(self, request, queryset):
        """Finaliza rifas activas"""
        actualizadas = queryset.filter(
            estado=EstadoRifa.ACTIVA
        ).update(estado=EstadoRifa.FINALIZADA)

        self.message_user(
            request,
            f"✅ {actualizadas} rifa(s) finalizada(s)",
            level=messages.SUCCESS
        )

    @admin.action(description='❌ Cancelar rifas seleccionadas')
    def cancelar_rifas(self, request, queryset):
        """Cancela rifas"""
        actualizadas = queryset.filter(
            estado__in=[EstadoRifa.ACTIVA, EstadoRifa.FINALIZADA]
        ).update(estado=EstadoRifa.CANCELADA)

        self.message_user(
            request,
            f"❌ {actualizadas} rifa(s) cancelada(s)",
            level=messages.SUCCESS
        )

    # ============================================
    # 💾 SAVE OVERRIDE
    # ============================================

    def save_model(self, request, obj, form, change):
        """Asigna creado_por automáticamente"""
        if not change:  # Solo en creación
            obj.creado_por = request.user

        super().save_model(request, obj, form, change)

        if not change:
            logger.info(f"Rifa creada por {request.user.email}: {obj.titulo}")


# ============================================
# 🎟️ ADMIN: PARTICIPACIÓN
# ============================================

@admin.register(Participacion)
class ParticipacionAdmin(admin.ModelAdmin):
    """
    Admin para Participaciones en Rifas
    """

    list_display = [
        'usuario_info',
        'rifa_titulo',
        'pedidos_completados_badge',
        'ganador_badge',
        'fecha_registro'
    ]

    list_filter = [
        'ganador',
        'rifa__mes',
        'rifa__anio',
        'fecha_registro'
    ]

    search_fields = [
        'usuario__email',
        'usuario__first_name',
        'usuario__last_name',
        'rifa__titulo'
    ]

    readonly_fields = [
        'id',
        'rifa',
        'usuario',
        'pedidos_completados',
        'ganador',
        'fecha_registro'
    ]

    def has_add_permission(self, request):
        """No permitir crear manualmente"""
        return False

    def has_change_permission(self, request, obj=None):
        """No permitir editar"""
        return False

    def usuario_info(self, obj):
        """Información del usuario"""
        return format_html(
            '<strong>{}</strong><br>'
            '<small style="color: #666;">{}</small>',
            obj.usuario.get_full_name(),
            obj.usuario.email
        )
    usuario_info.short_description = 'Usuario'

    def rifa_titulo(self, obj):
        """Título de la rifa"""
        return obj.rifa.titulo
    rifa_titulo.short_description = 'Rifa'

    def pedidos_completados_badge(self, obj):
        """Badge de pedidos"""
        return format_html(
            '<span style="background-color: #007bff; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">📦 {}</span>',
            obj.pedidos_completados
        )
    pedidos_completados_badge.short_description = 'Pedidos'

    def ganador_badge(self, obj):
        """Badge de ganador"""
        if obj.ganador:
            return format_html(
                '<span style="background-color: #ffd700; color: #000; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">🏆 GANADOR</span>'
            )
        return '—'
    ganador_badge.short_description = 'Resultado'
